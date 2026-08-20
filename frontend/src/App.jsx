// =============================================================================
// PotholeVision — Main App Dashboard (Monochrome Edition)
// =============================================================================

import { useState, useCallback, useEffect } from 'react';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import ImageUploader from './components/ImageUploader';
import LiveCamera from './components/LiveCamera';
import MetricsPanel from './components/MetricsPanel';
import DetectionView from './components/DetectionView';
import ThreeDViewer from './components/ThreeDViewer';
import AuditTable from './components/AuditTable';
import { analyzeImage, analyzeSample, checkHealth } from './api/client';
import { Camera, Upload, AlertCircle, RefreshCw, Layers, ShieldCheck, Sparkles } from 'lucide-react';

export default function App() {
  // ── Mode: 'camera' (Live Road Vision) or 'upload' (Single Image) ──
  const [activeMode, setActiveMode] = useState('camera');

  // ── State ────────────────────────────────────────────────
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [backendOnline, setBackendOnline] = useState(null);

  // Analysis results
  const [metrics, setMetrics] = useState(null);
  const [detections, setDetections] = useState(null);
  const [images, setImages] = useState(null);

  // Sidebar settings
  const [confidence, setConfidence] = useState(0.35);
  const [showHeatmap, setShowHeatmap] = useState(true);
  const [showBlueprint, setShowBlueprint] = useState(true);

  // ── Initial Health Check ─────────────────────────────────
  useEffect(() => {
    checkHealth()
      .then(() => setBackendOnline(true))
      .catch((err) => {
        console.warn('Backend health check failed:', err);
        setBackendOnline(false);
      });
  }, []);

  // ── Handlers ─────────────────────────────────────────────
  const handleAnalysisResult = useCallback((data) => {
    if (data.success) {
      setMetrics(data.metrics);
      setDetections(data.detections);
      setImages(data.images);
      setError(null);
      setBackendOnline(true);
    } else {
      setError(data.error || 'Analysis failed.');
    }
  }, []);

  const handleUpload = useCallback(
    async (file) => {
      setIsLoading(true);
      setError(null);
      try {
        const result = await analyzeImage(file);
        handleAnalysisResult(result);
      } catch (err) {
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    },
    [handleAnalysisResult]
  );

  const handleAnalyzeSample = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await analyzeSample();
      handleAnalysisResult(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, [handleAnalysisResult]);

  const hasResults = metrics && detections && images;

  return (
    <div className="min-h-screen bg-black text-zinc-100 bg-grid-pattern flex flex-col selection:bg-white selection:text-black">
      
      {/* Tactical HUD Header */}
      <Header backendOnline={backendOnline} />

      {/* Main Content Area */}
      <div className="mx-auto flex w-full max-w-7xl flex-1 flex-col lg:flex-row gap-6 p-4 sm:p-6 lg:p-8">
        
        {/* Left Parameter Sidebar */}
        <Sidebar
          confidence={confidence}
          onConfidenceChange={setConfidence}
          showHeatmap={showHeatmap}
          onToggleHeatmap={() => setShowHeatmap((v) => !v)}
          showBlueprint={showBlueprint}
          onToggleBlueprint={() => setShowBlueprint((v) => !v)}
          onAnalyzeSample={handleAnalyzeSample}
          isLoading={isLoading}
        />

        {/* Center Main Dashboard */}
        <main className="flex-1 space-y-6 min-w-0">
          
          {/* Mode Switcher Tabs */}
          <div className="flex items-center gap-2 rounded-2xl border border-white/10 bg-zinc-950/80 p-1.5 backdrop-blur-xl shadow-lg">
            <button
              onClick={() => setActiveMode('camera')}
              className={`flex flex-1 items-center justify-center gap-2 rounded-xl py-3 text-xs font-bold font-mono uppercase tracking-wider transition-all cursor-pointer ${
                activeMode === 'camera'
                  ? 'bg-white text-black shadow-[0_0_20px_rgba(255,255,255,0.3)]'
                  : 'text-zinc-400 hover:text-white hover:bg-zinc-900/50'
              }`}
            >
              <Camera className="h-4 w-4" />
              <span>Live Road Camera Feed</span>
            </button>

            <button
              onClick={() => setActiveMode('upload')}
              className={`flex flex-1 items-center justify-center gap-2 rounded-xl py-3 text-xs font-bold font-mono uppercase tracking-wider transition-all cursor-pointer ${
                activeMode === 'upload'
                  ? 'bg-white text-black shadow-[0_0_20px_rgba(255,255,255,0.3)]'
                  : 'text-zinc-400 hover:text-white hover:bg-zinc-900/50'
              }`}
            >
              <Upload className="h-4 w-4" />
              <span>High-Res Road Image Upload</span>
            </button>
          </div>

          {/* Backend warming up notice */}
          {backendOnline === false && (
            <div className="flex items-center justify-between gap-3 rounded-2xl border border-white/20 bg-zinc-900/80 p-4 text-xs text-zinc-300 backdrop-blur-xl shadow-lg">
              <div className="flex items-center gap-2.5">
                <RefreshCw className="h-4 w-4 animate-spin text-white flex-shrink-0" />
                <span>
                  <strong>Hugging Face ZeroGPU Backend:</strong> Server may take ~10-20 seconds on initial cold start.
                </span>
              </div>
              <button
                onClick={() => {
                  checkHealth()
                    .then(() => setBackendOnline(true))
                    .catch(() => setBackendOnline(false));
                }}
                className="rounded-lg border border-white/20 bg-black px-3 py-1 text-xs font-mono font-bold text-white hover:bg-zinc-800 transition-all cursor-pointer"
              >
                Retry Status
              </button>
            </div>
          )}

          {/* Error Banner */}
          {error && (
            <div className="flex items-center justify-between gap-3 rounded-2xl border border-white/40 bg-zinc-900 p-4 text-xs font-mono text-white shadow-xl">
              <div className="flex items-center gap-2.5">
                <AlertCircle className="h-4 w-4 text-white flex-shrink-0" />
                <span>{error}</span>
              </div>
              <button
                onClick={() => setError(null)}
                className="rounded-lg p-1 text-zinc-400 hover:bg-zinc-800 hover:text-white"
              >
                ✕
              </button>
            </div>
          )}

          {/* Camera or Uploader Component based on Active Mode */}
          {activeMode === 'camera' ? (
            <LiveCamera
              onAnalysisResult={handleAnalysisResult}
              onError={(errMsg) => setError(errMsg)}
              isAnalyzingGlobal={isLoading}
            />
          ) : (
            <ImageUploader onUpload={handleUpload} isLoading={isLoading} />
          )}

          {/* Results Sections */}
          {hasResults && (
            <div className="space-y-6 pt-2">
              
              {/* 1. HUD Telemetry Metrics Panel */}
              <MetricsPanel metrics={metrics} />

              {/* 2. Visual Overlays (Annotated, CAD Blueprint, Heatmap) */}
              <DetectionView
                images={images}
                showHeatmap={showHeatmap}
                showBlueprint={showBlueprint}
              />

              {/* 3. Interactive 3D Surface Topography */}
              <ThreeDViewer detections={detections} />

              {/* 4. Structured Defect Audit Table */}
              <AuditTable detections={detections} />

            </div>
          )}

          {/* Empty state when no results & upload mode */}
          {!hasResults && !isLoading && !error && activeMode === 'upload' && (
            <div className="flex min-h-[180px] flex-col items-center justify-center rounded-3xl border border-white/10 bg-zinc-950/60 p-8 text-center backdrop-blur-xl">
              <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-xl border border-white/10 bg-zinc-900">
                <Layers className="h-6 w-6 text-white" />
              </div>
              <p className="text-xs text-zinc-400 max-w-sm">
                Upload a road photograph or click <strong className="text-white">"Test Sample Road Image"</strong> in the sidebar to view automated pothole segmentation and 3D depth maps.
              </p>
            </div>
          )}

        </main>

      </div>

      {/* Footer */}
      <footer className="mt-auto border-t border-white/10 bg-black/90 py-4 text-center text-[11px] font-mono text-zinc-500">
        <span>POTHOLEVISION AI &copy; 2026 &mdash; MONOCULAR DEPTH ESTIMATION &amp; INFRASTRUCTURE AUDIT</span>
      </footer>

    </div>
  );
}
