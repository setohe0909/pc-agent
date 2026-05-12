from typing import Annotated, TypedDict, Union, List, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from app.domain.ports.llm import LLMPort
from app.domain.ports.memory import MemoryPort
from app.domain.ports.marketing import MarketingPort
import json

class MarketingState(TypedDict):
    """Estado del flujo de marketing avanzado."""
    prompt: str
    sub_command: str
    payload: dict
    context: str
    suggested_action: Optional[dict]
    tool_results: Optional[dict]
    requires_approval: bool
    is_approved: bool
    final_message: Optional[str]
    errors: List[str]

class MarketingGraph:
    def __init__(self, llm: LLMPort, memory: MemoryPort, marketing: MarketingPort):
        self.llm = llm
        self.memory = memory
        self.marketing = marketing
        self._graph = self._build_graph()

    def _get_marketing_tools(self) -> List[dict]:
        """Define el esquema de herramientas para el LLM."""
        return [
            {
                "name": "qualify_leads",
                "description": "Analiza interacciones recientes para encontrar prospectos con alta intención de compra.",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "monitor_trends",
                "description": "Busca tendencias virales actuales en redes sociales para la marca.",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "analyze_sentiment",
                "description": "Evalúa el sentimiento general de los comentarios y detecta posibles crisis.",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "plan_campaign",
                "description": "Crea una propuesta detallada de campaña publicitaria.",
                "parameters": {
                    "type": "object", 
                    "properties": {
                        "topic": {"type": "string", "description": "El tema o producto de la campaña"}
                    },
                    "required": ["topic"]
                }
            }
        ]

    def _build_graph(self):
        workflow = StateGraph(MarketingState)

        # Definir Nodos
        workflow.add_node("initialize", self._initialize_node)
        workflow.add_node("retrieve_context", self._retrieve_context_node)
        workflow.add_node("analyze_intent", self._analyze_intent_node)
        workflow.add_node("execute_tool", self._execute_tool_node)
        workflow.add_node("human_approval", self._human_approval_node)
        workflow.add_node("finalize", self._finalize_node)

        # Definir Flujo
        workflow.set_entry_point("initialize")
        workflow.add_edge("initialize", "retrieve_context")
        workflow.add_edge("retrieve_context", "analyze_intent")
        
        # Lógica condicional después de analizar intención
        workflow.add_conditional_edges(
            "analyze_intent",
            self._decide_approval_path,
            {
                "needs_approval": "human_approval",
                "direct_execution": "execute_tool",
                "just_chat": "finalize"
            }
        )

        workflow.add_edge("human_approval", "execute_tool")
        workflow.add_edge("execute_tool", "finalize")
        workflow.add_edge("finalize", END)

        return workflow.compile()

    def _decide_approval_path(self, state: MarketingState):
        if state.get("errors"):
            return "just_chat"
        
        suggested = state.get("suggest_action") # Nota: hubo un typo en el dict, corregido abajo
        if not state.get("suggested_action"):
            return "just_chat"
        
        if state["requires_approval"]:
            return "needs_approval"
        
        return "direct_execution"

    async def _initialize_node(self, state: MarketingState) -> dict:
        print("[GRAPH][INIT] Iniciando flujo de marketing...")
        return {
            "sub_command": state.get("payload", {}).get("sub_command", "chat"),
            "is_approved": state.get("payload", {}).get("is_approved", False),
            "errors": []
        }

    async def _retrieve_context_node(self, state: MarketingState) -> dict:
        print("[GRAPH][CONTEXT] Recuperando contexto...")
        context = await self.memory.get_context("marketer")
        return {"context": context}

    async def _analyze_intent_node(self, state: MarketingState) -> dict:
        print(f"[GRAPH][INTENT] Analizando intención nativa para: {state['prompt']}")
        
        # Si el sub_command ya viene forzado desde Discord (vía botones), saltamos el análisis
        forced_cmds = ["qualify", "trends", "sentiment"]
        if state["sub_command"] in forced_cmds:
            return {
                "suggested_action": {"tool_name": f"{state['sub_command']}_leads" if state["sub_command"]=="qualify" else state["sub_command"], "arguments": {}},
                "requires_approval": False
            }

        # Usar Native Tool Calling
        system_instruction = (
            "Eres un Marketer experto. Decide qué herramienta usar según la petición. "
            "Si es algo que publica en redes o genera un plan costoso, requiere aprobación."
        )
        tools = self._get_marketing_tools()
        
        try:
            decision = await self.llm.get_tools_response(state["prompt"], tools, system_instruction)
            
            if "tool_name" in decision:
                # Acciones que requieren aprobación (ej. planear campaña)
                needs_approval = decision["tool_name"] in ["plan_campaign"]
                return {
                    "suggested_action": decision,
                    "requires_approval": needs_approval
                }
            else:
                return {"final_message": decision.get("message"), "suggested_action": None}
        except Exception as e:
            print(f"[GRAPH][ERROR] Fallo en Tool Calling: {e}")
            return {"errors": [str(e)]}

    async def _human_approval_node(self, state: MarketingState) -> dict:
        print("[GRAPH][APPROVAL] Verificando aprobación humana...")
        
        # Si ya viene aprobado en el payload inicial, continuamos
        if state["is_approved"]:
            print("[GRAPH][APPROVAL] Aprobación detectada en el estado.")
            return {"is_approved": True}
        
        # Si no está aprobado, enviamos una señal (en una implementación real aquí pausaríamos el grafo)
        # Por ahora, simulamos que 'plan_campaign' siempre requiere aprobación vía mensaje especial
        suggested = state["suggested_action"]
        msg = f"⚠️ **ACCIÓN REQUERIDA**: El agente desea ejecutar `{suggested['tool_name']}` con args `{suggested['arguments']}`. ¿Confirmas?"
        
        return {
            "final_message": msg,
            "requires_approval": True,
            "results": {"status": "requires_approval", "message": msg}
        }

    async def _execute_tool_node(self, state: MarketingState) -> dict:
        if state.get("requires_approval") and not state["is_approved"]:
            return {} # Salta ejecución si falta aprobación

        action = state["suggested_action"]
        if not action:
            return {}

        tool_name = action["tool_name"]
        args = action["arguments"]
        print(f"[GRAPH][EXECUTE] Ejecutando: {tool_name} con {args}")

        try:
            if "qualify" in tool_name:
                result = await self._qualify_leads()
            elif "trends" in tool_name:
                result = await self._monitor_trends()
            elif "sentiment" in tool_name:
                result = await self._analyze_sentiment()
            elif "plan" in tool_name:
                result = await self._plan_campaign(args.get("topic", state["prompt"]), state["context"])
            else:
                result = {"status": "error", "message": f"Herramienta {tool_name} no implementada."}
            
            return {"tool_results": result}
        except Exception as e:
            return {"errors": [str(e)]}

    async def _finalize_node(self, state: MarketingState) -> dict:
        print("[GRAPH][FINALIZE] Generando respuesta final...")
        
        if state.get("errors"):
            return {"results": {"status": "error", "message": f"Errores en el grafo: {state['errors']}"}}
        
        if state.get("tool_results"):
            return {"results": state["tool_results"]}
        
        if state.get("final_message"):
            return {"results": {"status": "success", "message": state["final_message"]}}
        
        # Chat por defecto si nada más ocurrió
        chat_res = await self._marketing_chat(state["prompt"], state["context"])
        return {"results": chat_res}

    async def run(self, prompt: str, payload: dict) -> dict:
        initial_state = {
            "prompt": prompt,
            "payload": payload,
            "sub_command": payload.get("sub_command", "chat"),
            "context": "",
            "suggested_action": None,
            "tool_results": None,
            "requires_approval": False,
            "is_approved": payload.get("is_approved", False),
            "final_message": None,
            "errors": []
        }
        final_state = await self._graph.ainvoke(initial_state)
        return final_state.get("results") or {"status": "error", "message": "Grafo terminó sin resultados."}

    # --- Lógica de Negocio (Mantenida igual para consistencia) ---

    async def _marketing_chat(self, prompt: str, context: str) -> dict:
        system = f"Eres experto en marketing. Contexto:\n{context}"
        res = await self.llm.chat(f"{system}\n\nUsuario: {prompt}")
        return {"status": "success", "message": res}

    async def _qualify_leads(self) -> dict:
        comments = await self.marketing.get_comments("instagram", "latest_post")
        return {"status": "success", "message": f"### 🎯 Leads Cualificados\nHe encontrado {len(comments)} interacciones interesantes. Usando **Native Tool Calling** para profundizar."}

    async def _monitor_trends(self) -> dict:
        return {"status": "success", "message": "🚀 **Tendencias**: Se detecta un pico de interés en 'IA Agents' y 'LangGraph'. Sugiero post educativo."}

    async def _analyze_sentiment(self) -> dict:
        return {"status": "success", "message": "✨ **Sentimiento**: 95% positivo. Sin alertas de crisis."}

    async def _plan_campaign(self, topic: str, context: str) -> dict:
        plan = await self.llm.chat(f"Genera un plan de marketing para {topic}. Contexto: {context}")
        return {"status": "success", "message": f"## 📅 Plan de Campaña: {topic}\n\n{plan}"}
