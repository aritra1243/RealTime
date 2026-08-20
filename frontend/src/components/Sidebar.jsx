// =============================================================================
// PotholeVision — Sidebar Component
// =============================================================================

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
    <aside className="sidebar app-sidebar" id="sidebar">
      {/* Config Section */}
      <div className="sidebar-section">
        <div className="sidebar-title">⚙️ Configuration</div>

        {/* Confidence Threshold */}
        <div>
          <label className="sidebar-label" htmlFor="confidence-slider">
            Detection Confidence
          </label>
          <input
            id="confidence-slider"
            className="sidebar-slider"
            type="range"
            min="0.1"
            max="1.0"
            step="0.05"
            value={confidence}
            onChange={(e) => onConfidenceChange(parseFloat(e.target.value))}
          />
          <div className="sidebar-value">{confidence.toFixed(2)}</div>
        </div>
      </div>

      {/* Display Toggles */}
      <div className="sidebar-section">
        <div className="sidebar-title">🎨 Display Options</div>

        <div className="toggle-row">
          <span className="toggle-label">Depth Heatmap</span>
          <label className="toggle-switch" id="toggle-heatmap">
            <input
              type="checkbox"
              checked={showHeatmap}
              onChange={onToggleHeatmap}
            />
            <span className="toggle-track"></span>
          </label>
        </div>

        <div className="toggle-row">
          <span className="toggle-label">Blueprint Panel</span>
          <label className="toggle-switch" id="toggle-blueprint">
            <input
              type="checkbox"
              checked={showBlueprint}
              onChange={onToggleBlueprint}
            />
            <span className="toggle-track"></span>
          </label>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="sidebar-section">
        <div className="sidebar-title">🚀 Quick Actions</div>
        <button
          className="btn btn-primary btn-block"
          id="btn-sample"
          onClick={onAnalyzeSample}
          disabled={isLoading}
        >
          {isLoading ? (
            <>
              <span className="loading-spinner"></span>
              Analyzing...
            </>
          ) : (
            '🔍 Analyze Sample Image'
          )}
        </button>
      </div>

      {/* Info */}
      <div className="sidebar-section" style={{ marginTop: 'auto' }}>
        <div className="sidebar-title">ℹ️ About</div>
        <p style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', lineHeight: 1.5 }}>
          PotholeVision uses YOLOv8 + MiDaS for real-time pothole detection with monocular
          depth estimation and 3D surface reconstruction.
        </p>
      </div>
    </aside>
  );
}
