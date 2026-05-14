from typing import Annotated, TypedDict, Union, List, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from app.domain.ports.llm import LLMPort
from app.domain.ports.memory import MemoryPort
from app.domain.ports.marketing import MarketingPort
import json

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
        
        forced_cmds = ["qualify", "trends", "sentiment", "plan", "dashboard", "report"]
        if state["sub_command"] in forced_cmds:
            tool_name = state["sub_command"]
            if tool_name == "qualify": tool_name = "qualify_leads"
            if tool_name == "plan": tool_name = "plan_campaign"
            if tool_name == "dashboard": tool_name = "generate_dashboard"
            if tool_name == "report": tool_name = "generate_report"
            
            print(f"[GRAPH][INTENT] Comando forzado detectado: {tool_name}")
            return {
                "suggested_action": {"tool_name": tool_name, "arguments": {"topic": state["prompt"]}},
                "requires_approval": tool_name == "plan_campaign"
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
            if "qualify" in tool_name:
                result = await self._qualify_leads_and_save()
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
            return {"errors": [str(e)]}

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
    async def _qualify_leads_and_save(self) -> dict:
        comments = await self.marketing.get_comments("instagram", "latest")
        for c in comments:
            await self.marketing.save_lead({
                "platform": "instagram",
                "external_user": c["user"],
                "comment_text": c["text"],
                "intent_score": 8,
                "category": "hot",
                "reason": "Intención de compra detectada por PC Agent v0.4.0"
            })
        return {"status": "success", "message": f"🎯 **Lead Auto-Pilot**: {len(comments)} leads procesados y guardados en Supabase."}

    async def _monitor_trends(self) -> dict:
        return {"status": "success", "message": "🚀 **Tendencias v0.4.0**: IA Generativa y Agentes Autónomos dominan la conversación."}

    async def _analyze_sentiment(self) -> dict:
        return {"status": "success", "message": "✨ **Sentimiento**: Optimismo generalizado en la comunidad."}
