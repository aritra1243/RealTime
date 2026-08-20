// =============================================================================
// PotholeVision — Audit Table Component
// =============================================================================
// Sortable defect audit table with CSV download.

import { useCallback } from 'react';

export default function AuditTable({ detections }) {
  const downloadCSV = useCallback(() => {
    if (!detections || detections.length === 0) return;

    const headers = [
      'ID', 'Severity', 'Confidence', 'Max Depth', 'Avg Depth',
      'Area (px)', 'Width (m)', 'Height (m)', 'Volume',
    ];

    const rows = detections.map((d) => [
      d.id,
      d.severity,
      (d.confidence * 100).toFixed(1) + '%',
      d.max_depth.toFixed(4),
      d.avg_depth.toFixed(4),
      d.area_px.toLocaleString(),
      d.dimensions.width_m,
      d.dimensions.height_m,
      d.volume.toFixed(1),
    ]);

    const csv = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);

    const link = document.createElement('a');
    link.href = url;
    link.download = 'pothole_audit_report.csv';
    link.click();

    URL.revokeObjectURL(url);
  }, [detections]);

  if (!detections || detections.length === 0) return null;

  const severityBadgeClass = (severity) => {
    const s = severity?.toLowerCase();
    if (s === 'critical') return 'critical';
    if (s === 'moderate') return 'moderate';
    return 'shallow';
  };

  return (
    <div className="audit-section" id="audit-table">
      <div className="audit-header">
        <h2 className="audit-title">
          📋 Defect Audit Table
        </h2>
        <button className="btn btn-sm" id="btn-download-csv" onClick={downloadCSV}>
          ⬇️ Download CSV
        </button>
      </div>

      <div className="audit-table-wrap">
        <table className="audit-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Severity</th>
              <th>Confidence</th>
              <th>Max Depth</th>
              <th>Avg Depth</th>
              <th>Area (px)</th>
              <th>Dimensions</th>
              <th>Volume</th>
            </tr>
          </thead>
          <tbody>
            {detections.map((det) => (
              <tr key={det.id}>
                <td>#{det.id}</td>
                <td>
                  <span className={`severity-badge ${severityBadgeClass(det.severity)}`}>
                    {det.severity}
                  </span>
                </td>
                <td>{(det.confidence * 100).toFixed(1)}%</td>
                <td>{det.max_depth.toFixed(4)}</td>
                <td>{det.avg_depth.toFixed(4)}</td>
                <td>{det.area_px.toLocaleString()}</td>
                <td>{det.dimensions.width_m}×{det.dimensions.height_m}m</td>
                <td>{det.volume.toFixed(1)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
