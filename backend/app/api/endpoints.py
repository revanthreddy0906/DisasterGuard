import base64
import io
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from PIL import Image
from app.services.model_loader import get_model_loader
from app.services.patch_analyzer import PatchAnalyzer
from app.schemas.prediction import PredictionResponse
from app.core.config import settings

router = APIRouter()


@router.post('/predict', response_model=PredictionResponse)
async def predict_damage(pre_image: UploadFile = File(...), post_image: UploadFile = File(...)):
    try:
        model_loader = get_model_loader()
        pre_content = await pre_image.read()
        post_content = await post_image.read()

        # Decode images
        img_pre = Image.open(io.BytesIO(pre_content)).convert("RGB")
        img_post = Image.open(io.BytesIO(post_content)).convert("RGB")

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
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


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
