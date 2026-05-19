import json
import os
import sys
from pathlib import Path
import google.generativeai as genai
from litellm import acompletion

from app.domain.ports.llm import LLMPort


class OpenClawLLMAdapter(LLMPort):
    def __init__(self) -> None:
        import litellm
        
        # Integrar observability con langfuse
        if os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"):
            litellm.success_callback = ["langfuse"]
            litellm.failure_callback = ["langfuse"]

    def _get_provider_info(self, policy: str) -> tuple[str, str]:
        # Recargar configuracion runtime dinamicamente
        config_path = os.getenv("RUNTIME_CONFIG_PATH", "/config/runtime-config.json")
        runtime_config = {}
        try:
            if Path(config_path).exists():
                runtime_config = json.loads(Path(config_path).read_text(encoding="utf-8"))
        except Exception:
            pass

        provider = runtime_config.get("default_llm_provider") or os.getenv("DEFAULT_LLM_PROVIDER", "openai")
        
        if provider == "gemini":
            model = "models/gemini-2.0-flash-lite" if policy == "cheap" else "models/gemini-2.0-flash"
            return "gemini", model
        elif provider == "ollama":
            return "ollama", "llama3:latest"
        elif provider == "openai":
            model = "gpt-4o-mini" if policy == "cheap" else "gpt-4o"
            return "openai", model
        
        return "openai", "gpt-4o-mini"

    async def _generate_with_fallback(self, prompt: str, system_instruction: str | None = None, response_mime_type: str = "text/plain", **kwargs) -> str:
        # Enfocamos en los modelos más estables y probables de tener cuota
        model_candidates = [
            "models/gemini-2.0-flash-lite",
            "models/gemini-2.0-flash",
            "models/gemini-2.5-flash",
        ]
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        genai.configure(api_key=api_key)
        
        last_error = None
        quota_errors_count = 0
        
        for model_name in model_candidates:
            try:
                print(f"[OPEN CLAW] Intentando con modelo: {model_name}...", file=sys.stderr)
                model = genai.GenerativeModel(model_name, system_instruction=system_instruction)
                gen_config = genai.GenerationConfig(response_mime_type=response_mime_type)
                
                content = [prompt]
                if "images" in kwargs and kwargs["images"]:
                    for img_bytes in kwargs["images"]:
                        content.append({
                            "mime_type": "image/jpeg",
                            "data": img_bytes
                        })
                
                response = await model.generate_content_async(content, generation_config=gen_config)
                
                if not response.candidates or not response.candidates[0].content.parts:
                    print(f"[OPEN CLAW WARNING] Modelo {model_name} no devolvió contenido.", file=sys.stderr)
                    continue
                    
                return response.text
            except Exception as e:
                last_error = e
                err_str = str(e)
                print(f"[OPEN CLAW WARNING] Error en {model_name}: {err_str}", file=sys.stderr)
                
                if "429" in err_str:
                    quota_errors_count += 1
                    if quota_errors_count >= 2:
                        print("[OPEN CLAW CRITICAL] Demasiados errores de cuota (429). Abortando para evitar timeout.", file=sys.stderr)
                        break
                    continue
                elif "404" in err_str or "not found" in err_str.lower():
                    continue
                else:
                    # Otros errores (como 400 Bad Request) deben lanzarse inmediatamente
                    raise e
        
        if last_error and "429" in str(last_error):
             raise Exception("⚠️ Todos los modelos de Gemini han agotado su cuota (429). Por favor, intenta más tarde o configura una OPENAI_API_KEY en el .env")
        raise last_error or Exception("No se pudo obtener respuesta de ningún modelo configurado.")


    async def chat(self, prompt: str, context: dict | None = None, images: list[bytes] | None = None, system_instruction: str | None = None) -> str:
        provider, model = self._get_provider_info(policy="cheap")
        
        if provider == "gemini":
            full_prompt = prompt
            if context:
                full_prompt = f"Contexto:\n{json.dumps(context)}\n\nPregunta: {prompt}"
            
            try:
                return await self._generate_with_fallback(full_prompt, images=images, system_instruction=system_instruction)
            except Exception as e:
                # Si falla Gemini y tenemos OpenAI, intentamos el fallback
                openai_key = os.getenv("OPENAI_API_KEY")
                if openai_key:
                    print(f"[OPEN CLAW] Gemini falló ({e}). Intentando fallback con OpenAI...", file=sys.stderr)
                    return await self._chat_with_litellm("openai", "gpt-4o-mini", prompt, context, system_instruction)
                raise e

        return await self._chat_with_litellm(provider, model, prompt, context, system_instruction)

    async def _chat_with_litellm(self, provider: str, model: str, prompt: str, context: dict | None = None, system_instruction: str | None = None) -> str:
        litellm_model = f"{provider}/{model}" if provider != "openai" else f"openai/{model}"
        messages = [{"role": "user", "content": prompt}]
        if system_instruction:
            messages.insert(0, {"role": "system", "content": system_instruction})
        if context:
            messages.insert(0, {"role": "system", "content": f"Contexto: {json.dumps(context)}"})
        
        response = await acompletion(model=litellm_model, messages=messages)
        return response.choices[0].message.content

    async def analyze_trade(self, market_data: dict, prompt: str) -> dict:
        provider, model = self._get_provider_info(policy="smart")
        system_prompt = (
            "Eres un analista financiero. Tienes acceso a datos del mercado de predicciones (Kalshi/Polymarket). "
            "Responde en formato JSON estricto con las claves: 'decision' (string) y 'should_trade' (boolean)."
        )
        user_content = f"Mercados:\n{json.dumps(market_data)}\n\nSolicitud: {prompt}"

        if provider == "gemini":
            try:
                response_text = await self._generate_with_fallback(
                    user_content, 
                    system_instruction=system_prompt,
                    response_mime_type="application/json"
                )
                return json.loads(response_text)
            except Exception as e:
                openai_key = os.getenv("OPENAI_API_KEY")
                if openai_key:
                    print(f"[OPEN CLAW] Gemini falló en análisis ({e}). Intentando fallback con OpenAI...", file=sys.stderr)
                    return await self._analyze_trade_with_litellm("openai", "gpt-4o", user_content, system_prompt)
                return {"decision": f"Error Gemini: {e}", "should_trade": False}
        else:
            return await self._analyze_trade_with_litellm(provider, model, user_content, system_prompt)

    async def _analyze_trade_with_litellm(self, provider: str, model: str, user_content: str, system_prompt: str) -> dict:
        litellm_model = f"{provider}/{model}" if provider != "openai" else f"openai/{model}"
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        response = await acompletion(model=litellm_model, messages=messages, response_format={"type": "json_object"})
        return json.loads(response.choices[0].message.content)

    def _to_gemini_schema(self, schema):
        if isinstance(schema, list):
            return [self._to_gemini_schema(item) for item in schema]
        if not isinstance(schema, dict):
            return schema

        converted = {}
        for key, value in schema.items():
            if key == "type" and isinstance(value, str):
                converted[key] = value.upper()
            else:
                converted[key] = self._to_gemini_schema(value)
        return converted

    def _to_gemini_tools(self, tools: list[dict]) -> list[dict]:
        return [
            {
                "name": tool["name"],
                "description": tool.get("description", ""),
                "parameters": self._to_gemini_schema(tool.get("parameters", {"type": "object", "properties": {}})),
            }
            for tool in tools
        ]

    def _to_openai_tools(self, tools: list[dict]) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get("parameters", {"type": "object", "properties": {}}),
                },
            }
            for tool in tools
        ]

    def _is_schema_key_error(self, exc: Exception) -> bool:
        if not isinstance(exc, KeyError):
            return False
        schema_types = {"object", "string", "array", "boolean", "number", "integer"}
        return str(exc).strip("'\"") in schema_types


    async def get_tools_response(self, prompt: str, tools: list[dict], system_instruction: str | None = None) -> dict:
        provider, model = self._get_provider_info(policy="smart")
        
        if provider == "gemini":
            api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
            genai.configure(api_key=api_key)
            gemini_tools = self._to_gemini_tools(tools)

            model_candidates = [
                model,
                "models/gemini-2.0-flash",
                "models/gemini-2.0-flash-lite",
                "models/gemini-2.5-flash",
            ]

            last_exc = None
            for candidate in model_candidates:
                try:
                    model_instance = genai.GenerativeModel(
                        model_name=candidate,
                        system_instruction=system_instruction,
                        tools=gemini_tools,
                    )
                    chat = model_instance.start_chat()
                    response = await chat.send_message_async(prompt)
                    fc = response.candidates[0].content.parts[0].function_call
                    if fc:
                        return {
                            "tool_name": fc.name,
                            "arguments": dict(fc.args),
                        }
                    return {"message": response.text}
                except Exception as exc:
                    last_exc = exc
                    err_str = str(exc)
                    if "429" in err_str or "quota" in err_str.lower() or "Quota" in err_str:
                        print(f"[OPEN CLAW WARNING] Cuota excedida en {candidate}, probando siguiente...", file=sys.stderr)
                        continue
                    if self._is_schema_key_error(exc):
                        raise RuntimeError(
                            "La detección de herramientas con Gemini falló por un schema JSON incompatible "
                            f"({exc!r}). Esto suele pasar cuando Gemini recibe tipos como 'object'/'string' "
                            "sin traducir a su formato interno. Revisa que assistant-runtime esté corriendo "
                            "con la versión actualizada y reinicia el servicio si sigue usando una imagen anterior."
                        ) from exc
                    raise RuntimeError(
                        f"Falló la detección de intención con Gemini usando el modelo {candidate}: {exc}"
                    ) from exc

            raise RuntimeError(
                "⚠️ Todos los modelos de Gemini han agotado su cuota (429). "
                "Configura una OPENAI_API_KEY en .env o intenta más tarde."
            ) from last_exc
        else:
            # Fallback a LiteLLM (que soporta tool calling para OpenAI/Anthropic)
            try:
                litellm_model = f"{provider}/{model}"
                messages = [{"role": "user", "content": prompt}]
                if system_instruction:
                    messages.insert(0, {"role": "system", "content": system_instruction})
                    
                response = await acompletion(
                    model=litellm_model,
                    messages=messages,
                    tools=self._to_openai_tools(tools),
                    tool_choice="auto"
                )
                
                message = response.choices[0].message
                if message.tool_calls:
                    tc = message.tool_calls[0]
                    return {
                        "tool_name": tc.function.name,
                        "arguments": json.loads(tc.function.arguments)
                    }
                return {"message": message.content}
            except Exception as exc:
                if self._is_schema_key_error(exc):
                    raise RuntimeError(
                        "La detección de herramientas falló por un schema JSON incompatible "
                        f"({exc!r}). El adapter esperaba convertir los tools al formato de LiteLLM/OpenAI."
                    ) from exc
                raise RuntimeError(
                    f"Falló la detección de intención con {provider} usando el modelo {model}: {exc}"
                ) from exc

    async def generate_image(self, prompt: str, context: dict | None = None) -> str:
        from litellm import aimage_generation
        import os

        generation_provider = (context or {}).get("image_generation_provider") or os.getenv("PICTURE_IMAGE_GENERATION_PROVIDER")
        if (context or {}).get("prefer_free_model") and not generation_provider:
            generation_provider = "ollama"
        if str(generation_provider or "").strip().lower() == "ollama":
            return await self._generate_image_with_ollama(prompt)
        
        provider, _ = self._get_provider_info(policy="smart")
        
        # Asegurar que las llaves estén en el entorno para LiteLLM
        gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if gemini_key:
            os.environ["GEMINI_API_KEY"] = gemini_key
            os.environ["GOOGLE_API_KEY"] = gemini_key

        if provider == "gemini":
            # Candidatos de Imagen (Google AI Studio)
            # Priorizamos modelos estables de la serie 3.0
            candidates = [
                "gemini/imagen-3.0-generate-001",
                "gemini/imagen-3.0-fast-generate-001",
                "google/imagen-3.0-generate-001",
            ]
            
            for model in candidates:
                try:
                    print(f"[OPEN CLAW] Intentando generar imagen con Gemini ({model})...", file=sys.stderr)
                    response = await aimage_generation(
                        model=model,
                        prompt=prompt,
                        api_key=gemini_key
                    )
                    if response.data and len(response.data) > 0:
                        url = response.data[0].url
                        if url:
                            print(f"[OPEN CLAW SUCCESS] Imagen generada con {model}", file=sys.stderr)
                            return url
                    print(f"[OPEN CLAW WARNING] {model} no devolvió una URL válida.", file=sys.stderr)
                except Exception as e:
                    err_msg = str(e)
                    if "429" in err_msg:
                        print(f"[OPEN CLAW ERROR] Quota Exceeded para {model}.", file=sys.stderr)
                    else:
                        print(f"[OPEN CLAW ERROR] Falló Imagen {model}: {err_msg}", file=sys.stderr)
                    continue

        # Backup a DALL-E 3 si existe la key de OpenAI
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            os.environ["OPENAI_API_KEY"] = openai_key
            print(f"[OPEN CLAW] Usando DALL-E 3 como backup...", file=sys.stderr)
            try:
                response = await aimage_generation(
                    model="openai/dall-e-3",
                    prompt=prompt,
                    api_key=openai_key
                )
                if response.data and len(response.data) > 0:
                    return response.data[0].url
            except Exception as e:
                print(f"[OPEN CLAW ERROR] Falló backup DALL-E 3: {str(e)}", file=sys.stderr)
            
        raise Exception("No se pudo generar la imagen. Gemini Imagen falló y el backup de DALL-E 3 también (o no está configurado).")

    async def _generate_image_with_ollama(self, prompt: str) -> str:
        import httpx

        base_url = (
            os.getenv("OLLAMA_IMAGE_BASE_URL")
            or os.getenv("OLLAMA_BASE_URL")
            or "http://ollama:11434"
        ).rstrip("/")
        model = os.getenv("OLLAMA_IMAGE_MODEL", "x/z-image-turbo")
        payload = {
            "model": model,
            "prompt": prompt,
            "size": os.getenv("OLLAMA_IMAGE_SIZE", "1024x1024"),
            "response_format": "b64_json",
            "n": 1,
        }
        async with httpx.AsyncClient(timeout=300) as client:
            response = await client.post(f"{base_url}/v1/images/generations", json=payload)
        response.raise_for_status()
        data = response.json()
        try:
            image_b64 = data["data"][0]["b64_json"]
        except (KeyError, IndexError, TypeError) as exc:
            raise Exception("Ollama no devolvió una imagen válida en b64_json.") from exc
        return f"data:image/png;base64,{image_b64}"

    async def edit_image(
        self,
        prompt: str,
        image: bytes,
        mask: bytes | None = None,
        context: dict | None = None,
        image_mime: str | None = None,
        image_filename: str | None = None,
    ) -> str:
        from io import BytesIO
        from litellm import aimage_edit

        provider = str((context or {}).get("image_edit_provider") or os.getenv("PICTURE_IMAGE_EDIT_PROVIDER", "openai")).strip().lower()
        if (context or {}).get("prefer_free_model") and provider == "openai":
            provider = "local"
        if provider == "local":
            return await self._edit_image_with_local_provider(prompt, image, mask, context, image_mime, image_filename)
        if provider != "openai":
            raise Exception(f"Proveedor de edición de imagen no soportado: {provider}")

        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            raise Exception(
                "La edición fiel de imágenes requiere OPENAI_API_KEY con un modelo de edición configurado. "
                "La generación simple puede seguir usando Gemini, pero editar un diseño existente necesita un proveedor de image-edit."
            )

        image_file = BytesIO(image)
        image_file.name = image_filename or _filename_for_mime(image_mime)
        mask_file = None
        if mask:
            mask_file = BytesIO(mask)
            mask_file.name = "mask.png"

        edit_prompt = prompt
        if context:
            preserve = ", ".join(context.get("preserve") or [])
            checks = ", ".join(context.get("quality_checks") or [])
            edit_prompt = (
                f"{prompt}\n\nPreserve: {preserve or 'all non-requested visual elements'}."
                f"\nQuality checks: {checks or 'requested edit is visible and layout remains stable'}."
            )

        response = await aimage_edit(
            model=os.getenv("OPENAI_IMAGE_EDIT_MODEL", "openai/gpt-image-1"),
            image=image_file,
            mask=mask_file,
            prompt=edit_prompt,
            api_key=openai_key,
        )
        if response.data and len(response.data) > 0:
            first = response.data[0]
            if getattr(first, "url", None):
                return first.url
            if getattr(first, "b64_json", None):
                return f"data:image/png;base64,{first.b64_json}"
        raise Exception("El proveedor de edición no devolvió una imagen válida.")

    async def _edit_image_with_local_provider(
        self,
        prompt: str,
        image: bytes,
        mask: bytes | None,
        context: dict | None,
        image_mime: str | None,
        image_filename: str | None,
    ) -> str:
        import base64
        import httpx

        endpoint = os.getenv("PICTURE_LOCAL_IMAGE_EDIT_URL")
        if not endpoint:
            raise Exception("PICTURE_IMAGE_EDIT_PROVIDER=local requiere PICTURE_LOCAL_IMAGE_EDIT_URL.")

        payload = {
            "prompt": prompt,
            "image_b64": base64.b64encode(image).decode("ascii"),
            "image_mime": image_mime or "image/png",
            "image_filename": image_filename or _filename_for_mime(image_mime),
            "mask_b64": base64.b64encode(mask).decode("ascii") if mask else None,
            "context": context or {},
        }
        async with httpx.AsyncClient(timeout=300) as client:
            response = await client.post(endpoint, json=payload)
        response.raise_for_status()
        data = response.json()
        if data.get("image_url"):
            return data["image_url"]
        if data.get("image_b64"):
            mime = data.get("image_mime", "image/png")
            return f"data:{mime};base64,{data['image_b64']}"
        raise Exception("El proveedor local no devolvió image_url ni image_b64.")


def _filename_for_mime(mime: str | None) -> str:
    mapping = {
        "image/jpeg": "design.jpg",
        "image/jpg": "design.jpg",
        "image/webp": "design.webp",
        "image/png": "design.png",
    }
    return mapping.get((mime or "").lower(), "design.png")
