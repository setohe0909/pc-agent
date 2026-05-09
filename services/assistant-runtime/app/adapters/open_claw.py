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
            model = "gemini-1.5-flash" if policy == "cheap" else "gemini-1.5-pro"
            return "gemini", model
        elif provider == "ollama":
            return "ollama", "llama3:latest"
        elif provider == "openai":
            model = "gpt-4o-mini" if policy == "cheap" else "gpt-4o"
            return "openai", model
        
        return "openai", "gpt-4o-mini"

    async def chat(self, prompt: str, context: dict | None = None) -> str:
        provider, model = self._get_provider_info(policy="cheap")
        
        if provider == "gemini":
            api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
            genai.configure(api_key=api_key)
            gemini_model = genai.GenerativeModel(model)
            
            full_prompt = prompt
            if context:
                full_prompt = f"Contexto:\n{json.dumps(context)}\n\nPregunta: {prompt}"
            
            response = await gemini_model.generate_content_async(full_prompt)
            return response.text
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
            api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
            genai.configure(api_key=api_key)
            gemini_model = genai.GenerativeModel(
                model_name=model,
                system_instruction=system_prompt
            )
            response = await gemini_model.generate_content_async(
                user_content,
                generation_config=genai.GenerationConfig(response_mime_type="application/json")
            )
            try:
                return json.loads(response.text)
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
