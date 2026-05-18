import os

from app.domain.ports.llm import LLMPort
from app.domain.ports.memory import MemoryPort
from app.domain.ports.trading import RiskPolicyPort, TradeAuditEvent, TradeAuditRepository, TradingPort
from app.domain.trading_policies import ConfigurableRiskPolicy


class NoopTradeAuditRepository(TradeAuditRepository):
    async def record(self, event: TradeAuditEvent) -> None:
        return None


class TradingWorkflow:
    def __init__(
        self,
        trading_port: TradingPort,
        llm_port: LLMPort,
        memory_port: MemoryPort | None = None,
        risk_policy: RiskPolicyPort | None = None,
        audit_repository: TradeAuditRepository | None = None,
    ) -> None:
        self.trading = trading_port
        self.llm = llm_port
        self.memory = memory_port
        self.risk_policy = risk_policy or ConfigurableRiskPolicy()
        self.audit = audit_repository or NoopTradeAuditRepository()

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
        await self.audit.record(TradeAuditEvent(
            event_type="trade_analysis_created",
            actor_id=user_id,
            environment=getattr(self.risk_policy, "policy", None).environment if hasattr(self.risk_policy, "policy") else "paper",
            payload={"analysis": analysis, "prompt": prompt},
        ))
        
        if not analysis.get("should_trade"):
            return {
                "status": "rejected_by_analyst",
                "message": analysis.get("decision", "El Analista recomendo no operar.")
            }
            
        # 4. MOTOR DE RIESGO
        amount = analysis.get("amount", 10)
        ticker = analysis.get("ticker", markets[0]["ticker"] if markets else "")
        action = analysis.get("action", "BUY YES")
        risk = await self.risk_policy.evaluate(ticker=ticker, action=action, amount=float(amount), actor_id=user_id)
        await self.audit.record(TradeAuditEvent(
            event_type="trade_risk_decision",
            actor_id=user_id,
            ticker=ticker,
            environment=risk.policy.environment,
            payload={
                "approved": risk.approved,
                "reason": risk.reason,
                "amount": amount,
                "action": action,
                "policy": {
                    "max_order_amount": risk.policy.max_order_amount,
                    "max_daily_notional": risk.policy.max_daily_notional,
                    "trading_enabled": risk.policy.trading_enabled,
                },
            },
        ))
        if not risk.approved:
            return {
                "status": "rejected_by_risk",
                "message": risk.reason,
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
        await self.audit.record(TradeAuditEvent(
            event_type="trade_submit_attempt",
            actor_id=user_id,
            order_id=client_order_id,
            ticker=ticker,
            environment=risk.policy.environment,
            payload={"amount": amount, "action": action},
        ))
        order = await self.trading.place_order(
            ticker=ticker, 
            action=action, 
            amount=amount, 
            client_order_id=client_order_id
        )
        order_status = order.get("status", "unknown")
        await self.audit.record(TradeAuditEvent(
            event_type="trade_submit_result",
            actor_id=user_id,
            order_id=client_order_id,
            ticker=ticker,
            environment=risk.policy.environment,
            payload={"order": order},
        ))

        if order_status not in {"executed", "submitted", "filled", "partially_filled"}:
            return {
                "status": order_status,
                "message": order.get("message", "La orden no fue ejecutada."),
                "order": order,
                "critic_note": critic_opinion[:100] + "...",
            }
        
        # 7. Guardar en memoria
        if self.memory and user_id:
            await self.memory.save_interaction(user_id, {
                "type": "pro_trade_executed",
                "order_id": client_order_id,
                "analysis": analysis,
                "critic": critic_opinion
            })
            
        return {
            "status": order_status,
            "message": f"Analisis dual completado. Confianza: {analysis.get('confidence', 'Alta')}.",
            "order": order,
            "critic_note": critic_opinion[:100] + "..."
        }
