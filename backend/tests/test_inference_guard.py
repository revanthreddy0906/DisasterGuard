import asyncio
import sys
import time
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = PROJECT_ROOT / 'backend'
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.inference_guard import InferenceBusyError, InferenceGuard, InferenceTimeoutError  # noqa: E402


class InferenceGuardTests(unittest.IsolatedAsyncioTestCase):
    async def test_run_sync_success(self) -> None:
        guard = InferenceGuard(max_concurrency=1, queue_timeout_seconds=0.1, inference_timeout_seconds=1.0)

        def operation() -> str:
            return 'ok'

        result = await guard.run_sync(operation)
        self.assertEqual(result, 'ok')

        snapshot = guard.snapshot()
        self.assertEqual(snapshot['accepted_total'], 1)
        self.assertEqual(snapshot['succeeded_total'], 1)

    async def test_rejects_when_queue_is_saturated(self) -> None:
        guard = InferenceGuard(max_concurrency=1, queue_timeout_seconds=0.01, inference_timeout_seconds=1.0)

        def slow_operation() -> str:
            time.sleep(0.15)
            return 'slow'

        first_task = asyncio.create_task(guard.run_sync(slow_operation))
        await asyncio.sleep(0.02)

        with self.assertRaises(InferenceBusyError):
            await guard.run_sync(lambda: 'second')

        await first_task
        self.assertEqual(guard.snapshot()['rejected_total'], 1)

    async def test_times_out_long_running_operation(self) -> None:
        guard = InferenceGuard(max_concurrency=1, queue_timeout_seconds=0.1, inference_timeout_seconds=0.02)

        def too_slow() -> str:
            time.sleep(0.1)
            return 'late'

        with self.assertRaises(InferenceTimeoutError):
            await guard.run_sync(too_slow)

        snapshot = guard.snapshot()
        self.assertEqual(snapshot['timeout_total'], 1)


if __name__ == '__main__':
    unittest.main()
