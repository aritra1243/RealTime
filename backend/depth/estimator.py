# =============================================================================
# PotholeVision — MiDaS Depth Estimator
# =============================================================================

import cv2
import numpy as np
import torch

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class DepthEstimator:
    """
    Monocular depth estimation using MiDaS.
    
    Produces a relative depth map from a single RGB image.
    The depth values are relative (higher = farther from camera).
    """

    def __init__(self, model_type: str = None):
        """
        Initialize the depth estimator.
        
        Args:
            model_type: MiDaS model type. Options:
                        "DPT_Large"   — highest quality, slowest
                        "DPT_Hybrid"  — balanced
                        "MiDaS_small" — fastest, good enough for real-time
        """
        self.model_type = model_type or config.MIDAS_MODEL_TYPE
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        print(f"[Depth] Loading MiDaS model: {self.model_type} on {self.device}")

        # Load model from PyTorch Hub (trust_repo=True avoids interactive prompts)
        self.model = torch.hub.load("intel-isl/MiDaS", self.model_type, trust_repo=True)
        self.model.to(self.device)
        self.model.eval()

        # Load the appropriate transform
        midas_transforms = torch.hub.load("intel-isl/MiDaS", "transforms", trust_repo=True)
        if self.model_type == "DPT_Large" or self.model_type == "DPT_Hybrid":
            self.transform = midas_transforms.dpt_transform
        else:
            self.transform = midas_transforms.small_transform

        print(f"[Depth] MiDaS loaded successfully.")
        self._last_depth_map = None

    def estimate(self, frame: np.ndarray) -> np.ndarray:
        """
        Estimate depth from a single BGR frame.
        
        Args:
            frame: BGR image (H x W x 3)
            
        Returns:
            depth_map: Float32 array (H x W) with relative depth values.
                       Higher values = farther from camera.
                       Normalized to [0, 1] range.
        """
        h, w = frame.shape[:2]

        # Convert BGR to RGB
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Apply MiDaS transform
        input_batch = self.transform(rgb).to(self.device)

        # Inference
        with torch.no_grad():
            prediction = self.model(input_batch)

            # Resize to original frame size
            prediction = torch.nn.functional.interpolate(
                prediction.unsqueeze(1),
                size=(h, w),
                mode="bicubic",
                align_corners=False,
            ).squeeze()

        # Convert to numpy
        depth_map = prediction.cpu().numpy()

        # Normalize to [0, 1]
        depth_min = depth_map.min()
        depth_max = depth_map.max()
        if depth_max - depth_min > 0:
            depth_map = (depth_map - depth_min) / (depth_max - depth_min)
        else:
            depth_map = np.zeros_like(depth_map)

        self._last_depth_map = depth_map.astype(np.float32)
        return self._last_depth_map

    def get_colored_depth(self, depth_map: np.ndarray = None) -> np.ndarray:
        """
        Convert depth map to a colored visualization.
        
        Args:
            depth_map: Float32 depth map [0, 1]. If None, uses last estimated.
            
        Returns:
            colored: BGR image (H x W x 3) with colormap applied.
        """
        if depth_map is None:
            depth_map = self._last_depth_map
        if depth_map is None:
            return None

        # Convert to uint8 for colormap
        depth_uint8 = (depth_map * 255).astype(np.uint8)
        colored = cv2.applyColorMap(depth_uint8, config.DEPTH_COLORMAP)
        return colored

    @property
    def last_depth_map(self):
        """Return the last computed depth map."""
        return self._last_depth_map
