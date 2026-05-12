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

    async def _generate_with_fallback(self, prompt: str, system_instruction: str | None = None, response_mime_type: str = "text/plain") -> str:
        model_candidates = ["models/gemini-flash-latest", "models/gemini-pro-latest", "models/gemini-2.0-flash-lite"]
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        genai.configure(api_key=api_key)
        
        last_error = None
        for model_name in model_candidates:
            try:
                print(f"[OPEN CLAW] Intentando con modelo: {model_name}...")
                model = genai.GenerativeModel(model_name, system_instruction=system_instruction)
                gen_config = genai.GenerationConfig(response_mime_type=response_mime_type)
                response = await model.generate_content_async(prompt, generation_config=gen_config)
                return response.text
            except Exception as e:
                last_error = e
                if "429" in str(e) or "404" in str(e):
                    print(f"[OPEN CLAW WARNING] Error en {model_name}. Saltando...")
                    continue
                else:
                    raise e
        raise last_error

    async def chat(self, prompt: str, context: dict | None = None) -> str:
        provider, model = self._get_provider_info(policy="cheap")
        
        if provider == "gemini":
            full_prompt = prompt
            if context:
                full_prompt = f"Contexto:\n{json.dumps(context)}\n\nPregunta: {prompt}"
            
            return await self._generate_with_fallback(full_prompt)
        else:
            # Fallback a litellm para otros proveedores
            litellm_model = f"{provider}/{model}" if provider != "openai" else f"openai/{model}"
            messages = [{"role": "user", "content": prompt}]
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
            except:
                return {"decision": "Error procesando JSON de Gemini", "should_trade": False}
        else:
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
            # Nota: Simplificado, Gemini espera objetos de tipo genai.types.Tool
            # Por ahora usaremos el formato que espera el SDK de Google
            
            model_instance = genai.GenerativeModel(
                model_name="models/gemini-pro", # Tool calling funciona mejor en pro
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
