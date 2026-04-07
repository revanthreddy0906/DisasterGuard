import io
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = PROJECT_ROOT / 'backend'
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app import main as app_main  # noqa: E402


def build_png_bytes(size: tuple[int, int] = (16, 16), color: str = 'red') -> bytes:
    image = Image.new('RGB', size, color=color)
    buf = io.BytesIO()
    image.save(buf, format='PNG')
    return buf.getvalue()


class ApiIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app_main.app)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.client.close()

    def test_health_success_observability_and_request_id(self) -> None:
        before = app_main.request_metrics.snapshot()

        with patch('app.main.get_model_loader', return_value=object()), patch('app.main.log_request') as log_request:
            response = self.client.get('/health', headers={'X-Request-ID': 'req-health-1'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['X-Request-ID'], 'req-health-1')

        payload = response.json()
        self.assertEqual(payload['status'], 'healthy')
        self.assertTrue(payload['model_loaded'])
        self.assertIsNone(payload['model_error'])

        after = app_main.request_metrics.snapshot()
        self.assertEqual(after['requests_total'], before['requests_total'] + 1)
        self.assertGreaterEqual(after['path_counts'].get('/health', 0), before['path_counts'].get('/health', 0) + 1)
        self.assertGreaterEqual(after['status_counts'].get('200', 0), before['status_counts'].get('200', 0) + 1)

        self.assertEqual(log_request.call_count, 1)
        logged_payload = log_request.call_args.args[1]
        self.assertEqual(logged_payload['event'], 'http_request')
        self.assertEqual(logged_payload['request_id'], 'req-health-1')
        self.assertEqual(logged_payload['method'], 'GET')
        self.assertEqual(logged_payload['path'], '/health')
        self.assertEqual(logged_payload['status_code'], 200)

    def test_health_generates_request_id_when_missing(self) -> None:
        with patch('app.main.get_model_loader', return_value=object()):
            response = self.client.get('/health')

        self.assertEqual(response.status_code, 200)
        request_id = response.headers.get('X-Request-ID')
        self.assertIsNotNone(request_id)
        self.assertRegex(request_id, r'^[0-9a-f]{32}$')

    def test_predict_rejects_invalid_content_type(self) -> None:
        files = {
            'pre_image': ('pre.txt', b'not-image', 'text/plain'),
            'post_image': ('post.txt', b'also-not-image', 'text/plain'),
        }

        response = self.client.post('/api/v1/predict', files=files)
        self.assertEqual(response.status_code, 415)
        self.assertEqual(response.json()['detail']['code'], 'unsupported_media_type')

    def test_predict_rejects_empty_payload(self) -> None:
        files = {
            'pre_image': ('pre.png', b'', 'image/png'),
            'post_image': ('post.png', build_png_bytes(), 'image/png'),
        }

        response = self.client.post('/api/v1/predict', files=files)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['detail']['code'], 'empty_upload')

    def test_predict_rejects_mismatched_dimensions(self) -> None:
        files = {
            'pre_image': ('pre.png', build_png_bytes(size=(16, 16)), 'image/png'),
            'post_image': ('post.png', build_png_bytes(size=(10, 12)), 'image/png'),
        }

        response = self.client.post('/api/v1/predict', files=files)
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()['detail']['code'], 'image_size_mismatch')

    def test_predict_success_with_mocked_inference(self) -> None:
        mocked_result = {
            'damage_class': 'severe-damage',
            'confidence': 0.91,
            'probabilities': {
                'no-damage': 0.03,
                'severe-damage': 0.91,
                'destroyed': 0.06,
            },
        }
        mocked_analysis = {
            'hotspots': [
                {'bbox': [0, 0, 8, 8], 'damage_class': 'severe-damage', 'confidence': 0.84},
                {'bbox': [8, 8, 16, 16], 'damage_class': 'no-damage', 'confidence': 0.9},
            ],
            'global_result': mocked_result,
        }

        with patch('app.api.endpoints._get_model_loader', return_value=object()), patch(
            'app.api.endpoints.PatchAnalyzer'
        ) as patch_analyzer:
            patch_analyzer.return_value.analyze.return_value = mocked_analysis

            response = self.client.post(
                '/api/v1/predict',
                files={
                    'pre_image': ('pre.png', build_png_bytes(), 'image/png'),
                    'post_image': ('post.png', build_png_bytes(), 'image/png'),
                },
                headers={'X-Request-ID': 'req-predict-ok'},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['damage_class'], 'severe-damage')
        self.assertEqual(payload['confidence'], 0.91)
        self.assertEqual(payload['probabilities']['severe-damage'], 0.91)
        self.assertEqual(payload['source_dimensions'], {'width': 16, 'height': 16})
        self.assertEqual(payload['hotspots'], [{'bbox': [0, 0, 8, 8], 'damage_class': 'severe-damage', 'confidence': 0.84}])
        self.assertEqual(response.headers.get('X-Request-ID'), 'req-predict-ok')


if __name__ == '__main__':
    unittest.main()
