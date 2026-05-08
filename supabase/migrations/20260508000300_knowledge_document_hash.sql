alter table public.knowledge_documents
  add column if not exists content_hash text;

update public.knowledge_documents
set content_hash = encode(sha256((id::text || title || content)::bytea), 'hex')
where content_hash is null;

alter table public.knowledge_documents
  alter column content_hash set not null;

create unique index if not exists knowledge_documents_content_hash_idx
  on public.knowledge_documents (content_hash);
