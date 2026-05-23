import base64
import os

from app.domain.ports.coder_web import CoderWebAsset


def validate_generated_files(raw_files) -> list[dict]:
    if not isinstance(raw_files, list) or not raw_files:
        raise ValueError("La respuesta del LLM no incluyo archivos.")
    files = []
    for item in raw_files:
        if not isinstance(item, dict):
            raise ValueError("Cada archivo debe ser un objeto.")
        path = str(item.get("path") or "").strip()
        content = item.get("content")
        if not path or content is None:
            raise ValueError("Cada archivo requiere path y content.")
        files.append({"path": path, "content": str(content)})
    paths = {file["path"] for file in files}
    if not any(path.endswith("package.json") for path in paths):
        raise ValueError("El paquete debe incluir package.json para validacion build/test.")
    return files


def task_name(payload: dict, prompt: str, linear_issue: dict | None = None) -> str:
    raw = (
        payload.get("task_name")
        or payload.get("name")
        or (linear_issue or {}).get("identifier")
        or (linear_issue or {}).get("title")
        or prompt[:48]
        or f"coder-web-{os.urandom(2).hex()}"
    )
    return str(raw).strip()


def asset_from_image(index: int, image: bytes) -> CoderWebAsset:
    ext = "png" if image.startswith(b"\x89PNG") else "jpg" if image.startswith(b"\xff\xd8") else "bin"
    return CoderWebAsset(
        path=f"public/coder-web-assets/reference-{index}.{ext}",
        content_b64=base64.b64encode(image).decode("ascii"),
    )
