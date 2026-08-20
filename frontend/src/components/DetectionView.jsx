// =============================================================================
// PotholeVision — Monochrome Detection View Component
// =============================================================================

import { useState } from 'react';
import { Eye, Layers, Compass, Maximize2, Download, X } from 'lucide-react';

export default function DetectionView({ images, showHeatmap, showBlueprint }) {
  const [activeModalImg, setActiveModalImg] = useState(null);

  if (!images) return null;

  const { annotated, blueprint, heatmap } = images;
  const showHeatmapPanel = showHeatmap && heatmap;
  const showBlueprintPanel = showBlueprint && blueprint;

  const downloadImage = (b64, name) => {
    const link = document.createElement('a');
    link.href = `data:image/jpeg;base64,${b64}`;
    link.download = `${name}_potholevision.jpg`;
    link.click();
  };

  return (
    <div className="space-y-4">
      
      {/* Section Title */}
      <div className="flex items-center justify-between border-b border-white/10 pb-2.5">
        <div className="flex items-center gap-2">
          <Eye className="h-4 w-4 text-white" />
          <h2 className="text-sm font-bold uppercase tracking-wider text-white font-mono">
            Optical Analysis &amp; CAD Reconstruction
          </h2>
        </div>
        <span className="text-[11px] font-mono text-zinc-500">
          RESOLUTION: 1280×720 AI OVERLAY
        </span>
      </div>

      {/* Grid of Panels */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        
        {/* 1. Annotated Optical Overlay */}
        {annotated && (
          <div className="group relative flex flex-col overflow-hidden rounded-2xl border border-white/10 bg-zinc-950/80 backdrop-blur-xl shadow-xl hover:border-white/30 transition-all">
            <div className="flex items-center justify-between border-b border-white/10 bg-zinc-900/60 px-4 py-2.5">
              <span className="text-xs font-semibold text-white flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-white"></span>
                Annotated Overlay
              </span>
              <div className="flex items-center gap-1.5 opacity-80 group-hover:opacity-100 transition-opacity">
                <button
                  onClick={() => setActiveModalImg({ b64: annotated, title: 'Annotated Overlay' })}
                  className="rounded p-1 text-zinc-400 hover:bg-zinc-800 hover:text-white"
                  title="Expand"
                >
                  <Maximize2 className="h-3.5 w-3.5" />
                </button>
                <button
                  onClick={() => downloadImage(annotated, 'annotated_overlay')}
                  className="rounded p-1 text-zinc-400 hover:bg-zinc-800 hover:text-white"
                  title="Download"
                >
                  <Download className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>

            <div className="relative aspect-video w-full overflow-hidden bg-black flex items-center justify-center">
              <img
                src={`data:image/jpeg;base64,${annotated}`}
                alt="Detection Overlay"
                className="h-full w-full object-contain"
              />
            </div>
          </div>
        )}

        {/* 2. Blueprint CAD Analysis */}
        {showBlueprintPanel && (
          <div className="group relative flex flex-col overflow-hidden rounded-2xl border border-white/10 bg-zinc-950/80 backdrop-blur-xl shadow-xl hover:border-white/30 transition-all">
            <div className="flex items-center justify-between border-b border-white/10 bg-zinc-900/60 px-4 py-2.5">
              <span className="text-xs font-semibold text-white flex items-center gap-1.5">
                <Compass className="h-3.5 w-3.5 text-zinc-300" />
                2D CAD Technical Blueprint
              </span>
              <div className="flex items-center gap-1.5 opacity-80 group-hover:opacity-100 transition-opacity">
                <button
                  onClick={() => setActiveModalImg({ b64: blueprint, title: 'CAD Blueprint' })}
                  className="rounded p-1 text-zinc-400 hover:bg-zinc-800 hover:text-white"
                  title="Expand"
                >
                  <Maximize2 className="h-3.5 w-3.5" />
                </button>
                <button
                  onClick={() => downloadImage(blueprint, 'blueprint_cad')}
                  className="rounded p-1 text-zinc-400 hover:bg-zinc-800 hover:text-white"
                  title="Download"
                >
                  <Download className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>

            <div className="relative aspect-video w-full overflow-hidden bg-black flex items-center justify-center">
              <img
                src={`data:image/jpeg;base64,${blueprint}`}
                alt="CAD Blueprint"
                className="h-full w-full object-contain"
              />
            </div>
          </div>
        )}

        {/* 3. Monocular Depth Heatmap */}
        {showHeatmapPanel && (
          <div className="group relative flex flex-col overflow-hidden rounded-2xl border border-white/10 bg-zinc-950/80 backdrop-blur-xl shadow-xl hover:border-white/30 transition-all">
            <div className="flex items-center justify-between border-b border-white/10 bg-zinc-900/60 px-4 py-2.5">
              <span className="text-xs font-semibold text-white flex items-center gap-1.5">
                <Layers className="h-3.5 w-3.5 text-zinc-300" />
                Monocular Depth Map
              </span>
              <div className="flex items-center gap-1.5 opacity-80 group-hover:opacity-100 transition-opacity">
                <button
                  onClick={() => setActiveModalImg({ b64: heatmap, title: 'Depth Heatmap' })}
                  className="rounded p-1 text-zinc-400 hover:bg-zinc-800 hover:text-white"
                  title="Expand"
                >
                  <Maximize2 className="h-3.5 w-3.5" />
                </button>
                <button
                  onClick={() => downloadImage(heatmap, 'depth_heatmap')}
                  className="rounded p-1 text-zinc-400 hover:bg-zinc-800 hover:text-white"
                  title="Download"
                >
                  <Download className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>

            <div className="relative aspect-video w-full overflow-hidden bg-black flex items-center justify-center">
              <img
                src={`data:image/jpeg;base64,${heatmap}`}
                alt="Depth Heatmap"
                className="h-full w-full object-contain"
              />
            </div>
          </div>
        )}

      </div>

      {/* Fullscreen Lightbox Modal */}
      {activeModalImg && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 p-4 backdrop-blur-md">
          <div className="relative max-h-[90vh] max-w-5xl overflow-hidden rounded-2xl border border-white/20 bg-zinc-950 p-2 shadow-2xl">
            <div className="flex items-center justify-between p-3 border-b border-white/10">
              <h3 className="text-sm font-mono font-bold text-white uppercase">
                {activeModalImg.title}
              </h3>
              <button
                onClick={() => setActiveModalImg(null)}
                className="rounded-lg p-1.5 text-zinc-400 hover:bg-zinc-800 hover:text-white"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <img
              src={`data:image/jpeg;base64,${activeModalImg.b64}`}
              alt={activeModalImg.title}
              className="max-h-[75vh] w-auto mx-auto object-contain py-2"
            />
          </div>
        </div>
      )}

    </div>
  );
}
