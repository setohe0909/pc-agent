import os
import re
from datetime import datetime
from pathlib import Path
from app.domain.ports.llm import LLMPort
from app.domain.ports.memory import MemoryPort

SUPPORTED_WRITER_COMMANDS = {"chat", "blog", "storytelling"}


class WriterWorkflow:
    def __init__(self, llm_port: LLMPort, memory_port: MemoryPort | None = None) -> None:
        self.llm = llm_port
        self.memory = memory_port
        self.obsidian_path = os.getenv("OBSIDIAN_VAULT_PATH", "/tmp/obsidian_vault")

    async def execute_writer_action(self, prompt: str, payload: dict) -> dict:
        payload = payload or {}
        sub_command = (payload.get("sub_command") or "chat").strip().lower()
        language = (payload.get("language") or "es").strip().lower()

        if sub_command not in SUPPORTED_WRITER_COMMANDS:
            return self._error(
                code="writer.unsupported_action",
                message=f"Writer no soporta la accion `{sub_command}`.",
                hint=f"Acciones soportadas: {', '.join(sorted(SUPPORTED_WRITER_COMMANDS))}.",
            )
        if not prompt or not prompt.strip():
            return self._error(
                code="writer.empty_prompt",
                message="Writer necesita un prompt con el tema o instruccion editorial.",
                hint="Envia una idea, briefing o texto base para trabajar.",
            )

        if sub_command == "blog":
            return await self._create_blog(prompt.strip(), language)
        if sub_command == "storytelling":
            return await self._create_storytelling(prompt.strip(), language)
        return await self._writer_chat(prompt.strip(), language)

    async def _writer_chat(self, prompt: str, language: str) -> dict:
        memory_context = ""
        if self.memory:
            memory_context = await self.memory.get_context("writer")

        lang_name = "Español" if language == "es" else "Inglés"
        system_instructions = (
            "Eres un experto en Copywriting, Storytelling y Redacción de Blogs de marca. "
            f"Tu idioma principal de respuesta para el contenido debe ser {lang_name}. "
            "Tu tono es creativo, profesional y persuasivo.\n"
            f"{memory_context}"
        )
        response = await self.llm.chat(prompt, system_instruction=system_instructions)
        await self._record_run("chat", prompt, response, None)
        return self._success(
            command="chat",
            message=response,
            content=response,
            artifact=None,
            metadata={"language": language},
        )

    async def _create_blog(self, prompt: str, language: str) -> dict:
        brand_info = await self._get_brand_info()
        trends = await self._get_trends()
        
        lang_name = "Español" if language == "es" else "Inglés"
        blog_prompt = (
            f"Genera un artículo de Blog profesional y optimizado para SEO.\n"
            f"Idioma: {lang_name}\n"
            f"Información de Marca: {brand_info}\n"
            f"Tendencias: {trends}\n"
            f"Idea/Tema: {prompt}\n\n"
            "El artículo debe incluir un título atractivo, introducción, subtítulos y una conclusión con llamado a la acción. "
            "IMPORTANTE: El título debe estar en la primera línea del mensaje."
        )
        
        content = await self.llm.chat(blog_prompt)
        keywords = await self._get_image_keywords(content)
        image_md = (
            "\n\n"
            f"<!-- Imagen sugerida: buscar asset licenciado para `{keywords}` antes de publicar. -->\n"
        )
        
        full_content = content + image_md
        first_line = content.split('\n')[0]
        title = first_line.replace('#', '').strip()[:50] or "blog-sin-titulo"
        
        try:
            filename = self._save_to_obsidian("Blog", title, full_content)
            await self._record_run("blog", prompt, full_content, filename)
            return self._success(
                command="blog",
                message=f"Blog creado y guardado en Obsidian: `{filename}`\n\n{full_content}",
                content=full_content,
                artifact=filename,
                metadata={"language": language, "image_keywords": keywords},
            )
        except Exception as e:
            return self._persistence_error("blog", str(e), full_content)

    async def _create_storytelling(self, prompt: str, language: str) -> dict:
        brand_info = await self._get_brand_info()
        
        lang_name = "Español" if language == "es" else "Inglés"
        story_prompt = (
            f"Genera una pieza de Storytelling emocional y cautivadora para la marca.\n"
            f"Idioma: {lang_name}\n"
            f"Información de Marca: {brand_info}\n"
            f"Contexto/Idea: {prompt}\n\n"
            "Usa una narrativa que conecte profundamente con la audiencia (ej: Viaje del Héroe). "
            "IMPORTANTE: El título debe estar en la primera línea del mensaje."
        )
        
        content = await self.llm.chat(story_prompt)
        keywords = await self._get_image_keywords(content)
        image_md = (
            "\n\n"
            f"<!-- Imagen sugerida: buscar asset licenciado para `{keywords}` antes de publicar. -->\n"
        )
        
        full_content = content + image_md

        first_line = content.split('\n')[0]
        title = first_line.replace('#', '').strip()[:50] or "story-sin-titulo"
        
        try:
            filename = self._save_to_obsidian("Story-telling", title, full_content)
            await self._record_run("storytelling", prompt, full_content, filename)
            return self._success(
                command="storytelling",
                message=f"Storytelling creado y guardado en Obsidian: `{filename}`\n\n{full_content}",
                content=full_content,
                artifact=filename,
                metadata={"language": language, "image_keywords": keywords},
            )
        except Exception as e:
            return self._persistence_error("storytelling", str(e), full_content)

    async def _get_image_keywords(self, content: str) -> str:
        """Pide al LLM 2 o 3 keywords en inglés para buscar una imagen representativa"""
        prompt = (
            f"Analiza este texto y devuelve 2 o 3 palabras clave en INGLÉS que describan la estética visual ideal para este contenido. "
            f"Responde únicamente las palabras separadas por comas, sin nada más.\n\n"
            f"Texto: {content[:500]}"
        )
        try:
            keywords = await self.llm.chat(prompt)
            # Limpiar posibles extras del LLM
            clean_keywords = keywords.strip().replace(".", "").replace("Keywords:", "").strip()
            return clean_keywords.replace(", ", ",")
        except Exception:
            return "lifestyle,minimalist"

    async def _get_brand_info(self) -> str:
        if self.memory:
            context = await self.memory.get_context("writer")
            if context:
                return context
        return "Sin contexto de marca configurado. Solicita brand voice, audiencia, oferta y restricciones antes de publicar."

    async def _get_trends(self) -> str:
        # Recuperar tendencias guardadas por el Marketer
        if self.memory:
            return await self.memory.get_context("marketing_trend")
        return "Minimalismo, autenticidad, sostenibilidad."

    def _save_to_obsidian(self, folder: str, title: str, content: str) -> str:
        date_str = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        clean_title = self._safe_filename(title)
        filename = f"{clean_title}-{date_str}.md"
        
        base_dir = Path(self.obsidian_path)
        target_dir = base_dir / folder
        
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
            self._apply_obsidian_permissions(target_dir, is_dir=True)
        except Exception as e:
            print(f"[OBSIDIAN ERROR] No se pudo crear el directorio {target_dir}: {e}")
            raise e
        
        file_path = target_dir / filename
        file_path.write_text(content, encoding="utf-8")
        self._apply_obsidian_permissions(file_path, is_dir=False)
        
        return f"{folder}/{filename}"

    def _safe_filename(self, title: str) -> str:
        normalized = re.sub(r"\s+", "-", title.strip().lower())
        cleaned = re.sub(r"[^a-z0-9\-_]+", "", normalized)
        return cleaned[:70].strip("-_") or "writer-draft"

    def _apply_obsidian_permissions(self, path: Path, is_dir: bool) -> None:
        mode = 0o775 if is_dir else 0o664
        try:
            path.chmod(mode)
        except Exception as exc:
            print(f"[OBSIDIAN PERMISSIONS WARNING] No se pudo ajustar chmod en {path}: {exc}")

        uid, gid = self._obsidian_owner_ids(path)
        if uid is None and gid is None:
            return
        try:
            os.chown(path, -1 if uid is None else uid, -1 if gid is None else gid)
        except AttributeError:
            return
        except PermissionError as exc:
            print(f"[OBSIDIAN PERMISSIONS WARNING] No se pudo ajustar propietario en {path}: {exc}")
        except Exception as exc:
            print(f"[OBSIDIAN PERMISSIONS WARNING] Error ajustando propietario en {path}: {exc}")

    def _obsidian_owner_ids(self, path: Path) -> tuple[int | None, int | None]:
        uid = self._parse_optional_int(os.getenv("OBSIDIAN_FILE_UID") or os.getenv("PUID"))
        gid = self._parse_optional_int(os.getenv("OBSIDIAN_FILE_GID") or os.getenv("PGID"))
        if (uid is None or gid is None) and self._is_container_vault_path(path):
            uid = 1000 if uid is None else uid
            gid = 1000 if gid is None else gid
        return uid, gid

    def _is_container_vault_path(self, path: Path) -> bool:
        try:
            return path.resolve().is_relative_to(Path("/vault"))
        except Exception:
            return str(path).startswith("/vault/")

    def _parse_optional_int(self, value: str | None) -> int | None:
        if value is None or value == "":
            return None
        try:
            return int(value)
        except ValueError:
            return None

    async def _record_run(self, command: str, prompt: str, content: str, artifact: str | None) -> None:
        if not self.memory:
            return
        try:
            await self.memory.save_interaction("writer", {
                "role": "assistant",
                "command": command,
                "prompt": prompt[:500],
                "artifact": artifact,
                "content_preview": content[:500],
                "created_at": datetime.utcnow().isoformat(),
            })
        except Exception as exc:
            print(f"[WRITER][MEMORY ERROR] {exc}")

    def _success(self, command: str, message: str, content: str, artifact: str | None, metadata: dict) -> dict:
        return {
            "status": "success",
            "message": message,
            "command": command,
            "content": content,
            "artifact": artifact,
            "metadata": metadata,
        }

    def _error(self, code: str, message: str, hint: str) -> dict:
        return {
            "status": "error",
            "code": code,
            "message": message,
            "hint": hint,
            "retryable": False,
        }

    def _persistence_error(self, command: str, detail: str, content: str) -> dict:
        return {
            "status": "error",
            "code": "writer.persistence_failed",
            "message": f"Writer genero el contenido de `{command}`, pero no pudo guardarlo.",
            "hint": "Revisa OBSIDIAN_VAULT_PATH y permisos de escritura antes de usarlo en produccion.",
            "retryable": True,
            "error_detail": detail,
            "content": content,
        }
