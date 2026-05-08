import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.domain.models import IngestionRun, IngestionSchedule
from app.ports.gateways import IngestionControl

DEFAULT_SCHEDULE = IngestionSchedule(
    market_ingestion_cron="0 */2 * * *",
    trends_ingestion_cron="15 */4 * * *",
    mentis_sync_cron="30 */2 * * *",
)


class JsonIngestionControl(IngestionControl):
    def __init__(self, path: Path = Path("ingestion-control.json")) -> None:
        self.path = path

    async def get_schedule(self) -> IngestionSchedule:
        data = self._read()
        schedule = data.get("schedule", {})
        return IngestionSchedule(
            market_ingestion_cron=schedule.get("market_ingestion_cron", DEFAULT_SCHEDULE.market_ingestion_cron),
            trends_ingestion_cron=schedule.get("trends_ingestion_cron", DEFAULT_SCHEDULE.trends_ingestion_cron),
            mentis_sync_cron=schedule.get("mentis_sync_cron", DEFAULT_SCHEDULE.mentis_sync_cron),
        )

    async def update_schedule(self, schedule: IngestionSchedule) -> IngestionSchedule:
        data = self._read()
        data["schedule"] = {
            "market_ingestion_cron": schedule.market_ingestion_cron,
            "trends_ingestion_cron": schedule.trends_ingestion_cron,
            "mentis_sync_cron": schedule.mentis_sync_cron,
        }
        self._write(data)
        return schedule

    async def list_runs(self) -> list[IngestionRun]:
        data = self._read()
        return [self._run_from_dict(row) for row in data.get("runs", [])]

    async def trigger_run(self, target: str) -> IngestionRun:
        data = self._read()
        now = datetime.now(timezone.utc)
        run = IngestionRun(
            id=str(uuid4()),
            target=target,
            status="queued",
            detail=(
                "Run registrado desde UI. El worker real todavia no consume esta cola; "
                "sirve como bitacora operativa hasta conectar un dispatcher."
            ),
            started_at=now,
            finished_at=None,
        )
        runs = data.get("runs", [])
        runs.insert(0, self._run_to_dict(run))
        data["runs"] = runs[:25]
        self._write(data)
        return run

    def _read(self) -> dict:
        if not self.path.exists():
            return {}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _write(self, data: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def _run_to_dict(run: IngestionRun) -> dict:
        return {
            "id": run.id,
            "target": run.target,
            "status": run.status,
            "detail": run.detail,
            "started_at": run.started_at.isoformat(),
            "finished_at": run.finished_at.isoformat() if run.finished_at else None,
        }

    @staticmethod
    def _run_from_dict(data: dict) -> IngestionRun:
        finished_at = data.get("finished_at")
        return IngestionRun(
            id=data["id"],
            target=data["target"],
            status=data["status"],
            detail=data["detail"],
            started_at=datetime.fromisoformat(data["started_at"]),
            finished_at=datetime.fromisoformat(finished_at) if finished_at else None,
        )
