import asyncio
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "services" / "assistant-runtime"))

from app.domain.ports.trading import RiskPolicy
from app.domain.trading_policies import ConfigurableRiskPolicy


class FakeExposureRepository:
    def __init__(self, used: float) -> None:
        self.used = used

    async def daily_notional(self, actor_id: str | None, environment: str) -> float:
        return self.used


class TradingRiskTests(unittest.TestCase):
    def test_rejects_amount_above_order_limit(self) -> None:
        async def scenario() -> None:
            policy = ConfigurableRiskPolicy(RiskPolicy(max_order_amount=5))
            decision = await policy.evaluate("KXTEST", "BUY YES", 10)
            self.assertFalse(decision.approved)
            self.assertIn("excede", decision.reason)

        asyncio.run(scenario())

    def test_rejects_missing_ticker(self) -> None:
        async def scenario() -> None:
            policy = ConfigurableRiskPolicy(RiskPolicy())
            decision = await policy.evaluate("", "BUY YES", 1)
            self.assertFalse(decision.approved)
            self.assertIn("ticker", decision.reason)

        asyncio.run(scenario())

    def test_live_trading_fails_closed_when_disabled(self) -> None:
        async def scenario() -> None:
            policy = ConfigurableRiskPolicy(RiskPolicy(environment="live", trading_enabled=False))
            decision = await policy.evaluate("KXTEST", "BUY YES", 1)
            self.assertFalse(decision.approved)
            self.assertIn("deshabilitado", decision.reason)

        asyncio.run(scenario())

    def test_allowed_tickers_are_enforced(self) -> None:
        async def scenario() -> None:
            policy = ConfigurableRiskPolicy(RiskPolicy(allowed_tickers=("KXOK",)))
            decision = await policy.evaluate("KXNO", "BUY YES", 1)
            self.assertFalse(decision.approved)

        asyncio.run(scenario())

    def test_daily_notional_limit_is_enforced(self) -> None:
        async def scenario() -> None:
            policy = ConfigurableRiskPolicy(
                RiskPolicy(max_order_amount=10, max_daily_notional=15),
                exposure_repository=FakeExposureRepository(used=10),
            )
            decision = await policy.evaluate("KXOK", "BUY YES", 6)
            self.assertFalse(decision.approved)
            self.assertIn("limite diario", decision.reason)

        asyncio.run(scenario())


if __name__ == "__main__":
    unittest.main()
