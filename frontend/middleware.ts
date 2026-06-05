import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const ROLE_ROUTES: Record<string, string[]> = {
  "/patient": ["patient"],
  "/donor": ["donor"],
  "/coordinator": ["coordinator"],
  "/hospital": ["hospital"],
  "/admin": ["admin"],
};

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  
  // Exclude static and api paths
  if (
    pathname.startsWith("/_next") ||
    pathname.startsWith("/api") ||
    pathname.includes("favicon.ico")
  ) {
    return NextResponse.next();
  }

  // Get auth cookies
  const token = request.cookies.get("veinconnect-token")?.value;
  const role = request.cookies.get("veinconnect-role")?.value;

  const isAuthPage = pathname === "/login" || pathname === "/signup";
  const isLandingPage = pathname === "/";

  // Redirect to login if accessing guarded routes without token
  if (!token && !isAuthPage && !isLandingPage) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  // Redirect to role dashboard if logged in and hitting auth pages
  if (token && isAuthPage) {
    const defaultDashboard = role ? `/${role}/dashboard` : "/";
    return NextResponse.redirect(new URL(defaultDashboard, request.url));
  }

  // Perform route role guard validations
  if (token && role) {
    for (const routePrefix in ROLE_ROUTES) {
      if (pathname.startsWith(routePrefix)) {
        const allowedRoles = ROLE_ROUTES[routePrefix];
        if (!allowedRoles.includes(role)) {
          // Wrong role accessing route, redirect back to own dashboard
          return NextResponse.redirect(new URL(`/${role}/dashboard`, request.url));
        }
      }
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/login",
    "/signup",
    "/patient/:path*",
    "/donor/:path*",
    "/coordinator/:path*",
    "/hospital/:path*",
    "/admin/:path*",
  ],
};
