// =============================================================================
// PotholeVision — Live Road Camera Component (Mobile & Webcam)
// =============================================================================
// Streams real-time camera feed, captures frames for AI analysis,
// and displays live Driver Safety Hazard alerts on road defects.

import { useState, useRef, useEffect, useCallback } from 'react';
import { analyzeFrame } from '../api/client';

export default function LiveCamera({ onAnalysisResult, onError, isAnalyzingGlobal }) {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [stream, setStream] = useState(null);
  const [isCameraActive, setIsCameraActive] = useState(false);
  const [isLiveAnalyzing, setIsLiveAnalyzing] = useState(false);
  const [facingMode, setFacingMode] = useState('environment'); // Default to rear camera for road
  const [liveOverlay, setLiveOverlay] = useState(null);
  const [liveMetrics, setLiveMetrics] = useState(null);
  const [fps, setFps] = useState(0);

  const isProcessingRef = useRef(false);
  const lastTimeRef = useRef(Date.now());
  const timerRef = useRef(null);

  // ─── Start Camera ─────────────────────────────────────────────────────────

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
      console.error('Camera access error:', err);
      onError(`Camera access failed: ${err.message}. Please allow camera permissions.`);
      setIsCameraActive(false);
    }
  }, [stream, facingMode, onError]);

  // ─── Stop Camera ──────────────────────────────────────────────────────────

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

  // ─── Flip Camera (Front / Rear) ──────────────────────────────────────────

  const toggleCameraFacing = useCallback(() => {
    const nextFacing = facingMode === 'environment' ? 'user' : 'environment';
    startCamera(nextFacing);
  }, [facingMode, startCamera]);

  // ─── Process Frame ────────────────────────────────────────────────────────

  const captureAndAnalyze = useCallback(async () => {
    if (!videoRef.current || !canvasRef.current || isProcessingRef.current) return;
    const video = videoRef.current;
    if (video.readyState !== 4) return; // HAVE_ENOUGH_DATA

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 360;

    // Draw video frame to hidden canvas
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
      console.warn('Real-time analysis tick error:', err);
    } finally {
      isProcessingRef.current = false;
    }
  }, [onAnalysisResult]);

  // ─── Live Analysis Loop ───────────────────────────────────────────────────

  useEffect(() => {
    if (isLiveAnalyzing && isCameraActive) {
      // Analyze a frame every 400ms for smooth live streaming without choking
      timerRef.current = setInterval(() => {
        captureAndAnalyze();
      }, 400);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
    }

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isLiveAnalyzing, isCameraActive, captureAndAnalyze]);

  // Auto-clean on unmount
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
    <div className="live-camera-container" id="live-camera">
      <div className="section-title">
        <span className="icon">🎥</span>
        Live Road Vision AI Camera
      </div>

      <div className="camera-viewport glass-card">
        {/* Video stream */}
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className={`camera-video ${!isCameraActive ? 'hidden' : ''}`}
        />

        {/* Live Annotated Overlay */}
        {liveOverlay && isLiveAnalyzing && (
          <img
            src={`data:image/jpeg;base64,${liveOverlay}`}
            alt="Real-time detection overlay"
            className="camera-overlay-image"
          />
        )}

        {/* Hidden canvas for grabbing frames */}
        <canvas ref={canvasRef} style={{ display: 'none' }} />

        {/* Placeholder when camera is stopped */}
        {!isCameraActive && (
          <div className="empty-state">
            <div className="empty-state-icon">📷</div>
            <p className="empty-state-text">
              Turn on the live camera to detect road defects, measure pothole depths,
              and receive real-time driver safety alerts.
            </p>
            <button
              className="btn btn-primary"
              style={{ marginTop: '16px' }}
              onClick={() => startCamera('environment')}
            >
              ▶️ Start Road Camera
            </button>
          </div>
        )}

        {/* Hazard Alert Banner */}
        {isCameraActive && isHazard && (
          <div className={`hazard-banner ${worstSeverity.toLowerCase()}`}>
            ⚠️ CAUTION: {worstSeverity} ROAD DEFECT DETECTED — SLOW DOWN!
          </div>
        )}

        {/* HUD Info */}
        {isCameraActive && (
          <div className="camera-hud">
            <div className="hud-badge">
              <span className="status-dot"></span>
              {isLiveAnalyzing ? `AI ACTIVE (${fps} FPS)` : 'CAMERA LIVE'}
            </div>
            {liveMetrics && (
              <div className="hud-badge">
                🕳️ Defects: {liveMetrics.pothole_count} | Status: {liveMetrics.road_status}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Camera Controls */}
      {isCameraActive && (
        <div className="camera-controls">
          <button
            className={`btn ${isLiveAnalyzing ? 'btn-danger' : 'btn-primary'}`}
            onClick={() => setIsLiveAnalyzing(!isLiveAnalyzing)}
          >
            {isLiveAnalyzing ? '⏸️ Pause AI Analysis' : '⚡ Start Real-Time AI Stream'}
          </button>

          <button
            className="btn"
            onClick={captureAndAnalyze}
            disabled={isLiveAnalyzing}
          >
            📸 Capture &amp; Inspect Blueprint
          </button>

          <button className="btn" onClick={toggleCameraFacing} title="Flip Camera">
            🔄 Flip ({facingMode === 'environment' ? 'Rear' : 'Front'})
          </button>

          <button className="btn btn-secondary" onClick={stopCamera}>
            ⏹️ Stop Camera
          </button>
        </div>
      )}
    </div>
  );
}
