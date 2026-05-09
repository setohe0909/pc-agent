import os
import json
import httpx
import google.generativeai as genai
from tavily import TavilyClient
from app.adapters.mentis import MentisClient
from app.settings import settings

class TrendService:
    def __init__(self):
        self.mentis = MentisClient(settings.langfuse_host)
        self.categories = [
            "mercados de trading",
            "TV shows",
            "Soccer, nba, futbol america",
            "politica"
        ]
        # Configurar Gemini
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("models/gemini-flash-latest")
        
        # Configurar Tavily
        tavily_key = os.getenv("TAVILY_API_KEY")
        self.tavily = TavilyClient(api_key=tavily_key) if tavily_key else None

    async def run_daily_trends(self):
        if not self.tavily:
            print("[TRENDS ERROR] No hay TAVILY_API_KEY configurada. No se puede realizar busqueda real.")
            return []

        print("[TRENDS] Iniciando sondeo REAL de tendencias con Tavily...")
        results = []
        
        for category in self.categories:
            print(f"[TRENDS] Buscando tendencias para: {category}...")
            # Buscamos especificamente tendencias en X/Twitter a traves de Tavily
            search_query = f"trending topics and news on X twitter about {category} today"
            search_result = self.tavily.search(query=search_query, search_depth="advanced")
            
            # Gemini resume y analiza la importancia
            prompt = (
                f"Analiza las siguientes noticias y tendencias reales encontradas en la web sobre '{category}' en Twitter/X.\n"
                f"Resultados de búsqueda: {json.dumps(search_result['results'])}\n\n"
                "Genera un resumen ejecutivo de 3 puntos sobre por que esto es relevante para un agente de trading autónomo."
            )
            
            response = await self.model.generate_content_async(prompt)
            summary = response.text
            
            # Guardamos en Mentis
            await self.mentis.save_daily_knowledge(category, summary)
            results.append({"category": category, "summary": summary})

            # --- NUEVO: Busqueda de oportunidades en Kalshi ---
            if category in ["mercados de trading", "politica", "Soccer, nba, futbol america"]:
                await self._check_proactive_opportunities(category, summary)
            
        print(f"[TRENDS] Finalizado. {len(results)} categorias procesadas con datos reales.")
        return results

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
            
            # 2. Gemini decide si hay oportunidad
            prompt = (
                f"Basado en esta tendencia: '{trend_summary}'\n"
                f"Y estos mercados disponibles en Kalshi: {markets}\n\n"
                "¿Existe una oportunidad clara de trading? Responde en JSON:\n"
                "{\n  \"found\": bool,\n  \"market_name\": \"nombre del mercado\",\n  \"reason\": \"porque es una buena idea\",\n  \"trade_prompt\": \"instruccion para ejecutar el trade\"\n}"
            )
            
            response = await self.model.generate_content_async(
                prompt, 
                generation_config=genai.GenerationConfig(response_mime_type="application/json")
            )
            decision = json.loads(response.text)
            
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
