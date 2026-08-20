# =============================================================================
# PotholeVision — Gradio 5 + FastAPI Unified Backend
# =============================================================================
# Native Hugging Face Spaces & ZeroGPU support + full REST API endpoints:
#   - GET  /api/health
#   - POST /api/analyze (multipart image file OR base64 JSON payload for live camera)
#   - POST /api/analyze/3d (3D surface mesh topography)
#   - GET  /api/sample (built-in sample road image)

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
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

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


# ZeroGPU registered inference function
@gpu_decorate
def run_pipeline(frame: np.ndarray) -> dict:
    return _execute_pipeline(frame)


# ─── Gradio Interactive Web UI ───────────────────────────────────────────────


def gradio_predict(img):
    """Handler for Hugging Face embedded Gradio interface."""
    if img is None:
        return None, "Please upload or capture a road image."

    # Convert RGB from Gradio to BGR for OpenCV
    bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    res = run_pipeline(bgr)

    # Decode annotated output back to RGB for display
    ann_b64 = res["images"]["annotated"]
    ann_bytes = base64.b64decode(ann_b64)
    ann_bgr = cv2.imdecode(np.frombuffer(ann_bytes, np.uint8), cv2.IMREAD_COLOR)
    ann_rgb = cv2.cvtColor(ann_bgr, cv2.COLOR_BGR2RGB)

    metrics = res["metrics"]
    summary = (
        f"Road Status: {metrics['road_status']}\n"
        f"Potholes Detected: {metrics['pothole_count']}\n"
        f"Max Depth: {metrics['max_depth']:.4f}\n"
        f"Total Volume: {metrics['total_volume']:.1f}\n"
        f"Latency: {metrics['latency_ms']:.1f} ms"
    )
    return ann_rgb, summary


with gr.Blocks(title="PotholeVision AI") as demo:
    gr.Markdown("# PotholeVision — Real-Time Road Defect & Depth Analysis")
    gr.Markdown(
        "AI-powered monocular depth estimation, YOLOv8 segmentation, and 3D surface topography.\n\n"
        "**REST API is active at `/api/analyze`, `/api/health`, and `/api/analyze/3d` for the React/Vercel frontend.**"
    )
    with gr.Row():
        with gr.Column():
            input_img = gr.Image(type="numpy", label="Road Image / Camera Feed")
            btn = gr.Button("Analyze Road Defect", variant="primary")
        with gr.Column():
            output_img = gr.Image(label="Annotated Detection & Depth Map")
            output_txt = gr.Textbox(label="Audit Metrics", lines=6)

    btn.click(fn=gradio_predict, inputs=input_img, outputs=[output_img, output_txt])


# ─── REST API Route Handlers (FastAPI on demo.app with include_in_schema=False) ───

demo.app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@demo.app.get("/api/health", include_in_schema=False)
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "PotholeVision API",
        "version": "2.0.0",
    }


@demo.app.post("/api/analyze", include_in_schema=False)
async def analyze_image(request: Request):
    """
    Analyze image from multipart form data or base64 JSON payload.
    Supports real-time live camera streaming and file uploads.
    """
    try:
        content_type = request.headers.get("content-type", "")

        # 1. Check if multipart form data
        if "multipart/form-data" in content_type:
            form = await request.form()
            file = form.get("image")
            if not file:
                return JSONResponse(status_code=400, content={"success": False, "error": "No 'image' file provided."})
            file_bytes = await file.read()
            frame = decode_image_bytes(file_bytes)

        # 2. Check if JSON payload (base64 webcam frame)
        elif "application/json" in content_type:
            body = await request.json()
            if not body or "image" not in body:
                return JSONResponse(status_code=400, content={"success": False, "error": "No 'image' in JSON payload."})
            frame = decode_image_base64_str(body["image"])

        else:
            # Fallback read raw body
            body_bytes = await request.body()
            if body_bytes:
                try:
                    data = json.loads(body_bytes.decode("utf-8"))
                    if "image" in data:
                        frame = decode_image_base64_str(data["image"])
                    else:
                        frame = decode_image_bytes(body_bytes)
                except Exception:
                    frame = decode_image_bytes(body_bytes)
            else:
                return JSONResponse(status_code=400, content={"success": False, "error": "Empty request."})

        result = run_pipeline(frame)
        return JSONResponse(content=result)

    except ValueError as e:
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"success": False, "error": f"Server error: {str(e)}"})


@demo.app.get("/api/sample", include_in_schema=False)
async def analyze_sample():
    """Analyze built-in sample image."""
    try:
        sample_path = os.path.join(config.ASSETS_DIR, "sample_pothole.jpg")
        if not os.path.exists(sample_path):
            try:
                from generate_sample import generate_sample_pothole_image
                generate_sample_pothole_image(sample_path)
            except Exception:
                pass

        if not os.path.exists(sample_path):
            return JSONResponse(status_code=404, content={"success": False, "error": "Sample image not found."})

        frame = cv2.imread(sample_path)
        if frame is None:
            return JSONResponse(status_code=500, content={"success": False, "error": "Could not read sample image."})

        result = run_pipeline(frame)
        return JSONResponse(content=result)

    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"success": False, "error": f"Server error: {str(e)}"})


@demo.app.post("/api/analyze/3d", include_in_schema=False)
async def get_3d_mesh(request: Request):
    """Get 3D surface mesh data for a specific detection."""
    try:
        data = await request.json()
        det_index = data.get("detection_index", 0)

        detections = _models.get("_last_detections", [])
        depth_map = _models.get("_last_depth_map", None)

        if not detections or depth_map is None:
            return JSONResponse(status_code=400, content={"success": False, "error": "No analysis results. Call /api/analyze first."})

        if det_index < 0 or det_index >= len(detections):
            return JSONResponse(status_code=400, content={"success": False, "error": "Invalid detection index."})

        det = detections[det_index]
        if det.mask is None or depth_map is None:
            return JSONResponse(status_code=400, content={"success": False, "error": "No mask or depth data."})

        x1, y1, x2, y2 = det.bbox
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(depth_map.shape[1], x2)
        y2 = min(depth_map.shape[0], y2)

        region_depth = depth_map[y1:y2, x1:x2].copy()
        region_mask = det.mask[y1:y2, x1:x2]

        if region_depth.size == 0:
            return JSONResponse(status_code=400, content={"success": False, "error": "Empty region."})

        ref_depth = float(np.median(region_depth))
        z_vals = -(region_depth - ref_depth)
        z_vals[region_mask == 0] = 0

        step = max(1, min(region_depth.shape) // 60)
        z_down = z_vals[::step, ::step]

        x_arr = (np.arange(z_down.shape[1]) * config.REAL_WORLD_SCALE * step).tolist()
        y_arr = (np.arange(z_down.shape[0]) * config.REAL_WORLD_SCALE * step).tolist()
        z_arr = z_down.tolist()

        return JSONResponse(content={
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
        return JSONResponse(status_code=500, content={"success": False, "error": f"Server error: {str(e)}"})


# ─── Entry Point ─────────────────────────────────────────────────────────────

port = int(os.environ.get("PORT", 7860))
print("=" * 60)
print("  PotholeVision — Launching Server on port", port)
print("=" * 60)

demo.launch(server_name="0.0.0.0", server_port=port)
