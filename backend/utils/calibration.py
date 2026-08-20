# =============================================================================
# PotholeVision — Camera Calibration Utilities
# =============================================================================

import cv2
import numpy as np
from typing import Tuple, Optional

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class CameraCalibration:
    """
    Camera calibration utilities for pixel-to-real-world conversion.
    
    Provides approximate spatial measurements using estimated camera parameters.
    For precise measurements, perform a full calibration with a checkerboard.
    """

    def __init__(
        self,
        focal_length_px: float = None,
        sensor_width_mm: float = None,
        frame_width: int = None,
        frame_height: int = None,
    ):
        self.focal_length = focal_length_px or config.FOCAL_LENGTH_PX
        self.sensor_width = sensor_width_mm or config.SENSOR_WIDTH_MM
        self.frame_width = frame_width or config.FRAME_WIDTH
        self.frame_height = frame_height or config.FRAME_HEIGHT

        # Intrinsic matrix (approximate)
        cx = self.frame_width / 2
        cy = self.frame_height / 2
        self.K = np.array([
            [self.focal_length, 0, cx],
            [0, self.focal_length, cy],
            [0, 0, 1]
        ], dtype=np.float64)

    def pixel_to_meters(self, pixel_size: float, distance_m: float = 1.0) -> float:
        """
        Convert pixel size to approximate real-world size in meters.
        
        Args:
            pixel_size: Size in pixels
            distance_m: Estimated distance from camera to object in meters
            
        Returns:
            Approximate size in meters
        """
        return (pixel_size * distance_m) / self.focal_length

    def estimate_road_distance(self, y_pixel: int, camera_height_m: float = 1.5) -> float:
        """
        Estimate distance to a point on the road based on its y-position.
        
        Assumes camera is mounted at a known height looking forward.
        Points lower in the image (higher y) are closer.
        
        Args:
            y_pixel: Y coordinate in the image
            camera_height_m: Height of camera above the road (meters)
            
        Returns:
            Approximate distance in meters
        """
        cy = self.frame_height / 2
        # Pixels below center represent closer objects
        delta_y = y_pixel - cy
        if delta_y <= 0:
            return float('inf')  # Above horizon

        angle = np.arctan2(delta_y, self.focal_length)
        distance = camera_height_m / np.tan(angle)
        return max(0.5, distance)

    def fit_reference_plane(
        self, depth_map: np.ndarray, mask: np.ndarray, margin: int = 30
    ) -> float:
        """
        Fit a reference plane to the road surface around a pothole.
        
        Returns the median depth of the road surface surrounding the mask.
        """
        kernel = np.ones((margin, margin), np.uint8)
        dilated = cv2.dilate(mask, kernel, iterations=1)
        ring = dilated - mask
        ring = np.clip(ring, 0, 1).astype(np.uint8)

        ref_depths = depth_map[ring > 0]
        if len(ref_depths) == 0:
            return float(np.median(depth_map))

        return float(np.median(ref_depths))

    @staticmethod
    def calibrate_from_checkerboard(
        images: list,
        board_size: Tuple[int, int] = (9, 6),
        square_size_mm: float = 25.0,
    ) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """
        Perform full camera calibration using checkerboard images.
        
        Args:
            images: List of BGR images containing checkerboard views
            board_size: (columns, rows) of inner corners
            square_size_mm: Size of each square in mm
            
        Returns:
            (camera_matrix, dist_coeffs) or None if calibration fails
        """
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

        # Prepare object points
        objp = np.zeros((board_size[0] * board_size[1], 3), np.float32)
        objp[:, :2] = np.mgrid[0:board_size[0], 0:board_size[1]].T.reshape(-1, 2)
        objp *= square_size_mm

        obj_points = []
        img_points = []

        for img in images:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            ret, corners = cv2.findChessboardCorners(gray, board_size, None)
            if ret:
                obj_points.append(objp)
                corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
                img_points.append(corners2)

        if len(obj_points) < 3:
            print("[Calibration] Not enough valid images (need at least 3)")
            return None

        h, w = images[0].shape[:2]
        ret, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(
            obj_points, img_points, (w, h), None, None
        )

        if ret:
            print(f"[Calibration] Success! RMS error: {ret:.4f}")
            return camera_matrix, dist_coeffs
        else:
            print("[Calibration] Failed.")
            return None
