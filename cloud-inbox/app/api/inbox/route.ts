import { NextRequest, NextResponse } from "next/server";

import { requireToken } from "@/lib/auth";
import { contentHash } from "@/lib/hash";
import { getSupabaseAdmin } from "@/lib/supabase";

const SOURCE_TYPES = new Set(["book", "article", "video", "course", "conversation", "manual"]);

export async function POST(request: NextRequest) {
  const auth = requireToken(request, process.env.INBOX_TOKEN, "INBOX_TOKEN");
  if (!auth.ok) {
    return NextResponse.json({ error: auth.message }, { status: auth.status });
  }

  const body = await request.json().catch(() => null);
  if (!body || typeof body.raw_input !== "string" || body.raw_input.trim().length === 0) {
    return NextResponse.json({ error: "raw_input is required" }, { status: 400 });
  }

  const sourceType = typeof body.source_type === "string" && SOURCE_TYPES.has(body.source_type)
    ? body.source_type
    : "manual";

  const payload = {
    title: textOrNull(body.title),
    source_type: sourceType,
    raw_input: body.raw_input.trim(),
    my_intent: textOrNull(body.my_intent),
    domain_hint: textOrNull(body.domain_hint),
    source_url: textOrNull(body.source_url)
  };
  const hash = contentHash(payload);
  const supabase = getSupabaseAdmin();

  const { data: existing, error: findError } = await supabase
    .from("inbox_items")
    .select("id,status,created_at")
    .eq("content_hash", hash)
    .maybeSingle();

  if (findError) {
    return supabaseError(findError.message);
  }

  if (existing) {
    return NextResponse.json({ ok: true, duplicate: true, item: existing });
  }

  const { data, error } = await supabase
    .from("inbox_items")
    .insert({ ...payload, content_hash: hash, status: "queued" })
    .select("id,status,created_at")
    .single();

  if (error) {
    return supabaseError(error.message);
  }

  return NextResponse.json({ ok: true, duplicate: false, item: data });
}

function supabaseError(message: string) {
  const normalized = message.toLowerCase();
  const error = normalized.includes("invalid api key")
    ? "Supabase API key 无效。请检查 EdgeOne 环境变量 SUPABASE_SERVICE_ROLE_KEY，值应为 Supabase 的 Secret key 或 service_role key，不要填 Published/anon key。"
    : message;

  return NextResponse.json({ error }, { status: 500 });
}

function textOrNull(value: unknown) {
  if (typeof value !== "string") return null;
  const trimmed = value.trim();
  return trimmed ? trimmed : null;
}
