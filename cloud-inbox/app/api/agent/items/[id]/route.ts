import { NextRequest, NextResponse } from "next/server";

import { requireToken } from "@/lib/auth";
import { getSupabaseAdmin } from "@/lib/supabase";

const STATUSES = new Set(["queued", "claimed", "processed", "failed"]);

export async function PATCH(
  request: NextRequest,
  context: { params: Promise<{ id: string }> }
) {
  const auth = requireToken(request, process.env.AGENT_TOKEN, "AGENT_TOKEN");
  if (!auth.ok) {
    return NextResponse.json({ error: auth.message }, { status: auth.status });
  }

  const { id } = await context.params;
  const body = await request.json().catch(() => null);
  if (!body || typeof body.status !== "string" || !STATUSES.has(body.status)) {
    return NextResponse.json({ error: "valid status is required" }, { status: 400 });
  }

  const patch: Record<string, unknown> = {
    status: body.status,
    updated_at: new Date().toISOString()
  };

  if (body.status === "claimed") patch.claimed_at = new Date().toISOString();
  if (body.status === "processed") patch.processed_at = new Date().toISOString();
  if (typeof body.source_path === "string") patch.source_path = body.source_path;
  if (Array.isArray(body.note_paths)) patch.note_paths = body.note_paths;
  if (typeof body.error === "string") patch.error = body.error.slice(0, 4000);

  const supabase = getSupabaseAdmin();
  const { data, error } = await supabase
    .from("inbox_items")
    .update(patch)
    .eq("id", id)
    .select("id,status,updated_at")
    .single();

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json({ item: data });
}
