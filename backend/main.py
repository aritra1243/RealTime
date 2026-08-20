# =============================================================================
# PotholeVision — Main Entry Point
# =============================================================================
# Real-time pothole detection, depth analysis, and blueprint overlay.
#
# Usage:
#   python main.py --source 0                 # Webcam
#   python main.py --source video.mp4          # Video file
#   python main.py --source image.jpg          # Single image
#
# Keyboard Controls:
#   q — Quit
#   b — Toggle blueprint panel
#   h — Toggle depth heatmap
#   d — Toggle detection boxes
#   m — Toggle segmentation masks
#   s — Save screenshot
#   e — Export 3D OBJ Blueprint mesh of current pothole
#   n — Select next pothole (in blueprint)
#   p — Select previous pothole (in blueprint)

import argparse
import cv2
import numpy as np
import time
import os
import sys

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from detection.detector import PotholeDetector
from depth.estimator import DepthEstimator
from analysis.pothole_analyzer import PotholeAnalyzer
from visualization.overlay import Overlay
from visualization.blueprint import BlueprintRenderer
from utils.logger import DefectLogger
from utils.mesh_exporter import MeshExporter


def parse_args():
    parser = argparse.ArgumentParser(
        description="PotholeVision — Real-Time Pothole Detection & Depth Analysis"
    )
    parser.add_argument(
        "--source", type=str, default="0",
        help="Input source: camera index (0, 1, ...), video file path, or image path"
    )
    parser.add_argument(
        "--no-depth", action="store_true",
        help="Disable depth estimation (faster, detection only)"
    )
    parser.add_argument(
        "--no-blueprint", action="store_true",
        help="Start with blueprint panel hidden"
    )
    parser.add_argument(
        "--save-dir", type=str, default="output",
        help="Directory to save screenshots and 3D exports"
    )
    parser.add_argument(
        "--model", type=str, default=None,
        help="Path to custom YOLOv8-seg model weights"
    )
    parser.add_argument(
        "--depth-model", type=str, default=None,
        help="MiDaS model type: DPT_Large, DPT_Hybrid, MiDaS_small"
    )
    parser.add_argument(
        "--no-log", action="store_true",
        help="Disable defect CSV/JSON session logging"
    )
    return parser.parse_args()


def is_image_file(path: str) -> bool:
    """Check if the source is an image file."""
    ext = os.path.splitext(path)[1].lower()
    return ext in (".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp")


def main():
    args = parse_args()

    # ===================================================================
    # Banner
    # ===================================================================
    print("=" * 62)
    print("  +-------------------------------------------------------+")
    print("  |         POTHOLEVISION -- Real-Time Analysis           |")
    print("  |   Pothole Detection * Depth Mapping * Blueprint       |")
    print("  +-------------------------------------------------------+")
    print("=" * 62)
    print()

    # ===================================================================
    # Initialize modules
    # ===================================================================
    print("[Main] Initializing modules...")

    # Detection
    detector = PotholeDetector(model_path=args.model)

    # Depth estimation
    depth_estimator = None
    if not args.no_depth:
        depth_model = args.depth_model or config.MIDAS_MODEL_TYPE
        depth_estimator = DepthEstimator(model_type=depth_model)
    else:
        print("[Main] Depth estimation DISABLED (--no-depth)")

    # Analysis & Visualizers
    analyzer = PotholeAnalyzer()
    overlay = Overlay()
    blueprint = BlueprintRenderer()
    logger = DefectLogger(log_dir=os.path.join(args.save_dir, "logs")) if not args.no_log else None

    show_blueprint = not args.no_blueprint
    os.makedirs(args.save_dir, exist_ok=True)

    print("[Main] All modules initialized!")
    print()

    # ===================================================================
    # Input source
    # ===================================================================
    source = args.source
    is_image = False

    if source.isdigit():
        source = int(source)
        print(f"[Main] Opening camera {source}...")
    elif is_image_file(source):
        is_image = True
        print(f"[Main] Loading image: {source}")
    else:
        print(f"[Main] Opening video: {source}")

    if is_image:
        frame = cv2.imread(source)
        if frame is None:
            print(f"[ERROR] Could not read image: {source}")
            return
        process_single_frame(
            frame, detector, depth_estimator, analyzer, overlay, blueprint,
            show_blueprint, args.save_dir, logger
        )
    else:
        cap = cv2.VideoCapture(source)
        if not cap.isOpened():
            print(f"[ERROR] Could not open source: {source}")
            return

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)

        w_actual = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h_actual = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"[Main] Capture active: {w_actual}x{h_actual}")
        print()
        print("  Controls:")
        print("    [Q] Quit        [B] Blueprint     [H] Heatmap     [S] Screenshot")
        print("    [E] Export 3D   [D] Boxes         [M] Masks       [N/P] Select Pothole")
        print()

        run_video_loop(
            cap, detector, depth_estimator, analyzer, overlay, blueprint,
            show_blueprint, args.save_dir, logger
        )
        cap.release()

    if logger:
        logger.save_summary_json()

    cv2.destroyAllWindows()
    print("\n[Main] PotholeVision shut down. Goodbye!")


def run_video_loop(cap, detector, depth_estimator, analyzer, overlay, blueprint,
                   show_blueprint, save_dir, logger):
    """Main video processing loop."""
    frame_count = 0
    depth_map = None
    depth_colored = None
    cached_detections = []

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[Main] End of video stream.")
            break

        frame_count += 1

        # ── Detection ────────────────────────────────────────────────
        if frame_count % config.SKIP_DETECTION_FRAMES == 0:
            detections = detector.detect(frame)
        else:
            detections = cached_detections

        # ── Depth Estimation ─────────────────────────────────────────
        if depth_estimator is not None and frame_count % config.SKIP_DEPTH_FRAMES == 0:
            depth_map = depth_estimator.estimate(frame)
            depth_colored = depth_estimator.get_colored_depth(depth_map)

        # ── Analysis ─────────────────────────────────────────────────
        if detections:
            detections = analyzer.analyze(detections, depth_map, frame.shape)
            if logger and frame_count % 15 == 0:
                logger.log_frame_detections(frame_count, detections)

        cached_detections = detections

        # ── Render Overlay ───────────────────────────────────────────
        display = overlay.render(frame, detections, depth_map, depth_colored)

        # ── Render Blueprint Panel ───────────────────────────────────
        if show_blueprint:
            bp_panel = blueprint.render(detections, depth_map)
            if display.shape[0] != bp_panel.shape[0]:
                bp_panel = cv2.resize(bp_panel, (bp_panel.shape[1], display.shape[0]))
            display = np.hstack([display, bp_panel])

        # ── Display ──────────────────────────────────────────────────
        cv2.imshow("PotholeVision", display)

        # ── Keyboard Input ───────────────────────────────────────────
        key = cv2.waitKey(1) & 0xFF

        if key == ord('q'):
            break
        elif key == ord('b'):
            show_blueprint = not show_blueprint
            print(f"[UI] Blueprint panel: {'ON' if show_blueprint else 'OFF'}")
        elif key == ord('h'):
            overlay.toggle_heatmap()
            print(f"[UI] Heatmap: {'ON' if overlay.show_heatmap else 'OFF'}")
        elif key == ord('d'):
            overlay.toggle_boxes()
            print(f"[UI] Boxes: {'ON' if overlay.show_boxes else 'OFF'}")
        elif key == ord('m'):
            overlay.toggle_masks()
            print(f"[UI] Masks: {'ON' if overlay.show_masks else 'OFF'}")
        elif key == ord('s'):
            save_screenshot(display, save_dir)
        elif key == ord('e'):
            if detections and depth_map is not None:
                idx = min(blueprint.selected_index, len(detections) - 1)
                obj_file = os.path.join(save_dir, f"pothole_{idx + 1}_{int(time.time())}.obj")
                MeshExporter.export_obj(detections[idx], depth_map, obj_file)
            else:
                print("[UI] No active pothole or depth map to export.")
        elif key == ord('n'):
            blueprint.select_next(len(detections))
            print(f"[UI] Selected pothole #{blueprint.selected_index + 1}")
        elif key == ord('p'):
            blueprint.select_prev(len(detections))
            print(f"[UI] Selected pothole #{blueprint.selected_index + 1}")


def process_single_frame(frame, detector, depth_estimator, analyzer, overlay,
                          blueprint, show_blueprint, save_dir, logger):
    """Process a single image."""
    print("[Main] Processing image...")

    detections = detector.detect(frame)
    print(f"[Main] Detected {len(detections)} road defect(s)")

    depth_map = None
    depth_colored = None
    if depth_estimator is not None:
        depth_map = depth_estimator.estimate(frame)
        depth_colored = depth_estimator.get_colored_depth(depth_map)
        print("[Main] Depth estimation complete")

    if detections:
        detections = analyzer.analyze(detections, depth_map, frame.shape)
        if logger:
            logger.log_frame_detections(1, detections)
        for i, det in enumerate(detections):
            print(f"  [{i+1}] {det.severity} | Conf: {det.confidence:.2%} | "
                  f"Depth: {det.max_depth:.4f} | Area: {det.area_px:,}px | Dim: {det.dimensions[0]}x{det.dimensions[1]}m")

    display = overlay.render(frame, detections, depth_map, depth_colored)

    if show_blueprint:
        bp_panel = blueprint.render(detections, depth_map)
        if display.shape[0] != bp_panel.shape[0]:
            bp_panel = cv2.resize(bp_panel, (bp_panel.shape[1], display.shape[0]))
        display = np.hstack([display, bp_panel])

    # Save output automatically for images
    out_file = os.path.join(save_dir, "processed_image_blueprint.jpg")
    cv2.imwrite(out_file, display)
    print(f"[Main] Saved blueprint output to: {out_file}")

    # Export 3D OBJ mesh of first pothole if present
    if detections and depth_map is not None:
        obj_file = os.path.join(save_dir, "pothole_sample_3d.obj")
        MeshExporter.export_obj(detections[0], depth_map, obj_file)

    print("\n[Main] Showing interactive window. Press any key or 'q' to exit.")
    cv2.imshow("PotholeVision", display)
    cv2.waitKey(0)


def save_screenshot(frame, save_dir):
    """Save a screenshot with timestamp."""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"potholevision_{timestamp}.jpg"
    filepath = os.path.join(save_dir, filename)
    cv2.imwrite(filepath, frame)
    print(f"[Screenshot] Saved: {filepath}")


if __name__ == "__main__":
    main()
