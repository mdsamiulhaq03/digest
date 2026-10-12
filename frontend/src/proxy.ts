import { NextResponse, type NextRequest } from "next/server";

import { TOKEN_COOKIE } from "@/lib/session-cookie";

const PUBLIC_PATHS = ["/login", "/register"];

// An optimistic first filter: no cookie, straight to the login page, before
// any rendering. It never checks the token itself - lib/auth.ts does that on
// every API call - and it deliberately doesn't send signed-in users away from
// /login: with an expired token in the cookie, that would loop between the
// two pages.
export function proxy(request: NextRequest) {
  const isPublic = PUBLIC_PATHS.includes(request.nextUrl.pathname);
  if (!isPublic && !request.cookies.has(TOKEN_COOKIE)) {
    return NextResponse.redirect(new URL("/login", request.url));
  }
  return NextResponse.next();
}

export const config = {
  // Not for route handlers, Next.js's own files, or static assets.
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
};
