"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

/** A band link that knows when it is the current page. Documents owns every
 * document and job page beneath it, but not the new-document form. */
export function NavLink({ href, children }: { href: string; children: React.ReactNode }) {
  const pathname = usePathname();
  const current =
    href === "/"
      ? pathname === "/" ||
        (pathname.startsWith("/documents/") && pathname !== "/documents/new") ||
        pathname.startsWith("/jobs/")
      : pathname === href;
  return (
    <Link
      href={href}
      aria-current={current ? "page" : undefined}
      className={`border-b-2 py-1 font-medium transition-colors ${
        current ? "border-on-band" : "border-transparent text-on-band-muted hover:text-on-band"
      }`}
    >
      {children}
    </Link>
  );
}
