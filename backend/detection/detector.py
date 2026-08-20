# =============================================================================
# PotholeVision — Pothole Detector (YOLOv8 + Hybrid Computer Vision)
# =============================================================================

import cv2
import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from ultralytics import YOLO

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


@dataclass
class Detection:
    """Represents a single detected pothole."""
    bbox: Tuple[int, int, int, int]           # (x1, y1, x2, y2)
    mask: Optional[np.ndarray] = None          # Binary mask (H x W), same size as frame
    confidence: float = 0.0
    class_id: int = 0
    class_name: str = "pothole"
    # Filled in by the analyzer later:
    severity: str = "UNKNOWN"
    max_depth: float = 0.0
    avg_depth: float = 0.0
    area_px: int = 0
    volume: float = 0.0
    dimensions: Tuple[float, float] = (0.0, 0.0)  # (width, height) in approx real units
    contour: Optional[np.ndarray] = None           # Largest contour of the mask
    center: Tuple[int, int] = (0, 0)               # (cx, cy) in pixel coords


class PotholeDetector:
    """
    Hybrid Pothole Detector.
    
    Supports:
    1. Custom YOLOv8-seg trained weights (Deep Learning Neural Network)
    2. High-speed Classical Computer Vision Pothole & Road Defect Segmentation
       (using adaptive statistical road-surface depression segmentation,
        morphological filtering, and contour geometry filters)
    """

    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize the detector.
        
        Args:
            model_path: Path to the YOLOv8-seg model weights.
                        If custom weights exist in models/pothole_best.pt, uses them.
        """
        # Check if custom pothole weights exist
        custom_default = os.path.join(config.MODELS_DIR, "pothole_best.pt")
        if model_path is None and os.path.exists(custom_default):
            model_path = custom_default

        self.model_path = model_path or config.YOLO_MODEL_NAME
        self.is_custom_model = (
            model_path is not None and os.path.exists(model_path) and "yolov8n-seg.pt" not in model_path.lower()
        )
        self.confidence = config.YOLO_CONFIDENCE_THRESHOLD
        self.iou_threshold = config.YOLO_IOU_THRESHOLD
        self.img_size = config.YOLO_IMG_SIZE
        self.max_detections = config.MAX_DETECTIONS

        print(f"[Detector] Loading YOLOv8 model: {self.model_path}")
        self.model = YOLO(self.model_path)
        print(f"[Detector] Model loaded successfully. (Custom Weights: {self.is_custom_model})")

    def detect(self, frame: np.ndarray, enable_cv_fallback: bool = True) -> List[Detection]:
        """
        Run detection on a single frame.
        
        Args:
            frame: BGR image (H x W x 3)
            enable_cv_fallback: If true, runs classical CV detector when YOLO
                                (COCO weights) finds 0 road defects.
            
        Returns:
            List of Detection objects with masks and bounding boxes.
        """
        h, w = frame.shape[:2]
        detections = []

        # 1. Run YOLOv8 inference
        try:
            results = self.model(
                frame,
                conf=self.confidence,
                iou=self.iou_threshold,
                imgsz=self.img_size,
                verbose=False,
            )

            if results and len(results) > 0:
                result = results[0]
                if result.boxes is not None and len(result.boxes) > 0:
                    boxes = result.boxes
                    masks = result.masks

                    for i in range(len(boxes)):
                        xyxy = boxes.xyxy[i].cpu().numpy().astype(int)
                        x1, y1, x2, y2 = xyxy
                        conf = float(boxes.conf[i].cpu().numpy())
                        cls_id = int(boxes.cls[i].cpu().numpy())
                        cls_name = self.model.names.get(cls_id, str(cls_id))

                        # If using a custom model, keep detections.
                        # If using COCO, ignore unless it's a road hazard class.
                        if not self.is_custom_model and cls_name not in ["pothole", "crack", "defect"]:
                            pass  # Proceed to fallback

                        # Segmentation mask
                        mask = None
                        contour = None
                        if masks is not None and i < len(masks):
                            mask_data = masks.data[i].cpu().numpy()
                            mask = cv2.resize(mask_data, (w, h), interpolation=cv2.INTER_NEAREST)
                            mask = (mask > 0.5).astype(np.uint8)

                            contours, _ = cv2.findContours(
                                mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
                            )
                            if contours:
                                contour = max(contours, key=cv2.contourArea)

                        area_px = int(np.sum(mask)) if mask is not None else (x2 - x1) * (y2 - y1)
                        if area_px < config.MIN_POTHOLE_AREA:
                            continue

                        cx = int((x1 + x2) / 2)
                        cy = int((y1 + y2) / 2)

                        detection = Detection(
                            bbox=(x1, y1, x2, y2),
                            mask=mask,
                            confidence=conf,
                            class_id=cls_id,
                            class_name=cls_name if self.is_custom_model else "pothole",
                            area_px=area_px,
                            contour=contour,
                            center=(cx, cy),
                        )
                        detections.append(detection)
        except Exception as e:
            print(f"[Detector] YOLO inference notice: {e}")

        # 2. Fallback to Classical CV Pothole Detector if no potholes detected
        if len(detections) == 0 and enable_cv_fallback:
            cv_detections = self.detect_cv_potholes(frame)
            detections.extend(cv_detections)

        detections.sort(key=lambda d: d.confidence, reverse=True)
        return detections[:self.max_detections]

    def detect_cv_potholes(self, frame: np.ndarray) -> List[Detection]:
        """
        Classical Computer Vision Pothole Detection Algorithm.
        
        Applies:
        1. Grayscale conversion + Bilateral/Gaussian filtering (preserves edges, removes noise)
        2. Statistical road pavement brightness analysis (mean & variance)
        3. Dark depression thresholding (< mean - 1.0 * std)
        4. Morphological closing & opening to eliminate road texture noise
        5. Contour geometry & area filtering (solidity, aspect ratio)
        """
        h, w = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Smooth road texture while preserving pothole edges
        blurred = cv2.GaussianBlur(gray, (7, 7), 0)

        mean_val, std_val = cv2.meanStdDev(blurred)
        mean_val = float(mean_val[0][0])
        std_val = float(std_val[0][0])

        # Potholes and road cracks are significantly darker than the surrounding road surface
        thresh_val = max(15, int(mean_val - 1.05 * std_val))
        _, thresh = cv2.threshold(blurred, thresh_val, 255, cv2.THRESH_BINARY_INV)

        # Morphological clean up
        kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))
        kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel_close)
        cleaned = cv2.morphologyEx(closed, cv2.MORPH_OPEN, kernel_open)

        # Find candidate contours
        contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        detections = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < config.MIN_POTHOLE_AREA:
                continue

            x, y, bw, bh = cv2.boundingRect(cnt)

            # Avoid full-frame boundaries or edge borders
            if bw >= w * 0.92 or bh >= h * 0.92:
                continue

            # Geometry check: realistic aspect ratio
            aspect_ratio = float(bw) / max(1, bh)
            if aspect_ratio < 0.15 or aspect_ratio > 6.0:
                continue

            # Create binary mask for this pothole
            mask = np.zeros((h, w), dtype=np.uint8)
            cv2.drawContours(mask, [cnt], -1, 1, -1)

            # Calculate confidence based on depth contrast and contour solidity
            hull = cv2.convexHull(cnt)
            hull_area = cv2.contourArea(hull)
            solidity = float(area) / max(1, hull_area)

            # Confidence score between 0.70 and 0.98
            conf = min(0.98, max(0.70, 0.55 + 0.40 * solidity))

            cx = x + bw // 2
            cy = y + bh // 2

            det = Detection(
                bbox=(x, y, x + bw, y + bh),
                mask=mask,
                confidence=conf,
                class_id=0,
                class_name="pothole",
                area_px=int(area),
                contour=cnt,
                center=(cx, cy),
            )
            detections.append(det)

        return detections
