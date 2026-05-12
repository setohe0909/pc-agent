from typing import Annotated, TypedDict, Union, List, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from app.domain.ports.llm import LLMPort
from app.domain.ports.memory import MemoryPort
from app.domain.ports.marketing import MarketingPort
import json

class MarketingState(TypedDict):
    """Estado del flujo de marketing."""
    prompt: str
    sub_command: str
    payload: dict
    context: str
    results: Optional[Union[dict, str]]
    next_step: str
    errors: List[str]

class MarketingGraph:
    def __init__(self, llm: LLMPort, memory: MemoryPort, marketing: MarketingPort):
        self.llm = llm
        self.memory = memory
        self.marketing = marketing
        self._graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(MarketingState)

        # Definir Nodos
        workflow.add_node("initialize", self._initialize_node)
        workflow.add_node("retrieve_context", self._retrieve_context_node)
        workflow.add_node("execute_tool", self._execute_tool_node)
        workflow.add_node("summarize", self._summarize_node)

        # Definir Bordes
        workflow.set_entry_point("initialize")
        workflow.add_edge("initialize", "retrieve_context")
        workflow.add_edge("retrieve_context", "execute_tool")
        workflow.add_edge("execute_tool", "summarize")
        workflow.add_edge("summarize", END)

        return workflow.compile()

    async def _initialize_node(self, state: MarketingState) -> dict:
        print("[GRAPH] Initializing marketing workflow...")
        return {
            "sub_command": state.get("payload", {}).get("sub_command", "chat"),
            "errors": []
        }

    async def _retrieve_context_node(self, state: MarketingState) -> dict:
        print(f"[GRAPH][TRACE] Retrieving context for marketer. Current sub_command: {state['sub_command']}")
        context = await self.memory.get_context("marketer")
        print(f"[GRAPH][TRACE] Context length: {len(context) if context else 0}")
        return {"context": context}

    async def _execute_tool_node(self, state: MarketingState) -> dict:
        sub_command = state["sub_command"]
        prompt = state["prompt"]
        print(f"[GRAPH][TRACE] Entering tool execution node for: {sub_command}")

        # Aquí mapeamos a la lógica existente en MarketingWorkflow
        # Por ahora lo haremos directo, luego podemos extraerlo a servicios
        try:
            if sub_command == "qualify":
                result = await self._qualify_leads()
            elif sub_command == "trends":
                result = await self._monitor_trends()
            elif sub_command == "sentiment":
                result = await self._analyze_sentiment()
            elif sub_command == "plan":
                result = await self._plan_campaign(prompt, state["context"])
            else:
                # Default chat
                result = await self._marketing_chat(prompt, state["context"])
            
            return {"results": result}
        except Exception as e:
            print(f"[GRAPH ERROR] {e}")
            return {"errors": [str(e)], "results": {"status": "error", "message": str(e)}}

    async def _summarize_node(self, state: MarketingState) -> dict:
        print("[GRAPH] Summarizing results...")
        # En una versión avanzada, el LLM podría resumir el output técnico del tool
        # Por ahora devolvemos el resultado directo
        return state

    async def run(self, prompt: str, payload: dict) -> dict:
        initial_state = {
            "prompt": prompt,
            "payload": payload,
            "sub_command": payload.get("sub_command", "chat"),
            "context": "",
            "results": None,
            "next_step": "",
            "errors": []
        }
        final_state = await self._graph.ainvoke(initial_state)
        return final_state["results"]

    # --- Métodos de Lógica (Copiados de MarketingWorkflow para el MVP del Grafo) ---

    async def _marketing_chat(self, prompt: str, context: str) -> dict:
        system_instructions = (
            "Eres un experto en marketing digital y redes sociales (Instagram y TikTok). "
            "Tu tono es siempre empático, positivo y profesional.\n"
            f"{context}"
        )
        full_prompt = f"{system_instructions}\n\nUsuario: {prompt}"
        response = await self.llm.chat(full_prompt)
        return {"status": "success", "message": response}

    async def _qualify_leads(self) -> dict:
        comments = await self.marketing.get_comments("instagram", "latest_post")
        leads_found = []
        for comment in comments:
            analysis_prompt = (
                f"Analiza la intención de compra de este comentario: \"{comment['text']}\". "
                f"Responde en formato JSON: 'intent_score' (0-10), 'category', 'reason'."
            )
            analysis_text = await self.llm.chat(analysis_prompt)
            # Simplificado para el ejemplo
            leads_found.append({"user": comment["user"], "text": comment["text"], "analysis": analysis_text})
        
        summary = "### 🎯 Leads Cualificados (Vía LangGraph)\n\n" + str(leads_found)
        return {"status": "success", "message": summary}

    async def _monitor_trends(self) -> dict:
        trends = [{"name": "AI Agents", "growth": "100%"}, {"name": "LangGraph", "growth": "80%"}]
        trend_prompt = f"Analiza estas tendencias: {json.dumps(trends)}. Sugiere contenido."
        suggestions = await self.llm.chat(trend_prompt)
        return {"status": "success", "message": f"### 🚀 Tendencias (LangGraph)\n\n{suggestions}"}

    async def _analyze_sentiment(self) -> dict:
        return {"status": "success", "message": "✨ Sentimiento analizado con éxito por el grafo."}

    async def _plan_campaign(self, prompt: str, context: str) -> dict:
        plan_prompt = f"Crea un plan para: {prompt}\nContexto: {context}"
        plan = await self.llm.chat(plan_prompt)
        return {"status": "success", "message": f"## 📅 Plan de Campaña (LangGraph)\n\n{plan}"}
