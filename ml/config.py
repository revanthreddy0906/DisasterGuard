import os
from pathlib import Path
import torch


# =========================
# PROJECT PATHS
# =========================

PROJECT_ROOT = Path(__file__).parent.parent.resolve()

DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
CHECKPOINT_DIR = PROJECT_ROOT / "checkpoints"

# Create directories if they don't exist
for d in [RAW_DATA_DIR, CHECKPOINT_DIR]:
    d.mkdir(parents=True, exist_ok=True)


# =========================
# DAMAGE CLASSES
# =========================

# We merged minor-damage + major-damage into "severe-damage"
# This gives us 3 clean classes instead of the original 4
DAMAGE_CLASSES = ["no-damage", "severe-damage", "destroyed"]
NUM_CLASSES = len(DAMAGE_CLASSES)

# Lookup dictionaries for converting between class names and numbers
CLASS_TO_IDX = {cls: idx for idx, cls in enumerate(DAMAGE_CLASSES)}
IDX_TO_CLASS = {idx: cls for cls, idx in CLASS_TO_IDX.items()}

# Higher weight = model pays more attention to that class
CLASS_WEIGHTS = [0.5, 1.0, 2.0]


# =========================
# DATA SPLIT RATIOS
# =========================

TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15


# =========================
# IMAGE SETTINGS
# =========================

IMG_SIZE = 224  # All images resized to 224x224

# ImageNet normalization values (required for EfficientNet)
IMG_MEAN = [0.485, 0.456, 0.406]
IMG_STD = [0.229, 0.224, 0.225]


# =========================
# MODEL SETTINGS
# =========================

BACKBONE = "efficientnet_b0"
BACKBONE_FEATURE_DIM = 1280  # EfficientNet-B0 outputs 1280 features
PRETRAINED = True
DROPOUT_RATE = 0.3


# =========================
# TRAINING SETTINGS
# =========================

SEED = 42
BATCH_SIZE = 32
NUM_WORKERS = min(4, os.cpu_count() or 1)
LEARNING_RATE = 1e-4
WEIGHT_DECAY = 1e-4
EPOCHS = 50
WARMUP_EPOCHS = 3  # Freeze backbone for first 3 epochs

# Focal Loss settings (handles class imbalance)
FOCAL_GAMMA = 1.0
FOCAL_ALPHA = CLASS_WEIGHTS


# =========================
# DEVICE SELECTION
# =========================

# Automatically pick the best available device
if torch.cuda.is_available():
    DEVICE = torch.device("cuda")
elif torch.backends.mps.is_available():
    DEVICE = torch.device("mps")
else:
    DEVICE = torch.device("cpu")
