# =============================================================================
# PotholeVision — High-Performance Gradio 5 + ZeroGPU Backend
# =============================================================================

import base64
import io
import os
import sys
import time
import json
import traceback

import cv2
import numpy as np
import gradio as gr

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from detection.detector import PotholeDetector, Detection
from depth.estimator import DepthEstimator
from analysis.pothole_analyzer import PotholeAnalyzer
from visualization.overlay import Overlay
from visualization.blueprint import BlueprintRenderer

# ─── Hugging Face ZeroGPU Support ────────────────────────────────────────────
try:
    import spaces

    def gpu_decorate(func):
        return spaces.GPU(duration=60)(func)

    print("[API] Hugging Face ZeroGPU support enabled.")
except Exception:
    def gpu_decorate(func):
        return func

    print("[API] Running in standard CPU/GPU mode.")

# ─── Lazy-loaded ML Models ──────────────────────────────────────────────────

_models = {}


def get_models():
    """Load detector, depth estimator, and analyzer once (lazy singleton)."""
    if "detector" not in _models:
        print("[API] Loading ML models (first request)...")
        _models["detector"] = PotholeDetector()
        _models["depth_estimator"] = DepthEstimator()
        _models["analyzer"] = PotholeAnalyzer()
        _models["overlay"] = Overlay()
        _models["blueprint"] = BlueprintRenderer()
        print("[API] All models loaded.")
    return _models


# ─── Helpers ─────────────────────────────────────────────────────────────────


def encode_image_base64(img: np.ndarray, quality: int = 75) -> str:
    """Encode a BGR OpenCV image to base64 JPEG string."""
    encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
    _, buffer = cv2.imencode(".jpg", img, encode_params)
    return base64.b64encode(buffer).decode("utf-8")


def decode_image_bytes(file_bytes: bytes) -> np.ndarray:
    """Decode raw bytes into a BGR OpenCV image."""
    nparr = np.frombuffer(file_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode image data.")
    return img


def decode_image_base64_str(b64_str: str) -> np.ndarray:
    """Decode base64 string or data URL into BGR OpenCV image."""
    if "," in b64_str:
        b64_str = b64_str.split(",", 1)[1]
    img_bytes = base64.b64decode(b64_str)
    return decode_image_bytes(img_bytes)


def detection_to_dict(det: Detection, index: int) -> dict:
    """Serialize a Detection object to a JSON-safe dict."""
    return {
        "id": index + 1,
        "severity": det.severity,
        "confidence": round(det.confidence, 4),
        "max_depth": round(det.max_depth, 4),
        "avg_depth": round(det.avg_depth, 4),
        "area_px": det.area_px,
        "volume": round(det.volume, 1),
        "dimensions": {
            "width_m": det.dimensions[0],
            "height_m": det.dimensions[1],
        },
        "bbox": {
            "x1": int(det.bbox[0]),
            "y1": int(det.bbox[1]),
            "x2": int(det.bbox[2]),
            "y2": int(det.bbox[3]),
        },
        "center": {"x": int(det.center[0]), "y": int(det.center[1])},
    }


def _execute_pipeline(frame: np.ndarray, is_fast_stream: bool = False) -> dict:
    """Run detection, depth estimation, and blueprint rendering."""
    models = get_models()
    detector = models["detector"]
    depth_estimator = models["depth_estimator"]
    analyzer = models["analyzer"]
    overlay = models["overlay"]
    blueprint = models["blueprint"]

    start_time = time.time()

    # If in fast stream mode, optimize frame scale for high FPS
    if is_fast_stream and max(frame.shape[:2]) > 640:
        scale = 640.0 / max(frame.shape[:2])
        frame = cv2.resize(frame, (0, 0), fx=scale, fy=scale)

    # ── Detection ────────────────────────────────────
    detections = detector.detect(frame)

    # ── Depth estimation ─────────────────────────────
    depth_map = depth_estimator.estimate(frame)
    depth_colored = depth_estimator.get_colored_depth(depth_map) if not is_fast_stream else None

    # ── Analysis ─────────────────────────────────────
    detections = analyzer.analyze(detections, depth_map, frame.shape)

    latency_ms = (time.time() - start_time) * 1000

    # ── Render annotated overlay ─────────────────────
    display = overlay.render(frame, detections, depth_map, depth_colored)
    annotated_b64 = encode_image_base64(display, quality=65 if is_fast_stream else 85)

    # ── Render blueprint & heatmap (only in full mode to maximize stream FPS) ──
    if not is_fast_stream:
        bp_panel = blueprint.render(detections, depth_map)
        blueprint_b64 = encode_image_base64(bp_panel, quality=80)
        heatmap_b64 = encode_image_base64(depth_colored, quality=80) if depth_colored is not None else None
    else:
        blueprint_b64 = None
        heatmap_b64 = None

    # ── Metrics ──────────────────────────────────────
    worst_severity = "CLEAR"
    max_depth = 0.0
    total_volume = 0.0

    if detections:
        worst_severity = max(detections, key=lambda d: d.max_depth).severity
        max_depth = max(d.max_depth for d in detections)
        total_volume = sum(d.volume for d in detections)

    # ── Serialize detections ─────────────────────────
    detections_data = [detection_to_dict(d, i) for i, d in enumerate(detections)]

    # Store for 3D requests
    _models["_last_detections"] = detections
    _models["_last_depth_map"] = depth_map

    return {
        "success": True,
        "metrics": {
            "road_status": worst_severity,
            "pothole_count": len(detections),
            "max_depth": round(max_depth, 4),
            "total_volume": round(total_volume, 1),
            "latency_ms": round(latency_ms, 1),
        },
        "detections": detections_data,
        "images": {
            "annotated": annotated_b64,
            "blueprint": blueprint_b64,
            "heatmap": heatmap_b64,
        },
    }


# ZeroGPU registered inference function
@gpu_decorate
def run_pipeline(frame: np.ndarray, is_fast_stream: bool = False) -> dict:
    return _execute_pipeline(frame, is_fast_stream)


# ─── Gradio Predict Functions ────────────────────────────────────────────────


def gradio_predict_json(image_input):
    """Full-fidelity analysis (for uploads and snapshots)."""
    if image_input is None:
        return json.dumps({"success": False, "error": "No image provided."})
    try:
        if isinstance(image_input, str):
            frame = decode_image_base64_str(image_input)
        elif isinstance(image_input, np.ndarray):
            frame = cv2.cvtColor(image_input, cv2.COLOR_RGB2BGR)
        else:
            return json.dumps({"success": False, "error": "Unsupported image format."})

        result = run_pipeline(frame, is_fast_stream=False)
        return json.dumps(result)
    except Exception as e:
        traceback.print_exc()
        return json.dumps({"success": False, "error": str(e)})


def gradio_predict_fast(image_input):
    """High-speed real-time live camera analysis."""
    if image_input is None:
        return json.dumps({"success": False, "error": "No image provided."})
    try:
        if isinstance(image_input, str):
            frame = decode_image_base64_str(image_input)
        elif isinstance(image_input, np.ndarray):
            frame = cv2.cvtColor(image_input, cv2.COLOR_RGB2BGR)
        else:
            return json.dumps({"success": False, "error": "Unsupported image format."})

        result = run_pipeline(frame, is_fast_stream=True)
        return json.dumps(result)
    except Exception as e:
        traceback.print_exc()
        return json.dumps({"success": False, "error": str(e)})


def gradio_predict_sample():
    """Analyze built-in sample image."""
    try:
        sample_path = os.path.join(config.ASSETS_DIR, "sample_pothole.jpg")
        if not os.path.exists(sample_path):
            from generate_sample import generate_sample_pothole_image
            generate_sample_pothole_image(sample_path)
        frame = cv2.imread(sample_path)
        result = run_pipeline(frame, is_fast_stream=False)
        return json.dumps(result)
    except Exception as e:
        traceback.print_exc()
        return json.dumps({"success": False, "error": str(e)})


def gradio_predict_3d(det_index_str):
    """Get 3D mesh for detection index."""
    try:
        det_index = int(det_index_str) if det_index_str else 0
        detections = _models.get("_last_detections", [])
        depth_map = _models.get("_last_depth_map", None)

        if not detections or depth_map is None:
            return json.dumps({"success": False, "error": "No detections found."})

        if det_index < 0 or det_index >= len(detections):
            return json.dumps({"success": False, "error": "Invalid index."})

        det = detections[det_index]
        x1, y1, x2, y2 = det.bbox
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(depth_map.shape[1], x2)
        y2 = min(depth_map.shape[0], y2)

        region_depth = depth_map[y1:y2, x1:x2].copy()
        region_mask = det.mask[y1:y2, x1:x2]

        ref_depth = float(np.median(region_depth))
        z_vals = -(region_depth - ref_depth)
        z_vals[region_mask == 0] = 0

        step = max(1, min(region_depth.shape) // 60)
        z_down = z_vals[::step, ::step]

        x_arr = (np.arange(z_down.shape[1]) * config.REAL_WORLD_SCALE * step).tolist()
        y_arr = (np.arange(z_down.shape[0]) * config.REAL_WORLD_SCALE * step).tolist()
        z_arr = z_down.tolist()

        return json.dumps({
            "success": True,
            "detection_index": det_index,
            "severity": det.severity,
            "surface": {"x": x_arr, "y": y_arr, "z": z_arr},
            "metadata": {
                "max_depth": round(det.max_depth, 4),
                "dimensions": {
                    "width_m": det.dimensions[0],
                    "height_m": det.dimensions[1],
                },
            },
        })
    except Exception as e:
        traceback.print_exc()
        return json.dumps({"success": False, "error": str(e)})


# ─── Gradio UI Interface ─────────────────────────────────────────────────────

with gr.Blocks(title="PotholeVision AI") as demo:
    gr.Markdown("# PotholeVision — Real-Time Road Defect & Depth Analysis")
    gr.Markdown("ZeroGPU Accelerated Monocular Depth Estimation & Autonomous Road Defect AI.")

    with gr.Row():
        with gr.Column():
            input_text = gr.Textbox(label="Image Data URL / Base64 / File", placeholder="data:image/jpeg;base64,...")
            analyze_btn = gr.Button("Analyze Road Image", variant="primary")
            fast_analyze_btn = gr.Button("Fast Stream Inference")
        with gr.Column():
            output_json = gr.JSON(label="Analysis Results (JSON)")

    sample_btn = gr.Button("Run Sample Analysis")
    sample_output = gr.JSON(label="Sample Results")

    det_idx_input = gr.Textbox(label="Defect Index", value="0")
    mesh_3d_btn = gr.Button("Get 3D Surface Mesh")
    mesh_3d_output = gr.JSON(label="3D Mesh Data")

    # Register named APIs for direct frontend access:
    analyze_btn.click(fn=gradio_predict_json, inputs=input_text, outputs=output_json, api_name="analyze")
    fast_analyze_btn.click(fn=gradio_predict_fast, inputs=input_text, outputs=output_json, api_name="analyze_fast")
    sample_btn.click(fn=gradio_predict_sample, inputs=[], outputs=sample_output, api_name="sample")
    mesh_3d_btn.click(fn=gradio_predict_3d, inputs=det_idx_input, outputs=mesh_3d_output, api_name="analyze_3d")


# ─── Entry Point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    print("=" * 60)
    print("  PotholeVision — Launching Server on port", port)
    print("=" * 60)

    demo.launch(server_name="0.0.0.0", server_port=port)
