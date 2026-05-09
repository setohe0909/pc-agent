import asyncio
import signal
import time
import httpx

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.content import chunk_document, content_hash, fetch_source_documents
from app.embedding import OllamaEmbedder
from app.settings import settings
from app.supabase_store import KnowledgeDocument, SupabaseKnowledgeStore


from langfuse.decorators import observe

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
    
    # Notificar a Discord si hay un canal configurado
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


def collect_markets() -> None:
    _run_job("collect_markets", ingest_enabled_sources())


from app.services.trend_service import TrendService

def collect_trends() -> None:
    print("[CRON] Iniciando recoleccion de tendencias diarias...")
    service = TrendService()
    _run_job("collect_trends", service.run_daily_trends())


def sync_mentis() -> None:
    print("Sincronizacion MentisDB pendiente: falta adapter MCP/read-write real.")


def _run_job(name: str, coroutine) -> None:
    try:
        saved = asyncio.run(coroutine)
        print(f"{name}: {saved} documentos/chunks procesados")
    except Exception as exc:
        print(f"{name}: fallo {exc}")


def main() -> None:
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(collect_markets, CronTrigger.from_crontab(settings.market_ingestion_cron))
    scheduler.add_job(collect_trends, CronTrigger.from_crontab(settings.trends_ingestion_cron))
    scheduler.add_job(sync_mentis, CronTrigger.from_crontab(settings.mentis_sync_cron))
    scheduler.start()

    print(
        "Ingestion worker activo",
        {
            "MARKET_INGESTION_CRON": settings.market_ingestion_cron,
            "TRENDS_INGESTION_CRON": settings.trends_ingestion_cron,
            "MENTIS_SYNC_CRON": settings.mentis_sync_cron,
            "EMBEDDING_MODEL": settings.embedding_model,
            "EMBEDDING_DIMENSIONS": settings.embedding_dimensions,
        },
    )

    running = True

    def stop(*_: object) -> None:
        nonlocal running
        running = False

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    while running:
        time.sleep(1)
    scheduler.shutdown()


if __name__ == "__main__":
    main()
