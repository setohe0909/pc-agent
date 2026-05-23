import os
import time
from collections import defaultdict, deque
from dataclasses import dataclass


@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    limit: int
    window_seconds: int
    retry_after_seconds: int = 0


class InMemoryRateLimiter:
    def __init__(self, limit: int | None = None, window_seconds: int | None = None) -> None:
        self.limit = int(limit if limit is not None else os.getenv("ASSISTANT_RATE_LIMIT_PER_MINUTE", "60"))
        self.window_seconds = int(window_seconds if window_seconds is not None else os.getenv("ASSISTANT_RATE_LIMIT_WINDOW_SECONDS", "60"))
        self._requests: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str) -> RateLimitDecision:
        if self.limit <= 0:
            return RateLimitDecision(allowed=True, limit=self.limit, window_seconds=self.window_seconds)
        now = time.monotonic()
        bucket = self._requests[key]
        cutoff = now - self.window_seconds
        while bucket and bucket[0] <= cutoff:
            bucket.popleft()
        if len(bucket) >= self.limit:
            retry_after = max(1, int(self.window_seconds - (now - bucket[0])))
            return RateLimitDecision(False, self.limit, self.window_seconds, retry_after)
        bucket.append(now)
        return RateLimitDecision(True, self.limit, self.window_seconds)
