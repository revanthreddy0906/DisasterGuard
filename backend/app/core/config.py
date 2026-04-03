import os
from pathlib import Path
import torch

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

    @property
    def DEVICE(self) -> str:
        if torch.backends.mps.is_available():
            return 'mps'
        elif torch.cuda.is_available():
            return 'cuda'
        return 'cpu'

settings = Settings()
