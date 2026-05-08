drop index if exists public.knowledge_documents_embedding_idx;
drop function if exists public.match_knowledge_documents(extensions.vector, int, jsonb);

alter table public.knowledge_documents
  drop column if exists embedding;

alter table public.knowledge_documents
  add column embedding extensions.vector(1024),
  add column if not exists embedding_provider text not null default 'ollama',
  add column if not exists embedding_model text not null default 'mxbai-embed-large';

create index if not exists knowledge_documents_embedding_idx
  on public.knowledge_documents
  using ivfflat (embedding extensions.vector_cosine_ops)
  with (lists = 100);

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
