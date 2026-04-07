import base64

from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from app.api.validation import decode_rgb_image, ensure_valid_upload
from app.core.config import settings
from app.core.inference_guard import InferenceBusyError, InferenceGuard, InferenceTimeoutError
from app.schemas.prediction import PredictionResponse
from app.services.model_loader import get_model_loader
from app.services.patch_analyzer import PatchAnalyzer

router = APIRouter()

predict_guard = InferenceGuard(
    max_concurrency=settings.PREDICT_MAX_CONCURRENCY,
    queue_timeout_seconds=settings.PREDICT_QUEUE_TIMEOUT_SECONDS,
    inference_timeout_seconds=settings.PREDICT_TIMEOUT_SECONDS,
)


def _get_model_loader():
    try:
        return get_model_loader()
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail={
                'code': 'model_checkpoint_missing',
                'message': 'Model checkpoint is unavailable on the server.',
            },
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={
                'code': 'model_unavailable',
                'message': 'Model could not be loaded for inference.',
            },
        ) from exc


@router.post('/predict', response_model=PredictionResponse)
async def predict_damage(request: Request, pre_image: UploadFile = File(...), post_image: UploadFile = File(...)):
    pre_content = await pre_image.read()
    post_content = await post_image.read()
    ensure_valid_upload(pre_image, pre_content, 'pre_image')
    ensure_valid_upload(post_image, post_content, 'post_image')

    img_pre = decode_rgb_image(pre_content, 'pre_image')
    img_post = decode_rgb_image(post_content, 'post_image')

    if img_pre.size != img_post.size:
        raise HTTPException(
            status_code=422,
            detail={
                'code': 'image_size_mismatch',
                'message': f'pre_image size {img_pre.size} does not match post_image size {img_post.size}.',
            },
        )

    def _run_prediction():
        model_loader = _get_model_loader()

        analyzer = PatchAnalyzer(model_loader)
        analysis = analyzer.analyze(img_pre, img_post, step=112)

        hotspots = analysis['hotspots']
        global_result = analysis['global_result']

        if global_result:
            result = global_result
        else:
            result = model_loader.predict(pre_content, post_content)

        damage_hotspots = [
            {
                'bbox': h['bbox'],
                'damage_class': h['damage_class'],
                'confidence': h['confidence'],
            }
            for h in hotspots
            if h['damage_class'] != 'no-damage'
        ]

        return {
            'damage_class': result['damage_class'],
            'confidence': result['confidence'],
            'probabilities': result['probabilities'],
            'hotspots': damage_hotspots,
            'source_dimensions': {
                'width': img_pre.width,
                'height': img_pre.height,
            },
        }

    try:
        return await predict_guard.run_sync(_run_prediction)
    except InferenceBusyError as exc:
        raise HTTPException(
            status_code=429,
            detail={
                'code': 'predict_backpressure',
                'message': 'Prediction service is busy. Please retry shortly.',
                'request_id': getattr(request.state, 'request_id', None),
            },
        ) from exc
    except InferenceTimeoutError as exc:
        raise HTTPException(
            status_code=504,
            detail={
                'code': 'predict_timeout',
                'message': 'Prediction exceeded the configured timeout.',
                'request_id': getattr(request.state, 'request_id', None),
            },
        ) from exc


def get_predict_metrics() -> dict[str, object]:
    return predict_guard.snapshot()


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
        pre_files = sorted(class_dir.glob('pre_*'))
        for pf in pre_files:
            # Derive matching post file from the pre filename
            post_candidate = class_dir / pf.name.replace('pre_', 'post_', 1)
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
                pre_files = sorted(class_dir.glob('pre_*'))
                post_files = sorted(class_dir.glob('post_*'))
                if pre_files and post_files:
                    pre_image = pre_files[0]
                    post_image = post_files[0]
                    pre_name = pre_files[0].name
                    post_name = post_files[0].name
                    break
            if pre_image:
                break

    if not pre_image or not post_image:
        raise HTTPException(status_code=404, detail='No sample images found')

    pre_b64 = base64.b64encode(pre_image.read_bytes()).decode()
    post_b64 = base64.b64encode(post_image.read_bytes()).decode()

    return {
        'pre_image': pre_b64,
        'post_image': post_b64,
        'pre_name': pre_name,
        'post_name': post_name,
    }
