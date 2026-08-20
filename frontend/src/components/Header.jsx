// =============================================================================
// PotholeVision — Header Component
// =============================================================================

export default function Header() {
  return (
    <header className="header app-header" id="app-header">
      <div className="header-brand">
        <span className="header-logo">🕳️ PotholeVision</span>
        <span className="header-tagline">
          Real-Time Computer Vision Road Defect &amp; Depth Analysis
        </span>
      </div>
      <div className="header-status">
        <span className="status-dot"></span>
        <span>System Online</span>
      </div>
    </header>
  );
}
