import { NextRequest } from "next/server";

export function requireToken(request: NextRequest, expected: string | undefined, label: string) {
  if (!expected) {
    return { ok: false, status: 500, message: `${label} is not configured` };
  }

  const authorization = request.headers.get("authorization") || "";
  const bearer = authorization.toLowerCase().startsWith("bearer ")
    ? authorization.slice(7).trim()
    : "";
  const headerToken = request.headers.get(`x-${label.toLowerCase().replace("_", "-")}`) || "";
  const token = bearer || headerToken;

  if (token !== expected) {
    return { ok: false, status: 401, message: "Unauthorized" };
  }

  return { ok: true, status: 200, message: "OK" };
}
