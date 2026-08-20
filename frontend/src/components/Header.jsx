// =============================================================================
// PotholeVision — Monochrome Tactical Header (Responsive)
// =============================================================================

import { useState, useEffect } from 'react';
import { Activity, ShieldCheck, Eye, Sliders, Menu, X } from 'lucide-react';

export default function Header({ backendOnline, onToggleSidebar, isSidebarOpen }) {
  const [time, setTime] = useState('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTime(now.toTimeString().split(' ')[0] + ' UTC');
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="sticky top-0 z-40 w-full border-b border-white/10 bg-black/85 backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-3.5 py-3 sm:px-6 lg:px-8">
        
        {/* Brand Logo & Title */}
        <div className="flex items-center gap-2.5 sm:gap-3">
          
          {/* Mobile Sidebar Toggle Button */}
          <button
            onClick={onToggleSidebar}
            aria-label="Toggle Configuration Sidebar"
            className="flex lg:hidden h-9 w-9 items-center justify-center rounded-xl border border-white/20 bg-zinc-900 text-white hover:bg-zinc-800 active:scale-95 transition-all"
          >
            {isSidebarOpen ? <X className="h-4 w-4" /> : <Sliders className="h-4 w-4" />}
          </button>

          <div className="relative flex h-9 w-9 sm:h-10 sm:w-10 items-center justify-center rounded-xl border border-white/20 bg-zinc-900 shadow-[0_0_15px_rgba(255,255,255,0.1)]">
            <Eye className="h-4 w-4 sm:h-5 sm:w-5 text-white" />
            <span className="absolute -top-1 -right-1 flex h-2 w-2 sm:h-2.5 sm:w-2.5">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-white opacity-75"></span>
              <span className="relative inline-flex h-2 w-2 sm:h-2.5 sm:w-2.5 rounded-full bg-white"></span>
            </span>
          </div>

          <div>
            <div className="flex items-center gap-1.5 sm:gap-2">
              <span className="font-extrabold text-base sm:text-lg tracking-wider text-white font-mono uppercase">
                PotholeVision
              </span>
              <span className="rounded border border-white/30 bg-white/10 px-1.5 py-0.5 text-[9px] sm:text-[10px] font-bold text-white uppercase tracking-widest">
                v2.0
              </span>
            </div>
            <p className="text-[11px] text-zinc-400 font-sans hidden md:block">
              Monocular Depth Estimation &amp; Autonomous Road Defect AI
            </p>
          </div>
        </div>

        {/* Telemetry & System Status */}
        <div className="flex items-center gap-2 sm:gap-4">
          
          {/* UTC Clock */}
          <div className="hidden sm:flex items-center gap-1.5 rounded-md border border-white/10 bg-zinc-950 px-2.5 py-1 text-xs font-mono text-zinc-300">
            <Activity className="h-3.5 w-3.5 text-zinc-400 animate-pulse" />
            <span>{time || '00:00:00 UTC'}</span>
          </div>

          {/* Backend Status Pill */}
          <div className="flex items-center gap-1.5 sm:gap-2 rounded-full border border-white/15 bg-zinc-900/90 px-2.5 sm:px-3 py-1 text-[11px] sm:text-xs font-medium text-white shadow-inner">
            <span className="relative flex h-2 w-2">
              <span className={`absolute inline-flex h-full w-full animate-ping rounded-full ${backendOnline ? 'bg-white' : 'bg-zinc-500'} opacity-75`}></span>
              <span className={`relative inline-flex h-2 w-2 rounded-full ${backendOnline ? 'bg-white' : 'bg-zinc-500'}`}></span>
            </span>
            <span className="tracking-wide">
              {backendOnline ? 'AI LIVE' : 'STARTING...'}
            </span>
          </div>

          {/* Model Badges */}
          <div className="hidden lg:flex items-center gap-1 rounded-md border border-white/10 bg-zinc-950 px-2 py-1 text-[11px] font-mono text-zinc-400">
            <ShieldCheck className="h-3.5 w-3.5 text-white" />
            <span>YOLOv8 + MiDaS</span>
          </div>

        </div>

      </div>
    </header>
  );
}
