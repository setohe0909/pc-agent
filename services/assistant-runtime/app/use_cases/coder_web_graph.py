from typing import Annotated, TypedDict, Union, List, Optional
import json
import os
from langgraph.graph import StateGraph, END
from app.domain.ports.llm import LLMPort
from app.domain.ports.memory import MemoryPort
from app.domain.ports.coder_web import CoderWebPort

class CoderWebState(TypedDict):
    """Estado robusto del flujo de Coder Web Agent v0.2.0."""
    prompt: str
    images: Optional[List[bytes]]
    project_type: str  # always 'repo' now
    stack: str
    context: str
    plan: Optional[dict]
    task_result: Optional[dict]
    payload: dict
    errors: List[str]
    warnings: List[str]
    results: Optional[dict]

class CoderWebGraph:
    def __init__(self, llm: LLMPort, memory: MemoryPort, coder_web: CoderWebPort):
        self.llm = llm
        self.memory = memory
        self.coder_web = coder_web
        self._graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(CoderWebState)

        # Definir Nodos
        workflow.add_node("initialize", self._initialize_node)
        workflow.add_node("analyze_mockup", self._analyze_mockup_node)
        workflow.add_node("analyze_references", self._analyze_references_node)
        workflow.add_node("retrieve_context", self._retrieve_context_node)
        workflow.add_node("analyze_request", self._analyze_request_node)
        workflow.add_node("plan_review", self._plan_review_node)
        workflow.add_node("execute_pilot_task", self._execute_pilot_task_node)
        workflow.add_node("finalize", self._finalize_node)

        # Definir Flujo
        workflow.set_entry_point("initialize")
        workflow.add_edge("initialize", "analyze_mockup")
        workflow.add_edge("analyze_mockup", "analyze_references")
        workflow.add_edge("analyze_references", "retrieve_context")
        workflow.add_edge("retrieve_context", "analyze_request")
        workflow.add_edge("analyze_request", "plan_review")
        workflow.add_edge("plan_review", "execute_pilot_task")
        workflow.add_edge("execute_pilot_task", "finalize")
        workflow.add_edge("finalize", END)

        return workflow.compile()


    async def _initialize_node(self, state: CoderWebState) -> dict:
        print("[CODER-WEB GRAPH] v0.6.0 - Iniciando...")
        return {"errors": [], "warnings": [], "stack": "React/TypeScript + Tailwind + Supabase"}

    async def _analyze_mockup_node(self, state: CoderWebState) -> dict:
        if not state.get("images"):
            return {}
        
        sys_instr = "Eres Pilot, un experto en diseño UI/UX y arquitectura de e-commerce. Tu tarea es analizar visualmente mockups."
        prompt = "Analiza este mockup o referencia para un ecommerce. Describe el layout, colores, tipografía y elementos clave de UI/UX que Pilot debe implementar."
        vision_analysis = await self.llm.chat(prompt, images=state["images"], system_instruction=sys_instr)
        return {"context": f"ANÁLISIS DE MOCKUP:\n{vision_analysis}\n\n"}

    async def _analyze_references_node(self, state: CoderWebState) -> dict:
        import re
        urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', state["prompt"])
        
        if not urls:
            return {}
        
        print(f"[CODER-WEB GRAPH][REFERENCES] Detectadas {len(urls)} URLs de referencia.")
        sys_instr = "Eres Pilot, experto en análisis de la competencia y UX Research."
        prompt = f"El usuario ha proporcionado estos links como referencia de diseño: {', '.join(urls)}. Basado en el nombre de los dominios y la descripción del usuario, infiere estilos y patrones UX."
        analysis = await self.llm.chat(prompt, system_instruction=sys_instr)
        return {"context": state.get("context", "") + f"ANÁLISIS DE REFERENCIAS EXTERNAS:\n{analysis}\n\n"}

    async def _retrieve_context_node(self, state: CoderWebState) -> dict:
        print("[CODER-WEB GRAPH] Recuperando memoria operativa...")
        context = await self.memory.get_context("coder-web")
        return {"context": context}

    async def _analyze_request_node(self, state: CoderWebState) -> dict:
        print(f"[CODER-WEB GRAPH][ANALYSIS] Procesando: {state['prompt']}")
        
        system_instruction = (
            "Eres el Agente Pilot, experto en arquitectura web y automatización de e-commerce. "
            "Tu objetivo es diseñar una solución técnica DETALLADA. "
            "Stack default para repos: React/TS + Tailwind + Supabase. "
            "Responde en formato JSON con: "
            "'project_type' (repo), 'stack', 'plan' (objeto con 'steps', 'architecture')."
        )
        
        try:
            analysis = await self.llm.chat(
                f"{system_instruction}\n\nContexto:\n{state['context']}\n\nSolicitud: {state['prompt']}\n\nResponde SOLO JSON."
            )
            
            if "```json" in analysis:
                analysis = analysis.split("```json")[1].split("```")[0].strip()
            
            data = json.loads(analysis)
            return {
                "project_type": "repo",
                "plan": data.get("plan", {"steps": ["Inicializar"], "architecture": "Standard"}),
                "stack": data.get("stack", state["stack"]),
                "payload": state["payload"]
            }
        except Exception as e:
            print(f"[CODER-WEB ERROR] Fallo análisis: {e}")
            return {"project_type": "repo", "plan": {"steps": ["Default Repo Setup"], "architecture": "Basic", "velo_code": ""}}

    async def _plan_review_node(self, state: CoderWebState) -> dict:
        print("[CODER-WEB GRAPH][REVIEW] Validando plan de Pilot...")
        plan_str = json.dumps(state["plan"])
        prompt = (
            f"Como experto arquitecto, revisa y COMPLETA este plan de Pilot para un proyecto {state['project_type']}:\n{plan_str}\n\n"
            f"Devuelve el plan actualizado en formato JSON."
        )
        sys_instr = "Eres el Arquitecto Pilot. Revisa, optimiza y escribe código para e-commerce."
        
        try:
            review_json = await self.llm.chat(prompt, context={"project_context": state["context"]}, system_instruction=sys_instr)
            if "```json" in review_json:
                review_json = review_json.split("```json")[1].split("```")[0].strip()
            
            updated_plan = json.loads(review_json)
            return {"plan": updated_plan}
        except:
            return {"plan": state["plan"]}


    async def _execute_pilot_task_node(self, state: CoderWebState) -> dict:
        project_type = state["project_type"]
        plan = state["plan"]
        print(f"[CODER-WEB GRAPH][EXECUTE] Pilot ejecutando {project_type}")
        
        try:
            res = await self.coder_web.create_repository(
                name=f"ecommerce-{os.urandom(2).hex()}",
                stack=state["stack"],
                description=state["prompt"]
            )
            
            await self.memory.save_memory("coder-web", f"Tarea completada ({project_type}): {state['prompt'][:50]}")
            return {"task_result": res}
        except Exception as e:
            return {"errors": [f"Error en ejecución Pilot: {str(e)}"]}

    async def _finalize_node(self, state: CoderWebState) -> dict:
        error_list = state.get("errors", [])
        warning_list = state.get("warnings", [])
        
        if error_list:
            return {"results": {"status": "error", "message": "\n".join(error_list), "warnings": warning_list}}
        
        res = state.get("task_result")
        if not res:
            return {"results": {"status": "error", "message": "Pilot no pudo generar un resultado válido.", "warnings": warning_list}}
        
        # Extraer detalles técnicos del plan para mostrarlos al usuario
        plan = state.get("plan", {})
        architecture = plan.get("architecture", "Estándar")
        
        steps = plan.get('steps', [])
        formatted_steps = []
        for s in steps:
            if isinstance(s, dict):
                formatted_steps.append(f"• {s.get('description') or s.get('name') or str(s)}")
            else:
                formatted_steps.append(f"• {str(s)}")
        
        steps_str = "\n".join(formatted_steps)

        res_info = f"🔗 **Repositorio:** {res.get('repo_url')}"

        msg = (
            f"✅ **Pilot ha completado la tarea con éxito**\n\n"
            f"🛠️ **Proyecto:** {state['project_type'].upper()}\n"
            f"📚 **Stack:** {state['stack']}\n\n"
            f"📋 **PLAN TÉCNICO:**\n{steps_str}\n\n"
            f"🏗️ **ARQUITECTURA & DISEÑO:**\n{architecture}\n\n"
            f"{res_info}"
        )
        
        return {"results": {"status": "success", "message": msg, "warnings": warning_list}}

    async def run(self, prompt: str, payload: dict, images: List[bytes] = None) -> dict:
        initial_state = {
            "prompt": prompt,
            "images": images,
            "project_type": "repo",
            "stack": "React/TypeScript + Tailwind + Supabase",
            "context": "",
            "plan": None,
            "task_result": None,
            "payload": payload,
            "errors": [],
            "warnings": [],
            "results": None
        }
        final_state = await self._graph.ainvoke(initial_state)
        return final_state.get("results")
