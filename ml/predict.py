import argparse

import cv2
import torch
import albumentations as A

from ml import config
from ml.model import SiameseDamageNet
from ml.dataset import get_val_transforms


# =========================
# LOAD TRAINED MODEL
# =========================

def load_model(checkpoint_path=None, device=None):
    device = device or config.DEVICE
    checkpoint_path = checkpoint_path or str(config.CHECKPOINT_DIR / "best_model.pth")

    print(f"[INFO] Loading model from {checkpoint_path}")
    model = SiameseDamageNet(pretrained=False).to(device)
    ckpt = torch.load(checkpoint_path, map_location=device, weights_only=False)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()
    print(f"[INFO] Model loaded (from epoch {ckpt.get('epoch', '?')})")

    return model


# =========================
# PREDICT DAMAGE
# =========================

def predict(pre_path, post_path, model=None, device=None):
    device = device or config.DEVICE

    # Load model if not provided
    if model is None:
        model = load_model(device=device)

    # Load and convert images to RGB
    pre_img = cv2.cvtColor(cv2.imread(pre_path), cv2.COLOR_BGR2RGB)
    post_img = cv2.cvtColor(cv2.imread(post_path), cv2.COLOR_BGR2RGB)

    # Apply the same validation transforms to both images
    transforms = get_val_transforms()
    result_pre = transforms(image=pre_img)
    pre_tensor = result_pre["image"].unsqueeze(0).to(device)

    # Replay the exact same transform on the post image
    result_post = A.ReplayCompose.replay(result_pre["replay"], image=post_img)
    post_tensor = result_post["image"].unsqueeze(0).to(device)

    # Run inference
    with torch.no_grad():
        logits = model(pre_tensor, post_tensor)
        probs = torch.softmax(logits, dim=1)

    # Get the predicted class
    idx = logits.argmax(dim=1).item()

    return {
        "class": config.IDX_TO_CLASS[idx],
        "confidence": probs[0, idx].item(),
        "probabilities": {
            config.IDX_TO_CLASS[i]: probs[0, i].item()
            for i in range(config.NUM_CLASSES)
        },
    }


# =========================
# RUN FROM COMMAND LINE
# =========================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Predict damage from image pair")
    parser.add_argument("--pre", type=str, required=True, help="Pre-disaster image")
    parser.add_argument("--post", type=str, required=True, help="Post-disaster image")
    parser.add_argument("--checkpoint", type=str,
                        default=str(config.CHECKPOINT_DIR / "best_model.pth"))
    args = parser.parse_args()

    result = predict(args.pre, args.post)

    print(f"\n{'=' * 40}")
    print(f"  Predicted: {result['class']}")
    print(f"  Confidence: {result['confidence']:.1%}")
    print(f"{'=' * 40}")
    for cls, prob in result["probabilities"].items():
        bar = "█" * int(prob * 30)
        print(f"  {cls:15s}: {prob:.4f} {bar}")
