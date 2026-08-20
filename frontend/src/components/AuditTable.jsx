// =============================================================================
// PotholeVision — Monochrome Defect Audit Table
// =============================================================================

import { useCallback } from 'react';
import { Download, Table, AlertTriangle, ShieldCheck } from 'lucide-react';

export default function AuditTable({ detections }) {
  const downloadCSV = useCallback(() => {
    if (!detections || detections.length === 0) return;

    const headers = [
      'ID',
      'Severity',
      'Confidence',
      'Max Depth (m)',
      'Avg Depth (m)',
      'Area (px)',
      'Width (m)',
      'Height (m)',
      'Volume (units)',
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
    link.download = `pothole_audit_report_${Date.now()}.csv`;
    link.click();

    URL.revokeObjectURL(url);
  }, [detections]);

  if (!detections || detections.length === 0) return null;

  const getSeverityPill = (severity) => {
    const s = severity?.toUpperCase();
    if (s === 'CRITICAL') {
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-white px-2.5 py-0.5 text-[11px] font-black text-black shadow-[0_0_10px_rgba(255,255,255,0.6)]">
          CRITICAL
        </span>
      );
    }
    if (s === 'MODERATE') {
      return (
        <span className="inline-flex items-center gap-1 rounded-full border border-white/40 bg-zinc-800 px-2.5 py-0.5 text-[11px] font-bold text-white">
          MODERATE
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 rounded-full border border-zinc-700 bg-zinc-900 px-2.5 py-0.5 text-[11px] font-semibold text-zinc-300">
        SHALLOW
      </span>
    );
  };

  return (
    <div className="space-y-4">
      
      {/* ─── Header ────────────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between border-b border-white/10 pb-3">
        <div className="flex items-center gap-2">
          <Table className="h-4 w-4 text-white" />
          <h2 className="text-sm font-bold uppercase tracking-wider text-white font-mono">
            Structured Defect Audit Report
          </h2>
        </div>

        <button
          onClick={downloadCSV}
          className="flex items-center gap-1.5 rounded-xl border border-white/20 bg-zinc-900 px-3.5 py-1.5 text-xs font-mono font-bold text-white hover:bg-white hover:text-black transition-all cursor-pointer shadow-sm"
        >
          <Download className="h-3.5 w-3.5" />
          <span>Export CSV</span>
        </button>
      </div>

      {/* ─── Table Container ───────────────────────────────────────────────── */}
      <div className="overflow-x-auto rounded-2xl border border-white/10 bg-zinc-950/90 backdrop-blur-xl shadow-xl">
        <table className="w-full text-left text-xs font-mono">
          
          <thead className="border-b border-white/10 bg-zinc-900/60 text-zinc-400 uppercase tracking-wider">
            <tr>
              <th className="px-4 py-3.5">Defect ID</th>
              <th className="px-4 py-3.5">Severity</th>
              <th className="px-4 py-3.5">Confidence</th>
              <th className="px-4 py-3.5">Max Depth</th>
              <th className="px-4 py-3.5">Avg Depth</th>
              <th className="px-4 py-3.5">Pixel Area</th>
              <th className="px-4 py-3.5">CAD Dimensions</th>
              <th className="px-4 py-3.5">Volume (fill)</th>
            </tr>
          </thead>

          <tbody className="divide-y divide-white/5 text-zinc-300">
            {detections.map((det) => (
              <tr
                key={det.id}
                className="hover:bg-zinc-900/40 transition-colors"
              >
                <td className="px-4 py-3.5 font-bold text-white">
                  #{det.id}
                </td>
                <td className="px-4 py-3.5">
                  {getSeverityPill(det.severity)}
                </td>
                <td className="px-4 py-3.5 text-zinc-300">
                  {(det.confidence * 100).toFixed(1)}%
                </td>
                <td className="px-4 py-3.5 font-bold text-white">
                  {det.max_depth.toFixed(4)}
                </td>
                <td className="px-4 py-3.5 text-zinc-400">
                  {det.avg_depth.toFixed(4)}
                </td>
                <td className="px-4 py-3.5 text-zinc-400">
                  {det.area_px.toLocaleString()} px
                </td>
                <td className="px-4 py-3.5 text-zinc-300">
                  {det.dimensions.width_m}m × {det.dimensions.height_m}m
                </td>
                <td className="px-4 py-3.5 font-bold text-zinc-200">
                  {det.volume.toFixed(1)}
                </td>
              </tr>
            ))}
          </tbody>

        </table>
      </div>

    </div>
  );
}
