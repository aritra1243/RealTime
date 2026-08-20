// =============================================================================
// PotholeVision — Main App Component
// =============================================================================
// Orchestrates the full dashboard: sidebar, image upload, metrics,
// detection view, 3D viewer, and audit table.

import { useState, useCallback } from 'react';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import ImageUploader from './components/ImageUploader';
import MetricsPanel from './components/MetricsPanel';
import DetectionView from './components/DetectionView';
import ThreeDViewer from './components/ThreeDViewer';
import AuditTable from './components/AuditTable';
import { analyzeImage, analyzeSample } from './api/client';

export default function App() {
  // ── State ────────────────────────────────────────────────
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Analysis results
  const [metrics, setMetrics] = useState(null);
  const [detections, setDetections] = useState(null);
  const [images, setImages] = useState(null);

  // Sidebar settings
  const [confidence, setConfidence] = useState(0.35);
  const [showHeatmap, setShowHeatmap] = useState(true);
  const [showBlueprint, setShowBlueprint] = useState(true);

  // ── Handlers ─────────────────────────────────────────────

  const handleAnalysisResult = useCallback((data) => {
    if (data.success) {
      setMetrics(data.metrics);
      setDetections(data.detections);
      setImages(data.images);
      setError(null);
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
        {/* Upload Section */}
        <ImageUploader onUpload={handleUpload} isLoading={isLoading} />

        {/* Error Banner */}
        {error && (
          <div
            style={{
              margin: 'var(--space-md) 0',
              padding: 'var(--space-md) var(--space-lg)',
              background: 'rgba(244, 67, 54, 0.1)',
              border: '1px solid rgba(244, 67, 54, 0.3)',
              borderRadius: 'var(--radius-md)',
              color: 'var(--color-danger)',
              fontSize: '0.85rem',
            }}
            id="error-banner"
          >
            ⚠️ {error}
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

        {/* Empty state when no results */}
        {!hasResults && !isLoading && !error && (
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
