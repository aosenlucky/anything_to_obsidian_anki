import "server-only";

import { createClient } from "@supabase/supabase-js";

export type InboxItem = {
  id: string;
  title: string | null;
  source_type: string;
  raw_input: string;
  my_intent: string | null;
  domain_hint: string | null;
  source_url: string | null;
  content_hash: string;
  status: "queued" | "claimed" | "processed" | "failed";
  source_path: string | null;
  note_paths: string[] | null;
  error: string | null;
  created_at: string;
  updated_at: string;
};

export function getSupabaseAdmin() {
  const url = process.env.SUPABASE_URL;
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY;

  if (!url || !key) {
    throw new Error("Supabase environment variables are not configured.");
  }

  return createClient(url, key, {
    auth: {
      persistSession: false,
      autoRefreshToken: false
    }
  });
}
