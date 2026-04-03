import numpy as np
from PIL import Image


class PatchAnalyzer:
    """Sliding window patch analyzer.
    
    Breaks pre/post PIL Images into 224x224 patches and runs inference
    on each one. Returns a list of patch predictions with bounding boxes
    in image coordinates (x, y, w, h).
    """

    def __init__(self, model_loader, patch_size=224):
        self.model_loader = model_loader
        self.patch_size = patch_size

    def analyze(self, pre_pil: Image.Image, post_pil: Image.Image, step: int = 112):
        """
        Args:
            pre_pil:  PIL Image (pre-disaster)
            post_pil: PIL Image (post-disaster)
            step:     stride in pixels (112 = 50% overlap with 224 patch)
        
        Returns:
            dict with:
                hotspots: list of {bbox, damage_class, confidence, probabilities}
                global_result: aggregated prediction across all patches
        """
        W, H = pre_pil.size
        pre_np = np.array(pre_pil)
        post_np = np.array(post_pil)

        patch_results = []

        # Sliding window over the image
        for y in range(0, H - self.patch_size + 1, step):
            for x in range(0, W - self.patch_size + 1, step):
                pre_patch = pre_np[y:y + self.patch_size, x:x + self.patch_size]
                post_patch = post_np[y:y + self.patch_size, x:x + self.patch_size]

                pred = self.model_loader.predict_patch(pre_patch, post_patch)

                patch_results.append({
                    "bbox": [x, y, self.patch_size, self.patch_size],
                    "damage_class": pred["damage_class"],
                    "confidence": pred["confidence"],
                    "probabilities": pred["probabilities"]
                })

        if not patch_results:
            return {"hotspots": [], "global_result": None}

        # Aggregate: average probabilities across all patches
        prob_keys = list(patch_results[0]["probabilities"].keys())
        prob_sums = {k: 0.0 for k in prob_keys}
        for pr in patch_results:
            for k, v in pr["probabilities"].items():
                prob_sums[k] += v

        n = len(patch_results)
        global_probs = {k: v / n for k, v in prob_sums.items()}
        best_class = max(global_probs, key=global_probs.get)

        global_result = {
            "damage_class": best_class,
            "confidence": global_probs[best_class],
            "probabilities": global_probs
        }

        return {
            "hotspots": patch_results,
            "global_result": global_result
        }
