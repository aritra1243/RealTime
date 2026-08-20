# PotholeVision 🕳️🔍

**Real-Time Computer Vision Pothole Detection, Monocular Depth Estimation, and 2D/3D Blueprint HUD System.**

PotholeVision analyzes road conditions in real-time from camera feeds, calculates the exact spatial dimensions (width, length), relative depth, and estimated volume of road defects, issues driver hazard collision warnings, and renders real-time 2D/3D engineering blueprints on screen.

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd e:\RealTime
pip install -r requirements.txt
```

### 2. Run Real-Time Camera HUD Feed (Recommended)
```bash
# Live Webcam Feed
python main.py --source 0

# Video File Feed
python main.py --source path/to/road_video.mp4

# Test with Sample Road Image
python main.py --source assets/sample_pothole.jpg
```

### 3. Launch Interactive Web Dashboard
```bash
streamlit run app.py
```

---

## 🎮 Desktop HUD Controls

| Key | Action |
|:---:|:---|
| **`Q`** | Quit application |
| **`B`** | Toggle side blueprint engineering panel (ON/OFF) |
| **`H`** | Toggle depth colormap heatmap overlay |
| **`D`** | Toggle bounding boxes & confidence labels |
| **`M`** | Toggle segmentation masks |
| **`E`** | Export 3D CAD mesh (`.obj`) of currently selected pothole |
| **`S`** | Save high-resolution HUD screenshot |
| **`N` / `P`** | Select Next / Previous pothole for blueprint inspection |

---

## 🏗️ Architecture & Pipeline

```
                       Camera / Video Input
                                │
          ┌─────────────────────┴─────────────────────┐
          ▼                                           ▼
   Object Detection                           Monocular Depth
(YOLOv8-seg / Hybrid CV)                       (MiDaS-small)
          │                                           │
   Defect Mask Polygon                             Depth Map
          └─────────────────────┬─────────────────────┘
                                ▼
                     Spatial Depth Analyzer
           ├── Road Surface Reference Plane Fitting
           ├── Relative Depth Extraction (Max & Avg)
           ├── Surface Area & Volume Integration
           └── Severity Rating (SHALLOW / MODERATE / CRITICAL)
                                │
          ┌─────────────────────┴─────────────────────┐
          ▼                                           ▼
   Real-Time Overlay                           2D Blueprint HUD
 ├── Glassmorphic HUD                       ├── Top-Down CAD View
 ├── Corner-Accented Boxes                  ├── Centerline Cross-Section
 ├── Driver Hazard Warning Alert            ├── Depth Heatmap & Legend
 └── Defect CSV/JSON Audit Logger           └── 3D OBJ Mesh Exporter
```

---

## 📊 Blueprint Engineering Panel

The blueprint side panel visualizes:
1. **Top-Down CAD View** — Real-world dimension annotations (width, length in meters) with contour outline.
2. **Cross-Section Profile** — Side profile showing depression curve against the road surface plane.
3. **Depth Heatmap** — Thermal colormap (Inferno/Magma) showing depth gradient inside the pothole.
4. **Numerical Audit Metrics** — Max depth, average depth, surface pixel count, volume, and dimensions.

---

## 🧠 Custom YOLOv8 Model Training

PotholeVision includes a complete dataset generator and training pipeline:

```bash
# Step 1: Generate or Download Dataset
python train.py --download

# Step 2: Train YOLOv8-seg on the dataset
python train.py --train --epochs 50

# Step 3: Run with your custom trained model
python main.py --source 0 --model runs/pothole_seg/weights/best.pt
```

---

## 📁 Project Structure

```
RealTime/
├── main.py                     # Main real-time OpenCV desktop entry point
├── app.py                      # Interactive Streamlit Web Dashboard & 3D Plotter
├── train.py                    # Complete YOLOv8 dataset download & training pipeline
├── config.py                   # Central system configuration & color palette
├── generate_sample.py          # Synthetic test image generator
├── requirements.txt            # Python dependencies
├── README.md                   # Full system documentation
│
├── detection/
│   ├── detector.py             # Hybrid YOLOv8-seg + Classical CV detector
│   └── download_model.py       # Model downloader
│
├── depth/
│   └── estimator.py            # MiDaS monocular depth estimation
│
├── analysis/
│   └── pothole_analyzer.py     # Relative depth, surface area & volume calculator
│
├── visualization/
│   ├── overlay.py              # Real-time camera overlay & hazard safety alert HUD
│   └── blueprint.py            # 2D CAD blueprint panel renderer
│
├── utils/
│   ├── calibration.py          # Camera calibration & pixel-to-meter geometry
│   ├── logger.py               # Automated CSV/JSON session defect logger
│   └── mesh_exporter.py        # 3D Wavefront (.obj) and PLY point cloud generator
│
├── assets/
│   └── sample_pothole.jpg      # High-detail test road image
│
├── output/                     # Auto-generated reports, 3D meshes & screenshots
└── models/                     # Cache directory for trained weights
```
