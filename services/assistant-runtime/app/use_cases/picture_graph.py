from typing import TypedDict, List, Optional
import json
from langgraph.graph import StateGraph, END
from app.domain.picture.models import PictureEditPlan, PictureOperation
from app.domain.ports.llm import LLMPort
from app.domain.ports.memory import MemoryPort

class PictureState(TypedDict):
    """Estado del flujo de Picture Agent."""
    prompt: str
    images: Optional[List[bytes]]
    image_metadata: List[dict]
    payload: dict
    context: str
    plan: Optional[dict]
    generation_prompt: Optional[str]
    image_url: Optional[str]
    final_message: Optional[str]
    errors: List[str]
    warnings: List[str]
    verification: Optional[dict]
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
        workflow.add_node("execute_image_task", self._execute_image_task_node)
        workflow.add_node("verify_result", self._verify_result_node)
        workflow.add_node("finalize", self._finalize_node)

        # Definir Flujo
        workflow.set_entry_point("initialize")
        workflow.add_edge("initialize", "retrieve_context")
        workflow.add_edge("retrieve_context", "analyze_request")
        workflow.add_edge("analyze_request", "execute_image_task")
        workflow.add_edge("execute_image_task", "verify_result")
        workflow.add_edge("verify_result", "finalize")
        workflow.add_edge("finalize", END)

        return workflow.compile()

    async def _initialize_node(self, state: PictureState) -> dict:
        print("[PICTURE GRAPH] Iniciando...")
        return {"errors": [], "warnings": []}

    async def _retrieve_context_node(self, state: PictureState) -> dict:
        print("[PICTURE GRAPH] Recuperando memoria proactiva...")
        context = await self.memory.get_context("picture")
        return {"context": context}

    async def _analyze_request_node(self, state: PictureState) -> dict:
        print(f"[PICTURE GRAPH] Analizando solicitud: {state['prompt']}")
        
        has_images = bool(state.get("images"))
        system_instruction = (
            "Eres un director de arte experto en herramientas creativas para diseñadores. "
            "Clasifica la solicitud y crea un plan ejecutable. Si hay imagen adjunta, prioriza edición fiel "
            "sobre recreación: conserva composición, logos, colores, espaciado y textos no solicitados. "
            "Responde SOLO JSON con: operation (generate|edit|replace_text|variations), generation_prompt, "
            "edit_prompt, target_text, replacement_text, preserve, quality_checks, confidence."
        )
        
        user_input = state["prompt"]
        if state.get("context"):
            user_input = f"Memoria de Estética/Preferencias:\n{state['context']}\n\nSolicitud: {user_input}"
            
        try:
            analysis = await self.llm.chat(
                (
                    "Crea un plan creativo estructurado para esta solicitud. "
                    f"Hay imagen adjunta: {has_images}. Solicitud/contexto:\n{user_input}"
                ),
                images=state.get("images"),
                system_instruction=system_instruction,
            )

            data = _extract_json_object(analysis)
            plan = PictureEditPlan.from_llm(data, original_prompt=state["prompt"], has_images=has_images)
            return {"plan": plan.to_dict(), "generation_prompt": plan.prompt}
        except Exception as e:
            print(f"[PICTURE GRAPH ERROR] Fallo análisis: {e}")
            plan = PictureEditPlan.infer(state["prompt"], has_images=has_images)
            return {
                "plan": plan.to_dict(),
                "generation_prompt": plan.prompt,
                "warnings": [f"Se usó análisis heurístico porque falló el plan del LLM: {e}"],
            }

    async def _execute_image_task_node(self, state: PictureState) -> dict:
        plan = PictureEditPlan.from_llm(state.get("plan") or {}, state["prompt"], bool(state.get("images")))
        prompt = plan.edit_prompt if plan.operation != PictureOperation.GENERATE else plan.prompt
        print(f"[PICTURE GRAPH] Ejecutando {plan.operation.value}: {prompt[:50]}...")
        try:
            if plan.operation == PictureOperation.GENERATE:
                picture_context = _picture_context(state, plan)
                try:
                    url = await self.llm.generate_image(prompt, context=picture_context)
                except TypeError as exc:
                    if "context" not in str(exc):
                        raise
                    url = await self.llm.generate_image(prompt)
            else:
                images = state.get("images") or []
                if not images:
                    return {"errors": ["Esta solicitud requiere una imagen adjunta para editar el diseño."]}
                metadata = _first_image_metadata(state.get("image_metadata") or [])
                context = _picture_context(state, plan, metadata)
                url = await self.llm.edit_image(
                    prompt,
                    image=images[0],
                    context=context,
                    image_mime=metadata.get("content_type"),
                    image_filename=metadata.get("filename"),
                )

            await self.memory.save_memory("picture_style", _memory_summary(plan))
            return {"image_url": url, "plan": plan.to_dict()}
        except Exception as e:
            return {"errors": [f"Error procesando imagen: {str(e)}"], "plan": plan.to_dict()}

    async def _verify_result_node(self, state: PictureState) -> dict:
        if state.get("errors"):
            return {}

        plan = state.get("plan") or {}
        operation = plan.get("operation", "generate")
        if operation == PictureOperation.GENERATE.value:
            return {"verification": {"status": "skipped", "reason": "generation_only"}}
        if state.get("payload", {}).get("verify_result") is False:
            return {"verification": {"status": "skipped", "reason": "disabled_by_payload"}}

        image_b64 = _image_b64(state.get("image_url"))
        if not image_b64:
            return {
                "verification": {
                    "status": "skipped",
                    "reason": "result_url_requires_external_fetch",
                },
                "warnings": state.get("warnings", []) + [
                    "No pude verificar automáticamente el resultado porque el proveedor devolvió una URL en vez de bytes."
                ],
            }

        try:
            import base64
            import binascii

            edited_image = base64.b64decode(image_b64, validate=True)
            verification_text = await self.llm.chat(
                (
                    "Verifica el resultado de edición de imagen contra este plan. "
                    "Responde SOLO JSON con passed (boolean), confidence (0-1), findings (array), "
                    f"requires_human_review (boolean). Plan:\n{json.dumps(plan, ensure_ascii=False)}"
                ),
                images=[edited_image],
                system_instruction=(
                    "Eres QA visual para diseño. Evalúas si la edición cumple la solicitud, "
                    "si el texto pedido está presente, si el texto anterior desapareció y si el layout se conserva."
                ),
            )
            verification = _normalize_verification(_extract_json_object(verification_text))
            warnings = state.get("warnings", [])
            if not verification["passed"]:
                warnings = warnings + ["La verificación automática marcó el resultado para revisión humana."]
            return {"verification": verification, "warnings": warnings}
        except (binascii.Error, ValueError, json.JSONDecodeError) as exc:
            return {
                "verification": {"status": "error", "reason": str(exc), "requires_human_review": True},
                "warnings": state.get("warnings", []) + [f"No pude verificar automáticamente el resultado: {exc}"],
            }

    async def _finalize_node(self, state: PictureState) -> dict:
        if state.get("errors"):
            return {"results": {"status": "error", "message": "\n".join(state["errors"]), "warnings": state.get("warnings", [])}}

        plan = state.get("plan") or {}
        verification = state.get("verification") or {"status": "skipped"}
        operation = plan.get("operation", "generate")
        checks = plan.get("quality_checks") or []
        checks_text = "\n".join(f"- {item}" for item in checks[:4])
        warning_text = ""
        if state.get("warnings"):
            warning_text = "\n\n**Avisos:**\n" + "\n".join(f"- {item}" for item in state["warnings"])

        image_ref = _image_reference_for_message(state["image_url"])
        msg = (
            "🎨 **Resultado Picture Agent**\n\n"
            f"**Modo:** `{operation}`\n"
            f"**Prompt aplicado:** {state.get('generation_prompt')}\n"
            f"{warning_text}"
        )
        if checks_text:
            msg += f"\n\n**Checks esperados:**\n{checks_text}"
        if verification.get("status") != "skipped":
            msg += f"\n\n**Verificación:** {verification.get('status', 'unknown')}"
            if verification.get("findings"):
                msg += "\n" + "\n".join(f"- {item}" for item in verification["findings"][:3])
        if image_ref:
            msg += f"\n\n{image_ref}"

        image_b64 = _image_b64(state["image_url"])
        status = "success"
        if verification.get("requires_human_review") or verification.get("passed") is False:
            status = "needs_review"
        return {
            "results": {
                "status": status,
                "message": msg,
                "warnings": state.get("warnings", []),
                "picture_plan": plan,
                "verification": verification,
                "image_url": state["image_url"] if not image_b64 else None,
                "image_b64": image_b64,
            }
        }

    async def run(self, prompt: str, payload: dict, images: List[bytes] = None, image_metadata: List[dict] = None) -> dict:
        initial_state = {
            "prompt": prompt,
            "images": images,
            "image_metadata": image_metadata or [],
            "payload": payload,
            "context": "",
            "plan": None,
            "generation_prompt": None,
            "image_url": None,
            "final_message": None,
            "errors": [],
            "warnings": [],
            "verification": None,
            "results": None
        }
        final_state = await self._graph.ainvoke(initial_state)
        return final_state.get("results")


def _extract_json_object(value: str) -> dict:
    text = (value or "").strip()
    if "```json" in text:
        text = text.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in text:
        text = text.split("```", 1)[1].split("```", 1)[0].strip()
    elif "{" in text and "}" in text:
        text = text[text.find("{"): text.rfind("}") + 1]
    return json.loads(text)


def _memory_summary(plan: PictureEditPlan) -> str:
    parts = [
        f"Operación: {plan.operation.value}",
        f"Prompt: {plan.prompt[:140]}",
    ]
    if plan.target_text or plan.replacement_text:
        parts.append(f"Texto: {plan.target_text or '?'} -> {plan.replacement_text or '?'}")
    if plan.preserve:
        parts.append(f"Preservar: {', '.join(plan.preserve[:5])}")
    return " | ".join(parts)


def _image_b64(image_ref: str | None) -> str | None:
    if not image_ref or not image_ref.startswith("data:image/"):
        return None
    if "," not in image_ref:
        return None
    return image_ref.split(",", 1)[1].strip() or None


def _image_reference_for_message(image_ref: str | None) -> str:
    if not image_ref:
        return ""
    if image_ref.startswith("data:image/"):
        return "[imagen adjunta como archivo]"
    return image_ref


def _first_image_metadata(metadata: List[dict]) -> dict:
    if not metadata:
        return {}
    first = metadata[0] or {}
    return {
        "filename": first.get("filename"),
        "content_type": first.get("content_type"),
        "size": first.get("size"),
    }


def _picture_context(state: PictureState, plan: PictureEditPlan, metadata: dict | None = None) -> dict:
    payload = state.get("payload") or {}
    context = {
        **plan.to_dict(),
        "prefer_free_model": bool(payload.get("prefer_free_model")),
        "image_generation_provider": payload.get("image_generation_provider"),
        "image_edit_provider": payload.get("image_edit_provider"),
    }
    if metadata is not None:
        context["base_image"] = metadata
        context["reference_images"] = (state.get("image_metadata") or [])[1:]
    return context


def _normalize_verification(data: dict) -> dict:
    findings = data.get("findings")
    if not isinstance(findings, list):
        findings = []
    confidence = data.get("confidence", 0)
    try:
        confidence = max(0.0, min(1.0, float(confidence)))
    except (TypeError, ValueError):
        confidence = 0.0
    passed = bool(data.get("passed")) and confidence >= 0.65
    return {
        "status": "passed" if passed else "needs_review",
        "passed": passed,
        "confidence": confidence,
        "findings": [str(item).strip() for item in findings if str(item).strip()],
        "requires_human_review": bool(data.get("requires_human_review")) or not passed,
    }
