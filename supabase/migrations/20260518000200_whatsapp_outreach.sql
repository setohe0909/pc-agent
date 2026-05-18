create extension if not exists pgcrypto with schema extensions;

create table if not exists public.whatsapp_contacts (
  id uuid primary key default gen_random_uuid(),
  phone_number text not null unique,
  display_name text,
  source text not null default 'manual',
  consent_status text not null default 'opted_in',
  tags text[] not null default '{}',
  metadata jsonb not null default '{}',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint whatsapp_contacts_consent_status_check
    check (consent_status in ('opted_in', 'opted_out', 'unknown'))
);

create index if not exists whatsapp_contacts_consent_idx
  on public.whatsapp_contacts (consent_status);

create index if not exists whatsapp_contacts_tags_idx
  on public.whatsapp_contacts using gin (tags);

create table if not exists public.whatsapp_campaigns (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  message_template text not null,
  status text not null default 'draft',
  target_tag text,
  scheduled_for timestamptz,
  recipient_count int not null default 0,
  metadata jsonb not null default '{}',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint whatsapp_campaigns_status_check
    check (status in ('draft', 'queued', 'sending', 'sent', 'paused', 'failed', 'cancelled'))
);

create index if not exists whatsapp_campaigns_status_idx
  on public.whatsapp_campaigns (status);

create index if not exists whatsapp_campaigns_created_at_idx
  on public.whatsapp_campaigns (created_at desc);

alter table public.whatsapp_contacts enable row level security;
alter table public.whatsapp_campaigns enable row level security;

drop policy if exists "service role manages whatsapp contacts" on public.whatsapp_contacts;
create policy "service role manages whatsapp contacts"
  on public.whatsapp_contacts
  for all
  to service_role
  using (true)
  with check (true);

drop policy if exists "service role manages whatsapp campaigns" on public.whatsapp_campaigns;
create policy "service role manages whatsapp campaigns"
  on public.whatsapp_campaigns
  for all
  to service_role
  using (true)
  with check (true);
