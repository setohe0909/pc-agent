import asyncio
import signal
import time
import httpx
import uvicorn
from fastapi import FastAPI, BackgroundTasks

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.content import chunk_document, content_hash, fetch_source_documents
from app.embedding import OllamaEmbedder
from app.settings import settings
from app.supabase_store import KnowledgeDocument, SupabaseKnowledgeStore
from app.services.trend_service import TrendService
from app.services.memory_consolidation import MemoryConsolidationService
from langfuse.decorators import observe

# --- Servidor API para ejecuciones manuales ---
app = FastAPI()

@app.post("/run/{target}")
async def run_manual_job(target: str, background_tasks: BackgroundTasks):
    print(f"[API] Solicitud de ejecucion manual recibida para: {target}")
    if target == "markets":
        background_tasks.add_task(ingest_enabled_sources)
    elif target == "trends":
        print("[API] Programando tarea de tendencias en segundo plano...")
        service = TrendService()
        background_tasks.add_task(service.run_daily_trends)
    elif target == "mentis":
        background_tasks.add_task(sync_mentis_async)
    elif target == "consolidation":
        service = MemoryConsolidationService()
        background_tasks.add_task(service.run_consolidation)
    elif target == "all":
        background_tasks.add_task(ingest_enabled_sources)
        service = TrendService()
        background_tasks.add_task(service.run_daily_trends)
    else:
        return {"status": "error", "message": f"Target {target} no valido"}
    return {"status": "triggered", "target": target}

async def sync_mentis_async():
    print("Sincronizacion MentisDB pendiente.")

@observe(name="ingest_enabled_sources")
async def ingest_enabled_sources() -> int:
    store = SupabaseKnowledgeStore(
        url=settings.supabase_url,
        publishable_key=settings.supabase_publishable_key,
        service_role_key=settings.supabase_service_role_key,
    )
    embedder = OllamaEmbedder(
        base_url=settings.ollama_base_url,
        model=settings.embedding_model,
        dimensions=settings.embedding_dimensions,
    )
    sources = await store.list_enabled_sources(settings.ingestion_max_sources_per_run)
    total_saved = 0
    for source in sources:
        try:
            raw_documents = await fetch_source_documents(source, settings.ingestion_max_documents_per_source)
            documents: list[KnowledgeDocument] = []
            for raw_document in raw_documents:
                for chunk in chunk_document(raw_document, settings.ingestion_chunk_chars):
                    if not chunk.content:
                        continue
                    embedding = await embedder.embed(f"{chunk.title}\n\n{chunk.content}")
                    documents.append(
                        KnowledgeDocument(
                            source_id=source.id,
                            title=chunk.title,
                            content=chunk.content,
                            metadata=chunk.metadata,
                            content_hash=content_hash(source.id, chunk.title, chunk.content),
                            embedding=embedding,
                            embedding_model=settings.embedding_model,
                        )
                    )
            saved = await store.upsert_documents(documents)
            total_saved += saved
            print(f"Fuente {source.name}: {saved} documentos/chunks guardados")
        except Exception as e:
            print(f"Error procesando fuente {source.name}: {e}")
    
    if total_saved > 0 and settings.discord_notifications_channel_id:
        await send_discord_notification(
            settings.discord_notifications_channel_id,
            f"✅ **Ingesta completada**: Se han procesado y vectorizado **{total_saved}** nuevos fragmentos de conocimiento."
        )
        
    return total_saved


async def send_discord_notification(channel_id: str, content: str):
    token = settings.discord_bot_token
    if not token:
        return
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    headers = {"Authorization": f"Bot {token}"}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(url, headers=headers, json={"content": content})
    except Exception as e:
        print(f"Error enviando notificacion a Discord: {e}")


# --- Manejadores para el Scheduler (Thread safe) ---
def collect_markets_sync():
    asyncio.run(ingest_enabled_sources())

def collect_trends_sync():
    print("[JOB] Iniciando recoleccion de tendencias via Scheduler...")
    service = TrendService()
    asyncio.run(service.run_daily_trends())

def consolidate_memory_sync():
    print("[JOB] Iniciando consolidacion de memoria via Scheduler...")
    service = MemoryConsolidationService()
    asyncio.run(service.run_consolidation())

def main() -> None:
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(collect_markets_sync, CronTrigger.from_crontab(settings.market_ingestion_cron))
    scheduler.add_job(collect_trends_sync, CronTrigger.from_crontab(settings.trends_ingestion_cron))
    # Consolidacion diaria a las 00:00 UTC
    scheduler.add_job(consolidate_memory_sync, CronTrigger.from_crontab("0 0 * * *"))
    scheduler.start()

    print("Ingestion worker activo con Scheduler y API en puerto 8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
