// =============================================================================
// PotholeVision — High-Performance ZeroGPU Client
// =============================================================================

const API_BASE = import.meta.env.VITE_API_URL || 'https://ari1324-potholevision-api.hf.space';

/**
 * Call Gradio 5 SSE endpoint (/gradio_api/call/<api_name>).
 */
async function callGradioApi(apiName, dataArray, signal) {
  const url = `${API_BASE}/gradio_api/call/${apiName}`;
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ data: dataArray }),
    signal,
  });

  if (!res.ok) {
    const errText = await res.text().catch(() => '');
    throw new Error(`API ${res.status}: ${errText || 'Inference failed'}`);
  }

  const { event_id } = await res.json();
  if (!event_id) {
    throw new Error('No event_id from inference backend.');
  }

  const eventRes = await fetch(`${url}/${event_id}`, { signal });
  if (!eventRes.ok) {
    throw new Error(`Stream error ${eventRes.status}`);
  }

  const eventText = await eventRes.text();

  for (const line of eventText.split('\n')) {
    if (line.startsWith('data:')) {
      const jsonStr = line.slice(5).trim();
      if (jsonStr && jsonStr !== 'null') {
        const parsed = JSON.parse(jsonStr);
        if (Array.isArray(parsed) && parsed.length > 0) {
          const item = parsed[0];
          return typeof item === 'string' ? JSON.parse(item) : item;
        }
        return typeof parsed === 'string' ? JSON.parse(parsed) : parsed;
      }
    }
  }

  throw new Error('Empty inference response.');
}

/**
 * Check backend health.
 */
export async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE}/config`, {
      headers: { Accept: 'application/json' },
    });
    if (!res.ok) throw new Error(`Backend returned status ${res.status}`);
    return { status: 'ok' };
  } catch (err) {
    throw new Error(`Cannot connect to backend (${API_BASE}). Check if server is running.`);
  }
}

/**
 * High-Speed Real-Time Video Frame Streamer.
 */
export async function analyzeFrameFast(base64Image, signal) {
  return await callGradioApi('analyze_fast', [base64Image], signal);
}

/**
 * Full-Fidelity Image Upload Analysis (includes CAD Blueprint & Heatmap).
 */
export async function analyzeImage(imageFile) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = async () => {
      try {
        const base64Data = reader.result;
        const result = await callGradioApi('analyze', [base64Data]);
        resolve(result);
      } catch (err) {
        reject(err);
      }
    };
    reader.onerror = () => reject(new Error('Failed to read image file'));
    reader.readAsDataURL(imageFile);
  });
}

/**
 * Analyze a video frame with full pipeline.
 */
export async function analyzeFrame(base64Image) {
  return await callGradioApi('analyze', [base64Image]);
}

/**
 * Analyze built-in sample image.
 */
export async function analyzeSample() {
  return await callGradioApi('sample', []);
}

/**
 * Get 3D surface mesh for a detection.
 */
export async function get3DMesh(detectionIndex) {
  return await callGradioApi('analyze_3d', [String(detectionIndex)]);
}
