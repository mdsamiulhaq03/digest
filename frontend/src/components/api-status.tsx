import { type ApiStatus, getApiStatus } from "@/lib/api";

const LABELS: Record<ApiStatus, string> = {
  ok: "Service is running",
  not_ready: "Service is starting up",
  unreachable: "Service can't be reached",
};

export async function ApiStatusLine() {
  const status = await getApiStatus();
  const dot = status === "ok" ? "bg-settled" : "bg-correction";
  return (
    <p className="inline-flex items-center gap-2">
      <span aria-hidden className={`size-1.5 rounded-full ${dot}`} />
      {LABELS[status]}
    </p>
  );
}
