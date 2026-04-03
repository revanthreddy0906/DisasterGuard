import torch
import torch.nn as nn
import torch.nn.functional as F

from ml import config


# =========================
# FOCAL LOSS
# =========================
# Standard Cross-Entropy loss fails when classes are imbalanced.
# In our dataset, ~60% of images are "no-damage". A lazy model could
# just guess "no-damage" every time and still get 60% accuracy.
#
# Focal Loss fixes this by:
#   1. DOWN-weighting easy, well-classified examples (intact buildings)
#   2. UP-weighting hard, misclassified examples (damaged buildings)
#
# gamma controls how much to focus on hard examples (higher = more focus)
# alpha provides per-class weights (higher weight = more important class)

class FocalLoss(nn.Module):

    def __init__(self, alpha=None, gamma=None, reduction="mean"):
        super().__init__()
        self.gamma = gamma if gamma is not None else config.FOCAL_GAMMA
        self.reduction = reduction

        if alpha is not None:
            self.register_buffer("alpha", torch.tensor(alpha, dtype=torch.float32))
        else:
            self.register_buffer("alpha", torch.tensor(config.FOCAL_ALPHA, dtype=torch.float32))

    def forward(self, logits, targets):
        # Get predicted probabilities
        probs = F.softmax(logits, dim=1)

        # Convert labels to one-hot: [2] -> [0, 0, 1]
        targets_oh = F.one_hot(targets, num_classes=logits.size(1)).float()

        # p_t = probability assigned to the correct class
        p_t = (probs * targets_oh).sum(dim=1)

        # Focal weight: (1 - p_t)^gamma
        # If model is confident and correct (p_t ~ 1.0), weight ~ 0 (ignore it)
        # If model is wrong (p_t ~ 0.0), weight ~ 1 (focus on it!)
        focal_weight = (1.0 - p_t) ** self.gamma

        # Standard cross-entropy loss per sample with label smoothing to prevent 100% over-confidence
        ce_loss = F.cross_entropy(logits, targets, reduction="none", label_smoothing=0.15)

        # Apply per-class alpha weights
        alpha_t = self.alpha.to(logits.device)[targets]

        # Final loss = alpha * focal_weight * cross_entropy
        loss = alpha_t * focal_weight * ce_loss

        return loss.mean() if self.reduction == "mean" else loss.sum()
