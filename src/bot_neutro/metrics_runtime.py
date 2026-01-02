from threading import Lock
from typing import Any, Dict, List


class InMemoryMetrics:
    def __init__(self) -> None:
        self._lock = Lock()
        self._requests_total: Dict[str, int] = {}
        self._errors_total: Dict[str, int] = {"/audio": 0, "/metrics": 0}
        self._llm_tier_denied_total: Dict[tuple[str, str, str], int] = {}
        self._rate_limit_hits_total: int = 0
        self._mem_reads_total: int = 0
        self._mem_writes_total: int = 0
        self._audio_sessions_purged_total: int = 0
        self._audio_sessions_current: int = 0

        self._latency_bucket_bounds: List[float] = [0.1, 0.5, 1.0, float("inf")]
        self._latency_buckets: Dict[str, Dict[float, int]] = {}
        self._latency_count: Dict[str, int] = {}
        self._latency_sum: Dict[str, float] = {}
        self._ensure_latency_route("/healthz")
        self._ensure_latency_route("/audio")

    def _ensure_latency_route(self, route: str) -> None:
        if route not in self._latency_buckets:
            self._latency_buckets[route] = {bound: 0 for bound in self._latency_bucket_bounds}
            self._latency_count[route] = 0
            self._latency_sum[route] = 0.0

    def inc_request(self, route: str) -> None:
        with self._lock:
            self._requests_total[route] = self._requests_total.get(route, 0) + 1

    def inc_error(self, route: str) -> None:
        with self._lock:
            self._errors_total[route] = self._errors_total.get(route, 0) + 1

    def inc_llm_tier_denied_total(
        self, route: str, requested_tier: str | None, authorized_tier: str
    ) -> None:
        with self._lock:
            key = (route, requested_tier or "none", authorized_tier)
            self._llm_tier_denied_total[key] = self._llm_tier_denied_total.get(key, 0) + 1

    def inc_rate_limit_hit(self) -> None:
        with self._lock:
            self._rate_limit_hits_total += 1

    def inc_mem_read(self) -> None:
        with self._lock:
            self._mem_reads_total += 1

    def inc_mem_write(self) -> None:
        with self._lock:
            self._mem_writes_total += 1

    def inc_audio_sessions_purged(self, count: int) -> None:
        with self._lock:
            self._audio_sessions_purged_total += count

    def set_audio_sessions_current(self, count: int) -> None:
        with self._lock:
            self._audio_sessions_current = count

    def observe_latency(self, route: str, duration_seconds: float) -> None:
        with self._lock:
            self._ensure_latency_route(route)
            self._latency_count[route] += 1
            self._latency_sum[route] += duration_seconds

            for bound in self._latency_bucket_bounds:
                if duration_seconds <= bound:
                    self._latency_buckets[route][bound] += 1

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            requests_total = dict(self._requests_total)
            errors_total = dict(self._errors_total)
            for route in ("/audio", "/metrics"):
                errors_total.setdefault(route, 0)

            latency_snapshot: Dict[str, Dict[str, Dict[float, int] | float | int]] = {}
            for route, buckets in self._latency_buckets.items():
                latency_snapshot[route] = {
                    "buckets": dict(buckets),
                    "count": self._latency_count.get(route, 0),
                    "sum": self._latency_sum.get(route, 0.0),
                }

            llm_tier_denied_snapshot = [
                {
                    "route": route,
                    "requested_tier": requested_tier,
                    "authorized_tier": authorized_tier,
                    "value": value,
                }
                for (
                    route,
                    requested_tier,
                    authorized_tier,
                ), value in self._llm_tier_denied_total.items()
            ]

            return {
                "requests_total": requests_total,
                "errors_total": errors_total,
                "llm_tier_denied_total": llm_tier_denied_snapshot,
                "rate_limit_hits_total": self._rate_limit_hits_total,
                "mem_reads_total": self._mem_reads_total,
                "mem_writes_total": self._mem_writes_total,
                "audio_sessions_purged_total": self._audio_sessions_purged_total,
                "audio_sessions_current": self._audio_sessions_current,
                "latency": latency_snapshot,
                "latency_bucket_bounds": list(self._latency_bucket_bounds),
            }


METRICS = InMemoryMetrics()


__all__ = ["InMemoryMetrics", "METRICS"]
