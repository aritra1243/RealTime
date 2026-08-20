// =============================================================================
// PotholeVision — Monochrome HUD Metrics Panel
// =============================================================================

import { AlertTriangle, ShieldCheck, Gauge, Box, Zap } from 'lucide-react';

export default function MetricsPanel({ metrics }) {
  if (!metrics) return null;

  const getStatusBadge = (status) => {
    const s = status?.toUpperCase() || 'CLEAR';
    if (s === 'CRITICAL') {
      return (
        <span className="inline-flex items-center gap-1.5 rounded-full bg-white px-3 py-0.5 text-xs font-black text-black shadow-[0_0_15px_rgba(255,255,255,0.7)] animate-pulse">
          <AlertTriangle className="h-3.5 w-3.5 fill-black text-white" />
          CRITICAL HAZARD
        </span>
      );
    }
    if (s === 'MODERATE') {
      return (
        <span className="inline-flex items-center gap-1.5 rounded-full border border-white/40 bg-zinc-800 px-3 py-0.5 text-xs font-bold text-white shadow-inner">
          <AlertTriangle className="h-3.5 w-3.5 text-white" />
          MODERATE DEFECT
        </span>
      );
    }
    if (s === 'SHALLOW') {
      return (
        <span className="inline-flex items-center gap-1.5 rounded-full border border-zinc-700 bg-zinc-900 px-3 py-0.5 text-xs font-semibold text-zinc-300">
          <ShieldCheck className="h-3.5 w-3.5 text-zinc-400" />
          SHALLOW SURFACE
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full border border-white/20 bg-zinc-900 px-3 py-0.5 text-xs font-semibold text-white">
        <ShieldCheck className="h-3.5 w-3.5 text-white" />
        ROAD CLEAR
      </span>
    );
  };

  const cards = [
    {
      id: 'road-status',
      label: 'ROAD SAFETY AUDIT',
      customValue: getStatusBadge(metrics.road_status),
      subtext: `${metrics.pothole_count || 0} defect zones identified`,
      icon: ShieldCheck,
    },
    {
      id: 'pothole-count',
      label: 'DEFECT COUNT',
      value: metrics.pothole_count ?? 0,
      unit: 'POTHOLES',
      subtext: 'Segmented contours',
      icon: AlertTriangle,
    },
    {
      id: 'max-depth',
      label: 'MAX DEPRESSION',
      value: metrics.max_depth ? metrics.max_depth.toFixed(4) : '0.0000',
      unit: 'REL UNITS',
      subtext: 'Relative MiDaS depth',
      icon: Gauge,
    },
    {
      id: 'total-volume',
      label: 'ESTIMATED VOLUME',
      value: metrics.total_volume ? metrics.total_volume.toFixed(1) : '0.0',
      unit: 'VOL UNITS',
      subtext: 'Asphalt fill material',
      icon: Box,
    },
    {
      id: 'latency',
      label: 'AI INFERENCE',
      value: metrics.latency_ms ? metrics.latency_ms.toFixed(1) : '0.0',
      unit: 'MS',
      subtext: 'ZeroGPU execution',
      icon: Zap,
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3.5 w-full">
      {cards.map((card) => {
        const IconComponent = card.icon;
        return (
          <div
            key={card.id}
            className="group relative flex flex-col justify-between rounded-2xl border border-white/10 bg-zinc-950/80 p-4.5 backdrop-blur-xl shadow-lg hover:border-white/30 hover:bg-zinc-900/90 transition-all duration-300"
          >
            {/* Corner Bracket Reticle */}
            <div className="hud-corner-tl opacity-40 group-hover:opacity-100 transition-opacity"></div>
            <div className="hud-corner-br opacity-40 group-hover:opacity-100 transition-opacity"></div>

            <div className="flex items-center justify-between text-zinc-400">
              <span className="text-[10px] font-bold font-mono tracking-widest text-zinc-400 uppercase">
                {card.label}
              </span>
              <IconComponent className="h-4 w-4 text-zinc-400 group-hover:text-white transition-colors" />
            </div>

            <div className="my-2">
              {card.customValue ? (
                <div>{card.customValue}</div>
              ) : (
                <div className="flex items-baseline gap-1.5">
                  <span className="text-2xl font-black tracking-tight text-white font-mono">
                    {card.value}
                  </span>
                  {card.unit && (
                    <span className="text-[10px] font-bold font-mono text-zinc-500">
                      {card.unit}
                    </span>
                  )}
                </div>
              )}
            </div>

            <span className="text-[11px] text-zinc-500 font-mono">
              {card.subtext}
            </span>
          </div>
        );
      })}
    </div>
  );
}
