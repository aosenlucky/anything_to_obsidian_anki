import { NextRequest, NextResponse } from "next/server";

import { requireToken } from "@/lib/auth";
import { getSupabaseAdmin } from "@/lib/supabase";

export async function GET(request: NextRequest) {
  const auth = requireToken(request, process.env.AGENT_TOKEN, "AGENT_TOKEN");
  if (!auth.ok) {
    return NextResponse.json({ error: auth.message }, { status: auth.status });
  }

  const url = new URL(request.url);
  const limit = Math.min(Number(url.searchParams.get("limit") || "10") || 10, 50);
  const supabase = getSupabaseAdmin();

  const { data, error } = await supabase
    .from("inbox_items")
    .select("*")
    .eq("status", "queued")
    .order("created_at", { ascending: true })
    .limit(limit);

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json({ items: data || [] });
}
