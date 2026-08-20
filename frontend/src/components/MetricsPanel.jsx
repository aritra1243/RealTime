// =============================================================================
// PotholeVision — Metrics Panel Component
// =============================================================================

export default function MetricsPanel({ metrics }) {
  if (!metrics) return null;

  const severityClass = (status) => {
    const s = status?.toLowerCase();
    if (s === 'critical') return 'severity-critical';
    if (s === 'moderate') return 'severity-moderate';
    if (s === 'shallow') return 'severity-shallow';
    return 'severity-clear';
  };

  const cards = [
    {
      id: 'metric-status',
      label: 'Road Status',
      value: metrics.road_status || 'CLEAR',
      className: severityClass(metrics.road_status),
    },
    {
      id: 'metric-count',
      label: 'Potholes Detected',
      value: metrics.pothole_count ?? 0,
    },
    {
      id: 'metric-depth',
      label: 'Max Defect Depth',
      value: metrics.max_depth?.toFixed(4) ?? '0.0000',
      unit: 'rel units',
    },
    {
      id: 'metric-volume',
      label: 'Total Defect Volume',
      value: metrics.total_volume?.toFixed(1) ?? '0.0',
      unit: 'vol units',
    },
    {
      id: 'metric-latency',
      label: 'Latency',
      value: metrics.latency_ms?.toFixed(1) ?? '0.0',
      unit: 'ms',
    },
  ];

  return (
    <div className="metrics-grid" id="metrics-panel">
      {cards.map((card) => (
        <div key={card.id} className="metric-card" id={card.id}>
          <div className="metric-label">{card.label}</div>
          <div className={`metric-value ${card.className || ''}`}>
            {card.value}
          </div>
          {card.unit && <div className="metric-unit">{card.unit}</div>}
        </div>
      ))}
    </div>
  );
}
