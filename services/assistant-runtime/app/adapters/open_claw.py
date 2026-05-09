import json
import os
from pathlib import Path

from litellm import acompletion

from app.domain.ports.llm import LLMPort


class OpenClawLLMAdapter(LLMPort):
    def __init__(self) -> None:
        import litellm
        
        # Integrar observability con langfuse
        if os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"):
            litellm.success_callback = ["langfuse"]
            litellm.failure_callback = ["langfuse"]

    def _get_provider(self, policy: str) -> str:
        # Recargar configuracion runtime dinamicamente
        config_path = os.getenv("RUNTIME_CONFIG_PATH", "/config/runtime-config.json")
        runtime_config = {}
        try:
            if Path(config_path).exists():
                runtime_config = json.loads(Path(config_path).read_text(encoding="utf-8"))
        except Exception:
            pass

        provider = runtime_config.get("default_llm_provider") or os.getenv("DEFAULT_LLM_PROVIDER", "openai")
        openai_key = runtime_config.get("openai_api_key") or os.getenv("OPENAI_API_KEY")
        
        # Fallback automatico si no hay API Key de OpenAI
        if provider == "openai" and not openai_key:
            provider = "ollama"

        if provider == "openai":
            # Inyectar key en el entorno para litellm (si viene de runtime config)
            if openai_key:
                os.environ["OPENAI_API_KEY"] = openai_key
            
            if policy == "cheap":
                return "openai/gpt-4o-mini"
            return "openai/gpt-4o"
        elif provider == "ollama":
            # Asegurar que litellm sepa donde esta ollama (prioridad a la UI)
            ollama_url = runtime_config.get("ollama_base_url") or os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
            os.environ["OLLAMA_API_BASE"] = ollama_url
            
            # Usar llama3 que es el que el usuario tiene
            return "ollama/llama3:latest"
        elif provider == "gemini":
            gemini_key = runtime_config.get("gemini_api_key") or os.getenv("GEMINI_API_KEY")
            if gemini_key:
                # Usar la variable estandar de Google AI Studio
                os.environ["GOOGLE_API_KEY"] = gemini_key
            
            # Forzar el uso de gemini/ (AI Studio via explicit api_key)
            if policy == "cheap":
                return "gemini/gemini-1.5-flash"
            return "gemini/gemini-1.5-pro"
        return "openai/gpt-4o-mini"

    async def chat(self, prompt: str, context: dict | None = None) -> str:
        model = self._get_provider(policy="cheap")
        messages = []
        if context:
            messages.append({
                "role": "system",
                "content": f"Contexto adicional:\n{json.dumps(context, indent=2)}"
            })
        messages.append({"role": "user", "content": prompt})

        # Pasamos la key explicitamente para evitar que litellm use VertexAI
        api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")

        response = await acompletion(
            model=model,
            messages=messages,
            api_key=api_key
        )
        content = response.choices[0].message.content
        if not content:
            print(f"[LLM ERROR] El modelo {model} devolvio una respuesta vacia.")
            return "Lo siento, no pude generar una respuesta. Por favor, intenta de nuevo o revisa la configuración de la IA."
        return content

    async def analyze_trade(self, market_data: dict, prompt: str) -> dict:
        # Usa el modelo mas inteligente (y mas caro) para decisiones financieras
        model = self._get_provider(policy="smart")
        system_prompt = (
            "Eres un analista financiero. Tienes acceso a datos del mercado de predicciones (Kalshi/Polymarket). "
            "El usuario ha solicitado realizar un trade o hacer un analisis. "
            "Responde en formato JSON estricto con las claves: "
            "'decision' (texto de tu analisis de la situacion) y "
            "'should_trade' (boolean: true si la orden del usuario es razonable basado en los mercados, false si no lo es o no encuentras el mercado)."
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Mercados disponibles:\n{json.dumps(market_data, indent=2)}\n\nSolicitud del usuario: {prompt}"}
        ]

        api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")

        response = await acompletion(
            model=model,
            messages=messages,
            response_format={"type": "json_object"},
            api_key=api_key
        )
        content = response.choices[0].message.content
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {"decision": "Error decodificando respuesta JSON del LLM.", "should_trade": False}
