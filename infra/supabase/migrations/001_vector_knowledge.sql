create extension if not exists vector with schema extensions;
create extension if not exists pgcrypto with schema extensions;

create table if not exists public.knowledge_sources (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  source_type text not null,
  url text,
  schedule text,
  enabled boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.knowledge_documents (
  id uuid primary key default gen_random_uuid(),
  source_id uuid references public.knowledge_sources(id) on delete set null,
  title text not null,
  content text not null,
  content_hash text not null,
  metadata jsonb not null default '{}',
  embedding extensions.vector(1024),
  embedding_provider text not null default 'ollama',
  embedding_model text not null default 'mxbai-embed-large',
  created_at timestamptz not null default now()
);

create index if not exists knowledge_documents_embedding_idx
  on public.knowledge_documents
  using ivfflat (embedding extensions.vector_cosine_ops)
  with (lists = 100);

create index if not exists knowledge_documents_metadata_idx
  on public.knowledge_documents
  using gin (metadata);

create unique index if not exists knowledge_documents_content_hash_idx
  on public.knowledge_documents (content_hash);

create or replace function public.match_knowledge_documents(
  query_embedding extensions.vector(1024),
  match_count int default 8,
  filter jsonb default '{}'
)
returns table (
  id uuid,
  source_id uuid,
  title text,
  content text,
  metadata jsonb,
  similarity float
)
language plpgsql
stable
as $$
begin
  return query
  select
    d.id,
    d.source_id,
    d.title,
    d.content,
    d.metadata,
    1 - (d.embedding <=> query_embedding) as similarity
  from public.knowledge_documents d
  where d.embedding is not null
    and d.metadata @> filter
  order by d.embedding <=> query_embedding
  limit match_count;
end;
$$;

alter table public.knowledge_sources enable row level security;
alter table public.knowledge_documents enable row level security;

drop policy if exists "read enabled knowledge sources" on public.knowledge_sources;
create policy "read enabled knowledge sources"
  on public.knowledge_sources
  for select
  to anon, authenticated
  using (enabled = true);

drop policy if exists "read knowledge documents" on public.knowledge_documents;
create policy "read knowledge documents"
  on public.knowledge_documents
  for select
  to anon, authenticated
  using (true);

drop policy if exists "service role manages knowledge sources" on public.knowledge_sources;
create policy "service role manages knowledge sources"
  on public.knowledge_sources
  for all
  to service_role
  using (true)
  with check (true);

drop policy if exists "service role manages knowledge documents" on public.knowledge_documents;
create policy "service role manages knowledge documents"
  on public.knowledge_documents
  for all
  to service_role
  using (true)
  with check (true);
