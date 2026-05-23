import json
import os
import time
from contextlib import asynccontextmanager


class RuntimeTracer:
    def __init__(self) -> None:
        self.enabled = os.getenv("LANGFUSE_ENABLED", "false").lower() == "true"

    @asynccontextmanager
    async def span(self, name: str, metadata: dict):
        start = time.perf_counter()
        trace_id = metadata.get("trace_id")
        if self.enabled:
            self._log("start", name, metadata)
        try:
            yield
            if self.enabled:
                self._log("success", name, {**metadata, "duration_ms": round((time.perf_counter() - start) * 1000, 2)})
        except Exception as exc:
            if self.enabled:
                self._log(
                    "error",
                    name,
                    {
                        **metadata,
                        "duration_ms": round((time.perf_counter() - start) * 1000, 2),
                        "error_type": type(exc).__name__,
                        "trace_id": trace_id,
                    },
                )
            raise

    def _log(self, event: str, name: str, metadata: dict) -> None:
        print(f"[RUNTIME TRACE] {event} {name} {json.dumps(_safe_metadata(metadata), sort_keys=True)}")


def _safe_metadata(metadata: dict) -> dict:
    redacted = {}
    for key, value in metadata.items():
        if any(secret in key.lower() for secret in ("token", "key", "secret", "password")):
            redacted[key] = "***"
        else:
            redacted[key] = value
    return redacted
