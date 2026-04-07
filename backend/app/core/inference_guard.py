import asyncio
import threading
import time
from typing import Any, Callable, TypeVar


class InferenceBusyError(RuntimeError):
    pass


class InferenceTimeoutError(RuntimeError):
    pass


T = TypeVar('T')


class InferenceGuard:
    def __init__(self, *, max_concurrency: int, queue_timeout_seconds: float, inference_timeout_seconds: float) -> None:
        self._max_concurrency = max_concurrency
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._queue_timeout_seconds = queue_timeout_seconds
        self._inference_timeout_seconds = inference_timeout_seconds

        self._lock = threading.Lock()
        self._inflight = 0
        self._accepted_total = 0
        self._rejected_total = 0
        self._timeout_total = 0
        self._failed_total = 0
        self._succeeded_total = 0
        self._success_latency_total_ms = 0.0

    async def run_sync(self, operation: Callable[[], T]) -> T:
        try:
            await asyncio.wait_for(self._semaphore.acquire(), timeout=self._queue_timeout_seconds)
        except asyncio.TimeoutError as exc:
            with self._lock:
                self._rejected_total += 1
            raise InferenceBusyError('prediction queue is saturated') from exc

        with self._lock:
            self._accepted_total += 1
            self._inflight += 1

        started_at = time.perf_counter()
        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(operation),
                timeout=self._inference_timeout_seconds,
            )
        except asyncio.TimeoutError as exc:
            with self._lock:
                self._timeout_total += 1
            raise InferenceTimeoutError('prediction timed out') from exc
        except Exception:
            with self._lock:
                self._failed_total += 1
            raise
        else:
            elapsed_ms = (time.perf_counter() - started_at) * 1000.0
            with self._lock:
                self._succeeded_total += 1
                self._success_latency_total_ms += elapsed_ms
            return result
        finally:
            with self._lock:
                self._inflight = max(self._inflight - 1, 0)
            self._semaphore.release()

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            succeeded_total = self._succeeded_total
            avg_success_latency_ms = self._success_latency_total_ms / succeeded_total if succeeded_total else 0.0
            return {
                'max_concurrency': self._max_concurrency,
                'queue_timeout_seconds': self._queue_timeout_seconds,
                'inference_timeout_seconds': self._inference_timeout_seconds,
                'inflight': self._inflight,
                'accepted_total': self._accepted_total,
                'rejected_total': self._rejected_total,
                'timeout_total': self._timeout_total,
                'failed_total': self._failed_total,
                'succeeded_total': succeeded_total,
                'avg_success_latency_ms': round(avg_success_latency_ms, 3),
            }
