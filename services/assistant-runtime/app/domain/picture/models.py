from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class PictureOperation(str, Enum):
    GENERATE = "generate"
    EDIT = "edit"
    REPLACE_TEXT = "replace_text"
    VARIATIONS = "variations"


@dataclass(frozen=True)
class PictureEditPlan:
    operation: PictureOperation
    prompt: str
    edit_prompt: str
    preserve: list[str] = field(default_factory=list)
    target_text: str | None = None
    replacement_text: str | None = None
    quality_checks: list[str] = field(default_factory=list)
    confidence: float = 0.5

    @classmethod
    def from_llm(cls, data: dict[str, Any], original_prompt: str, has_images: bool) -> "PictureEditPlan":
        operation = _normalize_operation(data.get("operation"), original_prompt, has_images)
        edit_prompt = str(data.get("edit_prompt") or data.get("generation_prompt") or original_prompt).strip()
        preserve = _string_list(data.get("preserve")) or _default_preserve(operation)
        quality_checks = _string_list(data.get("quality_checks")) or _default_quality_checks(operation)
        confidence = _clamp_float(data.get("confidence"), default=0.65 if has_images else 0.5)

        return cls(
            operation=operation,
            prompt=str(data.get("generation_prompt") or edit_prompt or original_prompt).strip(),
            edit_prompt=edit_prompt,
            preserve=preserve,
            target_text=_optional_text(data.get("target_text")),
            replacement_text=_optional_text(data.get("replacement_text")),
            quality_checks=quality_checks,
            confidence=confidence,
        )

    @classmethod
    def infer(cls, prompt: str, has_images: bool) -> "PictureEditPlan":
        operation = _normalize_operation(None, prompt, has_images)
        edit_prompt = _default_edit_prompt(prompt, operation)
        return cls(
            operation=operation,
            prompt=prompt,
            edit_prompt=edit_prompt,
            preserve=_default_preserve(operation),
            quality_checks=_default_quality_checks(operation),
            confidence=0.45 if has_images else 0.35,
        )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["operation"] = self.operation.value
        return data


def _normalize_operation(value: Any, prompt: str, has_images: bool) -> PictureOperation:
    raw = str(value or "").strip().lower().replace("-", "_")
    if raw in {item.value for item in PictureOperation}:
        return PictureOperation(raw)

    lowered = prompt.lower()
    text_markers = ("texto", "text", "copy", "headline", "titulo", "título", "reemplaza", "cambia")
    edit_markers = ("edita", "edit", "modifica", "ajusta", "quita", "remueve", "cambia", "replace")
    variation_markers = ("variacion", "variación", "variaciones", "variations", "versiones")

    if has_images and any(marker in lowered for marker in text_markers):
        return PictureOperation.REPLACE_TEXT
    if has_images and any(marker in lowered for marker in variation_markers):
        return PictureOperation.VARIATIONS
    if has_images and any(marker in lowered for marker in edit_markers):
        return PictureOperation.EDIT
    if has_images:
        return PictureOperation.EDIT
    return PictureOperation.GENERATE


def _default_edit_prompt(prompt: str, operation: PictureOperation) -> str:
    if operation == PictureOperation.REPLACE_TEXT:
        return (
            "Edit the provided design. Replace only the requested text while preserving layout, "
            f"typography style, hierarchy, colors, spacing, logo placement, and all other visual elements. Request: {prompt}"
        )
    if operation == PictureOperation.VARIATIONS:
        return f"Create a faithful design variation from the provided image. Preserve brand and layout logic. Request: {prompt}"
    if operation == PictureOperation.EDIT:
        return f"Edit the provided image while preserving everything not explicitly requested. Request: {prompt}"
    return prompt


def _default_preserve(operation: PictureOperation) -> list[str]:
    if operation in {PictureOperation.EDIT, PictureOperation.REPLACE_TEXT, PictureOperation.VARIATIONS}:
        return ["composition", "brand identity", "colors", "spacing", "logos", "non-target text"]
    return []


def _default_quality_checks(operation: PictureOperation) -> list[str]:
    if operation == PictureOperation.REPLACE_TEXT:
        return ["replacement text is present", "old target text is absent", "layout is preserved"]
    if operation in {PictureOperation.EDIT, PictureOperation.VARIATIONS}:
        return ["requested change is visible", "unrequested regions are preserved"]
    return ["prompt intent is represented"]


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _clamp_float(value: Any, default: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return max(0.0, min(1.0, number))
