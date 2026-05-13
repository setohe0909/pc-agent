from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.adapters.config.settings import settings

app = FastAPI(title="PC Agent Control API", version="0.6.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.on_event("startup")
async def startup_event():
    from app.adapters.config.runtime_config import RuntimeConfigStore
    from app.adapters.config.settings import settings
    
    store = RuntimeConfigStore()
    s_url = settings.effective("supabase_url")
    s_key = settings.effective("supabase_service_role_key")
    
    if s_url and s_key:
        print(f"[STARTUP] Intentando cargar configuración desde Supabase: {s_url}")
        success = await store.load_from_supabase(s_url, s_key)
        if success:
            print("[STARTUP] Configuración cargada exitosamente desde Supabase.")
        else:
            print("[STARTUP] No se encontró configuración previa en Supabase o hubo un error.")

app.include_router(router)
