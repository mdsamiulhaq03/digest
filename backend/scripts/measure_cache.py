"""What does the document cache actually save?

Creates documents for a throwaway user, waits for every upload's job to
finish, then reads each document twice: the first read is a cache miss (goes
to Postgres, then stores the result), the second is a hit. Prints both
distributions, split by document type. Needs no direct access to Redis.

    python scripts/measure_cache.py --base-url http://localhost:8000

These are client-side timings, and they carry transport overhead the cache
can't touch (~45 ms from Windows through Docker's port forwarding, and still
~40 ms inside the container for responses larger than one TCP segment). The
honest comparison is server-side: the `duration_ms` on each "request handled"
access-log line. Phase 6 measured cold 10.6 ms vs warm 4.9 ms (median) that way.
"""

import argparse
import asyncio
import time

import httpx
from measure_latency import build_csv, login, summarize

TEXT_BODY = " ".join(["The quick brown fox jumps over the lazy dog."] * 60)
CSV_ROWS_BYTES = 40 * 1024
JOB_POLL_SECONDS = 0.5
JOB_TIMEOUT_SECONDS = 120


async def create_text_documents(
    client: httpx.AsyncClient, headers: dict[str, str], count: int
) -> list[str]:
    ids = []
    for index in range(count):
        response = await client.post(
            "/documents",
            json={"title": f"text {index}", "text": TEXT_BODY},
            headers=headers,
        )
        response.raise_for_status()
        ids = [*ids, response.json()["id"]]
    return ids


async def create_csv_documents(
    client: httpx.AsyncClient, headers: dict[str, str], count: int
) -> list[str]:
    body = build_csv(CSV_ROWS_BYTES)
    accepted = []
    for _ in range(count):
        response = await client.post(
            "/documents/upload",
            files={"file": ("wide.csv", body, "text/csv")},
            headers=headers,
        )
        response.raise_for_status()
        accepted = [*accepted, response.json()]
    await wait_for_jobs(client, headers, [a["status_url"] for a in accepted])
    return [a["document_id"] for a in accepted]


async def wait_for_jobs(
    client: httpx.AsyncClient, headers: dict[str, str], status_urls: list[str]
) -> None:
    deadline = time.monotonic() + JOB_TIMEOUT_SECONDS
    pending = set(status_urls)
    while pending:
        if time.monotonic() > deadline:
            raise TimeoutError(
                f"{len(pending)} jobs still unfinished - is the worker running?"
            )
        states = {
            url: (await client.get(url, headers=headers)).json()["state"]
            for url in pending
        }
        failed = [url for url, state in states.items() if state == "failed"]
        if failed:
            raise RuntimeError(f"jobs failed: {failed}")
        pending = {url for url, state in states.items() if state != "succeeded"}
        if pending:
            await asyncio.sleep(JOB_POLL_SECONDS)


async def time_reads(
    client: httpx.AsyncClient, headers: dict[str, str], ids: list[str]
) -> list[float]:
    samples = []
    for document_id in ids:
        started = time.perf_counter()
        (
            await client.get(f"/documents/{document_id}", headers=headers)
        ).raise_for_status()
        samples = [*samples, (time.perf_counter() - started) * 1000]
    return samples


async def main(base_url: str, per_type: int) -> None:
    async with httpx.AsyncClient(base_url=base_url, timeout=60) as client:
        email, headers = await login(client)
        groups = {
            "text": await create_text_documents(client, headers, per_type),
            "csv (30 columns)": await create_csv_documents(client, headers, per_type),
        }
        # Every document is read once (cold) before any is read again (warm).
        cold = {
            name: await time_reads(client, headers, ids) for name, ids in groups.items()
        }
        warm = {
            name: await time_reads(client, headers, ids) for name, ids in groups.items()
        }

    print(f"\nGET /documents/{{id}}, {per_type} documents of each type")
    for name in groups:
        print(summarize(f"{name} cold (miss)", cold[name]))
        print(summarize(f"{name} warm (hit)", warm[name]))
    print(f"\n(measurement user: {email})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--per-type", type=int, default=25)
    args = parser.parse_args()
    asyncio.run(main(args.base_url, args.per_type))
