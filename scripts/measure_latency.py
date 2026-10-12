"""Does the API stay responsive while uploads are in flight?

Times GET /health while idle, then again while N large uploads run
concurrently, and prints both distributions. Phase 5's requirement: health
checks must not slow down just because someone else is uploading.

    python scripts/measure_latency.py --base-url http://localhost:8000

Registers a throwaway user (printed at the end) and uploads real files, so run
it against a development stack only.
"""

import argparse
import asyncio
import random
import statistics
import time
import uuid

import httpx

PASSWORD = "measure-latency-password"
PROBE_INTERVAL_SECONDS = 0.1
IDLE_SAMPLES = 20


def build_csv(size_bytes: int) -> bytes:
    columns = 30
    header = ",".join(f"c{i}" for i in range(columns)) + "\n"
    row_count = size_bytes // (columns * 8)
    rows = (
        ",".join(f"{random.random() * 1000:.3f}" for _ in range(columns)) + "\n"
        for _ in range(row_count)
    )
    return (header + "".join(rows)).encode()


async def login(client: httpx.AsyncClient) -> tuple[str, dict[str, str]]:
    email = f"latency-{uuid.uuid4().hex[:8]}@example.com"
    credentials = {"email": email, "password": PASSWORD}
    (await client.post("/auth/register", json=credentials)).raise_for_status()
    response = await client.post("/auth/login", json=credentials)
    response.raise_for_status()
    return email, {"Authorization": f"Bearer {response.json()['access_token']}"}


async def time_health(client: httpx.AsyncClient) -> float:
    started = time.perf_counter()
    (await client.get("/health")).raise_for_status()
    return (time.perf_counter() - started) * 1000


async def probe_until(client: httpx.AsyncClient, done: asyncio.Event) -> list[float]:
    samples: list[float] = []
    while not done.is_set():
        samples = [*samples, await time_health(client)]
        await asyncio.sleep(PROBE_INTERVAL_SECONDS)
    return samples


async def upload(
    client: httpx.AsyncClient, headers: dict[str, str], body: bytes, path: str
) -> tuple[int, float]:
    started = time.perf_counter()
    response = await client.post(
        path,
        files={"file": ("load.csv", body, "text/csv")},
        headers=headers,
    )
    return response.status_code, time.perf_counter() - started


def summarize(label: str, samples: list[float]) -> str:
    ordered = sorted(samples)
    p95 = ordered[max(0, round(len(ordered) * 0.95) - 1)]
    return (
        f"{label:<22} n={len(ordered):<4} median={statistics.median(ordered):7.1f} ms"
        f"   p95={p95:7.1f} ms   max={ordered[-1]:7.1f} ms"
    )


async def run_round(
    uploader: httpx.AsyncClient,
    prober: httpx.AsyncClient,
    headers: dict[str, str],
    body: bytes,
    uploads: int,
    path: str,
) -> tuple[list[int], list[float]]:
    """One burst of concurrent uploads, with /health probed throughout."""
    done = asyncio.Event()
    probe = asyncio.create_task(probe_until(prober, done))
    results = await asyncio.gather(
        *(upload(uploader, headers, body, path) for _ in range(uploads))
    )
    done.set()
    return [status for status, _ in results], await probe


async def main(
    base_url: str, uploads: int, size_mb: float, rounds: int, path: str
) -> None:
    body = build_csv(int(size_mb * 1024 * 1024))
    timeout = httpx.Timeout(120)
    async with (
        httpx.AsyncClient(base_url=base_url, timeout=timeout) as uploader,
        httpx.AsyncClient(base_url=base_url, timeout=timeout) as prober,
    ):
        email, headers = await login(uploader)
        idle = [await time_health(prober) for _ in range(IDLE_SAMPLES)]

        statuses: list[int] = []
        loaded: list[float] = []
        started = time.perf_counter()
        for _ in range(rounds):
            round_statuses, round_samples = await run_round(
                uploader, prober, headers, body, uploads, path
            )
            statuses = [*statuses, *round_statuses]
            loaded = [*loaded, *round_samples]
        wall_seconds = time.perf_counter() - started

    print(
        f"\n{rounds} rounds x {uploads} concurrent uploads of "
        f"{len(body) / 1e6:.1f} MB each"
    )
    print(f"  statuses {sorted(set(statuses))}, all done in {wall_seconds:.1f}s")
    print(summarize("GET /health idle", idle))
    print(summarize("GET /health uploading", loaded))
    print(f"\n(measurement user: {email})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--uploads", type=int, default=10)
    parser.add_argument("--size-mb", type=float, default=9.5)
    parser.add_argument("--rounds", type=int, default=5)
    parser.add_argument("--upload-path", default="/documents/upload")
    args = parser.parse_args()
    asyncio.run(
        main(args.base_url, args.uploads, args.size_mb, args.rounds, args.upload_path)
    )
