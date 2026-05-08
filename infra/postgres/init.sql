create extension if not exists vector;
create extension if not exists pgcrypto;

create table if not exists knowledge_sources (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  source_type text not null,
  url text,
  schedule text,
  enabled boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists knowledge_documents (
  id uuid primary key default gen_random_uuid(),
  source_id uuid references knowledge_sources(id),
  title text not null,
  content text not null,
  content_hash text not null,
  metadata jsonb not null default '{}',
  embedding vector(1024),
  embedding_provider text not null default 'ollama',
  embedding_model text not null default 'mxbai-embed-large',
  created_at timestamptz not null default now()
);

create index if not exists knowledge_documents_embedding_idx
  on knowledge_documents
  using ivfflat (embedding vector_cosine_ops)
  with (lists = 100);

create index if not exists knowledge_documents_metadata_idx
  on knowledge_documents
  using gin (metadata);

create unique index if not exists knowledge_documents_content_hash_idx
  on knowledge_documents (content_hash);
