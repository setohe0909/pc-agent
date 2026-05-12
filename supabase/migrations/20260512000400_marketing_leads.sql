-- Migración para tabla de leads calificados
create table if not exists public.marketing_leads (
    id uuid default gen_random_uuid() primary key,
    platform text not null,
    external_user text not null,
    comment_text text,
    intent_score int,
    category text,
    reason text,
    metadata jsonb default '{}'::jsonb,
    created_at timestamptz default now()
);

-- Habilitar RLS
alter table public.marketing_leads enable row level security;

-- Políticas simples para el service role
create policy "Service role can do everything on leads"
    on public.marketing_leads
    for all
    using (true)
    with check (true);
