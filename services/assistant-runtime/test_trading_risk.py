import asyncio
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "services" / "assistant-runtime"))

from app.domain.ports.trading import RiskPolicy
from app.domain.trading_policies import ConfigurableRiskPolicy


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


if __name__ == "__main__":
    unittest.main()
