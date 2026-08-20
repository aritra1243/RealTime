# =============================================================================
# PotholeVision — Session & Defect Logger
# =============================================================================
# Records all detected road defects, severity ratings, depths, and volumes
# into structured CSV and JSON audit reports.

import os
import csv
import json
import time
from datetime import datetime
from typing import List, Optional
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from detection.detector import Detection


class DefectLogger:
    """
    Logs detected potholes during a live camera or video session.
    """

    def __init__(self, log_dir: Optional[str] = None):
        self.log_dir = log_dir or os.path.join(config.BASE_DIR, "output", "logs")
        os.makedirs(self.log_dir, exist_ok=True)
        
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.csv_path = os.path.join(self.log_dir, f"pothole_session_{session_id}.csv")
        self.json_path = os.path.join(self.log_dir, f"pothole_session_{session_id}.json")
        self.records = []

        # Initialize CSV header
        with open(self.csv_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Timestamp",
                "Frame_ID",
                "Pothole_ID",
                "Severity",
                "Confidence",
                "Max_Depth_Rel",
                "Avg_Depth_Rel",
                "Surface_Area_px",
                "Est_Volume",
                "Width_m",
                "Length_m",
                "BBox_X1",
                "BBox_Y1",
                "BBox_X2",
                "BBox_Y2"
            ])

    def log_frame_detections(self, frame_id: int, detections: List[Detection]):
        """Log all detections found in a single frame."""
        if not detections:
            return

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

        with open(self.csv_path, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            for idx, det in enumerate(detections):
                x1, y1, x2, y2 = det.bbox
                record = {
                    "timestamp": now_str,
                    "frame_id": frame_id,
                    "pothole_id": idx + 1,
                    "severity": det.severity,
                    "confidence": round(det.confidence, 4),
                    "max_depth": round(det.max_depth, 4),
                    "avg_depth": round(det.avg_depth, 4),
                    "area_px": det.area_px,
                    "volume": round(det.volume, 2),
                    "width_m": det.dimensions[0],
                    "length_m": det.dimensions[1],
                    "bbox": [x1, y1, x2, y2]
                }
                self.records.append(record)

                writer.writerow([
                    now_str,
                    frame_id,
                    idx + 1,
                    det.severity,
                    f"{det.confidence:.2%}",
                    f"{det.max_depth:.4f}",
                    f"{det.avg_depth:.4f}",
                    det.area_px,
                    f"{det.volume:.1f}",
                    det.dimensions[0],
                    det.dimensions[1],
                    x1, y1, x2, y2
                ])

    def save_summary_json(self):
        """Export session JSON summary."""
        summary = {
            "total_defects_logged": len(self.records),
            "generated_at": datetime.now().isoformat(),
            "csv_log": self.csv_path,
            "records": self.records
        }
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        print(f"[Logger] Exported session report: {self.csv_path}")
