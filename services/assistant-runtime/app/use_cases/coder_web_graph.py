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
    project_type: str  # 'repo' or 'wix'
    stack: str
    context: str
    plan: Optional[dict]
    task_result: Optional[dict]
    versioning_status: Optional[dict]
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
        workflow.add_node("pilot_versioning", self._pilot_versioning_node)
        workflow.add_node("execute_pilot_task", self._execute_pilot_task_node)
        workflow.add_node("finalize", self._finalize_node)

        # Definir Flujo
        workflow.set_entry_point("initialize")
        workflow.add_edge("initialize", "analyze_mockup")
        workflow.add_edge("analyze_mockup", "analyze_references")
        workflow.add_edge("analyze_references", "retrieve_context")
        workflow.add_edge("retrieve_context", "analyze_request")
        workflow.add_edge("analyze_request", "plan_review")
        
        # Flujo condicional: Si es Wix, versionamos antes de tocar
        workflow.add_conditional_edges(
            "plan_review",
            self._decide_versioning,
            {
                "wix_flow": "pilot_versioning",
                "repo_flow": "execute_pilot_task"
            }
        )
        
        workflow.add_edge("pilot_versioning", "execute_pilot_task")
        workflow.add_edge("execute_pilot_task", "finalize")
        workflow.add_edge("finalize", END)

        return workflow.compile()

    def _decide_versioning(self, state: CoderWebState):
        if state.get("project_type") == "wix":
            return "wix_flow"
        return "repo_flow"

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
            "Tu objetivo es diseñar una solución técnica. "
            "Stack default para repos: React/TS + Tailwind + Supabase. "
            "Para Wix: Usa Velo API. "
            "Responde en formato JSON con: "
            "'project_type' (repo|wix), 'stack', 'plan' (objeto con 'steps' y 'architecture'), 'site_id' (si es wix)."
        )
        
        try:
            analysis = await self.llm.chat(
                f"{system_instruction}\n\nContexto:\n{state['context']}\n\nSolicitud: {state['prompt']}\n\nResponde SOLO JSON."
            )
            
            if "```json" in analysis:
                analysis = analysis.split("```json")[1].split("```")[0].strip()
            
            data = json.loads(analysis)
            return {
                "project_type": data.get("project_type", "repo"),
                "plan": data.get("plan", {"steps": ["Inicializar"], "architecture": "Standard"}),
                "stack": data.get("stack", state["stack"]),
                "payload": {**state["payload"], "site_id": state["payload"].get("site_id") or data.get("site_id")}
            }
        except Exception as e:
            print(f"[CODER-WEB ERROR] Fallo análisis: {e}")
            return {"project_type": "repo", "plan": {"steps": ["Default Repo Setup"], "architecture": "Basic"}}

    async def _plan_review_node(self, state: CoderWebState) -> dict:
        print("[CODER-WEB GRAPH][REVIEW] Validando plan de Pilot...")
        plan_str = json.dumps(state["plan"])
        prompt = (
            f"Como experto arquitecto, revisa este plan de Pilot para un proyecto {state['project_type']}:\n{plan_str}\n\n"
            f"Asegúrate de que el stack {state['stack']} se use correctamente. Sugiere mejoras si faltan componentes críticos de e-commerce."
        )
        sys_instr = "Eres el Arquitecto Pilot. Revisa y optimiza planes de desarrollo web."
        review = await self.llm.chat(prompt, context={"project_context": state["context"]}, system_instruction=sys_instr)
        # Inyectamos la revisión en el plan para la ejecución
        updated_plan = {**state["plan"], "review_notes": review}
        return {"plan": updated_plan}

    async def _pilot_versioning_node(self, state: CoderWebState) -> dict:
        site_id = state["payload"].get("site_id", "default_site")
        print(f"[CODER-WEB GRAPH][VERSIONING] Creando snapshot para Wix Site: {site_id}")
        version = await self.coder_web.create_site_version(site_id, f"Pre-update: {state['prompt'][:20]}")
        return {"versioning_status": version}

    async def _execute_pilot_task_node(self, state: CoderWebState) -> dict:
        project_type = state["project_type"]
        plan = state["plan"]
        print(f"[CODER-WEB GRAPH][EXECUTE] Pilot ejecutando {project_type}")
        
        try:
            if project_type == "repo":
                res = await self.coder_web.create_repository(
                    name=f"ecommerce-{os.urandom(2).hex()}",
                    stack=state["stack"],
                    description=state["prompt"]
                )
            else:
                site_id = state["payload"].get("site_id", "unknown_site")
                # Siempre trabajamos en DRAFT por defecto para iteración segura
                res = await self.coder_web.update_site_draft(site_id, plan)
            
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
        v_status = state.get("versioning_status", {})
        if v_status.get("status") == "success":
            v_info = f"\n📦 **Versión Wix Guardada:** {v_status.get('version_id')}"
        else:
            v_info = f"\n❌ **Fallo Versión Wix:** {v_status.get('message', 'Desconocido')}"
            
        res_info = f"🔗 **Resultado:** {res.get('repo_url') or res.get('summary')}"
        if res.get("preview_url"):
            res_info += f"\n🌐 **Link de Previsualización:** {res.get('preview_url')}"

        steps = state['plan'].get('steps', [])
        formatted_steps = []
        for s in steps:
            if isinstance(s, dict):
                formatted_steps.append(s.get("description") or s.get("name") or str(s))
            else:
                formatted_steps.append(str(s))

        msg = (
            f"✅ **Pilot ha completado la tarea con éxito**\n\n"
            f"🛠️ **Tipo de Proyecto:** {state['project_type'].upper()}\n"
            f"📚 **Stack:** {state['stack']}\n"
            f"📝 **Plan Ejecutado:** {', '.join(formatted_steps)}\n\n"
            f"{v_info}\n"
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
            "versioning_status": None,
            "payload": payload,
            "errors": [],
            "warnings": [],
            "results": None
        }
        final_state = await self._graph.ainvoke(initial_state)
        return final_state.get("results")
