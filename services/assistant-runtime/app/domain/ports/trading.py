from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol


class TradingPort(Protocol):
    async def get_markets(self) -> list[dict]:
        ...

    async def get_balance(self) -> float:
        ...

    async def place_order(self, ticker: str, action: str, amount: float, client_order_id: str | None = None) -> dict:
        ...


@dataclass(frozen=True)
class RiskPolicy:
    trading_enabled: bool = False
    environment: str = "paper"
    max_order_amount: float = 10.0
    max_daily_notional: float = 100.0
    allowed_tickers: tuple[str, ...] = ()
    denied_tickers: tuple[str, ...] = ()


@dataclass(frozen=True)
class RiskDecision:
    approved: bool
    reason: str
    policy: RiskPolicy


@dataclass(frozen=True)
class TradeAuditEvent:
    event_type: str
    actor_id: str | None = None
    order_id: str | None = None
    ticker: str | None = None
    environment: str = "paper"
    payload: dict = field(default_factory=dict)
    created_at: datetime | None = None


class RiskPolicyPort(Protocol):
    async def evaluate(self, ticker: str, action: str, amount: float, actor_id: str | None = None) -> RiskDecision:
        ...


class TradeAuditRepository(Protocol):
    async def record(self, event: TradeAuditEvent) -> None:
        ...
