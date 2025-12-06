from threading import Lock
from typing import Dict


class InMemoryMetrics:
    def __init__(self) -> None:
        self._lock = Lock()
        self._requests_total: Dict[str, int] = {}
        self._errors_total: Dict[str, int] = {"/audio": 0, "/metrics": 0}
        self._rate_limit_hits_total: int = 0
        self._mem_reads_total: int = 0
        self._mem_writes_total: int = 0

    def inc_request(self, route: str) -> None:
        with self._lock:
            self._requests_total[route] = self._requests_total.get(route, 0) + 1

    def inc_error(self, route: str) -> None:
        with self._lock:
            self._errors_total[route] = self._errors_total.get(route, 0) + 1

    def inc_rate_limit_hit(self) -> None:
        with self._lock:
            self._rate_limit_hits_total += 1

    def inc_mem_read(self) -> None:
        with self._lock:
            self._mem_reads_total += 1

    def inc_mem_write(self) -> None:
        with self._lock:
            self._mem_writes_total += 1

    def snapshot(self) -> Dict[str, Dict[str, int]]:
        with self._lock:
            requests_total = dict(self._requests_total)
            errors_total = dict(self._errors_total)
            for route in ("/audio", "/metrics"):
                errors_total.setdefault(route, 0)

            return {
                "requests_total": requests_total,
                "errors_total": errors_total,
                "rate_limit_hits_total": self._rate_limit_hits_total,
                "mem_reads_total": self._mem_reads_total,
                "mem_writes_total": self._mem_writes_total,
            }


METRICS = InMemoryMetrics()


__all__ = ["InMemoryMetrics", "METRICS"]
