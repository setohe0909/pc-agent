from typing import Annotated, TypedDict, Union, List, Optional
import json
from langgraph.graph import StateGraph, END
from app.domain.ports.llm import LLMPort
from app.domain.ports.memory import MemoryPort

class PictureState(TypedDict):
    """Estado del flujo de Picture Agent v0.1.0."""
    prompt: str
    images: Optional[List[bytes]]
    payload: dict
    context: str
    generation_prompt: Optional[str]
    image_url: Optional[str]
    final_message: Optional[str]
    errors: List[str]
    results: Optional[dict]


class PictureGraph:
    def __init__(self, llm: LLMPort, memory: MemoryPort):
        self.llm = llm
        self.memory = memory
        self._graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(PictureState)

        # Definir Nodos
        workflow.add_node("initialize", self._initialize_node)
        workflow.add_node("retrieve_context", self._retrieve_context_node)
        workflow.add_node("analyze_request", self._analyze_request_node)
        workflow.add_node("generate_image", self._generate_image_node)
        workflow.add_node("finalize", self._finalize_node)

        # Definir Flujo
        workflow.set_entry_point("initialize")
        workflow.add_edge("initialize", "retrieve_context")
        workflow.add_edge("retrieve_context", "analyze_request")
        workflow.add_edge("analyze_request", "generate_image")
        workflow.add_edge("generate_image", "finalize")
        workflow.add_edge("finalize", END)

        return workflow.compile()

    async def _initialize_node(self, state: PictureState) -> dict:
        print("[PICTURE GRAPH] Iniciando...")
        return {"errors": []}

    async def _retrieve_context_node(self, state: PictureState) -> dict:
        print("[PICTURE GRAPH] Recuperando memoria proactiva...")
        context = await self.memory.get_context("picture")
        return {"context": context}

    async def _analyze_request_node(self, state: PictureState) -> dict:
        print(f"[PICTURE GRAPH] Analizando solicitud: {state['prompt']}")
        
        system_instruction = (
            "Eres un experto en generación de imágenes y prompt engineering. "
            "Tu objetivo es crear un prompt altamente detallado para un generador de imágenes (Imagen 3) "
            "basado en la solicitud del usuario, el contexto de memoria y las imágenes proporcionadas (si las hay). "
            "Si hay imágenes adjuntas, úsalas como referencia estética o temática. "
            "Responde en formato JSON con la clave 'generation_prompt'."
        )
        
        user_input = state["prompt"]
        if state.get("context"):
            user_input = f"Memoria de Estética/Preferencias:\n{state['context']}\n\nSolicitud: {user_input}"
            
        try:
            # Usamos el chat con soporte de visión si hay imágenes
            analysis = await self.llm.chat(
                f"Genera un prompt detallado para un generador de imágenes basado en esto: {user_input}. Responde SOLO el JSON con 'generation_prompt'.",
                images=state.get("images")
            )
            
            # Limpiar respuesta si el LLM no fue estricto con JSON
            if "```json" in analysis:
                analysis = analysis.split("```json")[1].split("```")[0].strip()
            elif "{" not in analysis:
                 return {"generation_prompt": state["prompt"]} # Fallback al prompt original

            data = json.loads(analysis)
            return {"generation_prompt": data.get("generation_prompt", state["prompt"])}
        except Exception as e:
            print(f"[PICTURE GRAPH ERROR] Fallo análisis: {e}")
            return {"generation_prompt": state["prompt"]}

    async def _generate_image_node(self, state: PictureState) -> dict:
        prompt = state.get("generation_prompt") or state["prompt"]
        print(f"[PICTURE GRAPH] Generando imagen para: {prompt[:50]}...")
        try:
            url = await self.llm.generate_image(prompt)
            # Guardamos un resumen en memoria de lo que generamos (Memoria Proactiva)
            await self.memory.save_memory("picture_style", f"Generada imagen con prompt: {prompt[:100]}...")
            return {"image_url": url}
        except Exception as e:
            return {"errors": [f"Error generando imagen: {str(e)}"]}

    async def _finalize_node(self, state: PictureState) -> dict:
        if state.get("errors"):
            return {"results": {"status": "error", "message": "\n".join(state["errors"])}}
        
        msg = f"🎨 **Imagen Generada con Éxito**\n\n**Prompt Utilizado:** {state.get('generation_prompt')}\n\n{state['image_url']}"
        return {"results": {"status": "success", "message": msg}}

    async def run(self, prompt: str, payload: dict, images: List[bytes] = None) -> dict:
        initial_state = {
            "prompt": prompt,
            "images": images,
            "payload": payload,
            "context": "",
            "generation_prompt": None,
            "image_url": None,
            "final_message": None,
            "errors": [],
            "results": None
        }
        final_state = await self._graph.ainvoke(initial_state)
        return final_state.get("results")
