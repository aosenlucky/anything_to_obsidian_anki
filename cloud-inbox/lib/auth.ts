import { NextRequest } from "next/server";

import { cleanEnvValue } from "@/lib/env";

export function requireToken(request: NextRequest, expected: string | undefined, label: string) {
  const expectedToken = cleanEnvValue(expected);
  const name = label === "INBOX_TOKEN" ? "投递口令" : "本地同步口令";

  if (!expectedToken) {
    return { ok: false, status: 500, message: `${name}尚未在 EdgeOne 环境变量中配置。` };
  }

  const authorization = request.headers.get("authorization") || "";
  const bearer = authorization.toLowerCase().startsWith("bearer ")
    ? authorization.slice(7).trim()
    : "";
  const headerToken = request.headers.get(`x-${label.toLowerCase().replace("_", "-")}`) || "";
  const token = bearer || headerToken;

  if (token.trim() !== expectedToken) {
    return { ok: false, status: 401, message: `${name}不正确，请重新保存后再试。` };
  }

  return { ok: true, status: 200, message: "OK" };
}
