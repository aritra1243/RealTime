# =============================================================================
# PotholeVision — Configuration
# =============================================================================
# All tunable parameters for the real-time pothole detection pipeline.

import os

# ─── Paths ───────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
MODELS_DIR = os.path.join(BASE_DIR, "models")

# ─── Camera / Input ──────────────────────────────────────────────────────────
CAMERA_INDEX = 0                # Default webcam
FRAME_WIDTH = 1280              # Capture width
FRAME_HEIGHT = 720              # Capture height
FPS_TARGET = 30                 # Target FPS

# ─── YOLOv8 Detection ───────────────────────────────────────────────────────
YOLO_MODEL_NAME = "yolov8n-seg.pt"       # Nano-seg for speed
YOLO_MODEL_PATH = os.path.join(MODELS_DIR, YOLO_MODEL_NAME)
YOLO_CONFIDENCE_THRESHOLD = 0.35
YOLO_IOU_THRESHOLD = 0.45
YOLO_IMG_SIZE = 640

# Classes from COCO that could represent road-surface damage / obstacles
# We'll detect all objects and then filter to those at road-level
ROAD_LEVEL_CLASSES = []  # Empty = detect all; will be useful with custom model

# ─── MiDaS Depth Estimation ─────────────────────────────────────────────────
MIDAS_MODEL_TYPE = "MiDaS_small"         # Options: "DPT_Large", "DPT_Hybrid", "MiDaS_small"
DEPTH_COLORMAP = 2                        # cv2.COLORMAP_MAGMA = 2

# ─── Pothole Analysis ───────────────────────────────────────────────────────
# Severity thresholds (relative depth units — not cm unless calibrated)
SEVERITY_SHALLOW_MAX = 0.15              # 0–15% of depth range
SEVERITY_MODERATE_MAX = 0.35             # 15–35% of depth range
# Anything above SEVERITY_MODERATE_MAX is CRITICAL

# Minimum contour area (pixels) to consider as a valid pothole
MIN_POTHOLE_AREA = 500

# Reference plane margin: how many pixels around the mask to sample for
# the road surface reference depth
REFERENCE_MARGIN_PX = 30

# ─── Camera Calibration (approximate for a standard webcam) ──────────────
# These are rough defaults; override via calibration.py for accuracy
FOCAL_LENGTH_PX = 800.0                  # Approximate focal length in pixels
SENSOR_WIDTH_MM = 4.8                    # Typical phone/webcam sensor width
REAL_WORLD_SCALE = 0.01                  # Approximate m/pixel at 1m distance

# ─── Visualization — Colors (BGR for OpenCV) ────────────────────────────────
COLOR_SHALLOW = (0, 200, 0)              # Green
COLOR_MODERATE = (0, 180, 255)           # Orange
COLOR_CRITICAL = (0, 0, 255)             # Red
COLOR_MASK_ALPHA = 0.4                   # Mask overlay transparency
COLOR_BLUEPRINT_BG = (30, 30, 30)        # Dark background for blueprint
COLOR_HEATMAP_ALPHA = 0.6               # Heatmap overlay transparency
COLOR_TEXT = (255, 255, 255)             # White text
COLOR_PANEL_BG = (20, 20, 20)           # HUD panel background
COLOR_ACCENT = (0, 220, 255)            # Cyan accent

# ─── Visualization — Layout ─────────────────────────────────────────────────
BLUEPRINT_PANEL_WIDTH = 400              # Width of the side blueprint panel
BLUEPRINT_PANEL_HEIGHT = 720             # Height matches camera frame
HUD_FONT_SCALE = 0.6
HUD_THICKNESS = 1
STATS_BAR_HEIGHT = 40                    # Bottom stats bar height

# ─── Blueprint Rendering ────────────────────────────────────────────────────
BLUEPRINT_TOP_VIEW_HEIGHT = 250          # Height of top-down view section
BLUEPRINT_CROSS_SECTION_HEIGHT = 200     # Height of cross-section section
BLUEPRINT_HEATMAP_HEIGHT = 200           # Height of depth heatmap section
BLUEPRINT_PADDING = 15                   # Padding inside blueprint panel
BLUEPRINT_GRID_COLOR = (60, 60, 60)      # Grid line color
BLUEPRINT_CONTOUR_COLOR = (0, 255, 255)  # Cyan contour
CROSS_SECTION_LINE_COLOR = (0, 200, 255) # Orange line for cross-section

# ─── Performance ─────────────────────────────────────────────────────────────
SKIP_DEPTH_FRAMES = 2                    # Run depth estimation every N frames
SKIP_DETECTION_FRAMES = 1               # Run detection every N frames
MAX_DETECTIONS = 5                       # Max potholes to analyze per frame
