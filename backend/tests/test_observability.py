import json
import logging
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = PROJECT_ROOT / 'backend'
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.observability import RequestMetrics, log_request  # noqa: E402


class ObservabilityTests(unittest.TestCase):
    def test_request_metrics_snapshot_contains_aggregates(self) -> None:
        metrics = RequestMetrics()
        metrics.record_request(method='GET', path='/health', status_code=200, latency_ms=10.0)
        metrics.record_request(method='POST', path='/api/v1/predict', status_code=429, latency_ms=3.0)

        snapshot = metrics.snapshot()
        self.assertEqual(snapshot['requests_total'], 2)
        self.assertEqual(snapshot['method_counts']['GET'], 1)
        self.assertEqual(snapshot['method_counts']['POST'], 1)
        self.assertEqual(snapshot['status_counts']['200'], 1)
        self.assertEqual(snapshot['status_counts']['429'], 1)
        self.assertEqual(snapshot['path_counts']['/api/v1/predict'], 1)

    def test_log_request_emits_json(self) -> None:
        logger = logging.getLogger('test.request.logger')
        logger.handlers.clear()

        captured: list[str] = []

        class CaptureHandler(logging.Handler):
            def emit(self, record: logging.LogRecord) -> None:
                captured.append(record.getMessage())

        handler = CaptureHandler()
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        payload = {'event': 'http_request', 'status_code': 200, 'request_id': 'abc'}
        log_request(logger, payload)

        self.assertEqual(len(captured), 1)
        self.assertEqual(json.loads(captured[0]), payload)


if __name__ == '__main__':
    unittest.main()
