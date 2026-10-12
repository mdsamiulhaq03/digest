import { getApiStatus } from "@/lib/api";

// Proves the proxy path end to end: browser -> Next.js -> FastAPI.
export async function GET() {
  return Response.json({ frontend: "ok", api: await getApiStatus() });
}
