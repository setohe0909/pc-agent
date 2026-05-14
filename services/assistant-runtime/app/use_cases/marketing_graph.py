from typing import Annotated, TypedDict, Union, List, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from app.domain.ports.llm import LLMPort
from app.domain.ports.memory import MemoryPort
from app.domain.ports.marketing import MarketingPort
import json
import re
import unicodedata

class MarketingState(TypedDict):
    """Estado avanzado del flujo de marketing v0.4.0."""
    prompt: str
    images: Optional[List[bytes]]
    sub_command: str
    payload: dict
    context: str
    suggested_action: Optional[dict]
    tool_results: Optional[dict]
    requires_approval: bool
    is_approved: bool
    is_criticized: bool
    critic_feedback: Optional[str]
    refined_message: Optional[str]
    final_message: Optional[str]
    errors: List[str]
    results: Optional[dict]


class MarketingGraph:
    def __init__(self, llm: LLMPort, memory: MemoryPort, marketing: MarketingPort):
        self.llm = llm
        self.memory = memory
        self.marketing = marketing
        self._graph = self._build_graph()

    def _get_marketing_tools(self) -> List[dict]:
        return [
            {
                "name": "qualify_leads",
                "description": "Busca prospectos con intención de compra y los guarda en el CRM.",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "respond_to_comments",
                "description": "Responde comentarios recientes con tono empático de community manager.",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "monitor_trends",
                "description": "Busca tendencias virales actuales.",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "analyze_sentiment",
                "description": "Evalúa sentimiento y alertas de crisis.",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "plan_campaign",
                "description": "Propone un plan detallado de campaña.",
                "parameters": {
                    "type": "object", 
                    "properties": {
                        "topic": {"type": "string", "description": "Tema de la campaña"},
                        "goal": {"type": "string", "description": "Objetivo (ventas, awareness)"}
                    },
                    "required": ["topic"]
                }
            },
            {
                "name": "research_competitors",
                "description": "Analiza un competidor y propone una estrategia para superarlo.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "competitor": {"type": "string", "description": "Marca, cuenta o competidor a analizar"}
                    }
                }
            },
            {
                "name": "process_lead_magnets",
                "description": "Envía lead magnets por DM cuando encuentra palabras clave en comentarios.",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "generate_funnel",
                "description": "Diseña un funnel de ventas para un tema, producto o marca.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "topic": {"type": "string", "description": "Tema, producto o marca para el funnel"}
                    }
                }
            },
            {
                "name": "find_collaborations",
                "description": "Propone colaboraciones, micro-influencers y alianzas de marca.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "brand_profile": {"type": "string", "description": "Perfil de marca o nicho"}
                    }
                }
            },
            {
                "name": "get_marketing_memory",
                "description": "Muestra aprendizajes guardados del marketer.",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "generate_dashboard",
                "description": "Genera y analiza un dashboard de marketing desde Zernio.",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "generate_report",
                "description": "Genera un informe detallado de marketing desde Zernio.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "report_type": {"type": "string", "description": "Tipo de informe (ej. mensual, semanal, crecimiento)"}
                    },
                    "required": ["report_type"]
                }
            }
        ]

    def _direct_action_from_prompt(self, prompt: str) -> Optional[dict]:
        normalized = unicodedata.normalize("NFKD", prompt.casefold())
        normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
        normalized = re.sub(r"\s+", " ", normalized).strip()

        if any(word in normalized for word in ("dashboard", "tablero", "metricas", "analytics")):
            return {"tool_name": "generate_dashboard", "arguments": {}}

        if "reporte" in normalized or "informe" in normalized:
            report_type = "general"
            for candidate in ("diario", "semanal", "mensual", "crecimiento", "engagement"):
                if candidate in normalized:
                    report_type = candidate
                    break
            return {"tool_name": "generate_report", "arguments": {"report_type": report_type}}

        return None


    def _build_graph(self):
        workflow = StateGraph(MarketingState)

        # Definir Nodos
        workflow.add_node("initialize", self._initialize_node)
        workflow.add_node("analyze_image", self._analyze_image_node)
        workflow.add_node("retrieve_context", self._retrieve_context_node)
        workflow.add_node("analyze_intent", self._analyze_intent_node)
        workflow.add_node("critic_node", self._critic_node)
        workflow.add_node("brand_voice_refiner", self._brand_voice_refiner_node)
        workflow.add_node("human_approval", self._human_approval_node)
        workflow.add_node("execute_tool", self._execute_tool_node)
        workflow.add_node("finalize", self._finalize_node)

        # Definir Flujo
        workflow.set_entry_point("initialize")
        workflow.add_edge("initialize", "analyze_image")
        workflow.add_edge("analyze_image", "retrieve_context")
        workflow.add_edge("retrieve_context", "analyze_intent")
        
        # El Crítico revisa si el plan es sólido antes de pedir aprobación
        workflow.add_conditional_edges(
            "analyze_intent",
            self._decide_next_after_intent,
            {
                "needs_review": "critic_node",
                "direct_execution": "execute_tool",
                "just_chat": "finalize"
            }
        )

        workflow.add_edge("critic_node", "brand_voice_refiner")
        workflow.add_edge("brand_voice_refiner", "human_approval")
        workflow.add_edge("human_approval", "execute_tool")
        workflow.add_edge("execute_tool", "finalize")
        workflow.add_edge("finalize", END)

        return workflow.compile()

    def _decide_next_after_intent(self, state: MarketingState):
        if state.get("errors"): return "just_chat"
        action = state.get("suggested_action")
        if not action: return "just_chat"
        
        # Acciones complejas pasan por el Crítico y Refinador
        if action["tool_name"] in ["plan_campaign"]:
            return "needs_review"
        
        return "direct_execution"

    async def _initialize_node(self, state: MarketingState) -> dict:
        print("[GRAPH] v0.4.0 - Iniciando...")
        return {
            "sub_command": state.get("payload", {}).get("sub_command", "chat"),
            "is_approved": state.get("payload", {}).get("is_approved", False),
            "errors": []
        }

    async def _analyze_image_node(self, state: MarketingState) -> dict:
        if not state.get("images"):
            return {}
        
        print("[GRAPH][VISION] Analizando imágenes adjuntas...")
        prompt = "Analiza estas imágenes para una marca de marketing. ¿Qué elementos ves? ¿Cuál es la estética y el mensaje visual? Responde brevemente."
        vision_analysis = await self.llm.chat(prompt, images=state["images"])
        return {"context": f"ANÁLISIS VISUAL:\n{vision_analysis}\n\n"}

    async def _retrieve_context_node(self, state: MarketingState) -> dict:
        context = await self.memory.get_context("marketer")
        existing_context = state.get("context", "")
        return {"context": existing_context + context}

    async def _analyze_intent_node(self, state: MarketingState) -> dict:
        print(f"[GRAPH][INTENT] Analizando: {state['prompt']} (Sub: {state['sub_command']})")
        
        forced_cmds = [
            "respond", "qualify", "trends", "sentiment", "plan", "research",
            "dashboard", "report", "status", "magnet", "funnel", "collab", "memory"
        ]
        if state["sub_command"] in forced_cmds:
            tool_name = state["sub_command"]
            if tool_name == "respond": tool_name = "respond_to_comments"
            if tool_name == "qualify": tool_name = "qualify_leads"
            if tool_name == "plan": tool_name = "plan_campaign"
            if tool_name == "research": tool_name = "research_competitors"
            if tool_name == "dashboard": tool_name = "generate_dashboard"
            if tool_name == "report": tool_name = "generate_report"
            if tool_name == "status": tool_name = "get_status"
            if tool_name == "magnet": tool_name = "process_lead_magnets"
            if tool_name == "funnel": tool_name = "generate_funnel"
            if tool_name == "collab": tool_name = "find_collaborations"
            if tool_name == "memory": tool_name = "get_marketing_memory"
            
            print(f"[GRAPH][INTENT] Comando forzado detectado: {tool_name}")
            return {
                "suggested_action": {"tool_name": tool_name, "arguments": {"topic": state["prompt"]}},
                "requires_approval": tool_name == "plan_campaign"
            }

        direct_action = self._direct_action_from_prompt(state["prompt"])
        if direct_action:
            print(f"[GRAPH][INTENT] Acción directa detectada: {direct_action['tool_name']}")
            return {
                "suggested_action": direct_action,
                "requires_approval": False
            }

        tools = self._get_marketing_tools()
        decision = await self.llm.get_tools_response(state["prompt"], tools, "Eres un Marketer estratega.")
        
        if "tool_name" in decision:
            return {"suggested_action": decision, "requires_approval": decision["tool_name"] == "plan_campaign"}
        
        return {"final_message": decision.get("message"), "suggested_action": None}

    async def _critic_node(self, state: MarketingState) -> dict:
        print("[GRAPH][CRITIC] Evaluando propuesta del Marketer...")
        action = state["suggested_action"]
        prompt = f"Actúa como un Director Creativo Senior. Critica constructivamente este plan de marketing para '{action['arguments'].get('topic')}':\n{state['prompt']}\n\nEncuentra debilidades y sugiere mejoras."
        feedback = await self.llm.chat(prompt, context={"brand_context": state["context"]})
        return {"critic_feedback": feedback, "is_criticized": True}

    async def _brand_voice_refiner_node(self, state: MarketingState) -> dict:
        print("[GRAPH][VOICE] Refinando tono de marca...")
        action = state["suggested_action"]
        prompt = (
            f"Basado en el feedback del crítico:\n{state['critic_feedback']}\n\n"
            f"Refina el mensaje final de la propuesta de marketing para '{action['arguments'].get('topic')}' "
            f"asegurándote de que el tono sea empático, profesional y optimista."
        )
        refined = await self.llm.chat(prompt, context={"brand_context": state["context"]})
        return {"refined_message": refined}

    async def _human_approval_node(self, state: MarketingState) -> dict:
        if state["is_approved"]: return {"is_approved": True}
        
        suggested = state["suggested_action"]
        msg = f"🛡️ **Propuesta Refinada (v0.4.0)**:\n\n{state.get('refined_message', 'Plan estándar')}\n\n¿Aprobar ejecución de `{suggested['tool_name']}`?"
        return {
            "final_message": msg,
            "requires_approval": True,
            "tool_results": {"status": "requires_approval", "message": msg}
        }

    async def _execute_tool_node(self, state: MarketingState) -> dict:
        if state.get("requires_approval") and not state["is_approved"]:
            return {}

        action = state["suggested_action"]
        if not action: return {}

        tool_name = action["tool_name"]
        print(f"[GRAPH][EXECUTE] {tool_name}")

        try:
            if tool_name == "respond_to_comments":
                result = await self._respond_to_comments()
            elif tool_name == "get_status":
                result = await self._get_status()
            elif tool_name == "research_competitors":
                competitor = action.get("arguments", {}).get("competitor") or action.get("arguments", {}).get("topic") or state["prompt"]
                result = await self._research_competitors(competitor)
            elif tool_name == "process_lead_magnets":
                result = await self._process_lead_magnets()
            elif tool_name == "generate_funnel":
                topic = action.get("arguments", {}).get("topic") or state["prompt"]
                result = await self._generate_funnel(topic)
            elif tool_name == "find_collaborations":
                brand_profile = action.get("arguments", {}).get("brand_profile") or action.get("arguments", {}).get("topic") or state["prompt"]
                result = await self._find_collaborations(brand_profile)
            elif tool_name == "get_marketing_memory":
                result = await self._get_marketing_memory()
            elif "qualify" in tool_name:
                result = await self._qualify_leads()
            elif "trends" in tool_name:
                result = await self._monitor_trends()
            elif "sentiment" in tool_name:
                result = await self._analyze_sentiment()
            elif "plan" in tool_name:
                result = {"status": "success", "message": f"🚀 **Campaña Iniciada**: {state.get('refined_message', 'Procesada.')}"}
            elif "dashboard" in tool_name:
                data = await self.marketing.get_dashboard()
                msg = f"## 📊 Dashboard Zernio\n\n```json\n{json.dumps(data.get('metrics', {}), indent=2)}\n```\n\nEstado: Conectado vía Zernio."
                result = {"status": "success", "message": msg}
            elif "report" in tool_name:
                report_type = action.get("arguments", {}).get("report_type", "general")
                data = await self.marketing.generate_report(report_type)
                msg = f"## 📈 Informe Zernio ({report_type})\n\n{data.get('summary', '')}\n\nEnlace: {data.get('link', '#')}"
                result = {"status": "success", "message": msg}
            else:
                result = {"status": "error", "message": f"Herramienta {tool_name} no disponible."}
            
            return {"tool_results": result}
        except Exception as e:
            detail = str(e) or repr(e)
            return {
                "tool_results": {
                    "status": "error",
                    "message": (
                        f"No pude ejecutar la herramienta `{tool_name}`.\n"
                        f"Tipo: `{type(e).__name__}`\n"
                        f"Detalle: {detail}"
                    ),
                    "error_type": type(e).__name__,
                    "error_detail": detail,
                }
            }

    async def _finalize_node(self, state: MarketingState) -> dict:
        if state.get("errors"):
            return {"results": {"status": "error", "message": str(state["errors"])}}
        
        # Debug: Incluir llaves del estado si falla
        keys = list(state.keys())
        status = "requires_approval" if state.get("requires_approval") and not state.get("is_approved") else "success"
        
        if state.get("tool_results"):
            return {"results": state["tool_results"]}
        
        if state.get("final_message"):
            return {"results": {"status": status, "message": state["final_message"]}}
        
        sys_instr = (
            "Eres el Marketer Agent de PC Agent. Tu especialidad es el crecimiento orgánico, "
            "marketing digital, análisis de tendencias y gestión de comunidades. "
            "Habla siempre con propiedad de marketing y nunca te identifiques como analista financiero o de trading."
        )
        res = await self.llm.chat(state["prompt"], context={"brand": state["context"]}, system_instruction=sys_instr)
        return {"results": {"status": "success", "message": res}}

    async def run(self, prompt: str, payload: dict, images: List[bytes] = None) -> dict:
        initial_state = {
            "prompt": prompt,
            "images": images,
            "payload": payload,
            "sub_command": payload.get("sub_command", "chat"),
            "context": "",
            "suggested_action": payload.get("suggested_action"),
            "tool_results": None,
            "requires_approval": False,
            "is_approved": payload.get("is_approved", False),
            "is_criticized": False,
            "critic_feedback": None,
            "refined_message": None,
            "final_message": None,
            "errors": [],
            "results": None
        }
        final_state = await self._graph.ainvoke(initial_state)
        return final_state.get("results")

    # --- Business Logic ---
    async def _respond_to_comments(self) -> dict:
        comments = await self.marketing.get_comments("instagram", "latest_post")
        responses = []

        for comment in comments:
            response_prompt = (
                f"Actúa como un Community Manager empático y positivo. "
                f"Genera una respuesta corta y amable para este comentario: \"{comment['text']}\"."
            )
            reply_text = await self.llm.chat(response_prompt)
            await self.marketing.reply_to_comment("instagram", comment["id"], reply_text)
            responses.append({"comment": comment["text"], "reply": reply_text})

        if not responses:
            return {"status": "success", "message": "No encontré comentarios recientes para responder."}

        summary = "He respondido a los comentarios recientes de Instagram:\n\n"
        for response in responses:
            summary += f"- **Comentario:** {response['comment']}\n  **Respuesta:** {response['reply']}\n"
        return {"status": "success", "message": summary}

    async def _get_status(self) -> dict:
        status_report = (
            "**Estado del Sub-Agente !marketer**\n"
            "✅ Conexión Zernio: Activa\n"
            "✅ Acciones sociales: respond, qualify, magnet, sentiment\n"
            "✅ Estrategia: plan, research, trends, collab, funnel\n"
            "✅ Analítica: dashboard, report\n"
            "🧠 Memoria Mentis: disponible si Supabase está configurado"
        )
        return {"status": "success", "message": status_report}

    async def _research_competitors(self, competitor: str) -> dict:
        competitor = competitor.strip() or "competidor_generico"
        data = await self.marketing.get_competitor_data("instagram", competitor)
        research_prompt = (
            f"Analiza estos datos del competidor '{competitor}':\n{json.dumps(data)}\n\n"
            f"Propón una estrategia de campaña para superarlo basada en sus debilidades o aciertos."
        )
        research = await self.llm.chat(research_prompt)
        return {"status": "success", "message": f"## 🔍 Análisis de Competencia: {competitor}\n\n{research}"}

    async def _qualify_leads(self) -> dict:
        comments = await self.marketing.get_comments("instagram", "latest_post")
        leads_found = []

        for comment in comments:
            text = comment.get("text", "")
            hot_signal = any(word in text.upper() for word in ("INFO", "PRECIO", "COMPRAR", "QUIERO", "CATALOGO"))
            lead = {
                "platform": "instagram",
                "external_user": comment["user"],
                "comment_text": text,
                "intent_score": 8 if hot_signal else 5,
                "category": "hot" if hot_signal else "interested",
                "reason": "Intención detectada por palabra clave" if hot_signal else "Interacción positiva detectada"
            }
            if lead["intent_score"] >= 7:
                leads_found.append(lead)
                await self.marketing.save_lead(lead)
                await self.memory.save_memory(
                    category="marketing_lead",
                    summary=f"Lead cualificado detectado: {lead['external_user']} ({lead['category']})"
                )

        if not leads_found:
            return {"status": "success", "message": "No se encontraron leads de alta intención en las interacciones recientes."}

        summary = "### 🎯 Leads Cualificados Detectados\n\n"
        for lead in leads_found:
            summary += (
                f"👤 **{lead['external_user']}**: {lead['comment_text']}\n"
                f"🔥 **Intención**: {lead['intent_score']}/10 ({lead['category']})\n"
                f"💡 **Razón**: {lead['reason']}\n\n"
            )
        return {"status": "success", "message": summary}

    async def _process_lead_magnets(self) -> dict:
        magnets = {
            "GUIA": {"link": "https://brand.com/free-guide", "name": "Guía de Estilo"},
            "INFO": {"link": "https://brand.com/catalog", "name": "Catálogo 2026"}
        }
        comments = await self.marketing.get_comments("instagram", "latest_post")
        details = []

        for comment in comments:
            text_upper = comment["text"].upper()
            for trigger, data in magnets.items():
                if trigger in text_upper:
                    dm_text = f"¡Hola! Gracias por tu interés. Aquí tienes tu {data['name']}: {data['link']}"
                    await self.marketing.send_dm("instagram", comment["user"], dm_text)
                    details.append(f"✅ DM enviado a **{comment['user']}** (Trigger: `{trigger}`)")
                    break

        if not details:
            return {"status": "success", "message": "No se encontraron comentarios con palabras clave de Lead Magnet (GUIA, INFO)."}

        return {
            "status": "success",
            "message": "### 🧲 Automatización de Lead Magnets\n\n" + "\n".join(details) + f"\n\n**Total procesados:** {len(details)}"
        }

    async def _generate_funnel(self, prompt: str) -> dict:
        funnel_prompt = (
            f"Diseña un embudo de ventas completo para una marca con este enfoque: {prompt}\n\n"
            f"Estructura la respuesta en TOFU, MOFU y BOFU, con ideas de contenido, confianza y cierre."
        )
        funnel_strategy = await self.llm.chat(funnel_prompt)
        return {"status": "success", "message": f"## 🗺️ Estrategia de Funnel de Ventas\n\n{funnel_strategy}"}

    async def _monitor_trends(self) -> dict:
        trends_detected = [
            {"name": "Minimalist Lifestyle", "growth": "45%", "platform": "TikTok"},
            {"name": "Handmade Aesthetics", "growth": "30%", "platform": "Instagram"}
        ]
        trend_prompt = (
            f"Analiza estas tendencias crecientes:\n{json.dumps(trends_detected)}\n\n"
            f"Sugiere 2 ideas creativas de contenido que aprovechen estas tendencias."
        )
        suggestions = await self.llm.chat(trend_prompt)
        await self.memory.save_memory(
            category="marketing_trend",
            summary=f"Tendencia detectada: {trends_detected[0]['name']} ({trends_detected[0]['growth']})"
        )
        report = (
            "### 🚀 Tendencias Detectadas\n\n"
            f"- **{trends_detected[0]['name']}** ({trends_detected[0]['growth']} en {trends_detected[0]['platform']})\n"
            f"- **{trends_detected[1]['name']}** ({trends_detected[1]['growth']} en {trends_detected[1]['platform']})\n\n"
            f"💡 **Sugerencias de la IA**:\n{suggestions}"
        )
        return {"status": "success", "message": report}

    async def _analyze_sentiment(self) -> dict:
        comments = await self.marketing.get_comments("instagram", "latest_post")
        if not comments:
            return {"status": "success", "message": "No encontré comentarios recientes para analizar sentimiento."}

        sentiments = {"positive": 0, "neutral": 0, "negative": 0}
        alerts = []

        for comment in comments:
            sent_prompt = f"Clasifica el sentimiento de este comentario en POSITIVE, NEUTRAL o NEGATIVE: \"{comment['text']}\""
            res = (await self.llm.chat(sent_prompt)).upper()
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
        summary += "⚠️ **Alertas de Reputación Detectadas:**\n" + "\n".join(alerts) if alerts else "✨ El sentimiento general es saludable. ¡Sigue así!"
        return {"status": "success", "message": summary}

    async def _find_collaborations(self, prompt: str) -> dict:
        collab_prompt = (
            f"Busca y propón estrategias de colaboración para una marca con este perfil: {prompt}\n\n"
            f"Incluye micro-influencers, marcas complementarias e ideas de campaña."
        )
        suggestions = await self.llm.chat(collab_prompt)
        return {"status": "success", "message": f"## 🤝 Propuesta de Colaboraciones e Influencers\n\n{suggestions}"}

    async def _get_marketing_memory(self) -> dict:
        context = await self.memory.get_context("marketer")
        if not context:
            return {"status": "success", "message": "El Marketer aún no tiene aprendizajes guardados."}
        return {"status": "success", "message": f"### 🧠 Memoria de Aprendizaje (Marketer)\n\n{context}"}
