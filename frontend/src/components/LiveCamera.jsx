// =============================================================================
// PotholeVision — Ultra-Smooth Real-Time Tactical Road Vision Camera (60 FPS HUD)
// =============================================================================

import { useState, useRef, useEffect, useCallback } from 'react';
import { Camera, RefreshCw, Play, Pause, AlertTriangle, Eye, VideoOff, Crosshair, Zap } from 'lucide-react';
import { analyzeFrameFast, analyzeFrame } from '../api/client';

export default function LiveCamera({ onAnalysisResult, onError, isAnalyzingGlobal }) {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const hudCanvasRef = useRef(null);

  const [stream, setStream] = useState(null);
  const [isCameraActive, setIsCameraActive] = useState(false);
  const [isLiveAnalyzing, setIsLiveAnalyzing] = useState(false);
  const [facingMode, setFacingMode] = useState('environment');
  const [liveMetrics, setLiveMetrics] = useState(null);
  const [fps, setFps] = useState(0);
  const [aiLatency, setAiLatency] = useState(0);

  const isStreamingRef = useRef(false);
  const abortControllerRef = useRef(null);
  const detectionsRef = useRef([]);
  const frameCountRef = useRef(0);
  const lastFpsTimeRef = useRef(Date.now());

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
    isStreamingRef.current = false;
    setIsLiveAnalyzing(false);
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      setStream(null);
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setIsCameraActive(false);
    detectionsRef.current = [];
  }, [stream]);

  // ── Flip Facing ───────────────────────────────────────────────────────────
  const toggleCameraFacing = useCallback(() => {
    const nextFacing = facingMode === 'environment' ? 'user' : 'environment';
    startCamera(nextFacing);
  }, [facingMode, startCamera]);

  // ── High-Speed AI Streaming Loop ──────────────────────────────────────────
  const runAiStreamingLoop = useCallback(async () => {
    if (!isStreamingRef.current) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas || video.readyState !== 4) {
      if (isStreamingRef.current) {
        requestAnimationFrame(() => runAiStreamingLoop());
      }
      return;
    }

    // Downscale for ultra-fast AI inference (480x270 standard 16:9)
    canvas.width = 480;
    canvas.height = 270;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Fast JPEG encoding (~18KB)
    const base64Image = canvas.toDataURL('image/jpeg', 0.6);

    const startTime = performance.now();
    try {
      abortControllerRef.current = new AbortController();
      const result = await analyzeFrameFast(base64Image, abortControllerRef.current.signal);

      if (result && result.success) {
        const latency = Math.round(performance.now() - startTime);
        setAiLatency(latency);
        setLiveMetrics(result.metrics || null);
        detectionsRef.current = result.detections || [];
        onAnalysisResult(result);
      }
    } catch (err) {
      if (err.name !== 'AbortError') {
        console.warn('Fast stream tick notice:', err);
      }
    }

    // Immediately trigger next frame if still streaming (zero setInterval delay)
    if (isStreamingRef.current) {
      setTimeout(runAiStreamingLoop, 20);
    }
  }, [onAnalysisResult]);

  // ── 60 FPS Tactical HUD Canvas Rendering ──────────────────────────────────
  useEffect(() => {
    let animationFrameId;

    const renderHud = () => {
      const hudCanvas = hudCanvasRef.current;
      const video = videoRef.current;

      if (hudCanvas && video && video.readyState === 4) {
        const width = video.videoWidth || 640;
        const height = video.videoHeight || 360;

        if (hudCanvas.width !== width || hudCanvas.height !== height) {
          hudCanvas.width = width;
          hudCanvas.height = height;
        }

        const ctx = hudCanvas.getContext('2d');
        ctx.clearRect(0, 0, width, height);

        // Calculate smooth FPS
        frameCountRef.current += 1;
        const now = Date.now();
        if (now - lastFpsTimeRef.current >= 1000) {
          setFps(frameCountRef.current);
          frameCountRef.current = 0;
          lastFpsTimeRef.current = now;
        }

        // Draw HUD Overlays for detected potholes
        const detections = detectionsRef.current || [];
        const scaleX = width / 480;
        const scaleY = height / 270;

        detections.forEach((det, i) => {
          if (!det.bbox) return;

          const x1 = (det.bbox.x1 || 0) * scaleX;
          const y1 = (det.bbox.y1 || 0) * scaleY;
          const x2 = (det.bbox.x2 || 0) * scaleX;
          const y2 = (det.bbox.y2 || 0) * scaleY;
          const bw = x2 - x1;
          const bh = y2 - y1;

          // Glowing monochrome bounding box
          ctx.save();
          ctx.strokeStyle = '#ffffff';
          ctx.lineWidth = 2.5;
          ctx.shadowColor = '#ffffff';
          ctx.shadowBlur = 12;

          // Tactical Reticle Brackets
          const bLen = Math.min(20, Math.min(bw, bh) * 0.35);
          // Top-Left
          ctx.beginPath();
          ctx.moveTo(x1, y1 + bLen);
          ctx.lineTo(x1, y1);
          ctx.lineTo(x1 + bLen, y1);
          ctx.stroke();

          // Top-Right
          ctx.beginPath();
          ctx.moveTo(x2 - bLen, y1);
          ctx.lineTo(x2, y1);
          ctx.lineTo(x2, y1 + bLen);
          ctx.stroke();

          // Bottom-Left
          ctx.beginPath();
          ctx.moveTo(x1, y2 - bLen);
          ctx.lineTo(x1, y2);
          ctx.lineTo(x1 + bLen, y2);
          ctx.stroke();

          // Bottom-Right
          ctx.beginPath();
          ctx.moveTo(x2 - bLen, y2);
          ctx.lineTo(x2, y2);
          ctx.lineTo(x2, y2 - bLen);
          ctx.stroke();

          // Center Crosshair
          const cx = x1 + bw / 2;
          const cy = y1 + bh / 2;
          ctx.beginPath();
          ctx.moveTo(cx - 6, cy);
          ctx.lineTo(cx + 6, cy);
          ctx.moveTo(cx, cy - 6);
          ctx.lineTo(cx, cy + 6);
          ctx.stroke();

          // Tag Pill Badge
          const tag = `DEFECT #${det.id || i + 1} • ${det.severity || 'POTHOLE'} • ${(det.confidence * 100).toFixed(0)}%`;
          ctx.font = 'bold 12px "JetBrains Mono", monospace';
          const textMetrics = ctx.measureText(tag);
          const pWidth = textMetrics.width + 16;
          const pHeight = 22;
          const tagY = Math.max(10, y1 - 28);

          ctx.fillStyle = '#000000';
          ctx.fillRect(x1, tagY, pWidth, pHeight);
          ctx.strokeStyle = '#ffffff';
          ctx.lineWidth = 1.5;
          ctx.strokeRect(x1, tagY, pWidth, pHeight);

          ctx.fillStyle = '#ffffff';
          ctx.fillText(tag, x1 + 8, tagY + 15);

          ctx.restore();
        });
      }

      animationFrameId = requestAnimationFrame(renderHud);
    };

    if (isCameraActive) {
      animationFrameId = requestAnimationFrame(renderHud);
    }

    return () => {
      if (animationFrameId) cancelAnimationFrame(animationFrameId);
    };
  }, [isCameraActive]);

  // ── Toggle Live AI Streaming ──────────────────────────────────────────────
  const toggleStreaming = useCallback(() => {
    if (isLiveAnalyzing) {
      isStreamingRef.current = false;
      setIsLiveAnalyzing(false);
      if (abortControllerRef.current) abortControllerRef.current.abort();
    } else {
      isStreamingRef.current = true;
      setIsLiveAnalyzing(true);
      runAiStreamingLoop();
    }
  }, [isLiveAnalyzing, runAiStreamingLoop]);

  // ── Full-Resolution Snapshot Capture ──────────────────────────────────────
  const handleFullSnapshot = useCallback(async () => {
    if (!videoRef.current || !canvasRef.current) return;
    const video = videoRef.current;
    if (video.readyState !== 4) return;

    const canvas = canvasRef.current;
    canvas.width = video.videoWidth || 1280;
    canvas.height = video.videoHeight || 720;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const base64Image = canvas.toDataURL('image/jpeg', 0.85);

    try {
      const result = await analyzeFrame(base64Image);
      if (result && result.success) {
        onAnalysisResult(result);
      }
    } catch (err) {
      console.warn('Snapshot error:', err);
    }
  }, [onAnalysisResult]);

  useEffect(() => {
    return () => {
      isStreamingRef.current = false;
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
      <div className="relative aspect-[4/3] sm:aspect-video w-full overflow-hidden rounded-3xl border border-white/15 bg-zinc-950 shadow-2xl">
        
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

        {/* 60 FPS Hardware-Accelerated Canvas HUD Overlay */}
        <canvas
          ref={hudCanvasRef}
          className={`absolute inset-0 h-full w-full object-cover pointer-events-none z-15 ${!isCameraActive ? 'hidden' : ''}`}
        />

        {/* Hidden Processing Canvas */}
        <canvas ref={canvasRef} style={{ display: 'none' }} />

        {/* Laser Scanning Line during live AI */}
        {isCameraActive && isLiveAnalyzing && (
          <div className="animate-scanline z-10"></div>
        )}

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

        {/* Tactical HUD Telemetry Badges */}
        {isCameraActive && (
          <div className="absolute top-4 left-4 z-20 flex flex-wrap gap-2">
            <div className="flex items-center gap-2 rounded-full border border-white/20 bg-black/75 px-3 py-1 text-[11px] font-mono text-white backdrop-blur-md">
              <span className={`h-2 w-2 rounded-full ${isLiveAnalyzing ? 'bg-white animate-ping' : 'bg-zinc-500'}`}></span>
              <span>{isLiveAnalyzing ? `AI ACTIVE (${fps} FPS)` : `VIEWFINDER (${fps} FPS)`}</span>
            </div>

            {isLiveAnalyzing && aiLatency > 0 && (
              <div className="flex items-center gap-1.5 rounded-full border border-white/20 bg-black/75 px-3 py-1 text-[11px] font-mono text-white backdrop-blur-md">
                <Zap className="h-3 w-3 text-white" />
                <span>{aiLatency}ms CLOUD AI</span>
              </div>
            )}

            {liveMetrics && (
              <div className="flex items-center gap-2 rounded-full border border-white/20 bg-black/75 px-3 py-1 text-[11px] font-mono text-white backdrop-blur-md">
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
            
            {/* Real-Time Stream Toggle */}
            <button
              onClick={toggleStreaming}
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

            {/* Manual High-Res Snapshot */}
            <button
              onClick={handleFullSnapshot}
              className="flex items-center gap-2 rounded-xl border border-white/15 bg-zinc-900 px-4 py-2.5 text-xs font-semibold text-white hover:bg-zinc-800 transition-all cursor-pointer"
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
