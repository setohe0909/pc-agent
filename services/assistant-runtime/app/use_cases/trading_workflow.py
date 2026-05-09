from app.domain.ports.llm import LLMPort
from app.domain.ports.memory import MemoryPort
from app.domain.ports.trading import TradingPort


class TradingWorkflow:
    def __init__(self, trading_port: TradingPort, llm_port: LLMPort, memory_port: MemoryPort | None = None) -> None:
        self.trading = trading_port
        self.llm = llm_port
        self.memory = memory_port

    async def execute_chat(self, prompt: str, user_id: str | None = None) -> str:
        context = None
        system_instructions = "Eres un asistente financiero experto. Responde siempre de forma profesional y basada en datos."
        
        # Si parece una investigacion, reforzamos el rol del asistente
        if any(keyword in prompt.lower() for keyword in ["investiga", "research", "analiza", "tendencias"]):
            system_instructions += " El usuario solicita una investigacion profunda. Analiza tendencias, riesgos y oportunidades de mercado."

        if self.memory and user_id:
            context = await self.memory.get_context(user_id)
        
        # Enriquecemos el prompt con las instrucciones de sistema si es necesario
        full_prompt = f"{system_instructions}\n\nPregunta: {prompt}"
        response = await self.llm.chat(full_prompt, context)
        
        if self.memory and user_id:
            await self.memory.save_interaction(user_id, {"prompt": prompt, "response": response})
            
        return response

    async def execute_trade_decision(self, prompt: str, user_id: str | None = None) -> dict:
        # 1. Chequeo de Salud Financiera (Robustez)
        balance = await self.trading.get_balance()
        if balance <= 0:
            return {"status": "error", "message": "Saldo insuficiente o error consultando balance."}

        # 2. Obtener mercados disponibles
        markets = await self.trading.get_markets()
        
        # 3. FASE ANALISTA: Proponer una jugada
        analysis = await self.llm.analyze_trade(market_data=markets, prompt=prompt)
        
        if not analysis.get("should_trade"):
            return {
                "status": "rejected_by_analyst",
                "message": analysis.get("decision", "El Analista recomendo no operar.")
            }
            
        # 4. MOTOR DE RIESGO (Backend logic)
        amount = analysis.get("amount", 10)
        max_investment = 50.0 # Limite de seguridad configurable
        if amount > max_investment:
            return {
                "status": "rejected_by_risk",
                "message": f"La orden de ${amount} excede el limite de seguridad de ${max_investment}."
            }

        # 5. FASE CRITICO: ¿Tiene sentido la propuesta?
        # En una implementacion pro, aqui llamariamos a un LLM mas potente (ej: Gemini Pro) 
        # con un prompt de "Abogado del Diablo".
        critic_prompt = f"Actua como un gestor de riesgos senior. El analista propone {analysis.get('decision')}. ¿Ves algun riesgo oculto?"
        critic_opinion = await self.llm.chat(critic_prompt)
        
        if "RECHAZAR" in critic_opinion.upper():
            return {
                "status": "rejected_by_critic",
                "message": f"El Crítico rechazo la jugada: {critic_opinion}"
            }

        # 6. Si todo paso, preparar ejecucion con ID unico (Idempotencia)
        client_order_id = f"trade-{os.urandom(4).hex()}"
        ticker = analysis.get("ticker", markets[0]["ticker"])
        action = analysis.get("action", "BUY YES")
        
        order = await self.trading.place_order(
            ticker=ticker, 
            action=action, 
            amount=amount, 
            client_order_id=client_order_id
        )
        
        # 7. Guardar en memoria
        if self.memory and user_id:
            await self.memory.save_interaction(user_id, {
                "type": "pro_trade_executed",
                "order_id": client_order_id,
                "analysis": analysis,
                "critic": critic_opinion
            })
            
        return {
            "status": "executed",
            "message": f"Analisis dual completado. Confianza: {analysis.get('confidence', 'Alta')}.",
            "order": order,
            "critic_note": critic_opinion[:100] + "..."
        }
