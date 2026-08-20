// =============================================================================
// PotholeVision — API Client
// =============================================================================
// Communicates with the Flask backend (Render) from the React frontend (Vercel).

const API_BASE = import.meta.env.VITE_API_URL || '';

/**
 * Check backend health.
 */
export async function checkHealth() {
  const res = await fetch(`${API_BASE}/api/health`);
  if (!res.ok) throw new Error('Backend unreachable');
  return res.json();
}

/**
 * Upload an image and run the full detection + depth pipeline.
 * @param {File} imageFile - The image file to analyze.
 * @returns {Promise<Object>} Analysis results with detections, metrics, and images.
 */
export async function analyzeImage(imageFile) {
  const formData = new FormData();
  formData.append('image', imageFile);

  const res = await fetch(`${API_BASE}/api/analyze`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ error: 'Network error' }));
    throw new Error(error.error || `HTTP ${res.status}`);
  }

  return res.json();
}

/**
 * Analyze the built-in sample image.
 * @returns {Promise<Object>} Analysis results.
 */
export async function analyzeSample() {
  const res = await fetch(`${API_BASE}/api/sample`);

  if (!res.ok) {
    const error = await res.json().catch(() => ({ error: 'Network error' }));
    throw new Error(error.error || `HTTP ${res.status}`);
  }

  return res.json();
}

/**
 * Get 3D surface mesh data for a specific detection.
 * @param {number} detectionIndex - Index of the detection to get 3D data for.
 * @returns {Promise<Object>} 3D surface data (x, y, z arrays).
 */
export async function get3DMesh(detectionIndex) {
  const res = await fetch(`${API_BASE}/api/analyze/3d`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ detection_index: detectionIndex }),
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ error: 'Network error' }));
    throw new Error(error.error || `HTTP ${res.status}`);
  }

  return res.json();
}
