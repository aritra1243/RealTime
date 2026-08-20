// =============================================================================
// PotholeVision — Monochrome Interactive 3D Surface Topography Viewer
// =============================================================================

import { useState, useEffect } from 'react';
import { Box, RefreshCw, AlertTriangle, Layers } from 'lucide-react';
import { get3DMesh } from '../api/client';

export default function ThreeDViewer({ detections }) {
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [meshData, setMeshData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [Plot, setPlot] = useState(null);

  // Lazy load Plotly.js
  useEffect(() => {
    import('react-plotly.js')
      .then((mod) => {
        setPlot(() => mod.default);
      })
      .catch(() => {
        setError('Could not load 3D visualizer library.');
      });
  }, []);

  // Load 3D mesh on select
  useEffect(() => {
    if (!detections || detections.length === 0) return;

    setLoading(true);
    setError(null);

    get3DMesh(selectedIndex)
      .then((data) => {
        if (data.success) {
          setMeshData(data);
        } else {
          setError(data.error || 'Failed to load 3D topography.');
        }
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [selectedIndex, detections]);

  if (!detections || detections.length === 0) return null;

  const selectedDet = detections[selectedIndex];

  return (
    <div className="space-y-4">
      
      {/* ─── Header ────────────────────────────────────────────────────────── */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 pb-3">
        <div className="flex items-center gap-2">
          <Box className="h-4 w-4 text-white" />
          <h2 className="text-sm font-bold uppercase tracking-wider text-white font-mono">
            3D Volumetric Mesh &amp; Surface Topography
          </h2>
        </div>

        {/* Pothole Defect Selector Dropdown */}
        <div className="flex items-center gap-2">
          <label htmlFor="defect-select" className="text-xs font-mono text-zinc-400">
            INSPECT DEFECT:
          </label>
          <select
            id="defect-select"
            value={selectedIndex}
            onChange={(e) => setSelectedIndex(parseInt(e.target.value))}
            className="rounded-xl border border-white/20 bg-zinc-900 px-3 py-1.5 text-xs font-mono font-bold text-white shadow-inner focus:border-white focus:outline-none cursor-pointer"
          >
            {detections.map((det, i) => (
              <option key={i} value={i} className="bg-zinc-950 text-white">
                Defect #{det.id} — {det.severity} ({det.dimensions.width_m}m × {det.dimensions.height_m}m)
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* ─── 3D Viewport ───────────────────────────────────────────────────── */}
      <div className="relative aspect-[16/9] md:aspect-[21/9] min-h-[380px] w-full overflow-hidden rounded-3xl border border-white/10 bg-zinc-950 p-2 shadow-2xl">
        
        {/* Reticles */}
        <div className="hud-corner-tl opacity-30"></div>
        <div className="hud-corner-tr opacity-30"></div>
        <div className="hud-corner-bl opacity-30"></div>
        <div className="hud-corner-br opacity-30"></div>

        {loading && (
          <div className="flex h-full w-full flex-col items-center justify-center gap-3">
            <RefreshCw className="h-8 w-8 animate-spin text-white" />
            <p className="text-xs font-mono uppercase tracking-wider text-zinc-400">
              Generating 3D Surface Deposition Matrix...
            </p>
          </div>
        )}

        {error && (
          <div className="flex h-full w-full flex-col items-center justify-center gap-2 text-center p-6">
            <AlertTriangle className="h-8 w-8 text-zinc-400" />
            <p className="text-xs font-mono text-zinc-400">{error}</p>
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
                // Stark monochrome colorscale: Grayscale / Bone
                colorscale: 'Greys',
                reversescale: true,
                colorbar: {
                  title: 'Depth (m)',
                  titlefont: { color: '#a1a1aa', family: 'JetBrains Mono' },
                  tickfont: { color: '#a1a1aa', family: 'JetBrains Mono' },
                  len: 0.7,
                  thickness: 14,
                },
                contours: {
                  z: {
                    show: true,
                    usecolormap: true,
                    highlightcolor: '#ffffff',
                    project: { z: true },
                  },
                },
              },
            ]}
            layout={{
              autosize: true,
              paper_bgcolor: 'transparent',
              plot_bgcolor: 'transparent',
              margin: { l: 0, r: 0, b: 0, t: 10 },
              scene: {
                xaxis: {
                  title: 'Width (m)',
                  color: '#71717a',
                  gridcolor: '#27272a',
                  tickfont: { family: 'JetBrains Mono', size: 10 },
                },
                yaxis: {
                  title: 'Length (m)',
                  color: '#71717a',
                  gridcolor: '#27272a',
                  tickfont: { family: 'JetBrains Mono', size: 10 },
                },
                zaxis: {
                  title: 'Depth (m)',
                  color: '#71717a',
                  gridcolor: '#27272a',
                  tickfont: { family: 'JetBrains Mono', size: 10 },
                },
                aspectmode: 'data',
                camera: {
                  eye: { x: 1.4, y: -1.4, z: 1.1 },
                },
                bgcolor: '#09090b',
              },
            }}
            config={{
              displayModeBar: true,
              displaylogo: false,
              modeBarButtonsToRemove: ['toImage', 'hoverClosest3d'],
              responsive: true,
            }}
            style={{ width: '100%', height: '100%', minHeight: '360px' }}
            useResizeHandler
          />
        )}

      </div>

    </div>
  );
}
