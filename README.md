# PC Agent

Asistente modular para investigar mercados de Kalshi, operar bajo reglas controladas,
mantener memoria en Mentis, observar conversaciones con Langfuse y exponer una UI de
control.

## Servicios

- `control-api`: API principal y panel de control. Mantiene la configuracion,
  salud de servicios, fuentes de embeddings y verificaciones de Mentis.
- `assistant-runtime`: runtime donde vive el asistente Open-Claw y el router de
  modelos Gemini, MiniMax y GPT.
- `discord-bot`: puente con Discord para solicitudes, notificaciones operativas y
  estado del asistente.
- `ingestion-worker`: crons de recoleccion de mercados, tendencias y fuentes
  externas para Supabase/pgvector.
- `ui`: interfaz web para estado, configuracion, Discord, fuentes de datos y Mentis.
- `langfuse-*`: observabilidad self-hosted para trazas de conversaciones.
- `supabase-vector-db`: base Postgres con pgvector para desarrollo local.
- `ollama`: runtime local opcional para embeddings gratis con `mxbai-embed-large`.

## Inicio rapido

1. Copia `.env.example` a `.env` y completa las credenciales.
2. En Supabase, ejecuta la migracion de pgvector:

```text
infra/supabase/migrations/001_vector_knowledge.sql
```

3. Levanta la plataforma:

```bash
docker compose up --build
```

4. Abre la UI:

```text
http://localhost:8080
```

5. API de control:

```text
http://localhost:8000/health
```

## Arquitectura

La arquitectura sigue un enfoque hexagonal/Clean Architecture:

- El dominio no conoce Docker, HTTP, Discord, Kalshi, Supabase, Langfuse ni SDKs LLM.
- Los casos de uso coordinan decisiones del asistente.
- Los puertos definen capacidades como `KalshiGateway`, `MemoryStore`,
  `EmbeddingKnowledgeBase`, `ConversationTracer` y `NotificationSender`.
- Los adaptadores traducen SDKs externos hacia esos puertos.

Ver [docs/architecture.md](docs/architecture.md).

## Supabase PGVector

El proyecto esta configurado para usar:

```text
NEXT_PUBLIC_SUPABASE_URL=https://gerhikdxsbglfdsupmsi.supabase.co
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=sb_publishable_sV7xhYAjW0gg-2MXGk0MHg_jQ4l9GN9
```

La publishable key sirve para consultas permitidas por RLS. Para que los workers
inserten fuentes, documentos y embeddings hace falta una de estas opciones:

- `SUPABASE_SERVICE_ROLE_KEY` para usar la API de Supabase desde backend.
- `VECTOR_DATABASE_URL` de Postgres para escribir directamente desde workers.

El endpoint `/supabase/verify` revisa si la API REST responde y si la tabla
`knowledge_sources` ya existe.

## Decisiones De Trading

Toda decision de trading y toda apertura de posicion debe originarse en Discord.
El runtime rechaza acciones `trade_decision` y `open_position` si no incluyen:

- origen `platform=discord`;
- canal `DISCORD_REQUESTS_CHANNEL_ID`;
- aprobacion explicita;
- usuario aprobador incluido en `DISCORD_APPROVER_USER_IDS`, cuando esa lista esta configurada.

Comandos iniciales del bot:

```text
!ask pregunta general
!research solicitud de investigacion
!approve_trade decision aprobada para evaluar
```

La implementacion actual todavia no ejecuta ordenes reales de Kalshi; solo deja
la compuerta de seguridad antes de conectar el adapter de trading.

## Embeddings

El modelo por defecto es `mxbai-embed-large` via Ollama:

```text
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=mxbai-embed-large
EMBEDDING_DIMENSIONS=1024
OLLAMA_BASE_URL=http://ollama:11434
```

Para levantar Ollama local:

```bash
docker compose --profile embeddings up ollama
docker compose exec ollama ollama pull mxbai-embed-large
```
