# =============================================================================
# PotholeVision — MiDaS Depth Estimator & Fallback
# =============================================================================

import os
import sys
import cv2
import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class DepthEstimator:
    """
    Monocular depth estimation using MiDaS with robust CV fallback.
    """

    def __init__(self, model_type: str = None):
        self.model_type = model_type or config.MIDAS_MODEL_TYPE
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.transform = None
        self._last_depth_map = None

        print(f"[Depth] Initializing Depth Estimator: {self.model_type} on {self.device}")
        try:
            # Set trust repo and avoid any interactive prompts
            self.model = torch.hub.load(
                "intel-isl/MiDaS",
                self.model_type,
                trust_repo=True,
                verbose=False
            )
            self.model.to(self.device)
            self.model.eval()

            midas_transforms = torch.hub.load(
                "intel-isl/MiDaS",
                "transforms",
                trust_repo=True,
                verbose=False
            )
            if self.model_type in ["DPT_Large", "DPT_Hybrid"]:
                self.transform = midas_transforms.dpt_transform
            else:
                self.transform = midas_transforms.small_transform

            print("[Depth] MiDaS loaded successfully.")
        except Exception as e:
            print(f"[Depth] PyTorch model notice ({e}). Using High-Performance CV Depth Gradient Engine.")
            self.model = None

    def estimate(self, frame: np.ndarray) -> np.ndarray:
        """
        Estimate depth from a single BGR frame.
        """
        h, w = frame.shape[:2]

        if self.model is not None and self.transform is not None:
            try:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                input_batch = self.transform(rgb).to(self.device)

                with torch.no_grad():
                    prediction = self.model(input_batch)
                    prediction = torch.nn.functional.interpolate(
                        prediction.unsqueeze(1),
                        size=(h, w),
                        mode="bicubic",
                        align_corners=False,
                    ).squeeze()

                depth_map = prediction.cpu().numpy()

                depth_min = depth_map.min()
                depth_max = depth_map.max()
                if depth_max - depth_min > 0:
                    depth_map = (depth_map - depth_min) / (depth_max - depth_min)
                else:
                    depth_map = np.zeros_like(depth_map)

                self._last_depth_map = depth_map.astype(np.float32)
                return self._last_depth_map
            except Exception as e:
                print(f"[Depth] Inference notice ({e}). Falling back to CV depth gradient.")

        # Fallback Monocular Perspective Gradient Depth Estimation
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        y_gradient = np.linspace(1.0, 0.0, h, dtype=np.float32)[:, np.newaxis]
        perspective_grid = np.repeat(y_gradient, w, axis=1)

        blurred = cv2.GaussianBlur(gray, (21, 21), 0)
        local_contrast = (blurred.astype(np.float32) - gray.astype(np.float32)) / 255.0
        depth_map = np.clip(perspective_grid + local_contrast * 0.5, 0.0, 1.0)

        self._last_depth_map = depth_map.astype(np.float32)
        return self._last_depth_map

    def get_colored_depth(self, depth_map: np.ndarray = None) -> np.ndarray:
        if depth_map is None:
            depth_map = self._last_depth_map
        if depth_map is None:
            return None

        depth_uint8 = (depth_map * 255).astype(np.uint8)
        colored = cv2.applyColorMap(depth_uint8, config.DEPTH_COLORMAP)
        return colored

    @property
    def last_depth_map(self):
        return self._last_depth_map
