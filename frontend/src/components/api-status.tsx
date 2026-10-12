import { type ApiStatus, getApiStatus } from "@/lib/api";

const LABELS: Record<ApiStatus, string> = {
  ok: "ok",
  not_ready: "not ready",
  unreachable: "unreachable",
};

export async function ApiStatusLine() {
  const status = await getApiStatus();
  const colour = status === "ok" ? "text-green-600" : "text-red-600";
  return (
    <p>
      API: <span className={colour}>{LABELS[status]}</span>
    </p>
  );
}
