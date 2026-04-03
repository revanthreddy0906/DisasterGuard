import sys
from pathlib import Path

# Add project root to path so we can import ml modules
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import torch
import torch.nn.functional as F
import numpy as np
from PIL import Image
import io
from functools import lru_cache

from ml.model import SiameseDamageNet
from ml.dataset import get_val_transforms, apply_synchronized_transforms
from app.core.config import settings


class ModelLoader:
    _instance = None
    model = None
    transforms = None

    def __new__(cls):
        if cls._instance is None:
            instance = super(ModelLoader, cls).__new__(cls)
            try:
                instance.load_model()
                cls._instance = instance
            except Exception as e:
                raise e
        return cls._instance

    def load_model(self):
        print(f"Loading model from {settings.BEST_MODEL_PATH}...")
        device = torch.device(settings.DEVICE)
        self.model = SiameseDamageNet(pretrained=False)
        if not settings.BEST_MODEL_PATH.exists():
            raise FileNotFoundError(f"Model checkpoint not found at {settings.BEST_MODEL_PATH}")
        checkpoint = torch.load(settings.BEST_MODEL_PATH, map_location=device, weights_only=False)
        
        # Remap state dict keys from old architecture to new clean architecture
        state_dict = checkpoint["model_state_dict"]
        new_state_dict = {}
        for k, v in state_dict.items():
            k = k.replace("fusion.se.excitation.", "fusion.se.fc.")
            k = k.replace("classifier.classifier.", "classifier.")
            new_state_dict[k] = v
            
        self.model.load_state_dict(new_state_dict)
        self.model.to(device)
        self.model.eval()
        self.transforms = get_val_transforms()
        print("Model loaded successfully!")

    def predict(self, pre_image_bytes, post_image_bytes):
        device = torch.device(settings.DEVICE)
        pre_img = Image.open(io.BytesIO(pre_image_bytes)).convert("RGB")
        post_img = Image.open(io.BytesIO(post_image_bytes)).convert("RGB")
        pre_np = np.array(pre_img)
        post_np = np.array(post_img)
        pre_tensor, post_tensor = apply_synchronized_transforms(pre_np, post_np, self.transforms)
        pre_tensor = pre_tensor.unsqueeze(0).to(device)
        post_tensor = post_tensor.unsqueeze(0).to(device)
        with torch.no_grad():
            logits = self.model(pre_tensor, post_tensor)
            probs = F.softmax(logits, dim=1)
        probs_np = probs.cpu().numpy()[0]
        class_idx = np.argmax(probs_np)
        confidence = float(probs_np[class_idx])
        damage_class = settings.DAMAGE_CLASSES[class_idx]
        probabilities = {cls: float(prob) for cls, prob in zip(settings.DAMAGE_CLASSES, probs_np)}
        return {"damage_class": damage_class, "confidence": confidence, "probabilities": probabilities}


    def predict_patch(self, pre_np, post_np):
        device = torch.device(settings.DEVICE)
        pre_tensor, post_tensor = apply_synchronized_transforms(pre_np, post_np, self.transforms)
        pre_tensor = pre_tensor.unsqueeze(0).to(device)
        post_tensor = post_tensor.unsqueeze(0).to(device)
        with torch.no_grad():
            logits = self.model(pre_tensor, post_tensor)
            probs = F.softmax(logits, dim=1)
        probs_np = probs.cpu().numpy()[0]
        class_idx = np.argmax(probs_np)
        confidence = float(probs_np[class_idx])
        damage_class = settings.DAMAGE_CLASSES[class_idx]
        probabilities = {cls: float(prob) for cls, prob in zip(settings.DAMAGE_CLASSES, probs_np)}
        return {"damage_class": damage_class, "confidence": confidence, "probabilities": probabilities}

@lru_cache()
def get_model_loader():
    return ModelLoader()
