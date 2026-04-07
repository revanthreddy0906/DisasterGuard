import io

from fastapi import HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError

MAX_UPLOAD_BYTES = 25 * 1024 * 1024


def ensure_valid_upload(upload: UploadFile, content: bytes, field_name: str) -> None:
    if upload.content_type and not upload.content_type.startswith("image/"):
        raise HTTPException(
            status_code=415,
            detail={
                "code": "unsupported_media_type",
                "message": f"{field_name} must be an image upload.",
            },
        )

    if not content:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "empty_upload",
                "message": f"{field_name} is empty.",
            },
        )

    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail={
                "code": "payload_too_large",
                "message": f"{field_name} exceeds the 25MB upload limit.",
            },
        )


def decode_rgb_image(content: bytes, field_name: str) -> Image.Image:
    try:
        return Image.open(io.BytesIO(content)).convert("RGB")
    except (UnidentifiedImageError, OSError) as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "invalid_image",
                "message": f"{field_name} is not a valid readable image.",
            },
        ) from exc
