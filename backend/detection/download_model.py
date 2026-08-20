# =============================================================================
# PotholeVision — Model Downloader
# =============================================================================
# Downloads pre-trained model weights for the pipeline.

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def download_yolo_model():
    """Download YOLOv8n-seg model from Ultralytics."""
    from ultralytics import YOLO

    os.makedirs(config.MODELS_DIR, exist_ok=True)
    print(f"[Download] Downloading {config.YOLO_MODEL_NAME}...")
    model = YOLO(config.YOLO_MODEL_NAME)
    print(f"[Download] YOLOv8 model ready.")
    return model


def download_midas_model():
    """Download MiDaS model from PyTorch Hub."""
    import torch

    print(f"[Download] Downloading MiDaS ({config.MIDAS_MODEL_TYPE})...")
    model = torch.hub.load("intel-isl/MiDaS", config.MIDAS_MODEL_TYPE)
    print(f"[Download] MiDaS model ready.")
    return model


def download_all():
    """Download all required models."""
    print("=" * 60)
    print("  PotholeVision — Model Downloader")
    print("=" * 60)
    download_yolo_model()
    download_midas_model()
    print("\n✅ All models downloaded successfully!")


if __name__ == "__main__":
    download_all()
