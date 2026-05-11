import os
import json
import httpx
import google.generativeai as genai
from tavily import TavilyClient
from app.adapters.mentis import MentisClient
from app.settings import settings

class TrendService:
    def __init__(self):
        print("[TRENDS] Inicializando TrendService...")
        self.settings = settings
        self.mentis = MentisClient(settings.langfuse_host)
        self.categories = [
            "mercados de trading",
            "TV shows",
            "Soccer, nba, futbol america",
            "politica"
        ]
        # Configurar Gemini
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        print(f"[TRENDS] Configurando Gemini (API Key: {'Presente' if api_key else 'Faltante'})...")
        genai.configure(api_key=api_key)
        
        # Configurar Tavily
        tavily_key = os.getenv("TAVILY_API_KEY")
        print(f"[TRENDS] Configurando Tavily (API Key: {'Presente' if tavily_key else 'Faltante'})...")
        self.tavily = TavilyClient(api_key=tavily_key) if tavily_key else None
        print("[TRENDS] TrendService inicializado correctamente.")

    async def _generate_content_with_fallback(self, prompt: str, response_mime_type: str = "text/plain"):
        """Intenta generar contenido probando varios modelos por si hay limites de cuota"""
        import asyncio
        model_candidates = [
            "models/gemini-2.0-flash-lite",
            "models/gemini-3.1-flash-lite",
            "models/gemini-flash-latest",
            "models/gemini-pro-latest"
        ]
        
        last_error = None
        for model_name in model_candidates:
            try:
                print(f"[LLM] Intentando con modelo: {model_name}...")
                model = genai.GenerativeModel(model_name)
                gen_config = genai.GenerationConfig(response_mime_type=response_mime_type)
                response = await model.generate_content_async(prompt, generation_config=gen_config)
                return response.text
            except Exception as e:
                last_error = e
                if "429" in str(e):
                    print(f"[LLM WARNING] Cuota agotada en {model_name}. Reintentando en 2s con el siguiente...")
                    await asyncio.sleep(2)
                    continue
                else:
                    raise e
        raise last_error

    async def run_daily_trends(self):
        print("[TRENDS] Iniciando ejecucion de run_daily_trends...")
        if not self.tavily:
            print("[TRENDS ERROR] No hay TAVILY_API_KEY configurada.")
            return []

        print("[TRENDS] Iniciando sondeo REAL de tendencias con Tavily...")
        results = []
        
        try:
            for category in self.categories:
                print(f"[TRENDS] Buscando tendencias para: {category}...")
                search_query = f"trending topics and news on X twitter about {category} today"
                search_result = self.tavily.search(query=search_query, search_depth="advanced")
                
                prompt = (
                    f"Analiza estas noticias reales sobre '{category}' en Twitter/X:\n"
                    f"{json.dumps(search_result['results'])}\n\n"
                    "Genera un resumen ejecutivo de 3 puntos para un agente de trading."
                )
                
                # Usamos el nuevo helper con fallback
                summary = await self._generate_content_with_fallback(prompt)
                
                await self.mentis.save_daily_knowledge(category, summary)
                results.append({"category": category, "summary": summary})

                if category in ["mercados de trading", "politica", "Soccer, nba, futbol america"]:
                    await self._check_proactive_opportunities(category, summary)
            
            # --- Notificacion de Exito ---
            msg = f"📊 **Análisis de Tendencias Completado**\nSe han procesado **{len(results)}** categorías.\n"
            for r in results:
                msg += f"• *{r['category']}*: ✅\n"
            await self._send_notification(msg)

        except Exception as e:
            await self._send_notification(f"❌ **Error en Análisis de Tendencias**: {str(e)}")
            print(f"[TRENDS ERROR] {e}")

        return results

    async def _send_notification(self, content: str):
        """Helper para enviar notificaciones simples de texto"""
        token = settings.discord_bot_token
        channel_id = settings.discord_notifications_channel_id
        
        print(f"[NOTIFY] Intentando enviar a Discord (Canal: {channel_id})...")
        if not token or not channel_id: 
            print(f"[NOTIFY ERROR] Faltan credenciales. Token: {'Presente' if token else 'Faltante'}, Canal: {channel_id}")
            return
        
        url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
        headers = {"Authorization": f"Bot {token}"}
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, headers=headers, json={"content": content})
            print(f"[NOTIFY STATUS] {resp.status_code} - {resp.text}")

    async def _check_proactive_opportunities(self, category: str, trend_summary: str):
        """Busca oportunidades de trading reales basadas en la tendencia"""
        print(f"[OPPORTUNITIES] Buscando matches en Kalshi para {category}...")
        try:
            # 1. Obtenemos mercados reales de Kalshi via Assistant Runtime
            runtime_url = os.getenv("OPEN_CLAW_BASE_URL", "http://assistant-runtime:8100").rstrip("/")
            async with httpx.AsyncClient(timeout=10) as client:
                # El runtime tiene acceso a Kalshi, le pedimos la lista de mercados
                # Si no existe el endpoint, usamos un fallback de mercados comunes
                resp = await client.get(f"{runtime_url}/health") # Por ahora simulamos hasta tener el endpoint de mercados
                markets = ["FED Interest Rate", "NBA Winner", "Nasdaq Close", "Gas Prices"]
            
            # 2. Gemini decide si hay oportunidad (usando fallback)
            prompt = (
                f"Basado en esta tendencia: '{trend_summary}'\n"
                f"Y estos mercados disponibles en Kalshi: {markets}\n\n"
                "¿Existe una oportunidad clara de trading? Responde en JSON:\n"
                "{\n  \"found\": bool,\n  \"market_name\": \"nombre del mercado\",\n  \"reason\": \"porque es una buena idea\",\n  \"trade_prompt\": \"instruccion para ejecutar el trade\"\n}"
            )
            
            response_text = await self._generate_content_with_fallback(
                prompt, 
                response_mime_type="application/json"
            )
            decision = json.loads(response_text)
            
            if decision.get("found"):
                print(f"[ALERT] Oportunidad encontrada: {decision['market_name']}")
                # 3. Enviamos notificacion interactiva al Bot de Discord
                bot_api_url = "http://discord-bot:8001/notify/trade"
                async with httpx.AsyncClient(timeout=5) as client:
                    await client.post(bot_api_url, json={
                        "title": f"💰 OPORTUNIDAD EN {category.upper()}",
                        "message": f"**Mercado:** {decision['market_name']}\n\n**Analisis:** {decision['reason']}\n\n¿Deseas ejecutar esta operacion?",
                        "payload": {
                            "action_type": "trade_decision",
                            "prompt": decision["trade_prompt"],
                            "source": {"platform": "system", "reason": "trend_analysis"}
                        }
                    })
        except Exception as e:
            print(f"[OPPORTUNITIES ERROR] Fallo al buscar oportunidades: {e}")
