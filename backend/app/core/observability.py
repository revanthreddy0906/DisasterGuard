import json
import logging
import threading
import time
from collections import defaultdict
from typing import Any


class RequestMetrics:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._started_at = time.time()
        self._requests_total = 0
        self._latency_total_ms = 0.0
        self._method_counts: dict[str, int] = defaultdict(int)
        self._status_counts: dict[str, int] = defaultdict(int)
        self._path_counts: dict[str, int] = defaultdict(int)

    def record_request(self, *, method: str, path: str, status_code: int, latency_ms: float) -> None:
        with self._lock:
            self._requests_total += 1
            self._latency_total_ms += latency_ms
            self._method_counts[method] += 1
            self._status_counts[str(status_code)] += 1
            self._path_counts[path] += 1

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            requests_total = self._requests_total
            avg_latency_ms = self._latency_total_ms / requests_total if requests_total else 0.0
            method_counts = dict(self._method_counts)
            status_counts = dict(self._status_counts)
            path_counts = dict(self._path_counts)

        return {
            'uptime_seconds': round(max(time.time() - self._started_at, 0.0), 3),
            'requests_total': requests_total,
            'avg_latency_ms': round(avg_latency_ms, 3),
            'method_counts': method_counts,
            'status_counts': status_counts,
            'path_counts': path_counts,
        }


def configure_request_logger(level_name: str) -> logging.Logger:
    logger = logging.getLogger('app.request')
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(message)s'))
        logger.addHandler(handler)
    logger.setLevel(getattr(logging, level_name, logging.INFO))
    logger.propagate = False
    return logger


def log_request(logger: logging.Logger, payload: dict[str, Any]) -> None:
    logger.info(json.dumps(payload, separators=(',', ':'), sort_keys=True))
