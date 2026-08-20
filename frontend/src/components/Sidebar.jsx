// =============================================================================
// PotholeVision — Monochrome Tactical Control Sidebar
// =============================================================================

import { Sliders, Layers, Sparkles, Cpu, Info, Check, RefreshCw } from 'lucide-react';

export default function Sidebar({
  confidence,
  onConfidenceChange,
  showHeatmap,
  onToggleHeatmap,
  showBlueprint,
  onToggleBlueprint,
  onAnalyzeSample,
  isLoading,
}) {
  return (
    <aside className="w-full lg:w-72 flex-shrink-0 flex flex-col gap-6 rounded-2xl border border-white/10 bg-zinc-950/80 p-5 backdrop-blur-xl shadow-2xl">
      
      {/* ─── Control Section Header ────────────────────────────────────────── */}
      <div className="flex items-center gap-2 border-b border-white/10 pb-3">
        <Sliders className="h-4 w-4 text-white" />
        <h2 className="text-xs font-bold uppercase tracking-widest text-zinc-300 font-mono">
          Vision Parameters
        </h2>
      </div>

      {/* ─── Confidence Slider ────────────────────────────────────────────── */}
      <div className="space-y-2.5">
        <div className="flex items-center justify-between text-xs">
          <label htmlFor="confidence-slider" className="font-medium text-zinc-300">
            Confidence Threshold
          </label>
          <span className="rounded border border-white/20 bg-zinc-900 px-2 py-0.5 font-mono text-xs font-bold text-white">
            {(confidence * 100).toFixed(0)}%
          </span>
        </div>

        <input
          id="confidence-slider"
          type="range"
          min="0.1"
          max="0.95"
          step="0.05"
          value={confidence}
          onChange={(e) => onConfidenceChange(parseFloat(e.target.value))}
          className="w-full h-1.5 bg-zinc-800 rounded-lg appearance-none cursor-pointer focus:outline-none"
        />
        
        <div className="flex justify-between text-[10px] font-mono text-zinc-500">
          <span>HIGH RECALL (10%)</span>
          <span>STRICT (95%)</span>
        </div>
      </div>

      {/* ─── Display Layers ───────────────────────────────────────────────── */}
      <div className="space-y-3">
        <div className="flex items-center gap-2 border-b border-white/10 pb-2">
          <Layers className="h-4 w-4 text-white" />
          <h3 className="text-xs font-bold uppercase tracking-widest text-zinc-300 font-mono">
            Inspection Layers
          </h3>
        </div>

        {/* Toggle Heatmap */}
        <div className="flex items-center justify-between rounded-xl border border-white/5 bg-zinc-900/50 p-3 hover:border-white/20 transition-all">
          <div className="space-y-0.5">
            <span className="text-xs font-semibold text-white">Depth Heatmap</span>
            <p className="text-[11px] text-zinc-400">Monocular depth gradients</p>
          </div>

          <button
            type="button"
            role="switch"
            aria-checked={showHeatmap}
            onClick={onToggleHeatmap}
            className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
              showHeatmap ? 'bg-white' : 'bg-zinc-800'
            }`}
          >
            <span
              className={`pointer-events-none inline-block h-5 w-5 transform rounded-full shadow-lg ring-0 transition duration-200 ease-in-out ${
                showHeatmap ? 'translate-x-5 bg-black' : 'translate-x-0 bg-zinc-400'
              }`}
            />
          </button>
        </div>

        {/* Toggle Blueprint */}
        <div className="flex items-center justify-between rounded-xl border border-white/5 bg-zinc-900/50 p-3 hover:border-white/20 transition-all">
          <div className="space-y-0.5">
            <span className="text-xs font-semibold text-white">CAD Blueprint</span>
            <p className="text-[11px] text-zinc-400">Cross-section &amp; 2D specs</p>
          </div>

          <button
            type="button"
            role="switch"
            aria-checked={showBlueprint}
            onClick={onToggleBlueprint}
            className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
              showBlueprint ? 'bg-white' : 'bg-zinc-800'
            }`}
          >
            <span
              className={`pointer-events-none inline-block h-5 w-5 transform rounded-full shadow-lg ring-0 transition duration-200 ease-in-out ${
                showBlueprint ? 'translate-x-5 bg-black' : 'translate-x-0 bg-zinc-400'
              }`}
            />
          </button>
        </div>
      </div>

      {/* ─── Quick Sample Action ─────────────────────────────────────────── */}
      <div className="space-y-2.5">
        <button
          onClick={onAnalyzeSample}
          disabled={isLoading}
          className="group relative flex w-full items-center justify-center gap-2 rounded-xl bg-white px-4 py-3 text-xs font-bold text-black shadow-[0_0_20px_rgba(255,255,255,0.2)] hover:bg-zinc-200 hover:shadow-[0_0_30px_rgba(255,255,255,0.4)] active:scale-[0.98] transition-all disabled:opacity-50 cursor-pointer"
        >
          {isLoading ? (
            <>
              <RefreshCw className="h-4 w-4 animate-spin text-black" />
              <span>Analyzing Surface...</span>
            </>
          ) : (
            <>
              <Sparkles className="h-4 w-4 text-black group-hover:rotate-12 transition-transform" />
              <span>Test Sample Road Image</span>
            </>
          )}
        </button>
      </div>

      {/* ─── AI Pipeline Architecture ─────────────────────────────────────── */}
      <div className="mt-auto rounded-xl border border-white/10 bg-zinc-900/40 p-3.5 text-xs text-zinc-400 space-y-2">
        <div className="flex items-center gap-1.5 font-bold text-zinc-200 font-mono">
          <Cpu className="h-3.5 w-3.5 text-white" />
          <span>EDGE ARCHITECTURE</span>
        </div>
        <ul className="space-y-1 text-[11px] text-zinc-400 font-mono">
          <li className="flex items-center gap-1.5">
            <Check className="h-3 w-3 text-white" /> YOLOv8 Segmentation
          </li>
          <li className="flex items-center gap-1.5">
            <Check className="h-3 w-3 text-white" /> MiDaS Monocular Depth
          </li>
          <li className="flex items-center gap-1.5">
            <Check className="h-3 w-3 text-white" /> 3D Surface Topography
          </li>
        </ul>
      </div>

    </aside>
  );
}
