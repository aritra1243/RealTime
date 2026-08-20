# =============================================================================
# PotholeVision — Pothole Detector (YOLOv8 + Hybrid Computer Vision)
# =============================================================================

import cv2
import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

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
    1. YOLOv8 Segmentation
    2. Adaptive Computer Vision Pothole & Road Defect Segmentation
    """

    def __init__(self, model_path: Optional[str] = None):
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
        self.model = None

        try:
            from ultralytics import YOLO
            print(f"[Detector] Loading YOLOv8 model: {self.model_path}")
            self.model = YOLO(self.model_path)
            print(f"[Detector] Model loaded successfully. (Custom Weights: {self.is_custom_model})")
        except Exception as e:
            print(f"[Detector] YOLOv8 model load notice ({e}). Using Computer Vision Pothole & Defect Engine.")
            self.model = None

    def detect(self, frame: np.ndarray, enable_cv_fallback: bool = True) -> List[Detection]:
        h, w = frame.shape[:2]
        detections = []

        # 1. Run YOLOv8 inference if model is loaded
        if self.model is not None:
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
        h, w = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        blurred = cv2.GaussianBlur(gray, (7, 7), 0)
        mean_val, std_val = cv2.meanStdDev(blurred)
        mean_val = float(mean_val[0][0])
        std_val = float(std_val[0][0])

        thresh_val = max(15, int(mean_val - 1.05 * std_val))
        _, thresh = cv2.threshold(blurred, thresh_val, 255, cv2.THRESH_BINARY_INV)

        kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))
        kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel_close)
        cleaned = cv2.morphologyEx(closed, cv2.MORPH_OPEN, kernel_open)

        contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        detections = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < config.MIN_POTHOLE_AREA:
                continue

            x, y, bw, bh = cv2.boundingRect(cnt)

            if bw >= w * 0.92 or bh >= h * 0.92:
                continue

            aspect_ratio = float(bw) / max(1, bh)
            if aspect_ratio < 0.15 or aspect_ratio > 6.0:
                continue

            mask = np.zeros((h, w), dtype=np.uint8)
            cv2.drawContours(mask, [cnt], -1, 1, -1)

            hull = cv2.convexHull(cnt)
            hull_area = cv2.contourArea(hull)
            solidity = float(area) / max(1, hull_area)
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
