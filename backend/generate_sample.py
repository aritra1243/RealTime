# =============================================================================
# Generate a synthetic test image for PotholeVision
# =============================================================================
# Run this if you don't have a real pothole image handy.

import cv2
import numpy as np
import os

def generate_sample_pothole_image(output_path: str):
    """Generate a synthetic road+pothole image for testing."""
    width, height = 1280, 720
    img = np.zeros((height, width, 3), dtype=np.uint8)

    # Road surface (gray asphalt texture)
    road_base = np.random.randint(80, 120, (height, width), dtype=np.uint8)
    img[:, :, 0] = road_base
    img[:, :, 1] = road_base
    img[:, :, 2] = road_base

    # Add some road texture noise
    noise = np.random.randint(-15, 15, (height, width, 3), dtype=np.int16)
    img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    # Road lane markings
    cv2.line(img, (200, 0), (200, height), (200, 200, 200), 3)
    cv2.line(img, (1080, 0), (1080, height), (200, 200, 200), 3)

    # Dashed center line
    for y in range(0, height, 60):
        cv2.line(img, (640, y), (640, y + 30), (220, 220, 200), 2)

    # Pothole 1 (large)
    center1 = (500, 400)
    axes1 = (120, 80)
    # Dark depression
    cv2.ellipse(img, center1, axes1, 15, 0, 360, (40, 35, 30), -1)
    # Darker center
    cv2.ellipse(img, center1, (80, 50), 15, 0, 360, (25, 20, 18), -1)
    # Edge cracks
    for angle in range(0, 360, 30):
        rad = np.radians(angle)
        x1 = int(center1[0] + axes1[0] * np.cos(rad))
        y1 = int(center1[1] + axes1[1] * np.sin(rad))
        x2 = int(x1 + np.random.randint(10, 30) * np.cos(rad))
        y2 = int(y1 + np.random.randint(10, 30) * np.sin(rad))
        cv2.line(img, (x1, y1), (x2, y2), (50, 45, 40), 1)

    # Pothole 2 (medium)
    center2 = (850, 300)
    axes2 = (70, 55)
    cv2.ellipse(img, center2, axes2, -10, 0, 360, (45, 40, 35), -1)
    cv2.ellipse(img, center2, (45, 30), -10, 0, 360, (30, 25, 22), -1)

    # Pothole 3 (small)
    center3 = (400, 550)
    axes3 = (40, 35)
    cv2.ellipse(img, center3, axes3, 5, 0, 360, (50, 45, 40), -1)

    # Add some cracks across the road
    pts = np.array([[300, 200], [350, 250], [380, 350], [400, 380]], dtype=np.int32)
    cv2.polylines(img, [pts], False, (60, 55, 50), 2)

    pts2 = np.array([[700, 100], [720, 200], [710, 300]], dtype=np.int32)
    cv2.polylines(img, [pts2], False, (65, 60, 55), 1)

    # Slight blur for realism
    img = cv2.GaussianBlur(img, (3, 3), 0.5)

    # Save
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    cv2.imwrite(output_path, img)
    print(f"[Sample] Generated sample image: {output_path}")
    return img


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output = os.path.join(script_dir, "assets", "sample_pothole.jpg")
    generate_sample_pothole_image(output)
