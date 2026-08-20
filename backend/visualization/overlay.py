# =============================================================================
# PotholeVision — Camera Overlay Renderer
# =============================================================================
# Renders detection results, masks, depth heatmaps, HUD elements,
# and Road Hazard Safety Alerts directly onto the live camera feed.

import cv2
import numpy as np
import time
from typing import List, Optional, Tuple

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from detection.detector import Detection
from analysis.pothole_analyzer import PotholeAnalyzer


class Overlay:
    """
    Renders real-time overlays on the camera feed.
    
    Features:
    - Segmentation mask overlay with severity coloring
    - Bounding boxes with corner accents and metrics
    - Depth heatmap overlay on pothole regions
    - Road Hazard Driver Safety Alert HUD (pulsing warning banner)
    - HUD stats bar (FPS, detection count, worst severity)
    - Glassmorphic top banner
    """

    def __init__(self):
        self.show_masks = True
        self.show_boxes = True
        self.show_heatmap = True
        self.show_labels = True
        self.show_alerts = True

        # FPS tracking
        self._frame_times = []
        self._fps = 0.0

    def render(
        self,
        frame: np.ndarray,
        detections: List[Detection],
        depth_map: Optional[np.ndarray] = None,
        depth_colored: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """
        Render all overlays onto the frame.
        
        Args:
            frame: BGR camera frame (H x W x 3)
            detections: List of analyzed Detection objects
            depth_map: Normalized depth map [0, 1] (optional)
            depth_colored: Colored depth visualization (optional)
            
        Returns:
            Annotated frame with all overlays.
        """
        self._update_fps()
        output = frame.copy()

        # 1. Depth heatmap overlay on pothole regions
        if self.show_heatmap and depth_colored is not None:
            output = self._render_depth_heatmap(output, detections, depth_colored)

        # 2. Segmentation masks
        if self.show_masks:
            output = self._render_masks(output, detections)

        # 3. Bounding boxes and labels
        if self.show_boxes:
            output = self._render_boxes(output, detections)

        # 4. Road Hazard Alert (if dangerous pothole in trajectory)
        if self.show_alerts:
            output = self._render_hazard_alert(output, detections)

        # 5. HUD stats bar
        output = self._render_hud(output, detections)

        # 6. Title banner
        output = self._render_title_banner(output)

        return output

    def _render_masks(
        self, frame: np.ndarray, detections: List[Detection]
    ) -> np.ndarray:
        """Overlay colored segmentation masks."""
        overlay = frame.copy()

        for det in detections:
            if det.mask is None:
                continue

            color = PotholeAnalyzer.get_severity_color(det.severity)
            mask_colored = np.zeros_like(frame)
            mask_colored[det.mask > 0] = color

            # Blend mask onto frame
            mask_bool = det.mask > 0
            overlay[mask_bool] = cv2.addWeighted(
                frame[mask_bool], 1 - config.COLOR_MASK_ALPHA,
                mask_colored[mask_bool], config.COLOR_MASK_ALPHA,
                0,
            )

            # Draw contour outline
            if det.contour is not None:
                cv2.drawContours(overlay, [det.contour], -1, color, 2)

        return overlay

    def _render_boxes(
        self, frame: np.ndarray, detections: List[Detection]
    ) -> np.ndarray:
        """Draw bounding boxes with labels."""
        for det in detections:
            x1, y1, x2, y2 = det.bbox
            color = PotholeAnalyzer.get_severity_color(det.severity)

            # Draw box with corner accents
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

            corner_len = min(20, max(5, (x2 - x1) // 4), max(5, (y2 - y1) // 4))
            cv2.line(frame, (x1, y1), (x1 + corner_len, y1), color, 3)
            cv2.line(frame, (x1, y1), (x1, y1 + corner_len), color, 3)
            cv2.line(frame, (x2, y1), (x2 - corner_len, y1), color, 3)
            cv2.line(frame, (x2, y1), (x2, y1 + corner_len), color, 3)
            cv2.line(frame, (x1, y2), (x1 + corner_len, y2), color, 3)
            cv2.line(frame, (x1, y2), (x1, y2 - corner_len), color, 3)
            cv2.line(frame, (x2, y2), (x2 - corner_len, y2), color, 3)
            cv2.line(frame, (x2, y2), (x2, y2 - corner_len), color, 3)

            if self.show_labels:
                label = f"{det.severity} | {det.confidence:.0%}"
                (tw, th), _ = cv2.getTextSize(
                    label, cv2.FONT_HERSHEY_SIMPLEX, 0.48, 1
                )

                label_bg = frame.copy()
                cv2.rectangle(
                    label_bg, (x1, max(0, y1 - th - 8)), (x1 + tw + 8, y1), color, -1
                )
                frame = cv2.addWeighted(frame, 0.25, label_bg, 0.75, 0)

                cv2.putText(
                    frame, label, (x1 + 4, y1 - 4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.48, (255, 255, 255), 1,
                    cv2.LINE_AA,
                )

                if det.max_depth > 0:
                    depth_label = f"Depth: {det.max_depth:.3f} | Vol: {det.volume:.1f}"
                    cv2.putText(
                        frame, depth_label, (x1 + 4, y2 + 16),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.38, config.COLOR_ACCENT, 1,
                        cv2.LINE_AA,
                    )

        return frame

    def _render_hazard_alert(
        self, frame: np.ndarray, detections: List[Detection]
    ) -> np.ndarray:
        """Render pulsing driver safety hazard alert if dangerous pothole is present."""
        if not detections:
            return frame

        # Check if critical or moderate pothole exists
        critical_dets = [d for d in detections if d.severity in ["CRITICAL", "MODERATE"]]
        if not critical_dets:
            return frame

        h, w = frame.shape[:2]
        worst = max(critical_dets, key=lambda d: d.max_depth)

        # Flashing effect
        flash = (int(time.time() * 3) % 2 == 0)
        bg_color = (0, 0, 180) if worst.severity == "CRITICAL" else (0, 140, 220)
        border_color = (0, 0, 255) if flash else (0, 200, 255)

        banner_w = 480
        banner_h = 36
        bx1 = (w - banner_w) // 2
        by1 = 48
        bx2 = bx1 + banner_w
        by2 = by1 + banner_h

        overlay = frame.copy()
        cv2.rectangle(overlay, (bx1, by1), (bx2, by2), bg_color, -1)
        cv2.rectangle(overlay, (bx1, by1), (bx2, by2), border_color, 2)
        frame = cv2.addWeighted(frame, 0.25, overlay, 0.75, 0)

        alert_msg = f"[!] CAUTION: {worst.severity} ROAD DEFECT AHEAD - SLOW DOWN"
        cv2.putText(
            frame, alert_msg, (bx1 + 16, by1 + 24),
            cv2.FONT_HERSHEY_SIMPLEX, 0.48, (255, 255, 255), 2, cv2.LINE_AA
        )

        return frame

    def _render_depth_heatmap(
        self,
        frame: np.ndarray,
        detections: List[Detection],
        depth_colored: np.ndarray,
    ) -> np.ndarray:
        """Overlay depth heatmap only within pothole mask regions."""
        for det in detections:
            if det.mask is None:
                continue

            mask_bool = det.mask > 0
            frame[mask_bool] = cv2.addWeighted(
                frame[mask_bool], 1 - config.COLOR_HEATMAP_ALPHA,
                depth_colored[mask_bool], config.COLOR_HEATMAP_ALPHA,
                0,
            )

        return frame

    def _render_hud(
        self, frame: np.ndarray, detections: List[Detection]
    ) -> np.ndarray:
        """Render the bottom HUD stats bar."""
        h, w = frame.shape[:2]
        bar_h = config.STATS_BAR_HEIGHT

        bar_overlay = frame.copy()
        cv2.rectangle(bar_overlay, (0, h - bar_h), (w, h), config.COLOR_PANEL_BG, -1)
        frame = cv2.addWeighted(frame, 0.4, bar_overlay, 0.6, 0)

        y_text = h - 12
        font = cv2.FONT_HERSHEY_SIMPLEX

        # FPS
        fps_text = f"FPS: {self._fps:.1f}"
        cv2.putText(frame, fps_text, (15, y_text), font, 0.52,
                     config.COLOR_ACCENT, 1, cv2.LINE_AA)

        # Detection count
        count_text = f"Detections: {len(detections)}"
        cv2.putText(frame, count_text, (160, y_text), font, 0.52,
                     config.COLOR_TEXT, 1, cv2.LINE_AA)

        # Worst severity
        if detections:
            severity_order = {"CRITICAL": 3, "MODERATE": 2, "SHALLOW": 1, "UNKNOWN": 0}
            worst = max(detections, key=lambda d: severity_order.get(d.severity, 0))
            worst_color = PotholeAnalyzer.get_severity_color(worst.severity)
            sev_text = f"Worst: {worst.severity}"
            cv2.putText(frame, sev_text, (370, y_text), font, 0.52,
                         worst_color, 2, cv2.LINE_AA)
        else:
            cv2.putText(frame, "Road: CLEAR", (370, y_text), font, 0.52,
                         config.COLOR_SHALLOW, 1, cv2.LINE_AA)

        # Keyboard hints
        hints = "[Q]uit [B]lueprint [H]eatmap [S]creenshot [N/P]Select"
        cv2.putText(frame, hints, (w - 450, y_text), font, 0.38,
                     (140, 140, 140), 1, cv2.LINE_AA)

        return frame

    def _render_title_banner(self, frame: np.ndarray) -> np.ndarray:
        """Render the top title banner."""
        h, w = frame.shape[:2]

        bar_overlay = frame.copy()
        cv2.rectangle(bar_overlay, (0, 0), (w, 38), config.COLOR_PANEL_BG, -1)
        frame = cv2.addWeighted(frame, 0.4, bar_overlay, 0.6, 0)

        # Title
        title = "POTHOLEVISION"
        cv2.putText(frame, title, (15, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.68,
                     config.COLOR_ACCENT, 2, cv2.LINE_AA)

        subtitle = "Real-Time Road Defect & Depth Analysis"
        cv2.putText(frame, subtitle, (200, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.44,
                     (160, 160, 160), 1, cv2.LINE_AA)

        # Status dot
        cv2.circle(frame, (w - 25, 19), 6, (0, 220, 0), -1)

        return frame

    def _update_fps(self):
        """Track and calculate FPS."""
        now = time.time()
        self._frame_times.append(now)
        self._frame_times = self._frame_times[-30:]
        if len(self._frame_times) > 1:
            elapsed = self._frame_times[-1] - self._frame_times[0]
            if elapsed > 0:
                self._fps = (len(self._frame_times) - 1) / elapsed

    def toggle_masks(self):
        self.show_masks = not self.show_masks

    def toggle_boxes(self):
        self.show_boxes = not self.show_boxes

    def toggle_heatmap(self):
        self.show_heatmap = not self.show_heatmap

    def toggle_labels(self):
        self.show_labels = not self.show_labels
