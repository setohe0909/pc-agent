import os

from app.domain.ports.trading import RiskDecision, RiskPolicy, RiskPolicyPort


class ConfigurableRiskPolicy(RiskPolicyPort):
    def __init__(self, policy: RiskPolicy | None = None) -> None:
        self.policy = policy or self.from_environment()

    @classmethod
    def from_environment(cls) -> RiskPolicy:
        return RiskPolicy(
            trading_enabled=_truthy(os.getenv("KALSHI_TRADING_ENABLED", "false")),
            environment=os.getenv("KALSHI_ENV", "paper"),
            max_order_amount=float(os.getenv("KALSHI_MAX_ORDER_AMOUNT", "10")),
            max_daily_notional=float(os.getenv("KALSHI_MAX_DAILY_NOTIONAL", "100")),
            allowed_tickers=_csv(os.getenv("KALSHI_ALLOWED_TICKERS")),
            denied_tickers=_csv(os.getenv("KALSHI_DENIED_TICKERS")),
        )

    async def evaluate(self, ticker: str, action: str, amount: float, actor_id: str | None = None) -> RiskDecision:
        if not ticker:
            return self._reject("La orden no tiene ticker de mercado.")
        if amount <= 0:
            return self._reject("El monto debe ser mayor a cero.")
        if amount > self.policy.max_order_amount:
            return self._reject(
                f"La orden de ${amount:.2f} excede el limite por orden de ${self.policy.max_order_amount:.2f}."
            )
        if ticker in self.policy.denied_tickers:
            return self._reject(f"El mercado {ticker} esta bloqueado por politica.")
        if self.policy.allowed_tickers and ticker not in self.policy.allowed_tickers:
            return self._reject(f"El mercado {ticker} no esta en la lista permitida.")
        if self.policy.environment == "live" and not self.policy.trading_enabled:
            return self._reject("Trading live deshabilitado por configuracion.")
        return RiskDecision(approved=True, reason="Aprobado por politica de riesgo.", policy=self.policy)

    def _reject(self, reason: str) -> RiskDecision:
        return RiskDecision(approved=False, reason=reason, policy=self.policy)


def _truthy(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _csv(value: str | None) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(item.strip() for item in value.split(",") if item.strip())
