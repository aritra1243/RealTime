// =============================================================================
// PotholeVision — Gradio 5 ZeroGPU Client
// =============================================================================
// Seamlessly communicates with Hugging Face Gradio 5 ZeroGPU backend.

const API_BASE = import.meta.env.VITE_API_URL || 'https://ari1324-potholevision-api.hf.space';

/**
 * Helper to call Gradio 5 named API endpoints (/gradio_api/call/<api_name>).
 */
async function callGradioApi(apiName, dataArray) {
  const url = `${API_BASE}/gradio_api/call/${apiName}`;
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ data: dataArray }),
  });

  if (!res.ok) {
    const errText = await res.text().catch(() => '');
    throw new Error(`API error ${res.status}: ${errText || 'Inference request failed'}`);
  }

  const { event_id } = await res.json();
  if (!event_id) {
    throw new Error('No event_id returned from backend.');
  }

  // Fetch the SSE result from /gradio_api/call/<api_name>/<event_id>
  const eventRes = await fetch(`${url}/${event_id}`);
  if (!eventRes.ok) {
    throw new Error(`Inference stream error ${eventRes.status}`);
  }

  const eventText = await eventRes.text();

  // Find SSE data: [...] line
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

  throw new Error('Inference server returned empty result.');
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
 * Upload an image file and run the full detection + depth pipeline.
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
 * Analyze a live video / camera frame (base64 string).
 */
export async function analyzeFrame(base64Image) {
  return await callGradioApi('analyze', [base64Image]);
}

/**
 * Analyze the built-in sample image.
 */
export async function analyzeSample() {
  return await callGradioApi('sample', []);
}

/**
 * Get 3D surface mesh data for a specific detection.
 */
export async function get3DMesh(detectionIndex) {
  return await callGradioApi('analyze_3d', [String(detectionIndex)]);
}
