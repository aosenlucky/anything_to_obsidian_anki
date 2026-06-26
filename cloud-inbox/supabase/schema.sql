create extension if not exists pgcrypto;

create table if not exists public.inbox_items (
  id uuid primary key default gen_random_uuid(),
  title text,
  source_type text not null default 'manual'
    check (source_type in ('book', 'article', 'video', 'course', 'conversation', 'manual')),
  raw_input text not null,
  my_intent text,
  domain_hint text,
  source_url text,
  content_hash text not null unique,
  status text not null default 'queued'
    check (status in ('queued', 'claimed', 'processed', 'failed')),
  source_path text,
  note_paths jsonb,
  error text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  claimed_at timestamptz,
  processed_at timestamptz
);

create index if not exists inbox_items_status_created_idx
  on public.inbox_items (status, created_at);

alter table public.inbox_items enable row level security;

drop policy if exists "No direct anon access" on public.inbox_items;
create policy "No direct anon access"
  on public.inbox_items
  for all
  using (false)
  with check (false);
