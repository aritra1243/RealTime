// =============================================================================
// PotholeVision — Detection View Component
// =============================================================================
// Displays annotated image, blueprint panel, and depth heatmap.

export default function DetectionView({
  images,
  showHeatmap,
  showBlueprint,
}) {
  if (!images) return null;

  const { annotated, blueprint, heatmap } = images;

  // Determine how many panels to show
  const showHeatmapPanel = showHeatmap && heatmap;
  const showBlueprintPanel = showBlueprint && blueprint;

  // If only annotated, use single column
  const hasExtra = showHeatmapPanel || showBlueprintPanel;

  return (
    <div>
      <div className="section-title">
        <span className="icon">🎯</span>
        Detection Results
      </div>

      <div className={`detection-view ${!hasExtra ? 'single' : ''}`} id="detection-view">
        {/* Annotated Image */}
        <div className="image-panel" id="panel-annotated">
          <div className="image-panel-header">
            <span>🖼️ Annotated Detection Overlay</span>
          </div>
          <img
            src={`data:image/jpeg;base64,${annotated}`}
            alt="Pothole detection overlay with bounding boxes and severity labels"
          />
        </div>

        {/* Blueprint or Heatmap */}
        {showBlueprintPanel && (
          <div className="image-panel" id="panel-blueprint">
            <div className="image-panel-header">
              <span>📐 Blueprint Analysis</span>
            </div>
            <img
              src={`data:image/jpeg;base64,${blueprint}`}
              alt="2D CAD blueprint panel with top-down view, cross-section, and depth heatmap"
            />
          </div>
        )}

        {showHeatmapPanel && !showBlueprintPanel && (
          <div className="image-panel" id="panel-heatmap">
            <div className="image-panel-header">
              <span>🌡️ Depth Heatmap</span>
            </div>
            <img
              src={`data:image/jpeg;base64,${heatmap}`}
              alt="Monocular depth estimation heatmap"
            />
          </div>
        )}
      </div>

      {/* If both are enabled, show heatmap below */}
      {showHeatmapPanel && showBlueprintPanel && (
        <div className="detection-view single" style={{ marginTop: 'var(--space-md)' }}>
          <div className="image-panel" id="panel-heatmap">
            <div className="image-panel-header">
              <span>🌡️ Depth Heatmap</span>
            </div>
            <img
              src={`data:image/jpeg;base64,${heatmap}`}
              alt="Monocular depth estimation heatmap"
            />
          </div>
        </div>
      )}
    </div>
  );
}
