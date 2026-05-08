import json
import os

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
        # Politica de enrutamiento (Open-Claw router)
        provider = os.getenv("DEFAULT_LLM_PROVIDER", "openai")
        
        # Fallback automatico si no hay API Key de OpenAI
        if provider == "openai" and not os.getenv("OPENAI_API_KEY"):
            print("AVISO: OPENAI_API_KEY no encontrada. Usando Ollama como fallback.")
            provider = "ollama"

        if provider == "openai":
            if policy == "cheap":
                return "openai/gpt-4o-mini"
            return "openai/gpt-4o"
        elif provider == "anthropic":
            if policy == "cheap":
                return "anthropic/claude-3-haiku-20240307"
            return "anthropic/claude-3-5-sonnet-20241022"
        elif provider == "ollama":
            # Usar llama3 que es el que el usuario tiene descargado
            return "ollama/llama3:latest"
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

        response = await acompletion(
            model=model,
            messages=messages,
        )
        return response.choices[0].message.content

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

        response = await acompletion(
            model=model,
            messages=messages,
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {"decision": "Error decodificando respuesta JSON del LLM.", "should_trade": False}
