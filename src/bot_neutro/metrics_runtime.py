from threading import Lock
from typing import Dict


class InMemoryMetrics:
    def __init__(self) -> None:
        self._lock = Lock()
        self._requests_total: Dict[str, int] = {}
        self._errors_total: Dict[str, int] = {}

    def inc_request(self, route: str) -> None:
        with self._lock:
            self._requests_total[route] = self._requests_total.get(route, 0) + 1

    def inc_error(self, route: str) -> None:
        with self._lock:
            self._errors_total[route] = self._errors_total.get(route, 0) + 1

    def snapshot(self) -> Dict[str, Dict[str, int]]:
        with self._lock:
            return {
                "requests_total": dict(self._requests_total),
                "errors_total": dict(self._errors_total),
            }


METRICS = InMemoryMetrics()


__all__ = ["InMemoryMetrics", "METRICS"]
