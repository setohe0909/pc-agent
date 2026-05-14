# PC Agent

Version: `0.5.0`

PC Agent es una plataforma modular para investigar mercados de Kalshi, acumular
conocimiento en Supabase/pgvector, usar memoria operativa en MentisDB, observar
conversaciones con Langfuse y canalizar decisiones por Discord antes de cualquier
operacion.

## Que Incluye

- UI de control en `http://localhost:8080`.
- API de control para estado, configuracion runtime, Supabase y MentisDB.
- Runtime del asistente basado en **LangGraph** para flujos de estados resilientes.
- Soporte nativo para **Tool Calling** (Function Calling) con Gemini y OpenAI.
- Memoria Proactiva: Consolidación diaria de aprendizajes mediante resúmenes de IA.
- Bot de Discord interactivo con **Buttons** y **Embeds** para aprobaciones y marketing.
- Worker de ingestion que lee fuentes, genera embeddings con Ollama y guarda en Supabase.
- Migraciones Supabase para `knowledge_sources`, `knowledge_documents`, `mentis_memory` (pgvector).
- Docker Compose con perfiles opcionales para Ollama y Langfuse.

## Servicios

- `control-api`: API principal, health checks, configuracion runtime y fuentes de conocimiento.
- `assistant-runtime`: runtime del asistente (LangGraph) y herramientas autónomas.
- `discord-bot`: puente con Discord para solicitudes, investigacion y aprobaciones interactivas.
- `ingestion-worker`: crons de recoleccion, embeddings y **consolidación de memoria**.
- `ui`: consola web estatica estilo shadcn.
- `supabase-vector-db`: Postgres + pgvector local para desarrollo.
- `ollama`: runtime local opcional para embeddings.
- `langfuse-*`: observabilidad self-hosted bajo perfil `observability`.

## Inicio Rapido

1. Copia variables de entorno:

```bash
cp .env.example .env
```

2. Configura al menos:

```text
ADMIN_API_TOKEN=
SUPABASE_URL=
SUPABASE_PUBLISHABLE_KEY=
SUPABASE_SERVICE_ROLE_KEY=
DISCORD_BOT_TOKEN=
DISCORD_REQUESTS_CHANNEL_ID=
DISCORD_NOTIFICATIONS_CHANNEL_ID=
DISCORD_STATUS_CHANNEL_ID=
DISCORD_APPROVER_USER_IDS=
```

3. Levanta servicios base:

```bash
docker compose up --build
```

4. Abre la UI:

```text
http://localhost:8080
```

5. Usa el token admin en la barra lateral para guardar configuracion desde la UI.

## Perfiles Docker

Embeddings con Ollama:

```bash
docker compose --profile embeddings up --build
docker compose exec ollama ollama pull mxbai-embed-large
```

Observabilidad con Langfuse:

```bash
docker compose --profile observability up --build
```

Todo junto:

```bash
docker compose --profile embeddings --profile observability up --build
```

## UI

La consola incluye estas secciones:

- `Resumen`: salud de servicios, Supabase y MentisDB.
- `Discord`: token del bot, canales y usuarios aprobadores.
- `Conocimiento`: alta de fuentes RSS/web/manuales.
- `Configuracion`: URLs y claves runtime, sin exponer secretos.
- `Wiki`: guia rapida de uso dentro del producto.

La configuracion editable se guarda en `runtime-config.json`, excluido de git.
Los secretos se pueden guardar, pero la API solo devuelve si existen o no.

## Supabase PGVector

El proyecto usa Supabase como vector store publico para conocimiento. Tablas:

- `knowledge_sources`: fuentes habilitadas para ingestion.
- `knowledge_documents`: documentos/chunks con embeddings.

Funcion de busqueda:

```sql
public.match_knowledge_documents(query_embedding, match_count, filter)
```

Migraciones principales:

```text
supabase/migrations/20260508000100_vector_knowledge.sql
supabase/migrations/20260508000200_ollama_mxbai_embeddings.sql
supabase/migrations/20260508000300_knowledge_document_hash.sql
```

Para aplicar migraciones:

```bash
npm_config_cache=/private/tmp/pc-agent-npm-cache npx --yes supabase@latest db push --linked --workdir . --yes
```

## Embeddings

Modelo por defecto:

```text
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=mxbai-embed-large
EMBEDDING_DIMENSIONS=1024
OLLAMA_BASE_URL=http://ollama:11434
```

El worker descarga fuentes, extrae texto, divide en chunks, llama a Ollama
`/api/embed` y guarda en Supabase con `content_hash` para evitar duplicados.

## Discord Y Trading

Toda decision de trading y apertura de posicion debe originarse en Discord.
El runtime rechaza `trade_decision` y `open_position` si no incluyen:

- origen `platform=discord`;
- canal `DISCORD_REQUESTS_CHANNEL_ID`;
- aprobacion explicita;
- aprobador incluido en `DISCORD_APPROVER_USER_IDS`, si esa lista esta configurada.

Comandos iniciales:

```text
!ask pregunta general
!research solicitud de investigacion
!approve_trade decision aprobada para evaluar
!picture generacion de imagenes con IA y memoria proactiva
!marketer centro de control de marketing
!coder-web creacion y ajuste de e-commerce (Repo React-TS)
```

Importante: PC Agent `0.2.0` todavia no ejecuta ordenes reales de Kalshi. La
compuerta de seguridad esta lista antes de conectar el adapter de trading.

## MentisDB

MentisDB esta modelado como memoria operativa del asistente. La verificacion actual
detecta disponibilidad, pero la sincronizacion real read/write sigue pendiente de
adapter MCP/HTTP especifico.

Config recomendada:

```text
MENTIS_BASE_URL=http://localhost:9471
```

## Langfuse

Langfuse se levanta con el perfil `observability`. Sirve para revisar conversaciones,
trazas y llamadas a herramientas cuando el adapter de observabilidad este conectado
con claves reales.

## Arquitectura

El proyecto sigue un enfoque Clean/Hexagonal:

- Dominio y casos de uso no dependen de SDKs externos.
- Supabase, Discord, MentisDB, Langfuse, Ollama y Kalshi viven como adaptadores.
- Las reglas de decision de trading viven en el runtime/politicas, no en la UI.

Ver [docs/architecture.md](docs/architecture.md).

## Validacion

Pruebas actuales:

```bash
python3 tests/test_use_cases.py
python3 tests/test_assistant_runtime_gate.py
python3 tests/test_ingestion_worker.py
docker compose --profile observability --profile embeddings config
```

## Roadmap

- [x] Flujos de estados con LangGraph.
- [x] Native Tool Calling (Gemini/LiteLLM).
- [x] Consolidación proactiva de memoria.
- [ ] Adapter Kalshi live con límites de riesgo.
- [ ] UI avanzada para historial de consolidación de memoria.
