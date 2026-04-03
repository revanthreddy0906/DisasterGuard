import json
import os
from pathlib import Path
from collections import Counter

import cv2
import numpy as np
import torch
from torch.utils.data import Dataset
import albumentations as A
from albumentations.pytorch import ToTensorV2

from ml import config


# =========================
# DATA AUGMENTATION
# =========================
# These transforms help prevent overfitting by showing the model
# slightly different versions of each image every epoch.

def get_train_transforms():
    """Heavy augmentation for training data"""
    return A.ReplayCompose([
        A.RandomResizedCrop(
            size=(config.IMG_SIZE, config.IMG_SIZE),
            scale=(0.7, 1.0),   # Zoom in/out randomly
            ratio=(0.9, 1.1),
            p=1.0
        ),
        A.HorizontalFlip(p=0.5),
        A.VerticalFlip(p=0.5),
        A.RandomRotate90(p=0.5),
        A.OneOf([
            A.ColorJitter(brightness=0.2, contrast=0.2,
                          saturation=0.2, hue=0.05, p=1.0),
            A.RandomBrightnessContrast(brightness_limit=0.2,
                                       contrast_limit=0.2, p=1.0),
        ], p=0.5),
        A.GaussNoise(p=0.2),
        A.GaussianBlur(blur_limit=(3, 5), p=0.1),
        A.Normalize(mean=config.IMG_MEAN, std=config.IMG_STD),
        ToTensorV2(),
    ])


def get_val_transforms():
    """Simple resize + normalize for validation (no random augmentation)"""
    return A.ReplayCompose([
        A.Resize(config.IMG_SIZE, config.IMG_SIZE),
        A.Normalize(mean=config.IMG_MEAN, std=config.IMG_STD),
        ToTensorV2(),
    ])


def apply_synchronized_transforms(pre_image, post_image, transforms):
    """
    Apply the EXACT SAME random transform to both pre and post images.
    This is critical — if we flip the pre-image but not the post-image,
    the model would think everything changed!
    """
    # Transform the pre-image and record what random ops were applied
    result_pre = transforms(image=pre_image)
    pre_tensor = result_pre["image"]

    # Replay those exact same ops on the post-image
    result_post = A.ReplayCompose.replay(result_pre["replay"], image=post_image)
    post_tensor = result_post["image"]

    return pre_tensor, post_tensor


# =========================
# DATASET CLASS
# =========================
# Loads pre/post disaster image pairs with their damage labels.
# Supports two folder structures:
#   1. images/ + labels/ (raw xBD format)
#   2. class_name/pre_*.png + post_*.png (our prepared format)

class XBDDataset(Dataset):

    def __init__(self, data_dir, split="train", transforms=None, max_samples=None):
        self.data_dir = Path(data_dir)
        self.split = split
        self.transforms = transforms
        self.samples = []
        self._load_samples()

        if max_samples is not None:
            self.samples = self.samples[:max_samples]

    def _load_samples(self):
        """Try to load from images/labels structure, fall back to flat structure"""
        images_dir = self.data_dir / "images"
        labels_dir = self.data_dir / "labels"

        if not images_dir.exists():
            # Use flat class-folder structure instead
            self._load_flat_structure()
            return

        # Load from raw xBD images/ + labels/ directories
        post_images = sorted(images_dir.glob("*_post_disaster.*"))
        for post_path in post_images:
            stem = post_path.stem.replace("_post_disaster", "_pre_disaster")
            pre_path = images_dir / f"{stem}{post_path.suffix}"
            if not pre_path.exists():
                continue

            label_path = labels_dir / (post_path.stem + ".json")
            damage_label = self._parse_label(label_path) if label_path.exists() else 0

            self.samples.append({
                "pre_path": str(pre_path),
                "post_path": str(post_path),
                "label": damage_label,
            })

    def _load_flat_structure(self):
        """Load from prepared folder: no-damage/pre_001.png, post_001.png, etc."""
        for class_name in config.DAMAGE_CLASSES:
            class_dir = self.data_dir / class_name
            if not class_dir.exists():
                continue

            label_idx = config.CLASS_TO_IDX[class_name]
            for pre_path in sorted(class_dir.glob("pre_*.*")):
                post_path = class_dir / pre_path.name.replace("pre_", "post_")
                if post_path.exists():
                    self.samples.append({
                        "pre_path": str(pre_path),
                        "post_path": str(post_path),
                        "label": label_idx,
                    })

    def _parse_label(self, label_path):
        """Read JSON label and return the worst damage level found"""
        try:
            with open(label_path, "r") as f:
                data = json.load(f)

            worst = 0
            for feat in data.get("features", {}).get("xy", []):
                damage_type = feat.get("properties", {}).get("subtype", "no-damage")
                if damage_type in config.CLASS_TO_IDX:
                    worst = max(worst, config.CLASS_TO_IDX[damage_type])
            return worst
        except (json.JSONDecodeError, KeyError, TypeError):
            return 0

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        sample = self.samples[idx]

        # Load both images
        pre_img = cv2.imread(sample["pre_path"])
        post_img = cv2.imread(sample["post_path"])

        # Handle missing/corrupt images
        if pre_img is None or post_img is None:
            pre_img = np.zeros((config.IMG_SIZE, config.IMG_SIZE, 3), dtype=np.uint8)
            post_img = np.zeros((config.IMG_SIZE, config.IMG_SIZE, 3), dtype=np.uint8)

        # OpenCV loads as BGR, convert to RGB
        pre_img = cv2.cvtColor(pre_img, cv2.COLOR_BGR2RGB)
        post_img = cv2.cvtColor(post_img, cv2.COLOR_BGR2RGB)

        # Apply augmentation (synchronized for both images)
        if self.transforms is not None:
            pre_img, post_img = apply_synchronized_transforms(
                pre_img, post_img, self.transforms
            )
        else:
            # No transforms — just resize and convert to tensor
            pre_img = cv2.resize(pre_img, (config.IMG_SIZE, config.IMG_SIZE))
            post_img = cv2.resize(post_img, (config.IMG_SIZE, config.IMG_SIZE))
            pre_img = torch.from_numpy(pre_img).permute(2, 0, 1).float() / 255.0
            post_img = torch.from_numpy(post_img).permute(2, 0, 1).float() / 255.0

        label = sample["label"]
        return pre_img, post_img, label

    def get_class_distribution(self):
        """Count how many samples per class"""
        counts = {cls: 0 for cls in config.DAMAGE_CLASSES}
        for s in self.samples:
            counts[config.IDX_TO_CLASS[s["label"]]] += 1
        return counts

    def compute_class_weights(self):
        """
        Calculate inverse-frequency weights so the model pays more
        attention to rare classes (destroyed) and less to common ones (no-damage).
        """
        dist = self.get_class_distribution()
        total = sum(dist.values())
        if total == 0:
            return torch.ones(config.NUM_CLASSES)

        weights = []
        import math
        for cls in config.DAMAGE_CLASSES:
            count = dist[cls]
            raw_weight = total / (config.NUM_CLASSES * count) if count > 0 else 1.0
            weights.append(math.sqrt(raw_weight)) # Dampen extreme class imbalance weights

        return torch.tensor(weights, dtype=torch.float32)
