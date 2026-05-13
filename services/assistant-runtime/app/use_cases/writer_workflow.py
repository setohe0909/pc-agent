import os
import json
from datetime import datetime
from pathlib import Path
from app.domain.ports.llm import LLMPort
from app.domain.ports.memory import MemoryPort

class WriterWorkflow:
    def __init__(self, llm_port: LLMPort, memory_port: MemoryPort | None = None) -> None:
        self.llm = llm_port
        self.memory = memory_port
        # Obsidian path can be configured via environment variable
        self.obsidian_path = os.getenv("OBSIDIAN_VAULT_PATH", "/tmp/obsidian_vault")

    async def execute_writer_action(self, prompt: str, payload: dict) -> dict:
        sub_command = payload.get("sub_command", "chat")
        language = payload.get("language", "es") # Default to Spanish
        
        if sub_command == "blog":
            return await self._create_blog(prompt, language)
        elif sub_command == "storytelling":
            return await self._create_storytelling(prompt, language)
        else:
            return await self._writer_chat(prompt, language)

    async def _writer_chat(self, prompt: str, language: str) -> dict:
        # Recuperar memoria relevante
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
        response = await self.llm.chat(full_prompt, system_instruction=system_instructions)
        return {"status": "success", "message": response}

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
        
        # Generar imagen sugerida
        keywords = await self._get_image_keywords(content)
        image_url = f"https://source.unsplash.com/featured/?{keywords}"
        image_md = f"\n\n![Featured Image]({image_url})\n*Imagen sugerida vía Unsplash para: {keywords}*\n\n"
        
        full_content = content + image_md
        
        # Extraer título (primer línea usualmente)
        first_line = content.split('\n')[0]
        title = first_line.replace('#', '').strip()[:50] or "blog-sin-titulo"
        
        try:
            filename = self._save_to_obsidian("Blog", title, full_content)
            return {
                "status": "success", 
                "message": f"✅ Blog creado (con imagen) y guardado en Obsidian: `{filename}`\n\n{full_content}"
            }
        except Exception as e:
            return {
                "status": "success",
                "message": f"✅ Blog generado pero hubo un error al guardar en Obsidian: {str(e)}\n\n{full_content}"
            }

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
        
        # Generar imagen sugerida
        keywords = await self._get_image_keywords(content)
        image_url = f"https://source.unsplash.com/featured/?{keywords}"
        image_md = f"\n\n![Story Image]({image_url})\n*Visualización narrativa sugerida*\n\n"
        
        full_content = content + image_md

        # Extraer título
        first_line = content.split('\n')[0]
        title = first_line.replace('#', '').strip()[:50] or "story-sin-titulo"
        
        try:
            filename = self._save_to_obsidian("Story-telling", title, full_content)
            return {
                "status": "success", 
                "message": f"✅ Storytelling creado (con imagen) y guardado en Obsidian: `{filename}`\n\n{full_content}"
            }
        except Exception as e:
            return {
                "status": "success",
                "message": f"✅ Storytelling generado pero hubo un error al guardar en Obsidian: {str(e)}\n\n{full_content}"
            }

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
        except:
            return "lifestyle,minimalist"

    async def _get_brand_info(self) -> str:
        # En una implementación real, podríamos buscar específicamente 'brand_info' en la memoria
        return "Información de marca general basada en el contexto del sistema."

    async def _get_trends(self) -> str:
        # Recuperar tendencias guardadas por el Marketer
        if self.memory:
            return await self.memory.get_context("marketing_trend")
        return "Minimalismo, autenticidad, sostenibilidad."

    def _save_to_obsidian(self, folder: str, title: str, content: str) -> str:
        date_str = datetime.now().strftime("%Y-%m-%d")
        # Limpiar el título para que sea un nombre de archivo válido
        clean_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
        filename = f"{clean_title}-{date_str}.md"
        
        base_dir = Path(self.obsidian_path)
        target_dir = base_dir / folder
        
        # Intentar crear el directorio si no existe (puede fallar en entornos restringidos)
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"[OBSIDIAN ERROR] No se pudo crear el directorio {target_dir}: {e}")
            raise e
        
        file_path = target_dir / filename
        file_path.write_text(content, encoding="utf-8")
        
        return f"{folder}/{filename}"
