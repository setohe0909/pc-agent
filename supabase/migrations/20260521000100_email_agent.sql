create extension if not exists "pgcrypto";

create table if not exists public.email_bulk_jobs (
  id uuid primary key default gen_random_uuid(),
  provider text not null,
  account_id text,
  template_name text not null,
  template_subject text not null,
  template_body text not null,
  category text not null,
  status text not null check (
    status in ('requires_approval', 'approved', 'queued', 'sending', 'sent', 'failed', 'cancelled')
  ),
  requested_by text,
  approved_by text,
  approved_at timestamptz,
  recipient_count integer not null default 0,
  provider_result jsonb not null default '{}'::jsonb,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.email_bulk_job_recipients (
  id uuid primary key default gen_random_uuid(),
  job_id uuid not null references public.email_bulk_jobs(id) on delete cascade,
  email_id text not null,
  recipient text not null,
  subject text not null default '',
  status text not null default 'pending' check (
    status in ('pending', 'queued', 'sending', 'sent', 'failed', 'skipped')
  ),
  provider_message_id text,
  error_detail text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(job_id, email_id)
);

create table if not exists public.email_audit_events (
  id uuid primary key default gen_random_uuid(),
  job_id uuid references public.email_bulk_jobs(id) on delete set null,
  event_type text not null,
  actor_id text,
  detail text not null,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists email_bulk_jobs_status_idx on public.email_bulk_jobs(status);
create index if not exists email_bulk_jobs_created_at_idx on public.email_bulk_jobs(created_at desc);
create index if not exists email_bulk_job_recipients_job_idx on public.email_bulk_job_recipients(job_id);
create index if not exists email_audit_events_job_idx on public.email_audit_events(job_id);

alter table public.email_bulk_jobs enable row level security;
alter table public.email_bulk_job_recipients enable row level security;
alter table public.email_audit_events enable row level security;

drop policy if exists "service role manages email bulk jobs" on public.email_bulk_jobs;
create policy "service role manages email bulk jobs"
on public.email_bulk_jobs
for all
to service_role
using (true)
with check (true);

drop policy if exists "service role manages email bulk recipients" on public.email_bulk_job_recipients;
create policy "service role manages email bulk recipients"
on public.email_bulk_job_recipients
for all
to service_role
using (true)
with check (true);

drop policy if exists "service role manages email audit events" on public.email_audit_events;
create policy "service role manages email audit events"
on public.email_audit_events
for all
to service_role
using (true)
with check (true);
