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
        if self.memory and user_id:
            context = await self.memory.get_context(user_id)
        
        response = await self.llm.chat(prompt, context)
        
        if self.memory and user_id:
            await self.memory.save_interaction(user_id, {"prompt": prompt, "response": response})
            
        return response

    async def execute_trade_decision(self, prompt: str, user_id: str | None = None) -> dict:
        # 1. Obtener mercados disponibles
        markets = await self.trading.get_markets()
        
        # 2. Analizar con el LLM (Open-Claw router)
        analysis = await self.llm.analyze_trade(market_data=markets, prompt=prompt)
        
        if not analysis.get("should_trade"):
            return {
                "status": "rejected_by_llm",
                "message": analysis.get("decision", "El LLM recomendo NO hacer el trade o no encontro el mercado.")
            }
            
        # 3. Si el LLM aprobo, extraer los parametros de la intencion de trade
        # (Para este demo, extraeremos de forma basica un ticker o usaremos uno por defecto
        # en un entorno real el LLM debe devolver el JSON con el ticker exacto y accion).
        ticker = analysis.get("ticker", markets[0]["ticker"])
        action = analysis.get("action", "BUY YES")
        amount = analysis.get("amount", 10)
        
        # 4. Colocar la orden en Kalshi (Demo)
        order = await self.trading.place_order(ticker=ticker, action=action, amount=amount)
        
        # 5. Guardar evento en la memoria
        if self.memory and user_id:
            await self.memory.save_interaction(user_id, {
                "type": "trade_executed",
                "prompt": prompt,
                "analysis": analysis,
                "order": order
            })
            
        return {
            "status": "executed",
            "message": analysis.get("decision", "El LLM aprobo la orden."),
            "order": order
        }
