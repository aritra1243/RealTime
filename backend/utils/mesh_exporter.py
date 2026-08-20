# =============================================================================
# PotholeVision — 3D Mesh & Point Cloud Exporter
# =============================================================================
# Converts 2D pothole masks and monocular depth maps into 3D CAD/OBJ meshes
# and PLY point clouds for civil engineering and road maintenance analysis.

import os
import numpy as np
from typing import Optional, Tuple
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from detection.detector import Detection


class MeshExporter:
    """
    Exports pothole surface geometry as 3D Wavefront (.obj) or Point Cloud (.ply).
    """

    @staticmethod
    def export_obj(
        det: Detection,
        depth_map: np.ndarray,
        output_path: str,
        depth_scale: float = 0.5,
        grid_step: int = 2
    ) -> bool:
        """
        Export a detected pothole's 3D depression as an OBJ mesh.
        
        Args:
            det: Detection object with mask and bbox.
            depth_map: Normalized depth map [0, 1].
            output_path: Target .obj filepath.
            depth_scale: Vertical exaggeration factor for 3D visualization.
            grid_step: Downsampling step for mesh density.
        """
        if det.mask is None or depth_map is None:
            return False

        x1, y1, x2, y2 = det.bbox
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(depth_map.shape[1], x2)
        y2 = min(depth_map.shape[0], y2)

        pothole_mask = det.mask[y1:y2:grid_step, x1:x2:grid_step]
        pothole_depth = depth_map[y1:y2:grid_step, x1:x2:grid_step]

        gh, gw = pothole_mask.shape
        if gh < 2 or gw < 2:
            return False

        # Reference depth of road perimeter
        ref_depth = np.median(pothole_depth)

        vertices = []
        vertex_indices = np.full((gh, gw), -1, dtype=int)
        v_count = 1

        # Generate 3D vertices
        for r in range(gh):
            for c in range(gw):
                if pothole_mask[r, c] > 0:
                    z = -(pothole_depth[r, c] - ref_depth) * depth_scale * 100.0
                    x = (c - gw / 2) * config.REAL_WORLD_SCALE * grid_step * 10.0
                    y = -(r - gh / 2) * config.REAL_WORLD_SCALE * grid_step * 10.0
                    vertices.append((x, y, z))
                    vertex_indices[r, c] = v_count
                    v_count += 1

        if not vertices:
            return False

        faces = []
        for r in range(gh - 1):
            for c in range(gw - 1):
                v00 = vertex_indices[r, c]
                v01 = vertex_indices[r, c + 1]
                v10 = vertex_indices[r + 1, c]
                v11 = vertex_indices[r + 1, c + 1]

                if v00 > 0 and v01 > 0 and v10 > 0:
                    faces.append((v00, v01, v10))
                if v01 > 0 and v11 > 0 and v10 > 0:
                    faces.append((v01, v11, v10))

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("# PotholeVision 3D Surface Blueprint\n")
            f.write(f"# Severity: {det.severity} | Max Depth: {det.max_depth:.4f}\n")
            for vx, vy, vz in vertices:
                f.write(f"v {vx:.4f} {vy:.4f} {vz:.4f}\n")
            for f0, f1, f2 in faces:
                f.write(f"f {f0} {f1} {f2}\n")

        print(f"[MeshExporter] Saved 3D OBJ blueprint: {output_path} ({len(vertices)} vertices, {len(faces)} faces)")
        return True

    @staticmethod
    def export_ply(
        det: Detection,
        depth_map: np.ndarray,
        output_path: str,
        depth_scale: float = 0.5
    ) -> bool:
        """Export pothole 3D point cloud as PLY file."""
        if det.mask is None or depth_map is None:
            return False

        x1, y1, x2, y2 = det.bbox
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(depth_map.shape[1], x2)
        y2 = min(depth_map.shape[0], y2)

        mask = det.mask[y1:y2, x1:x2]
        depth = depth_map[y1:y2, x1:x2]

        pts = []
        ref_depth = np.median(depth)
        for r in range(mask.shape[0]):
            for c in range(mask.shape[1]):
                if mask[r, c] > 0:
                    z = -(depth[r, c] - ref_depth) * depth_scale
                    pts.append((c, r, z))

        if not pts:
            return False

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("ply\nformat ascii 1.0\n")
            f.write(f"element vertex {len(pts)}\n")
            f.write("property float x\nproperty float y\nproperty float z\n")
            f.write("end_header\n")
            for px, py, pz in pts:
                f.write(f"{px:.4f} {py:.4f} {pz:.4f}\n")

        print(f"[MeshExporter] Saved 3D PLY Point Cloud: {output_path}")
        return True
