# =============================================================================
# PotholeVision — Blueprint Renderer
# =============================================================================
# Renders a technical blueprint side panel showing:
# 1. Top-down contour view with dimensions
# 2. Cross-section depth profile
# 3. Depth heatmap of the pothole
# 4. Numerical dimensional analysis

import cv2
import numpy as np
from typing import List, Optional, Tuple

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from detection.detector import Detection
from analysis.pothole_analyzer import PotholeAnalyzer


class BlueprintRenderer:
    """
    Renders a technical blueprint panel showing detailed analysis
    of the currently selected pothole.
    
    The panel contains three primary engineering sections:
    1. Top-down view — Pothole contour with dimension annotations
    2. Cross-section  — Depth profile along the centerline
    3. Depth heatmap  — Color-coded depth within the pothole
    """

    def __init__(self):
        self.panel_width = config.BLUEPRINT_PANEL_WIDTH
        self.panel_height = config.BLUEPRINT_PANEL_HEIGHT
        self.padding = config.BLUEPRINT_PADDING
        self.selected_index = 0  # Index of the selected pothole

    def render(
        self,
        detections: List[Detection],
        depth_map: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """
        Render the complete blueprint panel.
        
        Args:
            detections: List of analyzed Detection objects.
            depth_map: Normalized depth map [0, 1] (optional).
            
        Returns:
            Blueprint panel image (panel_height x panel_width x 3) BGR.
        """
        panel = np.full(
            (self.panel_height, self.panel_width, 3),
            config.COLOR_BLUEPRINT_BG,
            dtype=np.uint8,
        )

        # Draw panel border
        cv2.rectangle(panel, (0, 0), (self.panel_width - 1, self.panel_height - 1),
                       (60, 60, 60), 1)

        # Title
        self._draw_section_title(panel, "BLUEPRINT ANALYSIS", 6, accent=True)

        if not detections:
            # No detections — show "scanning" message
            self._draw_no_detection(panel)
            return panel

        # Select the pothole to display
        idx = min(self.selected_index, len(detections) - 1)
        det = detections[idx]

        # Info header
        self._draw_info_header(panel, det, idx, len(detections))

        # Dynamic layout heights
        # Total height = 720
        # Header: y=0..85
        # 3 main sections: each ~160px
        # Stats footer: ~95px
        section_h = 135

        # Section 1: Top-down contour view
        y_offset = 80
        self._draw_section_title(panel, "TOP-DOWN VIEW", y_offset)
        y_offset += 22
        self._draw_top_view(panel, det, y_offset, section_h)

        # Section 2: Cross-section
        y_offset += section_h + 10
        self._draw_section_title(panel, "CROSS-SECTION PROFILE", y_offset)
        y_offset += 22
        self._draw_cross_section(panel, det, depth_map, y_offset, section_h)

        # Section 3: Depth heatmap
        y_offset += section_h + 10
        self._draw_section_title(panel, "DEPTH HEATMAP", y_offset)
        y_offset += 22
        self._draw_depth_heatmap(panel, det, depth_map, y_offset, section_h)

        # Stats footer
        y_offset += section_h + 10
        self._draw_stats_footer(panel, det, y_offset)

        return panel

    def _draw_section_title(
        self, panel: np.ndarray, title: str, y: int, accent: bool = False
    ):
        """Draw a section title with an underline."""
        color = config.COLOR_ACCENT if accent else (180, 180, 180)
        font_scale = 0.52 if accent else 0.42
        thickness = 2 if accent else 1

        cv2.putText(
            panel, title, (self.padding, y + 14),
            cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness, cv2.LINE_AA,
        )

        # Underline
        line_y = y + 18
        cv2.line(
            panel, (self.padding, line_y),
            (self.panel_width - self.padding, line_y),
            (50, 50, 50), 1,
        )

    def _draw_info_header(
        self, panel: np.ndarray, det: Detection, idx: int, total: int
    ):
        """Draw detection info header."""
        y = 42
        color = PotholeAnalyzer.get_severity_color(det.severity)
        font = cv2.FONT_HERSHEY_SIMPLEX

        # Severity badge
        badge_text = f" {det.severity} "
        (tw, th), _ = cv2.getTextSize(badge_text, font, 0.45, 1)
        cv2.rectangle(panel, (self.padding, y - th - 3),
                       (self.padding + tw + 6, y + 3), color, -1)
        cv2.putText(panel, badge_text, (self.padding + 3, y),
                     font, 0.45, (0, 0, 0), 1, cv2.LINE_AA)

        # Detection info
        info = f"Target #{idx + 1}/{total} | Conf: {det.confidence:.0%}"
        cv2.putText(panel, info, (self.padding + tw + 14, y),
                     font, 0.38, (150, 150, 150), 1, cv2.LINE_AA)

        # Dimensions
        y += 20
        dim_text = f"Approx Size: {det.dimensions[0]:.2f}m W x {det.dimensions[1]:.2f}m L"
        cv2.putText(panel, dim_text, (self.padding, y),
                     font, 0.36, config.COLOR_TEXT, 1, cv2.LINE_AA)

    def _draw_top_view(
        self, panel: np.ndarray, det: Detection, y_start: int, height: int
    ):
        """Draw the top-down contour view of the pothole."""
        p = self.padding
        view_w = self.panel_width - 2 * p
        view_h = height

        # Background with grid
        self._draw_grid(panel, p, y_start, view_w, view_h)

        if det.contour is None or len(det.contour) < 3:
            cv2.putText(panel, "No contour data", (p + 20, y_start + view_h // 2),
                         cv2.FONT_HERSHEY_SIMPLEX, 0.4, (100, 100, 100), 1)
            return

        # Normalize contour to fit in the view
        contour = det.contour.copy().reshape(-1, 2).astype(np.float32)
        cx, cy = contour.mean(axis=0)
        contour -= [cx, cy]

        # Scale to fit
        extent = contour.max(axis=0) - contour.min(axis=0)
        max_extent = max(extent[0], extent[1])
        if max_extent > 0:
            scale = min(view_w, view_h) * 0.72 / max_extent
        else:
            scale = 1.0
        contour *= scale

        # Center in view
        contour[:, 0] += p + view_w // 2
        contour[:, 1] += y_start + view_h // 2
        contour = contour.astype(np.int32).reshape(-1, 1, 2)

        # Draw filled contour with transparency
        overlay = panel.copy()
        cv2.fillPoly(overlay, [contour], (40, 80, 40))
        cv2.addWeighted(overlay, 0.35, panel, 0.65, 0, panel)

        # Draw contour outline
        cv2.drawContours(panel, [contour], -1, config.BLUEPRINT_CONTOUR_COLOR, 2)

        # Draw center crosshair
        center_x = p + view_w // 2
        center_y = y_start + view_h // 2
        ch_size = 7
        cv2.line(panel, (center_x - ch_size, center_y),
                 (center_x + ch_size, center_y), (120, 120, 120), 1)
        cv2.line(panel, (center_x, center_y - ch_size),
                 (center_x, center_y + ch_size), (120, 120, 120), 1)

        # Dimension annotations
        dim_text_w = f"W: {det.dimensions[0]:.2f}m"
        dim_text_h = f"L: {det.dimensions[1]:.2f}m"
        cv2.putText(panel, dim_text_w, (p + view_w // 2 - 25, y_start + view_h - 6),
                     cv2.FONT_HERSHEY_SIMPLEX, 0.34, config.COLOR_ACCENT, 1, cv2.LINE_AA)
        cv2.putText(panel, dim_text_h, (p + 4, y_start + view_h // 2),
                     cv2.FONT_HERSHEY_SIMPLEX, 0.34, config.COLOR_ACCENT, 1, cv2.LINE_AA)

    def _draw_cross_section(
        self,
        panel: np.ndarray,
        det: Detection,
        depth_map: Optional[np.ndarray],
        y_start: int,
        height: int,
    ):
        """Draw the cross-section depth profile."""
        p = self.padding
        view_w = self.panel_width - 2 * p
        view_h = height

        # Background with grid
        self._draw_grid(panel, p, y_start, view_w, view_h)

        profile = PotholeAnalyzer.get_depth_profile(det, depth_map, num_points=view_w)

        if profile is None or len(profile) == 0:
            cv2.putText(panel, "Depth profile unavailable", (p + 20, y_start + view_h // 2),
                         cv2.FONT_HERSHEY_SIMPLEX, 0.38, (100, 100, 100), 1)
            return

        profile_max = profile.max()
        if profile_max > 0:
            profile_norm = profile / profile_max
        else:
            profile_norm = profile

        # Draw the road surface line (flat line at top)
        road_y = y_start + 14
        cv2.line(panel, (p, road_y), (p + view_w, road_y),
                 (120, 120, 120), 1, cv2.LINE_AA)
        cv2.putText(panel, "Road Surface", (p + 5, road_y - 3),
                     cv2.FONT_HERSHEY_SIMPLEX, 0.28, (120, 120, 120), 1)

        # Draw the depth profile as a filled area
        usable_h = view_h - 26
        points = []
        for i, d in enumerate(profile_norm):
            x = p + i
            y = road_y + int(d * usable_h)
            points.append([x, y])

        if len(points) > 1:
            pts = np.array(points, dtype=np.int32)
            fill_pts = np.vstack([
                [[p, road_y]],
                pts.reshape(-1, 1, 2).reshape(-1, 2),
                [[p + view_w - 1, road_y]],
            ]).reshape(-1, 1, 2).astype(np.int32)

            overlay = panel.copy()
            cv2.fillPoly(overlay, [fill_pts], (30, 60, 120))
            cv2.addWeighted(overlay, 0.45, panel, 0.55, 0, panel)

            cv2.polylines(panel, [pts.reshape(-1, 1, 2)], False,
                           config.CROSS_SECTION_LINE_COLOR, 2, cv2.LINE_AA)

        # Max depth marker
        max_idx = int(np.argmax(profile_norm))
        max_x = p + max_idx
        max_y = road_y + int(profile_norm[max_idx] * usable_h)
        cv2.circle(panel, (max_x, max_y), 4, config.COLOR_CRITICAL, -1)
        cv2.putText(panel, f"Max: {det.max_depth:.3f}", (max_x + 6, max_y + 3),
                     cv2.FONT_HERSHEY_SIMPLEX, 0.30, config.COLOR_CRITICAL, 1)

    def _draw_depth_heatmap(
        self,
        panel: np.ndarray,
        det: Detection,
        depth_map: Optional[np.ndarray],
        y_start: int,
        height: int,
    ):
        """Draw a depth heatmap of the pothole region."""
        p = self.padding
        view_w = self.panel_width - 2 * p
        view_h = height

        if det.mask is None or depth_map is None:
            self._draw_grid(panel, p, y_start, view_w, view_h)
            cv2.putText(panel, "No depth data", (p + 20, y_start + view_h // 2),
                         cv2.FONT_HERSHEY_SIMPLEX, 0.38, (100, 100, 100), 1)
            return

        # Extract the pothole region from depth map
        x1, y1, x2, y2 = det.bbox
        x1 = max(0, min(x1, depth_map.shape[1] - 1))
        x2 = max(x1 + 1, min(x2, depth_map.shape[1]))
        y1 = max(0, min(y1, depth_map.shape[0] - 1))
        y2 = max(y1 + 1, min(y2, depth_map.shape[0]))

        region = depth_map[y1:y2, x1:x2].copy()
        mask_region = det.mask[y1:y2, x1:x2]

        if region.size == 0 or mask_region.size == 0:
            return

        # Apply mask
        region[mask_region == 0] = 0

        # Safe resize
        region_resized = cv2.resize(region, (view_w, view_h), interpolation=cv2.INTER_LINEAR)
        mask_resized = cv2.resize(mask_region, (view_w, view_h), interpolation=cv2.INTER_NEAREST)

        # Apply colormap
        region_uint8 = (region_resized * 255).astype(np.uint8)
        heatmap = cv2.applyColorMap(region_uint8, cv2.COLORMAP_INFERNO)

        # Black out non-pothole background
        heatmap[mask_resized == 0] = config.COLOR_BLUEPRINT_BG
        cv2.rectangle(heatmap, (0, 0), (view_w - 1, view_h - 1), (60, 60, 60), 1)

        # Safe placement within bounds
        y_end = min(self.panel_height, y_start + view_h)
        h_actual = y_end - y_start
        panel[y_start:y_end, p:p + view_w] = heatmap[:h_actual, :]

        # Color bar legend
        bar_w = 12
        bar_x = p + view_w - bar_w - 5
        for i in range(min(h_actual, view_h)):
            val = int(255 * i / max(1, view_h))
            color_pixel = cv2.applyColorMap(
                np.array([[val]], dtype=np.uint8), cv2.COLORMAP_INFERNO
            )[0, 0].tolist()
            cv2.line(panel, (bar_x, y_start + i), (bar_x + bar_w, y_start + i),
                      color_pixel, 1)

        cv2.putText(panel, "Deep", (bar_x - 6, y_start + h_actual - 4),
                     cv2.FONT_HERSHEY_SIMPLEX, 0.24, config.COLOR_TEXT, 1)
        cv2.putText(panel, "Flat", (bar_x - 6, y_start + 10),
                     cv2.FONT_HERSHEY_SIMPLEX, 0.24, config.COLOR_TEXT, 1)

    def _draw_stats_footer(
        self, panel: np.ndarray, det: Detection, y_start: int
    ):
        """Draw the stats footer with numerical values."""
        font = cv2.FONT_HERSHEY_SIMPLEX
        p = self.padding
        y = y_start

        stats = [
            ("Max Depth", f"{det.max_depth:.4f} rel units"),
            ("Avg Depth", f"{det.avg_depth:.4f} rel units"),
            ("Surface Area", f"{det.area_px:,} px"),
            ("Est. Volume", f"{det.volume:.1f} vol units"),
            ("Dimensions", f"{det.dimensions[0]:.2f}m x {det.dimensions[1]:.2f}m"),
        ]

        for label, value in stats:
            if y + 16 >= self.panel_height:
                break
            cv2.putText(panel, f"{label}:", (p, y + 13),
                         font, 0.34, (130, 130, 130), 1, cv2.LINE_AA)
            cv2.putText(panel, value, (p + 105, y + 13),
                         font, 0.34, config.COLOR_ACCENT, 1, cv2.LINE_AA)
            y += 16

    def _draw_grid(
        self, panel: np.ndarray, x: int, y: int, w: int, h: int
    ):
        """Draw a technical grid background."""
        cv2.rectangle(panel, (x, y), (x + w, y + h), (50, 50, 50), 1)
        grid_spacing = 25
        for gx in range(x + grid_spacing, x + w, grid_spacing):
            cv2.line(panel, (gx, y), (gx, y + h), config.BLUEPRINT_GRID_COLOR, 1)
        for gy in range(y + grid_spacing, y + h, grid_spacing):
            cv2.line(panel, (x, gy), (x + w, gy), config.BLUEPRINT_GRID_COLOR, 1)

    def _draw_no_detection(self, panel: np.ndarray):
        """Draw the 'scanning' message when no potholes are detected."""
        center_x = self.panel_width // 2
        center_y = self.panel_height // 2

        cv2.circle(panel, (center_x, center_y - 20), 40, (50, 50, 50), 2)
        cv2.circle(panel, (center_x, center_y - 20), 30, (40, 40, 40), 1)

        cv2.line(panel, (center_x - 50, center_y - 20),
                 (center_x + 50, center_y - 20), (50, 50, 50), 1)
        cv2.line(panel, (center_x, center_y - 70),
                 (center_x, center_y + 30), (50, 50, 50), 1)

        cv2.putText(panel, "SCANNING ROAD...", (center_x - 65, center_y + 55),
                     cv2.FONT_HERSHEY_SIMPLEX, 0.48, (100, 100, 100), 1, cv2.LINE_AA)
        cv2.putText(panel, "Ready for real-time feed", (center_x - 78, center_y + 80),
                     cv2.FONT_HERSHEY_SIMPLEX, 0.36, (70, 70, 70), 1, cv2.LINE_AA)

    def select_next(self, total: int):
        """Select the next pothole."""
        self.selected_index = (self.selected_index + 1) % max(1, total)

    def select_prev(self, total: int):
        """Select the previous pothole."""
        self.selected_index = (self.selected_index - 1) % max(1, total)
