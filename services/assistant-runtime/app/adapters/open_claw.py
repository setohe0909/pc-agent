import json
import os
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
            # Usamos los alias 'latest' que el escaneo confirmo como disponibles
            model = "models/gemini-flash-latest" if policy == "cheap" else "models/gemini-pro-latest"
            return "gemini", model
        elif provider == "ollama":
            return "ollama", "llama3:latest"
        elif provider == "openai":
            model = "gpt-4o-mini" if policy == "cheap" else "gpt-4o"
            return "openai", model
        
        return "openai", "gpt-4o-mini"

    async def _generate_with_fallback(self, prompt: str, system_instruction: str | None = None, response_mime_type: str = "text/plain", **kwargs) -> str:
        import sys
        # Enfocamos en los modelos más estables y probables de tener cuota
        model_candidates = [
            "models/gemini-1.5-flash",
            "models/gemini-1.5-pro",
            "models/gemini-2.0-flash",
            "models/gemini-2.0-flash-lite"
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


    async def get_tools_response(self, prompt: str, tools: list[dict], system_instruction: str | None = None) -> dict:
        provider, model = self._get_provider_info(policy="smart")
        
        if provider == "gemini":
            api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
            genai.configure(api_key=api_key)
            
            # Convertir esquemas de herramientas a formato Gemini
            
            model_instance = genai.GenerativeModel(
                model_name=model, 
                system_instruction=system_instruction,
                tools=tools
            )
            
            chat = model_instance.start_chat()
            response = await chat.send_message_async(prompt)
            
            # Extraer llamadas a funciones
            fc = response.candidates[0].content.parts[0].function_call
            if fc:
                return {
                    "tool_name": fc.name,
                    "arguments": dict(fc.args)
                }
            return {"message": response.text}
        else:
            # Fallback a LiteLLM (que soporta tool calling para OpenAI/Anthropic)
            litellm_model = f"{provider}/{model}"
            messages = [{"role": "user", "content": prompt}]
            if system_instruction:
                messages.insert(0, {"role": "system", "content": system_instruction})
                
            response = await acompletion(
                model=litellm_model,
                messages=messages,
                tools=tools,
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

    async def generate_image(self, prompt: str) -> str:
        from litellm import aimage_generation
        provider, _ = self._get_provider_info(policy="smart")
        
        if provider == "gemini":
            # Candidatos de Imagen (Google AI Studio)
            # Priorizamos modelos 'fast' y 'v3' que suelen ser más accesibles en free tier
            candidates = [
                "gemini/imagen-3.0-fast-generate-001",
                "gemini/imagen-3.0-generate-001",
                "gemini/imagen-4.0-fast-generate-001",
                "gemini/imagen-4.0-generate-001"
            ]
            api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
            
            for model in candidates:
                try:
                    print(f"[OPEN CLAW] Intentando generar imagen con Gemini ({model})...")
                    # Intentar con timeout extendido para imágenes
                    response = await aimage_generation(
                        model=model,
                        prompt=prompt,
                        api_key=api_key
                    )
                    if response.data and len(response.data) > 0:
                        url = response.data[0].url
                        if url:
                            return url
                        # Si LiteLLM devolvió bytes en lugar de URL, esto fallará con 'list index out of range'
                        # o devolverá None.
                    print(f"[OPEN CLAW WARNING] {model} no devolvió una URL válida.")
                except Exception as e:
                    # Capturar el error 429 específicamente para informar al usuario
                    if "429" in str(e):
                        print(f"[OPEN CLAW ERROR] Quota Exceeded para {model}. Reintenta en unos minutos.")
                    else:
                        print(f"[OPEN CLAW ERROR] Falló Imagen {model}: {str(e)}")
                    continue

        # Backup a DALL-E 3 si existe la key de OpenAI
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            print(f"[OPEN CLAW] Usando DALL-E 3 como backup...")
            response = await aimage_generation(
                model="dall-e-3",
                prompt=prompt,
                api_key=openai_key
            )
            return response.data[0].url
            
        raise Exception("No se pudo generar la imagen con Gemini Imagen y no hay 'OPENAI_API_KEY' configurada para DALL-E 3.")
