from typing import Annotated, TypedDict, Union, List, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from app.domain.ports.llm import LLMPort
from app.domain.ports.memory import MemoryPort
from app.domain.ports.marketing import MarketingPort
from app.use_cases.marketing_automation import MarketingAutomationService
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
        self.automation = MarketingAutomationService(llm=llm, memory=memory, marketing=marketing)
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
            },
            {
                "name": "get_top_content",
                "description": "Lista los mejores contenidos de Instagram y TikTok.",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "get_audience_insights",
                "description": "Analiza segmentos de audiencia, ubicaciones, preferencias y oportunidades.",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "get_growth_alerts",
                "description": "Muestra alertas de rendimiento, riesgo y oportunidades de crecimiento.",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "review_recent_comments",
                "description": "Resume comentarios recientes y señales de intención.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sentiment": {"type": "string", "description": "Filtro opcional: negative"}
                    }
                }
            },
            {
                "name": "draft_comment_replies",
                "description": "Prepara borradores de respuesta sin publicarlos.",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "get_sales_leads",
                "description": "Lista leads detectados y próximos pasos sugeridos.",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "generate_content_plan",
                "description": "Genera un calendario de contenido basado en métricas reales de Zernio.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "horizon": {"type": "string", "description": "Horizonte del plan, por ejemplo 7 días"}
                    }
                }
            },
            {
                "name": "repurpose_top_content",
                "description": "Convierte contenido ganador en nuevas piezas para otros canales.",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "get_best_hours",
                "description": "Recomienda mejores horarios de publicación por canal y formato.",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "create_campaign",
                "description": "Genera una campaña asistida basada en métricas de Zernio y pide aprobación.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "topic": {"type": "string", "description": "Objetivo, producto o tema de la campaña"}
                    },
                    "required": ["topic"]
                }
            },
            {
                "name": "generate_post_queue",
                "description": "Genera borradores de posts para Instagram y TikTok y pide aprobación para programar/publicar.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "topic": {"type": "string", "description": "Campaña, producto o tema para los posts"}
                    },
                    "required": ["topic"]
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

        direct_patterns = [
            (("top content", "mejor contenido", "contenidos top", "top contenidos"), "get_top_content"),
            (("audiencia", "segmenta", "segmentos"), "get_audience_insights"),
            (("alerta", "alertas", "riesgo"), "get_growth_alerts"),
            (("comentarios negativos", "negative comments"), "review_recent_comments"),
            (("comentarios", "comments"), "review_recent_comments"),
            (("borradores", "drafts", "respuestas para aprobacion"), "draft_comment_replies"),
            (("leads", "prospectos", "oportunidades de venta"), "get_sales_leads"),
            (("calendario", "content plan", "plan de contenido"), "generate_content_plan"),
            (("repurpose", "reutiliza", "convierte mi mejor"), "repurpose_top_content"),
            (("mejores horarios", "best hours", "horarios"), "get_best_hours"),
            (("campana", "campanas", "campaign"), "create_campaign"),
            (("posts", "post ", "publicaciones"), "generate_post_queue"),
        ]
        for keywords, tool_name in direct_patterns:
            if any(keyword in normalized for keyword in keywords):
                arguments = {"topic": prompt}
                if tool_name == "review_recent_comments" and "negativ" in normalized:
                    arguments["sentiment"] = "negative"
                return {"tool_name": tool_name, "arguments": arguments}

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
            "dashboard", "report", "status", "magnet", "funnel", "collab", "memory",
            "top-content", "audience", "alerts", "comments", "negative-comments",
            "reply-drafts", "leads", "content-plan", "repurpose", "best-hours",
            "competitors", "campaign", "posts"
        ]
        if state["sub_command"] in forced_cmds:
            tool_name = state["sub_command"]
            aliases = {
                "respond": "respond_to_comments",
                "qualify": "qualify_leads",
                "plan": "plan_campaign",
                "research": "research_competitors",
                "competitors": "research_competitors",
                "dashboard": "generate_dashboard",
                "report": "generate_report",
                "status": "get_status",
                "magnet": "process_lead_magnets",
                "funnel": "generate_funnel",
                "collab": "find_collaborations",
                "memory": "get_marketing_memory",
                "top-content": "get_top_content",
                "audience": "get_audience_insights",
                "alerts": "get_growth_alerts",
                "comments": "review_recent_comments",
                "negative-comments": "review_recent_comments",
                "reply-drafts": "draft_comment_replies",
                "leads": "get_sales_leads",
                "content-plan": "generate_content_plan",
                "repurpose": "repurpose_top_content",
                "best-hours": "get_best_hours",
                "campaign": "create_campaign",
                "posts": "generate_post_queue",
            }
            tool_name = aliases.get(tool_name, tool_name)
            
            print(f"[GRAPH][INTENT] Comando forzado detectado: {tool_name}")
            return {
                "suggested_action": {
                    "tool_name": tool_name,
                    "arguments": {"topic": state["prompt"], "sentiment": "negative" if state["sub_command"] == "negative-comments" else None}
                },
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
                result = await self._respond_to_comments(state.get("payload", {}))
            elif tool_name == "get_status":
                result = await self._get_status()
            elif tool_name == "research_competitors":
                competitor = action.get("arguments", {}).get("competitor") or action.get("arguments", {}).get("topic") or state["prompt"]
                result = await self._research_competitors(competitor)
            elif tool_name == "process_lead_magnets":
                result = await self._process_lead_magnets(state.get("payload", {}))
            elif tool_name == "generate_funnel":
                topic = action.get("arguments", {}).get("topic") or state["prompt"]
                result = await self._generate_funnel(topic)
            elif tool_name == "find_collaborations":
                brand_profile = action.get("arguments", {}).get("brand_profile") or action.get("arguments", {}).get("topic") or state["prompt"]
                result = await self._find_collaborations(brand_profile)
            elif tool_name == "get_marketing_memory":
                result = await self._get_marketing_memory()
            elif tool_name == "get_top_content":
                result = await self._get_top_content()
            elif tool_name == "get_audience_insights":
                result = await self._get_audience_insights()
            elif tool_name == "get_growth_alerts":
                result = await self._get_growth_alerts()
            elif tool_name == "review_recent_comments":
                result = await self._review_recent_comments(action.get("arguments", {}).get("sentiment"))
            elif tool_name == "draft_comment_replies":
                result = await self._draft_comment_replies()
            elif tool_name == "get_sales_leads":
                result = await self._get_sales_leads()
            elif tool_name == "generate_content_plan":
                result = await self._generate_content_plan(action.get("arguments", {}).get("horizon") or action.get("arguments", {}).get("topic") or "7 días")
            elif tool_name == "repurpose_top_content":
                result = await self._repurpose_top_content()
            elif tool_name == "get_best_hours":
                result = await self._get_best_hours()
            elif tool_name == "create_campaign":
                topic = action.get("arguments", {}).get("topic") or state["prompt"]
                result = await self.automation.plan_campaign(topic, payload=state.get("payload", {}), context=state.get("context", ""))
            elif tool_name == "generate_post_queue":
                topic = action.get("arguments", {}).get("topic") or state["prompt"]
                result = await self.automation.generate_post_queue(topic, payload=state.get("payload", {}), context=state.get("context", ""))
            elif "qualify" in tool_name:
                result = await self._qualify_leads(state.get("payload", {}))
            elif "trends" in tool_name:
                result = await self._monitor_trends()
            elif "sentiment" in tool_name:
                result = await self._analyze_sentiment()
            elif "plan" in tool_name:
                result = {"status": "success", "message": f"🚀 **Campaña Iniciada**: {state.get('refined_message', 'Procesada.')}"}
            elif "dashboard" in tool_name:
                data = await self.marketing.get_dashboard()
                msg = self._format_dashboard(data)
                result = {"status": "success", "message": msg, "dashboard": data}
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
    def _format_dashboard(self, data: dict) -> str:
        metrics = data.get("metrics", {})
        platforms = data.get("platforms", {})
        instagram = platforms.get("instagram", {})
        tiktok = platforms.get("tiktok", {})
        audience = data.get("audience", {})
        recommendations = data.get("recommendations", [])
        accounts = data.get("accounts", {})

        def value(source: dict, key: str, default: str = "N/D") -> str:
            raw = source.get(key, default)
            return str(raw)

        def content_line(platform_data: dict) -> str:
            top_content = platform_data.get("top_content", {})
            if not top_content:
                return "N/D"
            title = top_content.get("title", "Contenido destacado")
            metric = top_content.get("views") or top_content.get("reach") or "N/D"
            engagement = top_content.get("engagement_rate", "N/D")
            return f"{title} ({metric}, ER {engagement})"

        recommendation_lines = "\n".join(f"- {item}" for item in recommendations[:3]) or "- Sin recomendaciones disponibles."
        location_text = ", ".join(audience.get("top_locations", [])) or "N/D"
        best_windows = data.get("best_posting_windows", {})
        window_text = best_windows.get("recommendation", "N/D")

        return (
            f"## 📊 Dashboard Zernio\n"
            f"**Periodo:** {data.get('period', 'Últimos 30 días')}\n"
            f"**Cuentas:** Instagram {accounts.get('instagram', 'conectado')} · TikTok {accounts.get('tiktok', 'conectado')}\n\n"
            f"### Resumen ejecutivo\n"
            f"- Alcance total: **{value(metrics, 'total_reach')}**\n"
            f"- Impresiones totales: **{value(metrics, 'total_impressions')}**\n"
            f"- Engagement total: **{value(metrics, 'total_engagement_rate')}**\n"
            f"- Crecimiento de seguidores: **{value(metrics, 'followers_growth')}**\n"
            f"- Leads detectados: **{value(metrics, 'leads_detected')}**\n"
            f"- Sentimiento: **{value(metrics, 'sentiment_score')}**\n\n"
            f"### Instagram\n"
            f"- Crecimiento: **{value(instagram, 'followers_growth')}**\n"
            f"- Alcance: **{value(instagram, 'reach')}** · Impresiones: **{value(instagram, 'impressions')}**\n"
            f"- Engagement: **{value(instagram, 'engagement_rate')}**\n"
            f"- Visitas al perfil: **{value(instagram, 'profile_visits')}** · Clicks web: **{value(instagram, 'website_clicks')}**\n"
            f"- Top content: **{content_line(instagram)}**\n\n"
            f"### TikTok\n"
            f"- Crecimiento: **{value(tiktok, 'followers_growth')}**\n"
            f"- Views: **{value(tiktok, 'views')}** · Completion rate: **{value(tiktok, 'completion_rate')}**\n"
            f"- Engagement: **{value(tiktok, 'engagement_rate')}** · Shares: **{value(tiktok, 'shares')}**\n"
            f"- Visitas al perfil: **{value(tiktok, 'profile_visits')}**\n"
            f"- Top content: **{content_line(tiktok)}**\n\n"
            f"### Audiencia\n"
            f"- Ubicaciones top: **{location_text}**\n"
            f"- Edad principal: **{audience.get('top_age_range', 'N/D')}**\n"
            f"- Mejores horarios: **{window_text}**\n\n"
            f"### Próximas acciones sugeridas\n"
            f"{recommendation_lines}\n\n"
            f"Estado: Conectado vía Zernio."
        )

    async def _respond_to_comments(self, payload: dict | None = None) -> dict:
        return await self.automation.respond_to_comments(payload)

    async def _get_status(self) -> dict:
        accounts = await self.marketing.get_connected_accounts()
        ig = accounts.get("instagram", "no conectada")
        tt = accounts.get("tiktok", "no conectada")
        lines = [
            "**Estado del Sub-Agente !marketer**",
            f"✅ Cuentas: Instagram **{ig}** · TikTok **{tt}**",
            "✅ Analítica: dashboard, report, top-content, audience, alerts, best-hours",
            "✅ Comunidad: comments, negative-comments, reply-drafts, respond, qualify, leads, magnet",
            "✅ Estrategia: campaign, posts, content-plan, repurpose, plan, research, competitors, trends, collab, funnel",
            "✅ Autonomía: modo asistido por defecto; publicaciones, DMs y respuestas requieren aprobación",
            "✅ Visual: dashboard con imagen adjunta en Discord",
            "🧠 Memoria Mentis: disponible si Supabase está configurado",
            "",
            "_Datos obtenidos desde conexiones reales en system_config_",
        ]
        return {"status": "success", "message": "\n".join(lines)}

    async def _research_competitors(self, competitor: str) -> dict:
        competitor = competitor.strip() or "competidor_generico"
        data = await self.marketing.get_competitor_data("instagram", competitor)
        research_prompt = (
            f"Analiza estos datos del competidor '{competitor}':\n{json.dumps(data)}\n\n"
            f"Propón una estrategia de campaña para superarlo basada en sus debilidades o aciertos."
        )
        research = await self.llm.chat(research_prompt)
        return {"status": "success", "message": f"## 🔍 Análisis de Competencia: {competitor}\n\n{research}"}

    async def _qualify_leads(self, payload: dict | None = None) -> dict:
        return await self.automation.qualify_leads(payload)

    async def _process_lead_magnets(self, payload: dict | None = None) -> dict:
        return await self.automation.process_lead_magnets(payload)

    async def _generate_funnel(self, prompt: str) -> dict:
        funnel_prompt = (
            f"Diseña un embudo de ventas completo para una marca con este enfoque: {prompt}\n\n"
            f"Estructura la respuesta en TOFU, MOFU y BOFU, con ideas de contenido, confianza y cierre."
        )
        funnel_strategy = await self.llm.chat(funnel_prompt)
        return {"status": "success", "message": f"## 🗺️ Estrategia de Funnel de Ventas\n\n{funnel_strategy}"}

    async def _monitor_trends(self) -> dict:
        existing = await self.memory.get_context("marketer")
        context = existing or "Sin contexto de marca disponible"

        trend_prompt = (
            "Eres un estratega de marketing digital. Identifica 2 tendencias reales y actuales "
            "en redes sociales (TikTok, Instagram) que sean relevantes para marcas y creadores.\n\n"
            f"Contexto de la marca:\n{context}\n\n"
            "Para cada tendencia incluye:\n"
            "- Nombre de la tendencia\n"
            "- Plataforma principal\n"
            "- Por qué está creciendo\n"
            "- Oportunidad de contenido para la marca\n\n"
            "Responde con datos reales, no inventes métricas exactas."
        )
        analysis = await self.llm.chat(trend_prompt)

        await self.memory.save_memory(
            category="marketing_trend",
            summary=f"Análisis de tendencias real: {analysis[:200]}..."
        )

        report = f"### 🚀 Tendencias Detectadas\n\n{analysis}"
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

    async def _get_top_content(self) -> dict:
        content = await self.marketing.get_top_content(limit=5)
        if not content:
            return {"status": "success", "message": "No encontré contenido destacado en Zernio todavía."}

        lines = ["## 🏆 Top Content Zernio\n"]
        for index, item in enumerate(content, start=1):
            metric = item.get("views") or item.get("reach") or "N/D"
            lines.append(
                f"{index}. **{item.get('title', 'Contenido')}** ({item.get('platform', 'canal')})\n"
                f"   - Formato: {item.get('format', 'N/D')} · Alcance/Views: **{metric}** · ER: **{item.get('engagement_rate', 'N/D')}**\n"
                f"   - Tema: {item.get('topic', 'N/D')} · Shares: {item.get('shares', 'N/D')} · Saves: {item.get('saves', 'N/D')}"
            )
        return {"status": "success", "message": "\n".join(lines)}

    async def _get_audience_insights(self) -> dict:
        audience = await self.marketing.get_audience_insights()
        segments = audience.get("segments", [])
        segment_lines = "\n".join(
            f"- **{segment.get('name')}** ({segment.get('share')}): {segment.get('signal')}"
            for segment in segments
        ) or "- Sin segmentos disponibles."
        preferences = ", ".join(audience.get("content_preferences", [])) or "N/D"
        windows = ", ".join(audience.get("best_posting_windows", [])) or "N/D"
        locations = ", ".join(audience.get("top_locations", [])) or "N/D"

        msg = (
            "## 👥 Audiencia Zernio\n\n"
            f"- Ubicaciones principales: **{locations}**\n"
            f"- Edad principal: **{audience.get('top_age_range', 'N/D')}**\n"
            f"- Mejores horarios: **{windows}**\n"
            f"- Preferencias de contenido: **{preferences}**\n\n"
            "### Segmentos\n"
            f"{segment_lines}"
        )
        return {"status": "success", "message": msg}

    async def _get_growth_alerts(self) -> dict:
        alerts = await self.marketing.get_alerts()
        if not alerts:
            return {"status": "success", "message": "No hay alertas activas de crecimiento o reputación."}

        severity_icon = {"high": "🔴", "medium": "🟠", "low": "🟢"}
        lines = ["## 🚨 Alertas Zernio\n"]
        for alert in alerts:
            severity = alert.get("severity", "low")
            lines.append(
                f"{severity_icon.get(severity, '⚪')} **{alert.get('title', 'Alerta')}** ({alert.get('platform', 'general')})\n"
                f"- Detalle: {alert.get('detail', 'N/D')}\n"
                f"- Acción sugerida: {alert.get('recommendation', 'Revisar manualmente')}"
            )
        return {"status": "success", "message": "\n\n".join(lines)}

    async def _review_recent_comments(self, sentiment: str | None = None) -> dict:
        comments = await self.marketing.get_comments("instagram", "latest_post")
        if sentiment == "negative":
            negative_terms = ("malo", "caro", "problema", "no me gusta", "demora", "queja")
            comments = [comment for comment in comments if any(term in comment.get("text", "").lower() for term in negative_terms)]

        if not comments:
            label = "negativos " if sentiment == "negative" else ""
            return {"status": "success", "message": f"No encontré comentarios {label}recientes."}

        lines = ["## 💬 Comentarios recientes\n"]
        for comment in comments[:8]:
            text = comment.get("text", "")
            signal = "lead" if any(word in text.upper() for word in ("INFO", "PRECIO", "COMPRAR", "QUIERO")) else "comunidad"
            lines.append(f"- **{comment.get('user', 'usuario')}**: {text}\n  Señal: `{signal}`")
        return {"status": "success", "message": "\n".join(lines)}

    async def _draft_comment_replies(self) -> dict:
        comments = await self.marketing.get_comments("instagram", "latest_post")
        if not comments:
            return {"status": "success", "message": "No encontré comentarios recientes para preparar respuestas."}

        lines = ["## ✍️ Borradores de respuesta\n"]
        for comment in comments[:5]:
            prompt = (
                f"Redacta una respuesta breve, cálida y orientada a conversión para este comentario: "
                f"\"{comment.get('text', '')}\". No publiques, solo entrega el borrador."
            )
            draft = await self.llm.chat(prompt)
            lines.append(f"- **{comment.get('user', 'usuario')}**: {comment.get('text', '')}\n  Borrador: {draft}")
        return {"status": "success", "message": "\n".join(lines)}

    async def _get_sales_leads(self) -> dict:
        leads = await self.marketing.get_leads()
        if not leads:
            return {"status": "success", "message": "No hay leads detectados por Zernio en este momento."}

        lines = ["## 🔥 Leads detectados\n"]
        for lead in leads:
            lines.append(
                f"- **{lead.get('user')}** ({lead.get('platform')}) · Score: **{lead.get('intent_score')}/10** · Estado: **{lead.get('status')}**\n"
                f"  Señal: {lead.get('signal')}\n"
                f"  Siguiente paso: {lead.get('suggested_next_step', 'Contactar con mensaje personalizado')}"
            )
        return {"status": "success", "message": "\n".join(lines)}

    async def _generate_content_plan(self, horizon: str) -> dict:
        dashboard = await self.marketing.get_dashboard()
        top_content = await self.marketing.get_top_content(limit=5)
        best_hours = await self.marketing.get_best_posting_windows()
        prompt = (
            f"Crea un plan de contenido para {horizon} usando estos datos reales de Zernio.\n"
            f"Dashboard: {json.dumps(dashboard, ensure_ascii=False)}\n"
            f"Top content: {json.dumps(top_content, ensure_ascii=False)}\n"
            f"Mejores horarios: {json.dumps(best_hours, ensure_ascii=False)}\n\n"
            "Entrega un calendario claro por día con canal, formato, hook, CTA y métrica objetivo."
        )
        plan = await self.llm.chat(prompt, context={"brand_context": "marketing"})
        return {"status": "success", "message": f"## 🗓️ Plan de contenido basado en Zernio\n\n{plan}"}

    async def _repurpose_top_content(self) -> dict:
        top_content = await self.marketing.get_top_content(limit=3)
        if not top_content:
            return {"status": "success", "message": "No encontré contenido ganador para reutilizar."}

        prompt = (
            "Convierte estos contenidos ganadores en nuevas piezas para Instagram y TikTok.\n"
            f"{json.dumps(top_content, ensure_ascii=False)}\n\n"
            "Para cada contenido entrega: nuevo formato, hook, guion corto, CTA y por qué debería funcionar."
        )
        ideas = await self.llm.chat(prompt)
        return {"status": "success", "message": f"## ♻️ Repurpose de contenido ganador\n\n{ideas}"}

    async def _get_best_hours(self) -> dict:
        windows = await self.marketing.get_best_posting_windows()
        by_format = windows.get("by_format", {})
        format_lines = "\n".join(f"- {name}: **{hour}**" for name, hour in by_format.items()) or "- Sin desglose por formato."
        msg = (
            "## ⏰ Mejores horarios Zernio\n\n"
            f"- Instagram: **{', '.join(windows.get('instagram', [])) or 'N/D'}**\n"
            f"- TikTok: **{', '.join(windows.get('tiktok', [])) or 'N/D'}**\n\n"
            "### Por formato\n"
            f"{format_lines}\n\n"
            f"Recomendación: {windows.get('recommendation', 'Probar horarios y medir retención.')}"
        )
        return {"status": "success", "message": msg}
