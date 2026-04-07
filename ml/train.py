import argparse
import json
import os
import random
import time

import numpy as np
import torch
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingWarmRestarts, LinearLR, SequentialLR
from torch.utils.data import DataLoader
from sklearn.metrics import f1_score, accuracy_score
from tqdm import tqdm

from ml import config
from ml.dataset import XBDDataset, get_train_transforms, get_val_transforms
from ml.model import SiameseDamageNet
from ml.losses import FocalLoss


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    if torch.backends.cudnn.is_available():
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False


# =========================
# DATA LOADERS
# =========================

def create_data_loaders(data_dir, batch_size, max_samples=None, seed=None):
    # On Mac (MPS) and CPU, multi-worker loading causes issues
    if config.DEVICE.type in ("mps", "cpu"):
        num_workers = 0
        pin_memory = False
    else:
        num_workers = config.NUM_WORKERS
        pin_memory = True
    seed = seed if seed is not None else config.SEED
    generator = torch.Generator()
    generator.manual_seed(seed)

    print(f"[INFO] Loading training data from {data_dir}/train")
    train_ds = XBDDataset(
        os.path.join(data_dir, "train"), "train",
        get_train_transforms(), max_samples
    )

    print(f"[INFO] Loading validation data from {data_dir}/val")
    val_ds = XBDDataset(
        os.path.join(data_dir, "val"), "val",
        get_val_transforms(), max_samples
    )

    train_loader = DataLoader(
        train_ds, batch_size=batch_size, shuffle=True,
        num_workers=num_workers, pin_memory=pin_memory, drop_last=True, generator=generator
    )
    val_loader = DataLoader(
        val_ds, batch_size=batch_size, shuffle=False,
        num_workers=num_workers, pin_memory=pin_memory, generator=generator
    )

    return train_loader, val_loader


# =========================
# TRAIN ONE EPOCH
# =========================

def train_one_epoch(model, loader, criterion, optimizer, device):
    model.train()
    total_loss = 0.0
    all_preds = []
    all_targets = []

    for pre_img, post_img, labels in tqdm(loader, desc="  Train", leave=False):
        # Move data to GPU/MPS
        pre_img = pre_img.to(device)
        post_img = post_img.to(device)
        labels = labels.to(device).long()

        # Forward pass
        optimizer.zero_grad()
        logits = model(pre_img, post_img)
        loss = criterion(logits, labels)

        # Backward pass
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()

        # Track metrics
        total_loss += loss.item()
        all_preds.extend(logits.argmax(dim=1).cpu().numpy())
        all_targets.extend(labels.cpu().numpy())

    avg_loss = total_loss / len(loader)
    acc = accuracy_score(all_targets, all_preds)
    f1 = f1_score(all_targets, all_preds, average="weighted", zero_division=0)
    return avg_loss, acc, f1


# =========================
# VALIDATION
# =========================

@torch.no_grad()
def validate(model, loader, criterion, device):
    model.eval()
    total_loss = 0.0
    all_preds = []
    all_targets = []

    for pre_img, post_img, labels in tqdm(loader, desc="  Val", leave=False):
        pre_img = pre_img.to(device)
        post_img = post_img.to(device)
        labels = labels.to(device).long()

        logits = model(pre_img, post_img)
        loss = criterion(logits, labels)

        total_loss += loss.item()
        all_preds.extend(logits.argmax(dim=1).cpu().numpy())
        all_targets.extend(labels.cpu().numpy())

    avg_loss = total_loss / max(len(loader), 1)
    acc = accuracy_score(all_targets, all_preds)
    f1 = f1_score(all_targets, all_preds, average="weighted", zero_division=0)
    return avg_loss, acc, f1


# =========================
# MAIN TRAINING LOOP
# =========================

def train(data_dir, epochs, batch_size, lr):
    device = config.DEVICE
    set_seed(config.SEED)
    config.CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

    run_config = {
        "seed": config.SEED,
        "data_dir": data_dir,
        "epochs": epochs,
        "batch_size": batch_size,
        "learning_rate": lr,
        "weight_decay": config.WEIGHT_DECAY,
        "backbone": config.BACKBONE,
        "img_size": config.IMG_SIZE,
        "classes": config.DAMAGE_CLASSES,
        "device": str(device),
    }
    (config.CHECKPOINT_DIR / "training_config.json").write_text(
        json.dumps(run_config, indent=2),
        encoding="utf-8",
    )

    print("=" * 60)
    print("  Disaster Damage Assessment — Training")
    print("=" * 60)
    print(f"  Device:     {device}")
    print(f"  Epochs:     {epochs}")
    print(f"  Batch size: {batch_size}")
    print(f"  LR:         {lr}")
    print(f"  Seed:       {config.SEED}")
    print("=" * 60)

    # -------- Load Data --------
    train_loader, val_loader = create_data_loaders(data_dir, batch_size, seed=config.SEED)
    print(f"\n  Train samples: {len(train_loader.dataset)}")
    print(f"  Val samples:   {len(val_loader.dataset)}")
    print(f"  Distribution:  {train_loader.dataset.get_class_distribution()}")

    if len(train_loader.dataset) == 0:
        print("\n  ERROR: No training samples found!")
        return

    # -------- Build Model --------
    model = SiameseDamageNet().to(device)

    # Stage 1: Freeze the EfficientNet backbone
    # Only train the fusion + classifier layers first
    model.freeze_backbone()
    print(f"\n  Backbone FROZEN for first {model.freeze_epochs} epochs")

    # -------- Loss Function --------
    # Use inverse-frequency class weights so the model focuses on rare classes
    class_weights = train_loader.dataset.compute_class_weights()
    print(f"  Class weights: {class_weights.tolist()}")
    criterion = FocalLoss(alpha=class_weights.tolist())

    # -------- Optimizer --------
    optimizer = AdamW(
        filter(lambda p: p.requires_grad, model.parameters()),
        lr=lr, weight_decay=config.WEIGHT_DECAY
    )

    # -------- Learning Rate Schedule --------
    # Warm up LR for first 3 epochs, then cosine decay
    warmup = LinearLR(optimizer, start_factor=0.1, total_iters=config.WARMUP_EPOCHS)
    cosine = CosineAnnealingWarmRestarts(optimizer, T_0=10, T_mult=2)
    scheduler = SequentialLR(optimizer, [warmup, cosine], milestones=[config.WARMUP_EPOCHS])

    # -------- Training Loop --------
    best_f1 = 0.0
    epoch_history = []

    print(f"\n{'─' * 60}")
    print("  Starting training...\n")

    for epoch in range(epochs):
        t0 = time.time()

        # Stage 2: Unfreeze backbone after warmup epochs
        if epoch == model.freeze_epochs:
            model.unfreeze_backbone()
            # Use a 10x smaller LR for the pre-trained backbone
            optimizer = AdamW(model.parameters(), lr=lr * 0.1,
                              weight_decay=config.WEIGHT_DECAY)
            print(f"\n  Backbone UNFROZEN at epoch {epoch + 1}")

        # Train for one epoch
        train_loss, train_acc, train_f1 = train_one_epoch(
            model, train_loader, criterion, optimizer, device
        )

        # Validate
        val_loss, val_acc, val_f1 = validate(
            model, val_loader, criterion, device
        )

        scheduler.step()
        elapsed = time.time() - t0

        # Print results
        print(f"  Epoch {epoch+1:3d}/{epochs} | "
              f"TrLoss: {train_loss:.4f} | VaLoss: {val_loss:.4f} | "
              f"VaAcc: {val_acc:.4f} | VaF1: {val_f1:.4f} | "
              f"Time: {elapsed:.1f}s")
        epoch_history.append({
            "epoch": epoch + 1,
            "train_loss": train_loss,
            "train_acc": train_acc,
            "train_f1_weighted": train_f1,
            "val_loss": val_loss,
            "val_acc": val_acc,
            "val_f1_weighted": val_f1,
            "elapsed_sec": elapsed,
        })

        # Save best model
        if val_f1 > best_f1:
            best_f1 = val_f1
            save_path = str(config.CHECKPOINT_DIR / "best_model.pth")
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "val_f1": val_f1,
                "seed": config.SEED,
                "run_config": run_config,
            }, save_path)
            print(f"  --> Best model saved! (F1: {val_f1:.4f})")

    (config.CHECKPOINT_DIR / "training_summary.json").write_text(
        json.dumps(
            {
                "best_val_f1_weighted": best_f1,
                "epochs": epochs,
                "history": epoch_history,
                "run_config": run_config,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"\n{'=' * 60}")
    print(f"  Training Complete! Best Val F1: {best_f1:.4f}")
    print(f"{'=' * 60}")


# =========================
# RUN FROM COMMAND LINE
# =========================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train damage assessment model")
    parser.add_argument("--data_dir", type=str, default=str(config.DATA_DIR / "prepared"))
    parser.add_argument("--epochs", type=int, default=config.EPOCHS)
    parser.add_argument("--batch_size", type=int, default=config.BATCH_SIZE)
    parser.add_argument("--lr", type=float, default=config.LEARNING_RATE)
    args = parser.parse_args()

    train(args.data_dir, args.epochs, args.batch_size, args.lr)
