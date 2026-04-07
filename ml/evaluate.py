import argparse
import json
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader
from sklearn.metrics import classification_report, f1_score, accuracy_score, confusion_matrix
from tqdm import tqdm

from ml import config
from ml.dataset import XBDDataset, get_val_transforms
from ml.model import SiameseDamageNet


# =========================
# EVALUATE MODEL
# =========================

def evaluate(checkpoint_path, data_dir, batch_size=None):
    batch_size = batch_size or config.BATCH_SIZE
    device = config.DEVICE

    # -------- Load Model --------
    print(f"[INFO] Loading model from {checkpoint_path}")
    model = SiameseDamageNet(pretrained=False).to(device)
    ckpt = torch.load(checkpoint_path, map_location=device, weights_only=False)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()

    # -------- Load Test Data --------
    test_ds = XBDDataset(str(Path(data_dir) / "test"), "test", get_val_transforms())

    if len(test_ds) == 0:
        print("  ERROR: No test samples found!")
        return

    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False)

    print(f"  Test samples:  {len(test_ds)}")
    print(f"  Distribution:  {test_ds.get_class_distribution()}")

    # -------- Run Predictions --------
    all_preds = []
    all_targets = []

    with torch.no_grad():
        for pre_img, post_img, labels in tqdm(test_loader, desc="Evaluating"):
            pre_img = pre_img.to(device)
            post_img = post_img.to(device)

            logits = model(pre_img, post_img)
            all_preds.extend(logits.argmax(dim=1).cpu().numpy())
            all_targets.extend(labels.numpy())

    all_preds = np.array(all_preds)
    all_targets = np.array(all_targets)

    # -------- Print Results --------
    acc = accuracy_score(all_targets, all_preds)
    f1_w = f1_score(all_targets, all_preds, average="weighted", zero_division=0)
    f1_m = f1_score(all_targets, all_preds, average="macro", zero_division=0)

    print(f"\n{'=' * 50}")
    print(f"  Test Results")
    print(f"{'=' * 50}")
    print(f"  Accuracy:      {acc:.4f}")
    print(f"  F1 (weighted): {f1_w:.4f}")
    print(f"  F1 (macro):    {f1_m:.4f}")
    print(f"{'=' * 50}")

    report_text = classification_report(
        all_targets,
        all_preds,
        target_names=config.DAMAGE_CLASSES,
        zero_division=0,
    )
    print(f"\n{report_text}")

    cm = confusion_matrix(all_targets, all_preds, labels=list(range(config.NUM_CLASSES))).tolist()
    artifacts_dir = Path(config.CHECKPOINT_DIR)
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    metrics_payload = {
        "checkpoint": str(checkpoint_path),
        "data_dir": str(data_dir),
        "test_samples": int(len(test_ds)),
        "accuracy": float(acc),
        "f1_weighted": float(f1_w),
        "f1_macro": float(f1_m),
        "classes": config.DAMAGE_CLASSES,
        "confusion_matrix": cm,
    }
    (artifacts_dir / "evaluation_metrics.json").write_text(
        json.dumps(metrics_payload, indent=2),
        encoding="utf-8",
    )

    report_lines = [
        "Disaster Damage Assessment — Evaluation Report",
        "=" * 50,
        "",
        f"Checkpoint: {checkpoint_path}",
        f"Data dir:   {data_dir}",
        f"Test samples: {len(test_ds)}",
        "",
        f"Accuracy:      {acc:.4f}",
        f"F1 (macro):    {f1_m:.4f}",
        f"F1 (weighted): {f1_w:.4f}",
        "",
        "Confusion Matrix:",
        str(cm),
        "",
        "Classification Report:",
        report_text,
    ]
    (artifacts_dir / "evaluation_report.txt").write_text(
        "\n".join(report_lines),
        encoding="utf-8",
    )


# =========================
# RUN FROM COMMAND LINE
# =========================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate damage model")
    parser.add_argument("--checkpoint", type=str,
                        default=str(config.CHECKPOINT_DIR / "best_model.pth"))
    parser.add_argument("--data_dir", type=str,
                        default=str(config.DATA_DIR / "prepared"))
    parser.add_argument("--batch_size", type=int, default=config.BATCH_SIZE)
    args = parser.parse_args()

    evaluate(args.checkpoint, args.data_dir, args.batch_size)
