import torch
import torch.nn as nn
import timm
from ml import config


# =========================
# SQUEEZE-AND-EXCITATION
# =========================
# This is an attention mechanism.
# It looks at all 3840 fused features and learns which ones
# are important for detecting damage vs which are just noise.

class SEBlock(nn.Module):

    def __init__(self, channels, reduction=16):
        super().__init__()
        self.fc = nn.Sequential(
            nn.Linear(channels, channels // reduction, bias=False),
            nn.ReLU(inplace=True),
            nn.Linear(channels // reduction, channels, bias=False),
            nn.Sigmoid(),
        )

    def forward(self, x):
        # Multiply each feature by its importance score
        return x * self.fc(x)


# =========================
# FEATURE FUSION MODULE
# =========================
# Takes the pre-disaster features and post-disaster features
# and combines them in a way that highlights what changed.

class FeatureFusion(nn.Module):

    def __init__(self, feature_dim=1280, reduction=16):
        super().__init__()
        fused_dim = feature_dim * 3  # concat(pre, post) + |pre - post|
        self.bn = nn.BatchNorm1d(fused_dim)
        self.se = SEBlock(fused_dim, reduction=reduction)

    def forward(self, feat_pre, feat_post):
        # Method 1: Glue them side by side [pre | post] = 2560 features
        concat = torch.cat([feat_pre, feat_post], dim=1)

        # Method 2: What changed? |pre - post| = 1280 features
        diff = torch.abs(feat_pre - feat_post)

        # Merge both methods = 3840 total features
        fused = torch.cat([concat, diff], dim=1)

        # Normalize and apply attention
        return self.se(self.bn(fused))


# =========================
# SIAMESE DAMAGE NETWORK
# =========================
# The main model. Two images go in, one damage prediction comes out.
#
# Architecture:
#   Pre-image  --> [Shared EfficientNet] --> Pre-features (1280)
#   Post-image --> [Shared EfficientNet] --> Post-features (1280)
#                                              |
#                                   [Feature Fusion + SE Attention]
#                                              |
#                                        [Classifier MLP]
#                                              |
#                                   3 classes: no-damage, severe, destroyed

class SiameseDamageNet(nn.Module):

    def __init__(self, backbone=None, pretrained=None, num_classes=None,
                 feature_dim=None, dropout=None, freeze_epochs=3):
        super().__init__()
        backbone = backbone or config.BACKBONE
        pretrained = pretrained if pretrained is not None else config.PRETRAINED
        num_classes = num_classes or config.NUM_CLASSES
        feature_dim = feature_dim or config.BACKBONE_FEATURE_DIM
        dropout = dropout or config.DROPOUT_RATE
        self.freeze_epochs = freeze_epochs

        # -------- Shared Encoder --------
        # Both pre and post images pass through this same EfficientNet
        self.encoder = timm.create_model(
            backbone, pretrained=pretrained, num_classes=0, global_pool="avg"
        )

        # Verify the actual output dimension matches what we expect
        with torch.no_grad():
            dummy = torch.randn(1, 3, config.IMG_SIZE, config.IMG_SIZE)
            actual_dim = self.encoder(dummy).shape[1]
            if actual_dim != feature_dim:
                feature_dim = actual_dim

        # -------- Fusion --------
        self.fusion = FeatureFusion(feature_dim=feature_dim)

        # -------- Classifier Head --------
        # Simple MLP: 3840 -> 512 -> 128 -> 3
        fusion_dim = feature_dim * 3
        self.classifier = nn.Sequential(
            nn.Linear(fusion_dim, 512),
            nn.BatchNorm1d(512),
            nn.ReLU(inplace=True),
            nn.Dropout(p=dropout),

            nn.Linear(512, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(inplace=True),
            nn.Dropout(p=dropout * 0.67),

            nn.Linear(128, num_classes),
        )

    def forward(self, pre_img, post_img):
        # Pass both images through the SAME encoder (weight sharing)
        feat_pre = self.encoder(pre_img)
        feat_post = self.encoder(post_img)

        # Fuse the features together
        fused = self.fusion(feat_pre, feat_post)

        # Classify the fused features
        return self.classifier(fused)

    def freeze_backbone(self):
        """Freeze EfficientNet weights (only train the new layers)"""
        for p in self.encoder.parameters():
            p.requires_grad = False

    def unfreeze_backbone(self):
        """Unfreeze EfficientNet weights (fine-tune everything)"""
        for p in self.encoder.parameters():
            p.requires_grad = True
