create extension if not exists pgcrypto with schema extensions;

create table if not exists public.mentis_memory (
  id uuid primary key default gen_random_uuid(),
  category text not null,
  summary text not null,
  metadata jsonb not null default '{}',
  created_at timestamptz not null default now()
);

create index if not exists mentis_memory_category_idx
  on public.mentis_memory (category);

create index if not exists mentis_memory_created_at_idx
  on public.mentis_memory (created_at desc);

create index if not exists mentis_memory_metadata_type_idx
  on public.mentis_memory ((metadata->>'type'));

create index if not exists mentis_memory_metadata_idx
  on public.mentis_memory using gin (metadata);

alter table public.mentis_memory enable row level security;

drop policy if exists "service role manages mentis memory" on public.mentis_memory;
create policy "service role manages mentis memory"
  on public.mentis_memory
  for all
  to service_role
  using (true)
  with check (true);

create table if not exists public.trading_audit_events (
  id uuid primary key default gen_random_uuid(),
  event_type text not null,
  actor_id text,
  order_id text,
  ticker text,
  environment text not null default 'paper',
  payload jsonb not null default '{}',
  created_at timestamptz not null default now()
);

create index if not exists trading_audit_events_created_at_idx
  on public.trading_audit_events (created_at desc);

create index if not exists trading_audit_events_order_id_idx
  on public.trading_audit_events (order_id);

create index if not exists trading_audit_events_ticker_idx
  on public.trading_audit_events (ticker);

alter table public.trading_audit_events enable row level security;

drop policy if exists "service role manages trading audit events" on public.trading_audit_events;
create policy "service role manages trading audit events"
  on public.trading_audit_events
  for all
  to service_role
  using (true)
  with check (true);
