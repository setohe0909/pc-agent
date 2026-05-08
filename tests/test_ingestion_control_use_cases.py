import asyncio
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "services" / "control-api"))

from app.application.use_cases import GetIngestionSchedule, TriggerIngestionRun, UpdateIngestionSchedule
from app.domain.models import IngestionRun, IngestionSchedule


class FakeIngestionControl:
    def __init__(self) -> None:
        self.schedule = IngestionSchedule("0 */2 * * *", "15 */4 * * *", "30 */2 * * *")
        self.runs: list[IngestionRun] = []

    async def get_schedule(self) -> IngestionSchedule:
        return self.schedule

    async def update_schedule(self, schedule: IngestionSchedule) -> IngestionSchedule:
        self.schedule = schedule
        return schedule

    async def list_runs(self) -> list[IngestionRun]:
        return self.runs

    async def trigger_run(self, target: str) -> IngestionRun:
        run = IngestionRun(
            id="run",
            target=target,
            status="queued",
            detail="queued",
            started_at=datetime.now(timezone.utc),
        )
        self.runs.append(run)
        return run


class IngestionControlUseCaseTests(unittest.TestCase):
    def test_update_schedule_and_trigger_run(self) -> None:
        async def scenario() -> None:
            control = FakeIngestionControl()
            updated = await UpdateIngestionSchedule(control).execute(
                IngestionSchedule("0 8 * * *", "0 9 * * *", "0 10 * * *")
            )
            run = await TriggerIngestionRun(control).execute("all")
            current = await GetIngestionSchedule(control).execute()

            self.assertEqual(updated.market_ingestion_cron, "0 8 * * *")
            self.assertEqual(current, updated)
            self.assertEqual(run.target, "all")

        asyncio.run(scenario())


if __name__ == "__main__":
    unittest.main()
