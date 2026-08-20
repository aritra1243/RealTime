// =============================================================================
// PotholeVision — 3D Viewer Component
// =============================================================================
// Interactive Plotly.js 3D surface plot of pothole depth topography.

import { useState, useEffect } from 'react';
import { get3DMesh } from '../api/client';

export default function ThreeDViewer({ detections }) {
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [meshData, setMeshData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [Plot, setPlot] = useState(null);

  // Dynamically import react-plotly.js (heavy dep, lazy load)
  useEffect(() => {
    import('react-plotly.js').then((mod) => {
      setPlot(() => mod.default);
    }).catch(() => {
      setError('Could not load 3D viewer library.');
    });
  }, []);

  // Load 3D mesh when selection changes
  useEffect(() => {
    if (!detections || detections.length === 0) return;

    setLoading(true);
    setError(null);

    get3DMesh(selectedIndex)
      .then((data) => {
        if (data.success) {
          setMeshData(data);
        } else {
          setError(data.error || 'Failed to load 3D data.');
        }
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [selectedIndex, detections]);

  if (!detections || detections.length === 0) return null;

  const selectedDet = detections[selectedIndex];

  return (
    <div className="viewer-3d" id="viewer-3d">
      <div className="viewer-3d-header">
        <h2 className="viewer-3d-title">
          🌐 Interactive 3D Pothole Blueprint
        </h2>

        <select
          className="viewer-3d-select"
          id="pothole-select"
          value={selectedIndex}
          onChange={(e) => setSelectedIndex(parseInt(e.target.value))}
        >
          {detections.map((det, i) => (
            <option key={i} value={i}>
              Pothole #{det.id} — {det.severity} ({det.dimensions.width_m}×{det.dimensions.height_m}m)
            </option>
          ))}
        </select>
      </div>

      <div className="viewer-3d-body">
        {loading && (
          <div className="empty-state">
            <div className="loading-spinner lg"></div>
            <p className="loading-text">Loading 3D surface mesh...</p>
          </div>
        )}

        {error && (
          <div className="empty-state">
            <div className="empty-state-icon">⚠️</div>
            <p className="empty-state-text">{error}</p>
          </div>
        )}

        {!loading && !error && meshData && Plot && (
          <Plot
            data={[
              {
                type: 'surface',
                x: meshData.surface.x,
                y: meshData.surface.y,
                z: meshData.surface.z,
                colorscale: 'Inferno',
                colorbar: { title: 'Depth (m)', titlefont: { color: '#8b95a5' }, tickfont: { color: '#8b95a5' } },
                contours: {
                  z: { show: true, usecolormap: true, highlightcolor: '#00e5ff', project: { z: true } },
                },
              },
            ]}
            layout={{
              title: {
                text: `3D Surface Topography — ${selectedDet?.severity || ''} Pothole`,
                font: { color: '#e8eaed', size: 14, family: 'Inter, sans-serif' },
              },
              scene: {
                xaxis: { title: 'Width (m)', color: '#5a6577', gridcolor: '#2a3042' },
                yaxis: { title: 'Length (m)', color: '#5a6577', gridcolor: '#2a3042' },
                zaxis: { title: 'Depression (m)', color: '#5a6577', gridcolor: '#2a3042' },
                aspectmode: 'data',
                camera: { eye: { x: 1.5, y: -1.5, z: 1.2 } },
                bgcolor: '#111827',
              },
              paper_bgcolor: 'transparent',
              plot_bgcolor: 'transparent',
              margin: { l: 0, r: 0, b: 0, t: 40 },
              autosize: true,
              height: 420,
            }}
            config={{
              displayModeBar: true,
              displaylogo: false,
              modeBarButtonsToRemove: ['toImage'],
              responsive: true,
            }}
            style={{ width: '100%', height: '420px' }}
            useResizeHandler
          />
        )}

        {!loading && !error && !meshData && (
          <div className="empty-state">
            <div className="empty-state-icon">📊</div>
            <p className="empty-state-text">
              Select a pothole above to generate interactive 3D surface mesh.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
