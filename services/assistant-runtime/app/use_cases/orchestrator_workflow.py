from app.domain.ports.llm import LLMPort


class OrchestratorWorkflow:
    def __init__(self, llm_port: LLMPort) -> None:
        self.llm = llm_port

    async def run(self, prompt: str, payload: dict | None = None) -> dict:
        payload = payload or {}
        system_instruction = (
            "Eres SAVITAR, un orquestador de agentes de PC Agent. "
            "Tu trabajo es entender la intencion del usuario y coordinar o recomendar el sub-agente correcto. "
            "No eres un asistente financiero por defecto. Solo hablas de trading/finanzas si el usuario lo pide explicitamente. "
            "Agentes disponibles: Marketer para marketing, leads, campañas, Zernio y WhatsApp; "
            "Coder Web para desarrollo, repos, PRs y Linear; Writer para redaccion, blogs y storytelling; "
            "Picture para generacion/edicion de imagenes; Email para correos y respuestas bulk; "
            "Discord para canales, aprobaciones y operacion del bot; Model Status para proveedores/modelos. "
            "Responde en espanol, de forma breve, operativa y accionable. "
            "Si conviene delegar, indica a que agente delegarias y que comando o accion ejecutarias."
        )
        context = {
            "interface": payload.get("interface", "unknown"),
            "available_agents": ["marketer", "coder-web", "writer", "picture", "email", "discord", "model_status"],
        }
        response = await self.llm.chat(prompt, context=context, system_instruction=system_instruction)
        return {
            "status": "success",
            "message": response,
            "orchestrator": {
                "available_agents": context["available_agents"],
                "interface": context["interface"],
            },
        }
