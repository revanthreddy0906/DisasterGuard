import io
import sys
import unittest
from pathlib import Path

from fastapi import HTTPException, UploadFile
from PIL import Image
from starlette.datastructures import Headers

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.api.validation import MAX_UPLOAD_BYTES, decode_rgb_image, ensure_valid_upload  # noqa: E402


def build_upload(content_type: str = "image/png") -> UploadFile:
    return UploadFile(
        file=io.BytesIO(b"payload"),
        filename="sample.png",
        headers=Headers({"content-type": content_type}),
    )


class ValidationTests(unittest.TestCase):
    def test_rejects_non_image_upload(self) -> None:
        upload = build_upload(content_type="text/plain")
        with self.assertRaises(HTTPException) as ctx:
            ensure_valid_upload(upload, b"abc", "pre_image")
        self.assertEqual(ctx.exception.status_code, 415)

    def test_rejects_empty_upload(self) -> None:
        upload = build_upload()
        with self.assertRaises(HTTPException) as ctx:
            ensure_valid_upload(upload, b"", "pre_image")
        self.assertEqual(ctx.exception.status_code, 400)

    def test_rejects_oversized_upload(self) -> None:
        upload = build_upload()
        with self.assertRaises(HTTPException) as ctx:
            ensure_valid_upload(upload, b"x" * (MAX_UPLOAD_BYTES + 1), "pre_image")
        self.assertEqual(ctx.exception.status_code, 413)

    def test_decode_valid_image(self) -> None:
        image = Image.new("RGB", (10, 12), color="red")
        buf = io.BytesIO()
        image.save(buf, format="PNG")

        decoded = decode_rgb_image(buf.getvalue(), "pre_image")
        self.assertEqual(decoded.mode, "RGB")
        self.assertEqual(decoded.size, (10, 12))

    def test_decode_invalid_image_raises(self) -> None:
        with self.assertRaises(HTTPException) as ctx:
            decode_rgb_image(b"not-an-image", "pre_image")
        self.assertEqual(ctx.exception.status_code, 422)


if __name__ == "__main__":
    unittest.main()
