import os
import json
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
            
        print(f"[TRENDS] Finalizado. {len(results)} categorias procesadas con datos reales.")
        return results
