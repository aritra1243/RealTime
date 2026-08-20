# =============================================================================
# PotholeVision — Pothole Analyzer
# =============================================================================
# Combines detection masks with depth maps to calculate pothole dimensions,
# depth, volume, and severity.

import cv2
import numpy as np
from typing import List, Optional, Tuple
from scipy import ndimage

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from detection.detector import Detection


class PotholeAnalyzer:
    """
    Analyzes detected potholes by combining segmentation masks with depth maps.
    
    Calculates:
    - Max / average depth relative to surrounding road surface
    - Surface area (in pixels and approximate real-world units)
    - Volume estimation
    - Severity classification (SHALLOW / MODERATE / CRITICAL)
    """

    def __init__(self):
        self.reference_margin = config.REFERENCE_MARGIN_PX
        self.focal_length = config.FOCAL_LENGTH_PX
        self.scale = config.REAL_WORLD_SCALE

    def analyze(
        self,
        detections: List[Detection],
        depth_map: Optional[np.ndarray],
        frame_shape: Tuple[int, int],
    ) -> List[Detection]:
        """
        Analyze each detection using the depth map.
        
        Args:
            detections: List of Detection objects from the detector.
            depth_map: Normalized depth map [0, 1] (H x W). Can be None.
            frame_shape: (height, width) of the original frame.
            
        Returns:
            Updated list of Detection objects with depth/severity info filled in.
        """
        h, w = frame_shape[:2]

        for det in detections:
            if depth_map is not None and det.mask is not None:
                self._analyze_depth(det, depth_map, h, w)
            else:
                # Without depth, estimate severity from size alone
                self._analyze_size_only(det, h, w)

            # Calculate approximate real-world dimensions from contour
            self._calculate_dimensions(det)

        return detections

    def _analyze_depth(
        self, det: Detection, depth_map: np.ndarray, h: int, w: int
    ):
        """
        Extract depth information for a single detection.
        
        Strategy:
        1. Get the depth values inside the pothole mask
        2. Get the depth values of the surrounding road surface (reference plane)
        3. The pothole depth = road_surface_depth - pothole_depth
           (potholes are closer to the camera, so they have lower depth values
            in MiDaS output where higher = farther)
        """
        mask = det.mask
        if mask is None or mask.shape != depth_map.shape:
            return

        # ── Pothole region depths ────────────────────────────────────
        pothole_depths = depth_map[mask > 0]
        if len(pothole_depths) == 0:
            return

        # ── Reference road surface ───────────────────────────────────
        # Dilate the mask to get the surrounding road area
        kernel = np.ones((self.reference_margin, self.reference_margin), np.uint8)
        dilated = cv2.dilate(mask, kernel, iterations=1)
        reference_mask = dilated - mask  # Ring around the pothole

        # Clip to frame bounds
        reference_mask = np.clip(reference_mask, 0, 1).astype(np.uint8)

        reference_depths = depth_map[reference_mask > 0]
        if len(reference_depths) == 0:
            # Fallback: use median of entire depth map as reference
            reference_depth = np.median(depth_map)
        else:
            reference_depth = np.median(reference_depths)

        # ── Relative depth ───────────────────────────────────────────
        # In MiDaS, higher values = farther. Potholes are depressions,
        # so they might appear as lower values (closer) or higher values
        # (depending on the model and geometry).
        # We compute the absolute difference from the reference plane.
        pothole_median = np.median(pothole_depths)
        relative_depths = np.abs(pothole_depths - reference_depth)

        det.max_depth = float(np.max(relative_depths))
        det.avg_depth = float(np.mean(relative_depths))

        # ── Area ─────────────────────────────────────────────────────
        det.area_px = int(np.sum(mask > 0))

        # ── Volume estimation ────────────────────────────────────────
        # Approximate: sum of all relative depth values × pixel area
        det.volume = float(np.sum(relative_depths))

        # ── Severity classification ──────────────────────────────────
        det.severity = self._classify_severity(det.max_depth)

    def _analyze_size_only(self, det: Detection, h: int, w: int):
        """Fallback: estimate severity from size alone when no depth is available."""
        x1, y1, x2, y2 = det.bbox
        bbox_area = (x2 - x1) * (y2 - y1)
        frame_area = h * w

        # Larger potholes relative to frame = more severe
        area_ratio = bbox_area / frame_area
        if area_ratio < 0.02:
            det.severity = "SHALLOW"
        elif area_ratio < 0.08:
            det.severity = "MODERATE"
        else:
            det.severity = "CRITICAL"

        det.max_depth = area_ratio
        det.avg_depth = area_ratio * 0.7
        det.area_px = bbox_area

    def _calculate_dimensions(self, det: Detection):
        """Calculate approximate real-world dimensions from the contour."""
        if det.contour is not None and len(det.contour) >= 5:
            # Fit a rotated rectangle
            rect = cv2.minAreaRect(det.contour)
            (cx, cy), (w_px, h_px), angle = rect

            # Convert pixels to approximate real-world units
            w_real = w_px * self.scale
            h_real = h_px * self.scale
            det.dimensions = (round(w_real, 2), round(h_real, 2))
        else:
            x1, y1, x2, y2 = det.bbox
            det.dimensions = (
                round((x2 - x1) * self.scale, 2),
                round((y2 - y1) * self.scale, 2),
            )

    def _classify_severity(self, max_depth: float) -> str:
        """Classify pothole severity based on relative depth."""
        if max_depth < config.SEVERITY_SHALLOW_MAX:
            return "SHALLOW"
        elif max_depth < config.SEVERITY_MODERATE_MAX:
            return "MODERATE"
        else:
            return "CRITICAL"

    @staticmethod
    def get_severity_color(severity: str) -> Tuple[int, int, int]:
        """Get BGR color for a severity level."""
        colors = {
            "SHALLOW": config.COLOR_SHALLOW,
            "MODERATE": config.COLOR_MODERATE,
            "CRITICAL": config.COLOR_CRITICAL,
            "UNKNOWN": (128, 128, 128),
        }
        return colors.get(severity, (128, 128, 128))

    @staticmethod
    def get_depth_profile(
        det: Detection, depth_map: np.ndarray, num_points: int = 100
    ) -> Optional[np.ndarray]:
        """
        Extract a depth cross-section through the center of the pothole.
        
        Returns an array of depth values along the horizontal centerline.
        """
        if det.mask is None or depth_map is None:
            return None

        x1, y1, x2, y2 = det.bbox
        center_y = (y1 + y2) // 2

        # Clamp to frame bounds
        center_y = max(0, min(center_y, depth_map.shape[0] - 1))
        x1 = max(0, x1)
        x2 = min(x2, depth_map.shape[1])

        if x2 <= x1:
            return None

        # Extract the depth profile along the center line
        profile = depth_map[center_y, x1:x2].copy()

        # Get reference depth from edges
        edge_len = max(1, len(profile) // 10)
        ref_depth = np.mean(np.concatenate([profile[:edge_len], profile[-edge_len:]]))

        # Make relative to reference
        profile = np.abs(profile - ref_depth)

        # Resample to fixed number of points
        if len(profile) > 1:
            x_orig = np.linspace(0, 1, len(profile))
            x_new = np.linspace(0, 1, num_points)
            profile = np.interp(x_new, x_orig, profile)

        return profile
