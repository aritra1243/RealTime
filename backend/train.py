# =============================================================================
# PotholeVision — YOLOv8 Training Pipeline
# =============================================================================
# Train a custom YOLOv8-seg model on a pothole segmentation dataset.
#
# Usage:
#   Step 1: Download dataset
#       python train.py --download
#
#   Step 2: Train model
#       python train.py --train
#
#   Step 3: Test trained model
#       python train.py --test
#
#   All-in-one:
#       python train.py --download --train --test

import argparse
import os
import sys
import shutil
import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config


# ─── Dataset Configuration ───────────────────────────────────────────────────
DATASET_DIR = os.path.join(config.BASE_DIR, "datasets", "pothole_seg")
DATASET_YAML = os.path.join(DATASET_DIR, "data.yaml")

# Training configuration
TRAIN_CONFIG = {
    "model": "yolov8n-seg.pt",       # Base model (nano for speed)
    "epochs": 50,                     # Training epochs (increase for better results)
    "imgsz": 640,                     # Image size
    "batch": 8,                       # Batch size (lower if you run out of memory)
    "patience": 15,                   # Early stopping patience
    "save_period": 10,                # Save checkpoint every N epochs
    "project": os.path.join(config.BASE_DIR, "runs"),
    "name": "pothole_seg",
    "exist_ok": True,
    "pretrained": True,
    "optimizer": "auto",
    "lr0": 0.01,
    "lrf": 0.01,
    "augment": True,
    "mosaic": 1.0,
    "flipud": 0.5,
    "fliplr": 0.5,
    "hsv_h": 0.015,
    "hsv_s": 0.7,
    "hsv_v": 0.4,
}


def download_dataset(api_key: str = None):
    """
    Download a pothole segmentation dataset.
    
    Uses Roboflow API if provided, otherwise generates a synthetic dataset.
    """
    print("=" * 60)
    print("  STEP 1: Download Pothole Segmentation Dataset")
    print("=" * 60)

    os.makedirs(DATASET_DIR, exist_ok=True)

    if api_key:
        try:
            from roboflow import Roboflow
            print("[Dataset] Using Roboflow API to download dataset...")
            rf = Roboflow(api_key=api_key)
            project = rf.workspace().project("pothole-segmentation-g6hbh")
            version = project.version(1)
            dataset = version.download("yolov8", location=DATASET_DIR)
            print(f"[Dataset] Downloaded to: {DATASET_DIR}")
            _fix_data_yaml()
            return
        except Exception as e:
            print(f"[Dataset] Roboflow download failed: {e}")
            print("[Dataset] Falling back to synthetic dataset...")

    _create_manual_dataset()


def _create_manual_dataset():
    """
    Create a sample dataset structure with instructions for manual download.
    Also generates a small synthetic dataset for immediate testing.
    """
    import cv2
    import numpy as np

    print("[Dataset] Generating synthetic pothole dataset for training demo...")

    # Create directory structure
    for split in ["train", "val"]:
        os.makedirs(os.path.join(DATASET_DIR, split, "images"), exist_ok=True)
        os.makedirs(os.path.join(DATASET_DIR, split, "labels"), exist_ok=True)

    # Generate synthetic pothole images with segmentation labels
    num_train = 80
    num_val = 20

    print(f"[Dataset] Generating {num_train} training + {num_val} validation images...")

    for split, count in [("train", num_train), ("val", num_val)]:
        for idx in range(count):
            img, labels = _generate_synthetic_pothole(idx + (1000 if split == "val" else 0))
            img_path = os.path.join(DATASET_DIR, split, "images", f"pothole_{idx:04d}.jpg")
            lbl_path = os.path.join(DATASET_DIR, split, "labels", f"pothole_{idx:04d}.txt")

            cv2.imwrite(img_path, img)
            with open(lbl_path, "w") as f:
                f.write(labels)

    # Create data.yaml
    data_yaml = {
        "path": DATASET_DIR.replace("\\", "/"),
        "train": "train/images",
        "val": "val/images",
        "names": {
            0: "pothole",
        },
        "nc": 1,
    }

    with open(DATASET_YAML, "w") as f:
        yaml.dump(data_yaml, f, default_flow_style=False)

    print(f"[Dataset] Synthetic dataset created at: {DATASET_DIR}")
    print(f"[Dataset] data.yaml: {DATASET_YAML}")
    print()
    print("  +-------------------------------------------------------+")
    print("  |  NOTE: Generated synthetic dataset for demo/testing.  |")
    print("  |  For real-world deployment:                           |")
    print("  |    1. Go to universe.roboflow.com                     |")
    print("  |    2. Search 'pothole segmentation'                   |")
    print("  |    3. Download in YOLOv8 format                       |")
    print("  |    4. Extract to datasets/pothole_seg/                |")
    print("  +-------------------------------------------------------+")


def _generate_synthetic_pothole(seed: int):
    """Generate a single synthetic pothole image with YOLO segmentation labels."""
    import cv2
    import numpy as np

    np.random.seed(seed)
    width, height = 640, 640
    img = np.zeros((height, width, 3), dtype=np.uint8)

    # Road surface with texture
    base_gray = np.random.randint(80, 130)
    road = np.full((height, width), base_gray, dtype=np.uint8)
    noise = np.random.randint(-20, 20, (height, width), dtype=np.int16)
    road = np.clip(road.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    img[:, :, 0] = road
    img[:, :, 1] = road
    img[:, :, 2] = road

    # Random road markings
    if np.random.random() > 0.5:
        line_x = np.random.randint(100, width - 100)
        cv2.line(img, (line_x, 0), (line_x, height), (200, 200, 200), 2)

    # Generate 1-3 potholes
    num_potholes = np.random.randint(1, 4)
    labels = []

    for _ in range(num_potholes):
        # Random pothole parameters
        cx = np.random.randint(100, width - 100)
        cy = np.random.randint(100, height - 100)
        rx = np.random.randint(30, 120)
        ry = np.random.randint(25, 100)
        angle = np.random.randint(-30, 30)

        # Draw pothole (darker ellipse with darker center)
        dark1 = np.random.randint(30, 60)
        dark2 = np.random.randint(15, 35)
        cv2.ellipse(img, (cx, cy), (rx, ry), angle, 0, 360, (dark1, dark1 - 5, dark1 - 10), -1)
        cv2.ellipse(img, (cx, cy), (int(rx * 0.6), int(ry * 0.6)), angle, 0, 360,
                     (dark2, dark2 - 3, dark2 - 5), -1)

        # Edge roughness
        for a in range(0, 360, 20):
            rad = np.radians(a + angle)
            ex = int(cx + rx * np.cos(rad) + np.random.randint(-10, 10))
            ey = int(cy + ry * np.sin(rad) + np.random.randint(-10, 10))
            ex2 = int(ex + np.random.randint(5, 20) * np.cos(rad))
            ey2 = int(ey + np.random.randint(5, 20) * np.sin(rad))
            cv2.line(img, (ex, ey), (ex2, ey2), (dark1 + 10, dark1 + 5, dark1), 1)

        # Generate polygon points for YOLO segmentation label
        # Create ellipse contour points
        num_pts = 24
        polygon_pts = []
        for a in range(num_pts):
            theta = 2 * np.pi * a / num_pts
            # Add angle rotation
            angle_rad = np.radians(angle)
            px = rx * np.cos(theta)
            py = ry * np.sin(theta)
            # Rotate
            rpx = px * np.cos(angle_rad) - py * np.sin(angle_rad) + cx
            rpy = px * np.sin(angle_rad) + py * np.cos(angle_rad) + cy
            # Add slight randomness to edges
            rpx += np.random.randint(-5, 5)
            rpy += np.random.randint(-5, 5)
            # Normalize to [0, 1]
            norm_x = np.clip(rpx / width, 0, 1)
            norm_y = np.clip(rpy / height, 0, 1)
            polygon_pts.extend([f"{norm_x:.6f}", f"{norm_y:.6f}"])

        # YOLO segmentation format: class_id x1 y1 x2 y2 ... xn yn
        label_line = "0 " + " ".join(polygon_pts)
        labels.append(label_line)

    # Add some cracks
    for _ in range(np.random.randint(0, 4)):
        pts = []
        x, y = np.random.randint(50, width - 50), np.random.randint(50, height - 50)
        for _ in range(np.random.randint(3, 7)):
            x += np.random.randint(-40, 40)
            y += np.random.randint(-40, 40)
            pts.append([x, y])
        pts = np.array(pts, dtype=np.int32)
        cv2.polylines(img, [pts], False, (base_gray - 30, base_gray - 35, base_gray - 40), 1)

    # Blur for realism
    img = cv2.GaussianBlur(img, (3, 3), 0.5)

    return img, "\n".join(labels)


def _fix_data_yaml():
    """Fix the data.yaml paths after Roboflow download."""
    if not os.path.exists(DATASET_YAML):
        return

    with open(DATASET_YAML, "r") as f:
        data = yaml.safe_load(f)

    data["path"] = DATASET_DIR.replace("\\", "/")
    
    with open(DATASET_YAML, "w") as f:
        yaml.dump(data, f, default_flow_style=False)

    print(f"[Dataset] Fixed data.yaml paths → {DATASET_DIR}")


def train_model():
    """Train YOLOv8-seg on the pothole dataset."""
    from ultralytics import YOLO

    print("=" * 60)
    print("  STEP 2: Train YOLOv8-seg on Pothole Dataset")
    print("=" * 60)

    if not os.path.exists(DATASET_YAML):
        print(f"[ERROR] Dataset not found: {DATASET_YAML}")
        print("        Run 'python train.py --download' first.")
        return None

    # Load data.yaml to verify
    with open(DATASET_YAML, "r") as f:
        data = yaml.safe_load(f)
    
    print(f"[Train] Dataset: {DATASET_YAML}")
    print(f"[Train] Classes: {data.get('names', {})}")
    print(f"[Train] Config: {TRAIN_CONFIG['epochs']} epochs, "
          f"imgsz={TRAIN_CONFIG['imgsz']}, batch={TRAIN_CONFIG['batch']}")
    print()

    # Load base model
    model = YOLO(TRAIN_CONFIG["model"])

    # Train
    results = model.train(
        data=DATASET_YAML,
        epochs=TRAIN_CONFIG["epochs"],
        imgsz=TRAIN_CONFIG["imgsz"],
        batch=TRAIN_CONFIG["batch"],
        patience=TRAIN_CONFIG["patience"],
        save_period=TRAIN_CONFIG["save_period"],
        project=TRAIN_CONFIG["project"],
        name=TRAIN_CONFIG["name"],
        exist_ok=TRAIN_CONFIG["exist_ok"],
        pretrained=TRAIN_CONFIG["pretrained"],
        optimizer=TRAIN_CONFIG["optimizer"],
        lr0=TRAIN_CONFIG["lr0"],
        mosaic=TRAIN_CONFIG["mosaic"],
        flipud=TRAIN_CONFIG["flipud"],
        fliplr=TRAIN_CONFIG["fliplr"],
        hsv_h=TRAIN_CONFIG["hsv_h"],
        hsv_s=TRAIN_CONFIG["hsv_s"],
        hsv_v=TRAIN_CONFIG["hsv_v"],
        verbose=True,
    )

    # Find best weights
    best_weights = os.path.join(
        TRAIN_CONFIG["project"], TRAIN_CONFIG["name"], "weights", "best.pt"
    )

    if os.path.exists(best_weights):
        print()
        print("=" * 60)
        print(f"  ✅ Training complete!")
        print(f"  Best weights: {best_weights}")
        print()
        print(f"  To use with PotholeVision:")
        print(f"    python main.py --source 0 --model {best_weights}")
        print("=" * 60)

        # Copy best weights to models directory
        os.makedirs(config.MODELS_DIR, exist_ok=True)
        dest = os.path.join(config.MODELS_DIR, "pothole_best.pt")
        shutil.copy2(best_weights, dest)
        print(f"\n  Also copied to: {dest}")

        return best_weights
    else:
        print("[ERROR] Training completed but best.pt not found.")
        return None


def test_model(model_path: str = None):
    """Test the trained model on the validation set and sample image."""
    from ultralytics import YOLO
    import cv2
    import numpy as np

    print("=" * 60)
    print("  STEP 3: Test Trained Model")
    print("=" * 60)

    # Find the model
    if model_path is None:
        model_path = os.path.join(
            TRAIN_CONFIG["project"], TRAIN_CONFIG["name"], "weights", "best.pt"
        )
    if not os.path.exists(model_path):
        # Try models directory
        model_path = os.path.join(config.MODELS_DIR, "pothole_best.pt")
    if not os.path.exists(model_path):
        print(f"[ERROR] No trained model found. Run training first.")
        return

    print(f"[Test] Loading model: {model_path}")
    model = YOLO(model_path)

    # Validate on val set
    if os.path.exists(DATASET_YAML):
        print("[Test] Running validation...")
        metrics = model.val(data=DATASET_YAML, verbose=False)
        print(f"  mAP50:    {metrics.seg.map50:.4f}")
        print(f"  mAP50-95: {metrics.seg.map:.4f}")
        print()

    # Test on sample image
    sample = os.path.join(config.ASSETS_DIR, "sample_pothole.jpg")
    if os.path.exists(sample):
        print(f"[Test] Running inference on: {sample}")
        results = model(sample, conf=0.25, verbose=False)
        
        if results and len(results[0].boxes) > 0:
            print(f"  Detected {len(results[0].boxes)} pothole(s)!")
            for i, box in enumerate(results[0].boxes):
                conf = float(box.conf[0])
                print(f"    [{i+1}] confidence: {conf:.2%}")
            
            # Save annotated result
            annotated = results[0].plot()
            out_path = os.path.join(config.BASE_DIR, "output", "trained_result.jpg")
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            cv2.imwrite(out_path, annotated)
            print(f"  Saved: {out_path}")
        else:
            print("  No potholes detected in sample image.")
    
    print()
    print("  To run live detection:")
    print(f"    python main.py --source 0 --model {model_path}")


def main():
    parser = argparse.ArgumentParser(
        description="PotholeVision — Training Pipeline"
    )
    parser.add_argument("--download", action="store_true",
                        help="Download/generate pothole dataset")
    parser.add_argument("--train", action="store_true",
                        help="Train YOLOv8-seg on the dataset")
    parser.add_argument("--test", action="store_true",
                        help="Test the trained model")
    parser.add_argument("--model", type=str, default=None,
                        help="Path to model weights (for --test)")
    parser.add_argument("--epochs", type=int, default=None,
                        help="Override number of training epochs")
    parser.add_argument("--batch", type=int, default=None,
                        help="Override batch size")

    args = parser.parse_args()

    if args.epochs:
        TRAIN_CONFIG["epochs"] = args.epochs
    if args.batch:
        TRAIN_CONFIG["batch"] = args.batch

    if not any([args.download, args.train, args.test]):
        # Default: do everything
        args.download = True
        args.train = True
        args.test = True

    print()
    print("  +-------------------------------------------------------+")
    print("  |      POTHOLEVISION -- Training Pipeline               |")
    print("  +-------------------------------------------------------+")
    print()

    model_path = args.model

    if args.download:
        download_dataset()
        print()

    if args.train:
        model_path = train_model()
        print()

    if args.test:
        test_model(model_path)


if __name__ == "__main__":
    main()
