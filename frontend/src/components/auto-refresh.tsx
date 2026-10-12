"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

/** Re-renders the current page from the server every intervalMs, for as long
 * as it is on screen. The page stops rendering it once there is nothing left
 * to wait for, which stops the polling. */
export function AutoRefresh({ intervalMs }: { intervalMs: number }) {
  const router = useRouter();
  useEffect(() => {
    const timer = setInterval(() => router.refresh(), intervalMs);
    return () => clearInterval(timer);
  }, [router, intervalMs]);
  return null;
}
