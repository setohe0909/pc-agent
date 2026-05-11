from app.domain.ports.llm import LLMPort
from app.domain.ports.memory import MemoryPort
from app.domain.ports.marketing import MarketingPort
from app.adapters.marketing import SocialMediaStubAdapter
import json

class MarketingWorkflow:
    def __init__(self, llm_port: LLMPort, memory_port: MemoryPort | None = None, marketing_port: MarketingPort | None = None) -> None:
        self.llm = llm_port
        self.memory = memory_port
        self.marketing = marketing_port or SocialMediaStubAdapter()

    async def execute_marketing_action(self, prompt: str, payload: dict) -> dict:
        sub_command = payload.get("sub_command", "chat")
        
        if sub_command == "respond":
            return await self._respond_to_comments(prompt)
        elif sub_command == "plan":
            return await self._plan_campaign(prompt)
        elif sub_command == "research":
            return await self._research_competitors(prompt)
        elif sub_command == "status":
            return await self._get_status()
        else:
            # Default chat for marketing context
            return await self._marketing_chat(prompt)

    async def _marketing_chat(self, prompt: str) -> dict:
        system_instructions = (
            "Eres un experto en marketing digital y redes sociales (Instagram y TikTok). "
            "Tu tono es siempre empático, positivo y profesional. "
            "Ayudas a planificar campañas, responder comentarios y analizar la competencia."
        )
        full_prompt = f"{system_instructions}\n\nUsuario: {prompt}"
        response = await self.llm.chat(full_prompt)
        return {"status": "success", "message": response}

    async def _respond_to_comments(self, prompt: str) -> dict:
        # 1. Obtener comentarios (usando el stub por ahora)
        comments = await self.marketing.get_comments("instagram", "latest_post")
        
        responses = []
        for comment in comments:
            # 2. Generar respuesta empática con LLM
            response_prompt = (
                f"Actúa como un Community Manager empático y positivo. "
                f"Genera una respuesta corta y amable para este comentario de un cliente: \"{comment['text']}\". "
                f"Usa emojis si es apropiado."
            )
            reply_text = await self.llm.chat(response_prompt)
            
            # 3. Publicar respuesta (stub)
            await self.marketing.reply_to_comment("instagram", comment['id'], reply_text)
            responses.append({"comment": comment['text'], "reply": reply_text})

        summary = "He respondido a los comentarios recientes de Instagram de manera empática:\n\n"
        for r in responses:
            summary += f"- **Comentario:** {r['comment']}\n  **Respuesta:** {r['reply']}\n"
            
        return {"status": "success", "message": summary}

    async def _plan_campaign(self, prompt: str) -> dict:
        # Enriquecer con insights de diseño, temporada y tendencias (simulado o desde memoria)
        insights = "Tendencias actuales: Minimalismo, colores pastel, sostenibilidad. Temporada: Primavera."
        
        plan_prompt = (
            f"Basado en este tipo de marca y los siguientes insights:\n{insights}\n\n"
            f"El usuario solicita: {prompt}\n\n"
            f"Genera una planificación de campaña detallada para Instagram y TikTok con propuestas de posts, reels y fechas."
        )
        plan = await self.llm.chat(plan_prompt)
        
        return {"status": "success", "message": f"## 📅 Propuesta de Campaña\n\n{plan}"}

    async def _research_competitors(self, prompt: str) -> dict:
        competitor = prompt.replace("research ", "").strip() or "competidor_generico"
        data = await self.marketing.get_competitor_data("instagram", competitor)
        
        research_prompt = (
            f"Analiza los siguientes datos del competidor '{competitor}':\n{json.dumps(data)}\n\n"
            f"Propón una estrategia de campaña para superarlos basada en sus debilidades o aciertos."
        )
        research = await self.llm.chat(research_prompt)
        
        return {"status": "success", "message": f"## 🔍 Análisis de Competencia: {competitor}\n\n{research}"}

    async def _get_status(self) -> dict:
        # Simular chequeo de cuentas conectadas
        status_report = (
            "**Estado del Sub-Agente !marketer**\n"
            "✅ Conexión Instagram: Activa (Cuenta: @brand_oficial)\n"
            "✅ Conexión TikTok: Activa (Cuenta: @brand_tok)\n"
            "🧠 Modo: Empático & Positivo\n"
            "📅 Próxima campaña programada: Ninguna"
        )
        return {"status": "success", "message": status_report}
