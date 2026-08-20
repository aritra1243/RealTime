# =============================================================================
# PotholeVision — Flask REST API Backend
# =============================================================================
# Serves pothole detection, depth analysis, and 3D mesh data via REST endpoints.
# Compatible with Render, Hugging Face Spaces (CPU & ZeroGPU), and Vercel.

import base64
import io
import os
import sys
import time
import json
import traceback

import cv2
import numpy as np

from flask import Flask, request, jsonify
from flask_cors import CORS

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from detection.detector import PotholeDetector, Detection
from depth.estimator import DepthEstimator
from analysis.pothole_analyzer import PotholeAnalyzer
from visualization.overlay import Overlay
from visualization.blueprint import BlueprintRenderer
from utils.mesh_exporter import MeshExporter

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

# ─── App Setup ───────────────────────────────────────────────────────────────

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET,PUT,POST,DELETE,OPTIONS"
    return response


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


def encode_image_base64(img: np.ndarray, quality: int = 85) -> str:
    """Encode a BGR OpenCV image to base64 JPEG string."""
    encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
    _, buffer = cv2.imencode(".jpg", img, encode_params)
    return base64.b64encode(buffer).decode("utf-8")


def decode_image_data(req) -> np.ndarray:
    """
    Decode image from multipart file or base64 JSON payload.
    Supports real-time webcam frames and file uploads.
    """
    # 1. Check multipart file
    if "image" in req.files:
        file = req.files["image"]
        if file.filename != "":
            file_bytes = np.frombuffer(file.read(), np.uint8)
            img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            if img is not None:
                return img

    # 2. Check JSON with base64 data
    if req.is_json:
        data = req.get_json()
        if data and "image" in data:
            b64_str = data["image"]
            if "," in b64_str:
                b64_str = b64_str.split(",", 1)[1]
            img_bytes = base64.b64decode(b64_str)
            nparr = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is not None:
                return img

    raise ValueError("No valid 'image' provided (supports file upload or base64 JSON).")


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


def _execute_pipeline(frame: np.ndarray) -> dict:
    """Run detection, depth estimation, and blueprint rendering."""
    models = get_models()
    detector = models["detector"]
    depth_estimator = models["depth_estimator"]
    analyzer = models["analyzer"]
    overlay = models["overlay"]
    blueprint = models["blueprint"]

    start_time = time.time()

    # ── Detection ────────────────────────────────────────────
    detections = detector.detect(frame)

    # ── Depth estimation ─────────────────────────────────────
    depth_map = depth_estimator.estimate(frame)
    depth_colored = depth_estimator.get_colored_depth(depth_map)

    # ── Analysis ─────────────────────────────────────────────
    detections = analyzer.analyze(detections, depth_map, frame.shape)

    latency_ms = (time.time() - start_time) * 1000

    # ── Render annotated overlay ─────────────────────────────
    display = overlay.render(frame, detections, depth_map, depth_colored)
    annotated_b64 = encode_image_base64(display)

    # ── Render blueprint panel ───────────────────────────────
    bp_panel = blueprint.render(detections, depth_map)
    blueprint_b64 = encode_image_base64(bp_panel)

    # ── Depth heatmap ────────────────────────────────────────
    heatmap_b64 = encode_image_base64(depth_colored) if depth_colored is not None else None

    # ── Metrics ──────────────────────────────────────────────
    worst_severity = "CLEAR"
    max_depth = 0.0
    total_volume = 0.0

    if detections:
        worst_severity = max(detections, key=lambda d: d.max_depth).severity
        max_depth = max(d.max_depth for d in detections)
        total_volume = sum(d.volume for d in detections)

    # ── Serialize detections ─────────────────────────────────
    detections_data = [detection_to_dict(d, i) for i, d in enumerate(detections)]

    # ── Store detections + depth_map in memory for 3D requests ──
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


# ZeroGPU registered function
@gpu_decorate
def run_pipeline(frame: np.ndarray) -> dict:
    return _execute_pipeline(frame)


# ─── API Routes ──────────────────────────────────────────────────────────────


@app.route("/", methods=["GET"])
def root():
    """Root endpoint."""
    return jsonify({
        "status": "online",
        "service": "PotholeVision API",
        "message": "Backend API is running. Connect your Vercel frontend to this URL.",
        "version": "2.0.0",
        "endpoints": {
            "health": "/api/health",
            "analyze": "/api/analyze (POST - multipart or base64 JSON)",
            "3d_mesh": "/api/analyze/3d (POST)",
            "sample": "/api/sample (GET)"
        }
    })


@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "ok",
        "service": "PotholeVision API",
        "version": "2.0.0",
    })


@app.route("/api/analyze", methods=["POST", "OPTIONS"])
def analyze_image():
    """
    Analyze a road image for potholes and depth defects.
    Accepts both multipart/form-data ('image' file) and application/json ({'image': base64}).
    """
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    try:
        frame = decode_image_data(request)
        result = run_pipeline(frame)
        return jsonify(result)

    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": f"Internal server error: {str(e)}"}), 500


@app.route("/api/sample", methods=["GET"])
def analyze_sample():
    """Analyze the built-in sample pothole image."""
    try:
        sample_path = os.path.join(config.ASSETS_DIR, "sample_pothole.jpg")
        if not os.path.exists(sample_path):
            # Generate sample dynamically if not present
            try:
                from generate_sample import generate_sample_pothole_image
                generate_sample_pothole_image(sample_path)
            except Exception:
                pass

        if not os.path.exists(sample_path):
            return jsonify({
                "success": False,
                "error": "Sample image not found.",
            }), 404

        frame = cv2.imread(sample_path)
        if frame is None:
            return jsonify({"success": False, "error": "Could not read sample image."}), 500

        result = run_pipeline(frame)
        return jsonify(result)

    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": f"Internal server error: {str(e)}"}), 500


@app.route("/api/analyze/3d", methods=["POST", "OPTIONS"])
def get_3d_mesh():
    """
    Get 3D surface mesh data for a specific detected pothole.
    Expects JSON body: { "detection_index": 0 }
    """
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    try:
        data = request.get_json()
        if data is None:
            return jsonify({"success": False, "error": "JSON body required."}), 400

        det_index = data.get("detection_index", 0)

        detections = _models.get("_last_detections", [])
        depth_map = _models.get("_last_depth_map", None)

        if not detections or depth_map is None:
            return jsonify({
                "success": False,
                "error": "No analysis results available. Call /api/analyze first.",
            }), 400

        if det_index < 0 or det_index >= len(detections):
            return jsonify({
                "success": False,
                "error": f"Invalid detection_index. Must be 0-{len(detections) - 1}.",
            }), 400

        det = detections[det_index]

        if det.mask is None or depth_map is None:
            return jsonify({
                "success": False,
                "error": "No mask or depth data for this detection.",
            }), 400

        # Extract 3D surface data
        x1, y1, x2, y2 = det.bbox
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(depth_map.shape[1], x2)
        y2 = min(depth_map.shape[0], y2)

        region_depth = depth_map[y1:y2, x1:x2].copy()
        region_mask = det.mask[y1:y2, x1:x2]

        if region_depth.size == 0:
            return jsonify({"success": False, "error": "Empty pothole region."}), 400

        ref_depth = float(np.median(region_depth))

        # Calculate depression (negative depth into ground)
        z_vals = -(region_depth - ref_depth)
        z_vals[region_mask == 0] = 0

        # Downsample for web rendering
        step = max(1, min(region_depth.shape) // 60)
        z_down = z_vals[::step, ::step]

        x_arr = (np.arange(z_down.shape[1]) * config.REAL_WORLD_SCALE * step).tolist()
        y_arr = (np.arange(z_down.shape[0]) * config.REAL_WORLD_SCALE * step).tolist()
        z_arr = z_down.tolist()

        return jsonify({
            "success": True,
            "detection_index": det_index,
            "severity": det.severity,
            "surface": {
                "x": x_arr,
                "y": y_arr,
                "z": z_arr,
            },
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
        return jsonify({"success": False, "error": f"Internal server error: {str(e)}"}), 500


# ─── Entry Point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"

    print("=" * 60)
    print("  PotholeVision — Flask REST API")
    print(f"  Running on http://0.0.0.0:{port}")
    print("=" * 60)

    app.run(host="0.0.0.0", port=port, debug=debug)
