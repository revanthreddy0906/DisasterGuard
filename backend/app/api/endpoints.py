import base64
import io
from fastapi import APIRouter, UploadFile, File, HTTPException
from PIL import Image, UnidentifiedImageError
from app.services.model_loader import get_model_loader
from app.services.patch_analyzer import PatchAnalyzer
from app.schemas.prediction import PredictionResponse
from app.core.config import settings

router = APIRouter()
MAX_UPLOAD_BYTES = 25 * 1024 * 1024


def _ensure_valid_upload(upload: UploadFile, content: bytes, field_name: str) -> None:
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


def _decode_rgb_image(content: bytes, field_name: str) -> Image.Image:
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


def _get_model_loader():
    try:
        return get_model_loader()
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "model_checkpoint_missing",
                "message": "Model checkpoint is unavailable on the server.",
            },
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "model_unavailable",
                "message": "Model could not be loaded for inference.",
            },
        ) from exc


@router.post('/predict', response_model=PredictionResponse)
async def predict_damage(pre_image: UploadFile = File(...), post_image: UploadFile = File(...)):
    pre_content = await pre_image.read()
    post_content = await post_image.read()
    _ensure_valid_upload(pre_image, pre_content, "pre_image")
    _ensure_valid_upload(post_image, post_content, "post_image")

    img_pre = _decode_rgb_image(pre_content, "pre_image")
    img_post = _decode_rgb_image(post_content, "post_image")

    if img_pre.size != img_post.size:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "image_size_mismatch",
                "message": f"pre_image size {img_pre.size} does not match post_image size {img_post.size}.",
            },
        )

    model_loader = _get_model_loader()

    # Run sliding-window patch analysis
    analyzer = PatchAnalyzer(model_loader)
    analysis = analyzer.analyze(img_pre, img_post, step=112)

    hotspots = analysis["hotspots"]
    global_result = analysis["global_result"]

    # If patch analysis returned a global result, use the averaged prediction
    # (more realistic confidence since it averages across all patches)
    if global_result:
        result = global_result
    else:
        # Fallback to single-pass prediction
        result = model_loader.predict(pre_content, post_content)

    # Filter hotspots: only return patches with actual damage
    damage_hotspots = [
        {
            "bbox": h["bbox"],
            "damage_class": h["damage_class"],
            "confidence": h["confidence"]
        }
        for h in hotspots
        if h["damage_class"] != "no-damage"
    ]

    return {
        "damage_class": result["damage_class"],
        "confidence": result["confidence"],
        "probabilities": result["probabilities"],
        "hotspots": damage_hotspots
    }


@router.get('/sample-images')
async def get_sample_images():
    """Return a pair of sample images as base64 for the 'Try with sample data' feature.
    Uses real dataset images that have proper disaster-type names for location detection.
    """
    pre_image = None
    post_image = None
    pre_name = None
    post_name = None

    # Priority 1: Use real prepared dataset (has proper disaster-type filenames)
    prepared_dir = settings.BASE_DIR / 'data' / 'prepared'
    search_dirs = []
    for split in ['train', 'val', 'test']:
        for cls in ['destroyed', 'severe-damage', 'no-damage']:
            d = prepared_dir / split / cls
            if d.exists():
                search_dirs.append(d)

    # Find a matching pre/post pair from the prepared data
    for class_dir in search_dirs:
        pre_files = sorted(class_dir.glob("pre_*"))
        for pf in pre_files:
            # Derive matching post file from the pre filename
            post_candidate = class_dir / pf.name.replace("pre_", "post_", 1)
            if post_candidate.exists():
                pre_image = pf
                post_image = post_candidate
                pre_name = pf.name
                post_name = post_candidate.name
                break
        if pre_image:
            break

    # Priority 2: Fallback to data/sample directory
    if not pre_image:
        sample_dir = settings.SAMPLE_DATA_DIR
        for split_dir in ['train', 'val', 'test']:
            split_path = sample_dir / split_dir
            if not split_path.exists():
                continue
            for class_dir in split_path.iterdir():
                if not class_dir.is_dir():
                    continue
                pre_files = sorted(class_dir.glob("pre_*"))
                post_files = sorted(class_dir.glob("post_*"))
                if pre_files and post_files:
                    pre_image = pre_files[0]
                    post_image = post_files[0]
                    pre_name = pre_files[0].name
                    post_name = post_files[0].name
                    break
            if pre_image:
                break

    if not pre_image or not post_image:
        raise HTTPException(status_code=404, detail="No sample images found")

    pre_b64 = base64.b64encode(pre_image.read_bytes()).decode()
    post_b64 = base64.b64encode(post_image.read_bytes()).decode()

    return {
        "pre_image": pre_b64,
        "post_image": post_b64,
        "pre_name": pre_name,
        "post_name": post_name
    }
