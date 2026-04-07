import os
from pathlib import Path

import torch


def _env_int(name: str, default: int, minimum: int = 0) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return max(value, minimum)


def _env_float(name: str, default: float, minimum: float = 0.0) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = float(raw)
    except ValueError:
        return default
    return max(value, minimum)


class Settings:
    PROJECT_NAME: str = 'Disaster Damage Assessment API'
    VERSION: str = '1.0.0'
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent.parent
    CHECKPOINT_DIR: Path = BASE_DIR / 'checkpoints'
    BEST_MODEL_PATH: Path = CHECKPOINT_DIR / 'best_model.pth'
    SAMPLE_DATA_DIR: Path = BASE_DIR / 'data' / 'sample'
    DAMAGE_CLASSES: list[str] = ['no-damage', 'severe-damage', 'destroyed']
    IMG_SIZE: int = 224
    API_V1_STR: str = '/api/v1'

    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO').upper()
    REQUEST_ID_HEADER: str = 'X-Request-ID'

    PREDICT_MAX_CONCURRENCY: int = _env_int('PREDICT_MAX_CONCURRENCY', default=2, minimum=1)
    PREDICT_QUEUE_TIMEOUT_SECONDS: float = _env_float('PREDICT_QUEUE_TIMEOUT_SECONDS', default=0.25, minimum=0.0)
    PREDICT_TIMEOUT_SECONDS: float = _env_float('PREDICT_TIMEOUT_SECONDS', default=45.0, minimum=1.0)

    @property
    def DEVICE(self) -> str:
        if torch.backends.mps.is_available():
            return 'mps'
        if torch.cuda.is_available():
            return 'cuda'
        return 'cpu'


settings = Settings()
