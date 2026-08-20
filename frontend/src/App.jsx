// =============================================================================
// PotholeVision — Main App Component
// =============================================================================
// Full dashboard: live mobile road camera feed, image uploader,
// real-time metrics, detection overlays, 3D topography viewer, and audit report.

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

  // ── Render ───────────────────────────────────────────────

  const hasResults = metrics && detections && images;

  return (
    <div className="app-layout" id="app">
      <Header />

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

      <main className="app-main" id="main-content">
        {/* Mode Switcher Tabs */}
        <div className="mode-tabs">
          <button
            className={`mode-tab ${activeMode === 'camera' ? 'active' : ''}`}
            onClick={() => setActiveMode('camera')}
          >
            🎥 Live Road Camera Feed
          </button>
          <button
            className={`mode-tab ${activeMode === 'upload' ? 'active' : ''}`}
            onClick={() => setActiveMode('upload')}
          >
            📁 Upload Image
          </button>
        </div>

        {/* Backend offline warning banner if needed */}
        {backendOnline === false && (
          <div
            style={{
              margin: 'var(--space-sm) 0 var(--space-md)',
              padding: 'var(--space-sm) var(--space-md)',
              background: 'rgba(255, 152, 0, 0.12)',
              border: '1px solid rgba(255, 152, 0, 0.4)',
              borderRadius: 'var(--radius-md)',
              color: 'var(--color-warning)',
              fontSize: '0.82rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <span>
              ⚠️ Backend is starting or warming up. First request may take ~10-20 seconds.
            </span>
            <button
              className="btn btn-sm"
              onClick={() => {
                checkHealth()
                  .then(() => setBackendOnline(true))
                  .catch(() => setBackendOnline(false));
              }}
            >
              🔄 Retry Connection
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

        {/* Error Banner */}
        {error && (
          <div
            style={{
              margin: 'var(--space-md) 0',
              padding: 'var(--space-md) var(--space-lg)',
              background: 'rgba(244, 67, 54, 0.12)',
              border: '1px solid rgba(244, 67, 54, 0.35)',
              borderRadius: 'var(--radius-md)',
              color: 'var(--color-danger)',
              fontSize: '0.85rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
            id="error-banner"
          >
            <span>⚠️ {error}</span>
            <button
              style={{
                background: 'transparent',
                border: 'none',
                color: 'var(--color-danger)',
                cursor: 'pointer',
                fontSize: '1rem',
              }}
              onClick={() => setError(null)}
            >
              ✕
            </button>
          </div>
        )}

        {/* Results */}
        {hasResults && (
          <>
            {/* Metrics Bar */}
            <MetricsPanel metrics={metrics} />

            {/* Detection Images */}
            <DetectionView
              images={images}
              showHeatmap={showHeatmap}
              showBlueprint={showBlueprint}
            />

            {/* 3D Viewer */}
            <ThreeDViewer detections={detections} />

            {/* Audit Table */}
            <AuditTable detections={detections} />
          </>
        )}

        {/* Empty state when no results & upload mode */}
        {!hasResults && !isLoading && !error && activeMode === 'upload' && (
          <div className="empty-state" style={{ marginTop: 'var(--space-2xl)' }}>
            <div className="empty-state-icon">🕳️</div>
            <p className="empty-state-text">
              Upload a road image or click <strong>"Analyze Sample Image"</strong> in
              the sidebar to start pothole detection and depth analysis.
            </p>
          </div>
        )}
      </main>
    </div>
  );
}
