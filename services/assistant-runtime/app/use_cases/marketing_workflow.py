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
        elif sub_command == "qualify":
            return await self._qualify_leads()
        elif sub_command == "magnet":
            return await self._process_lead_magnets()
        elif sub_command == "funnel":
            return await self._generate_funnel(prompt)
        elif sub_command == "trends":
            return await self._monitor_trends()
        elif sub_command == "sentiment":
            return await self._analyze_sentiment()
        elif sub_command == "collab":
            return await self._find_collaborations(prompt)
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

    async def _qualify_leads(self) -> dict:
        # 1. Obtener interacciones recientes
        comments = await self.marketing.get_comments("instagram", "latest_post")
        
        leads_found = []
        for comment in comments:
            # 2. Analizar intención con LLM
            analysis_prompt = (
                f"Analiza la intención de compra de este comentario: \"{comment['text']}\". "
                f"Responde en formato JSON con los campos: "
                f"'intent_score' (0-10), 'category' (curious, interested, hot), 'reason' (breve)."
            )
            analysis_text = await self.llm.chat(analysis_prompt)
            try:
                # Intentar parsear JSON de la respuesta del LLM
                # Nota: En una implementación real usaríamos structured outputs
                import re
                json_match = re.search(r'\{.*\}', analysis_text, re.DOTALL)
                if json_match:
                    analysis = json.loads(json_match.group(0))
                else:
                    analysis = {"intent_score": 5, "category": "interested", "reason": "No se pudo parsear JSON"}
            except Exception:
                analysis = {"intent_score": 0, "category": "curious", "reason": "Error en análisis"}

            if analysis.get("intent_score", 0) >= 7:
                leads_found.append({
                    "user": comment["user"],
                    "text": comment["text"],
                    "analysis": analysis
                })

        if not leads_found:
            return {"status": "success", "message": "No se encontraron leads de alta intención en las interacciones recientes."}

        summary = "### 🎯 Leads Cualificados Detectados\n\n"
        for lead in leads_found:
            summary += (
                f"👤 **{lead['user']}**: {lead['text']}\n"
                f"🔥 **Intención**: {lead['analysis']['intent_score']}/10 ({lead['analysis']['category']})\n"
                f"💡 **Razón**: {lead['analysis']['reason']}\n\n"
            )
            
            # 3. Notificar vía Discord (simulado enviando al canal de notificaciones si estuviera conectado)
            # Aquí podríamos disparar un evento que el discord-bot escuche.
            
        return {"status": "success", "message": summary}

    async def _process_lead_magnets(self) -> dict:
        # 1. Definir disparadores y enlaces
        # En una versión real, esto vendría de la configuración guardada en Supabase
        magnets = {
            "GUIA": {"link": "https://brand.com/free-guide", "name": "Guía de Estilo"},
            "INFO": {"link": "https://brand.com/catalog", "name": "Catálogo 2026"}
        }
        
        comments = await self.marketing.get_comments("instagram", "latest_post")
        processed_count = 0
        details = []
        
        for comment in comments:
            text_upper = comment["text"].upper()
            for trigger, data in magnets.items():
                if trigger in text_upper:
                    # 2. Enviar DM (stub)
                    dm_text = f"¡Hola! Gracias por tu interés. Aquí tienes tu {data['name']}: {data['link']}"
                    await self.marketing.send_dm("instagram", comment["user"], dm_text)
                    
                    details.append(f"✅ DM enviado a **{comment['user']}** (Trigger: `{trigger}`)")
                    processed_count += 1
                    break
        
        if processed_count == 0:
            return {"status": "success", "message": "No se encontraron comentarios con palabras clave de Lead Magnet (GUIA, INFO)."}
            
        return {
            "status": "success", 
            "message": f"### 🧲 Automatización de Lead Magnets\n\n" + "\n".join(details) + f"\n\n**Total procesados:** {processed_count}"
        }

    async def _generate_funnel(self, prompt: str) -> dict:
        funnel_prompt = (
            f"Diseña un embudo de ventas (Sales Funnel) completo para una marca con este enfoque: {prompt}\n\n"
            f"Estructura la respuesta en las siguientes etapas:\n"
            f"1. **TOFU (Top of Funnel - Atracción)**: Ideas para Reels/TikToks virales, hashtags y ganchos (hooks).\n"
            f"2. **MOFU (Middle of Funnel - Confianza)**: Contenido educativo para carruseles, Stories interactivos y testimonios.\n"
            f"3. **BOFU (Bottom of Funnel - Venta)**: Estrategia de cierre, ofertas irresistibles y CTAs directos.\n\n"
            f"Usa un tono profesional, estratégico y creativo."
        )
        
        funnel_strategy = await self.llm.chat(funnel_prompt)
        
        return {
            "status": "success",
            "message": f"## 🗺️ Estrategia de Funnel de Ventas\n\n{funnel_strategy}"
        }

    async def _monitor_trends(self) -> dict:
        # 1. Simular obtención de tendencias (En real usaría APIs de TikTok/IG o scrapers)
        trends_detected = [
            {"name": "Minimalist Lifestyle", "growth": "45%", "platform": "TikTok"},
            {"name": "Handmade Aesthetics", "growth": "30%", "platform": "Instagram"}
        ]
        
        # 2. Generar sugerencias basadas en tendencias
        trend_prompt = (
            f"Analiza estas tendencias crecientes:\n{json.dumps(trends_detected)}\n\n"
            f"Sugiere 2 ideas creativas de contenido para una marca de diseño que aprovechen estas tendencias."
        )
        suggestions = await self.llm.chat(trend_prompt)
        
        report = (
            "### 🚀 Tendencias Detectadas (Viral Potential)\n\n"
            f"- **{trends_detected[0]['name']}** ({trends_detected[0]['growth']} en {trends_detected[0]['platform']})\n"
            f"- **{trends_detected[1]['name']}** ({trends_detected[1]['growth']} en {trends_detected[1]['platform']})\n\n"
            f"💡 **Sugerencias de la IA**:\n{suggestions}"
        )
        
        return {"status": "success", "message": report}

    async def _analyze_sentiment(self) -> dict:
        # 1. Obtener interacciones
        comments = await self.marketing.get_comments("instagram", "latest_post")
        
        sentiments = {"positive": 0, "neutral": 0, "negative": 0}
        alerts = []
        
        for comment in comments:
            # 2. Clasificar sentimiento con LLM
            sent_prompt = (
                f"Clasifica el sentimiento de este comentario en una sola palabra (POSITIVE, NEUTRAL, NEGATIVE): "
                f"\"{comment['text']}\""
            )
            res = await self.llm.chat(sent_prompt)
            res = res.upper()
            
            if "POSITIVE" in res:
                sentiments["positive"] += 1
            elif "NEGATIVE" in res:
                sentiments["negative"] += 1
                alerts.append(f"🚩 **Negativo**: \"{comment['text']}\" (Usuario: {comment['user']})")
            else:
                sentiments["neutral"] += 1

        total = len(comments)
        summary = (
            f"### 📊 Análisis de Sentimiento Reciente\n\n"
            f"✅ **Positivos**: {sentiments['positive']} ({(sentiments['positive']/total)*100:.1f}%)\n"
            f"😐 **Neutrales**: {sentiments['neutral']} ({(sentiments['neutral']/total)*100:.1f}%)\n"
            f"❌ **Negativos**: {sentiments['negative']} ({(sentiments['negative']/total)*100:.1f}%)\n\n"
        )
        
        if alerts:
            summary += "⚠️ **Alertas de Reputación Detectadas:**\n" + "\n".join(alerts)
            if sentiments["negative"] >= 2:
                summary += "\n\n🚨 **ALERTA DE CRISIS**: Se detecta un volumen inusual de comentarios negativos. Se recomienda intervención inmediata."
        else:
            summary += "✨ El sentimiento general es saludable. ¡Sigue así!"

        return {"status": "success", "message": summary}

    async def _find_collaborations(self, prompt: str) -> dict:
        collab_prompt = (
            f"Busca y propón estrategias de colaboración para una marca con este perfil: {prompt}\n\n"
            f"Incluye:\n"
            f"1. **Micro-Influencers**: Perfiles de nicho que encajen con la estética.\n"
            f"2. **Cuentas de Complemento**: Marcas no competidoras para sorteos o co-branding.\n"
            f"3. **Ideas de Campaña**: Formatos sugeridos para la colaboración (Takeover, unboxing, etc.).\n\n"
            f"El objetivo es expansión de audiencia y credibilidad."
        )
        
        suggestions = await self.llm.chat(collab_prompt)
        
        return {
            "status": "success",
            "message": f"## 🤝 Propuesta de Colaboraciones e Influencers\n\n{suggestions}"
        }
