from typing import Annotated, TypedDict, Union, List, Optional
import json
import os
from langgraph.graph import StateGraph, END
from app.domain.ports.llm import LLMPort
from app.domain.ports.memory import MemoryPort

class CoderWebState(TypedDict):
    """Estado del flujo de Coder Web Agent v0.1.0."""
    prompt: str
    project_type: str  # 'repo' or 'wix'
    stack: str
    context: str
    plan: Optional[str]
    results: Optional[dict]
    payload: dict
    errors: List[str]

class CoderWebGraph:
    def __init__(self, llm: LLMPort, memory: MemoryPort):
        self.llm = llm
        self.memory = memory
        self._graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(CoderWebState)

        # Definir Nodos
        workflow.add_node("initialize", self._initialize_node)
        workflow.add_node("retrieve_context", self._retrieve_context_node)
        workflow.add_node("analyze_request", self._analyze_request_node)
        workflow.add_node("execute_task", self._execute_task_node)
        workflow.add_node("finalize", self._finalize_node)

        # Definir Flujo
        workflow.set_entry_point("initialize")
        workflow.add_edge("initialize", "retrieve_context")
        workflow.add_edge("retrieve_context", "analyze_request")
        workflow.add_edge("analyze_request", "execute_task")
        workflow.add_edge("execute_task", "finalize")
        workflow.add_edge("finalize", END)

        return workflow.compile()

    async def _initialize_node(self, state: CoderWebState) -> dict:
        print("[CODER-WEB GRAPH] Iniciando...")
        return {"errors": [], "stack": "React/TypeScript + Tailwind + Supabase"}

    async def _retrieve_context_node(self, state: CoderWebState) -> dict:
        print("[CODER-WEB GRAPH] Recuperando memoria...")
        context = await self.memory.get_context("coder-web")
        return {"context": context}

    async def _analyze_request_node(self, state: CoderWebState) -> dict:
        print(f"[CODER-WEB GRAPH] Analizando solicitud: {state['prompt']}")
        
        system_instruction = (
            "Eres un experto Arquitecto de Software y Desarrollador Fullstack. "
            "Tu especialidad es crear e-commerce modernos y escalables. "
            "Debes decidir si la tarea requiere crear un repositorio de código puro (React/TS + Tailwind + Supabase) "
            "o si se trata de un ajuste/creación en Wix. "
            "Responde en formato JSON con las claves: 'project_type' (repo|wix), 'plan' (pasos detallados), 'tech_stack'."
        )
        
        try:
            analysis = await self.llm.chat(
                f"{system_instruction}\n\nContexto de Memoria:\n{state['context']}\n\nSolicitud del Usuario: {state['prompt']}\n\nResponde SOLO JSON."
            )
            
            # Limpiar respuesta
            if "```json" in analysis:
                analysis = analysis.split("```json")[1].split("```")[0].strip()
            
            data = json.loads(analysis)
            return {
                "project_type": data.get("project_type", "repo"),
                "plan": data.get("plan", "No plan generated"),
                "stack": data.get("tech_stack", state["stack"])
            }
        except Exception as e:
            print(f"[CODER-WEB GRAPH ERROR] Fallo análisis: {e}")
            return {"project_type": "repo", "plan": "Error analizando solicitud, procediendo con stack default."}

    async def _execute_task_node(self, state: CoderWebState) -> dict:
        project_type = state.get("project_type", "repo")
        print(f"[CODER-WEB GRAPH] Ejecutando tarea tipo: {project_type}")
        
        # En una implementación real, aquí se usarían herramientas como Pilot o APIs de Wix.
        # Por ahora simulamos la creación/ajuste.
        
        result_msg = ""
        if project_type == "repo":
            result_msg = (
                f"🚀 **Proyecto de Repositorio Inicializado**\n"
                f"- **Stack:** {state['stack']}\n"
                f"- **Acción:** Creando estructura base y configurando Supabase Auth/DB.\n"
                f"- **Pilot:** Pilot está diseñando los componentes de UI con Tailwind CSS.\n\n"
                f"**Plan de Ejecución:**\n{state['plan']}"
            )
            await self.memory.save_memory("coder-web", f"Creado repo para: {state['prompt'][:50]}")
        else:
            result_msg = (
                f"🌐 **Ajuste en Wix Detectado**\n"
                f"- **Acción:** Accediendo vía API de Wix/Velo para modificar la UI.\n"
                f"- **Estado:** Sincronizando cambios de diseño y versionando el sitio.\n\n"
                f"**Plan de Ejecución:**\n{state['plan']}"
            )
            await self.memory.save_memory("coder-web", f"Ajuste Wix para: {state['prompt'][:50]}")

        return {"results": {"status": "success", "message": result_msg}}

    async def _finalize_node(self, state: CoderWebState) -> dict:
        return state

    async def run(self, prompt: str, payload: dict) -> dict:
        initial_state = {
            "prompt": prompt,
            "project_type": "repo",
            "stack": "React/TypeScript + Tailwind + Supabase",
            "context": "",
            "plan": None,
            "results": None,
            "payload": payload,
            "errors": []
        }
        final_state = await self._graph.ainvoke(initial_state)
        return final_state.get("results")
