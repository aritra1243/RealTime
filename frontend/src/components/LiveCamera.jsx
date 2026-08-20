// =============================================================================
// PotholeVision — Monochrome Live Tactical Road Camera
// =============================================================================

import { useState, useRef, useEffect, useCallback } from 'react';
import { Camera, RefreshCw, Play, Pause, AlertTriangle, Eye, VideoOff, Crosshair } from 'lucide-react';
import { analyzeFrame } from '../api/client';

export default function LiveCamera({ onAnalysisResult, onError, isAnalyzingGlobal }) {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [stream, setStream] = useState(null);
  const [isCameraActive, setIsCameraActive] = useState(false);
  const [isLiveAnalyzing, setIsLiveAnalyzing] = useState(false);
  const [facingMode, setFacingMode] = useState('environment');
  const [liveOverlay, setLiveOverlay] = useState(null);
  const [liveMetrics, setLiveMetrics] = useState(null);
  const [fps, setFps] = useState(0);

  const isProcessingRef = useRef(false);
  const timerRef = useRef(null);

  // ── Start Camera ──────────────────────────────────────────────────────────
  const startCamera = useCallback(async (facing = facingMode) => {
    try {
      if (stream) {
        stream.getTracks().forEach((track) => track.stop());
      }

      const constraints = {
        video: {
          facingMode: { ideal: facing },
          width: { ideal: 1280 },
          height: { ideal: 720 },
        },
        audio: false,
      };

      const mediaStream = await navigator.mediaDevices.getUserMedia(constraints);
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }
      setStream(mediaStream);
      setIsCameraActive(true);
      setFacingMode(facing);
    } catch (err) {
      console.error('Camera error:', err);
      onError(`Camera access failed: ${err.message}. Please allow camera permissions.`);
      setIsCameraActive(false);
    }
  }, [stream, facingMode, onError]);

  // ── Stop Camera ───────────────────────────────────────────────────────────
  const stopCamera = useCallback(() => {
    setIsLiveAnalyzing(false);
    if (timerRef.current) clearInterval(timerRef.current);

    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      setStream(null);
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setIsCameraActive(false);
    setLiveOverlay(null);
  }, [stream]);

  // ── Flip Facing ───────────────────────────────────────────────────────────
  const toggleCameraFacing = useCallback(() => {
    const nextFacing = facingMode === 'environment' ? 'user' : 'environment';
    startCamera(nextFacing);
  }, [facingMode, startCamera]);

  // ── Capture & Process Frame ───────────────────────────────────────────────
  const captureAndAnalyze = useCallback(async () => {
    if (!videoRef.current || !canvasRef.current || isProcessingRef.current) return;
    const video = videoRef.current;
    if (video.readyState !== 4) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 360;

    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const base64Image = canvas.toDataURL('image/jpeg', 0.8);

    isProcessingRef.current = true;
    try {
      const now = Date.now();
      const result = await analyzeFrame(base64Image);
      if (result.success) {
        setLiveOverlay(result.images?.annotated || null);
        setLiveMetrics(result.metrics || null);
        onAnalysisResult(result);

        const delta = (Date.now() - now) / 1000;
        setFps(Math.round(1 / Math.max(0.1, delta)));
      }
    } catch (err) {
      console.warn('Live tick error:', err);
    } finally {
      isProcessingRef.current = false;
    }
  }, [onAnalysisResult]);

  // ── Live Stream Loop ──────────────────────────────────────────────────────
  useEffect(() => {
    if (isLiveAnalyzing && isCameraActive) {
      timerRef.current = setInterval(() => {
        captureAndAnalyze();
      }, 450);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isLiveAnalyzing, isCameraActive, captureAndAnalyze]);

  useEffect(() => {
    return () => {
      if (stream) {
        stream.getTracks().forEach((track) => track.stop());
      }
    };
  }, [stream]);

  const worstSeverity = liveMetrics?.road_status;
  const isHazard = worstSeverity === 'CRITICAL' || worstSeverity === 'MODERATE';

  return (
    <div className="space-y-4">
      
      {/* ── Viewport Container ─────────────────────────────────────────────── */}
      <div className="relative aspect-video w-full overflow-hidden rounded-3xl border border-white/15 bg-zinc-950 shadow-2xl">
        
        {/* Tactical Corner Brackets */}
        <div className="hud-corner-tl z-20"></div>
        <div className="hud-corner-tr z-20"></div>
        <div className="hud-corner-bl z-20"></div>
        <div className="hud-corner-br z-20"></div>

        {/* Video stream */}
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className={`h-full w-full object-cover ${!isCameraActive ? 'hidden' : ''}`}
        />

        {/* Laser Scanning Line during live AI */}
        {isCameraActive && isLiveAnalyzing && (
          <div className="animate-scanline z-10"></div>
        )}

        {/* Live Annotated Overlay */}
        {liveOverlay && isLiveAnalyzing && (
          <img
            src={`data:image/jpeg;base64,${liveOverlay}`}
            alt="Real-time detection overlay"
            className="absolute inset-0 h-full w-full object-contain pointer-events-none z-10"
          />
        )}

        {/* Hidden Canvas */}
        <canvas ref={canvasRef} style={{ display: 'none' }} />

        {/* Camera Inactive Empty State */}
        {!isCameraActive && (
          <div className="flex h-full w-full flex-col items-center justify-center p-8 text-center bg-zinc-950/90">
            <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl border border-white/20 bg-zinc-900 shadow-[0_0_30px_rgba(255,255,255,0.08)]">
              <Camera className="h-8 w-8 text-white" />
            </div>

            <h3 className="text-base font-bold uppercase tracking-wider text-white font-mono">
              Live Tactical Road Feed
            </h3>
            <p className="mt-1 max-w-md text-xs text-zinc-400">
              Mount your phone on dashboard or point camera at the road. YOLOv8 + MiDaS will detect potholes and calculate depression depth in real time.
            </p>

            <button
              onClick={() => startCamera('environment')}
              className="mt-6 flex items-center gap-2 rounded-xl bg-white px-6 py-3 text-xs font-black uppercase tracking-wider text-black shadow-[0_0_25px_rgba(255,255,255,0.3)] hover:bg-zinc-200 active:scale-95 transition-all cursor-pointer"
            >
              <Play className="h-4 w-4 fill-black text-black" />
              Initialize Rear Camera
            </button>
          </div>
        )}

        {/* Hazard Alert Banner */}
        {isCameraActive && isHazard && (
          <div className="absolute top-4 left-1/2 -translate-x-1/2 z-30 flex items-center gap-2 rounded-full border border-white bg-white px-4 py-1.5 text-xs font-black uppercase text-black shadow-[0_0_25px_rgba(255,255,255,0.9)] animate-bounce">
            <AlertTriangle className="h-4 w-4 fill-black text-white" />
            <span>WARNING: {worstSeverity} ROAD DEFECT AHEAD — SLOW DOWN!</span>
          </div>
        )}

        {/* Tactical HUD Overlay Elements */}
        {isCameraActive && (
          <div className="absolute top-4 left-4 z-20 flex flex-wrap gap-2">
            <div className="flex items-center gap-2 rounded-full border border-white/20 bg-black/70 px-3 py-1 text-[11px] font-mono text-white backdrop-blur-md">
              <span className={`h-2 w-2 rounded-full ${isLiveAnalyzing ? 'bg-white animate-ping' : 'bg-zinc-500'}`}></span>
              <span>{isLiveAnalyzing ? `AI ACTIVE (${fps} FPS)` : 'VIEWFINDER READY'}</span>
            </div>

            {liveMetrics && (
              <div className="flex items-center gap-2 rounded-full border border-white/20 bg-black/70 px-3 py-1 text-[11px] font-mono text-white backdrop-blur-md">
                <Crosshair className="h-3 w-3 text-white" />
                <span>DEFECTS: {liveMetrics.pothole_count}</span>
              </div>
            )}
          </div>
        )}

      </div>

      {/* ── Controls Bar ───────────────────────────────────────────────────── */}
      {isCameraActive && (
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-white/10 bg-zinc-950 p-4 backdrop-blur-xl">
          
          <div className="flex flex-wrap items-center gap-2.5">
            
            {/* Stream Toggle */}
            <button
              onClick={() => setIsLiveAnalyzing(!isLiveAnalyzing)}
              className={`flex items-center gap-2 rounded-xl px-4 py-2.5 text-xs font-bold uppercase tracking-wider transition-all cursor-pointer ${
                isLiveAnalyzing
                  ? 'bg-zinc-800 text-white border border-white/30 hover:bg-zinc-700'
                  : 'bg-white text-black shadow-[0_0_20px_rgba(255,255,255,0.25)] hover:bg-zinc-200'
              }`}
            >
              {isLiveAnalyzing ? (
                <>
                  <Pause className="h-3.5 w-3.5 fill-current" /> Pause AI Stream
                </>
              ) : (
                <>
                  <Play className="h-3.5 w-3.5 fill-current" /> Start Real-Time AI
                </>
              )}
            </button>

            {/* Manual Snapshot */}
            <button
              onClick={captureAndAnalyze}
              disabled={isLiveAnalyzing}
              className="flex items-center gap-2 rounded-xl border border-white/15 bg-zinc-900 px-4 py-2.5 text-xs font-semibold text-white hover:bg-zinc-800 disabled:opacity-40 transition-all cursor-pointer"
            >
              <Eye className="h-3.5 w-3.5 text-zinc-300" />
              Capture Blueprint Snapshot
            </button>

            {/* Flip Camera */}
            <button
              onClick={toggleCameraFacing}
              className="flex items-center gap-1.5 rounded-xl border border-white/15 bg-zinc-900 px-3.5 py-2.5 text-xs font-medium text-zinc-300 hover:bg-zinc-800 hover:text-white transition-all cursor-pointer"
              title="Switch between front and rear road camera"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              <span>{facingMode === 'environment' ? 'Rear Cam' : 'Front Cam'}</span>
            </button>

          </div>

          {/* Stop Camera Button */}
          <button
            onClick={stopCamera}
            className="flex items-center gap-1.5 rounded-xl border border-zinc-800 bg-black px-4 py-2.5 text-xs font-medium text-zinc-400 hover:bg-zinc-900 hover:text-white transition-all cursor-pointer"
          >
            <VideoOff className="h-3.5 w-3.5" />
            Stop Camera
          </button>

        </div>
      )}

    </div>
  );
}
