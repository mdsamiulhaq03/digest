import { type ApiStatus, getApiStatus } from "@/lib/api";

const LABELS: Record<ApiStatus, string> = {
  ok: "Service is running",
  not_ready: "Service is starting up",
  unreachable: "Service can't be reached",
};

export async function ApiStatusLine() {
  const status = await getApiStatus();
  return (
    <p className={`state ${status === "ok" ? "state-ready" : "state-failed"}`}>
      {LABELS[status]}
    </p>
  );
}
