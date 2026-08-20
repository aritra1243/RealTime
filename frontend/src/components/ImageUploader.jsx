// =============================================================================
// PotholeVision — Monochrome Image Uploader
// =============================================================================

import { useState, useRef, useCallback } from 'react';
import { UploadCloud, FileImage, RefreshCw } from 'lucide-react';

export default function ImageUploader({ onUpload, isLoading }) {
  const [dragOver, setDragOver] = useState(false);
  const [preview, setPreview] = useState(null);
  const [fileName, setFileName] = useState('');
  const fileInputRef = useRef(null);

  const handleFile = useCallback(
    (file) => {
      if (!file) return;

      const validTypes = ['image/jpeg', 'image/png', 'image/webp', 'image/jpg'];
      if (!validTypes.includes(file.type)) {
        alert('Please upload a valid image (JPG, PNG, or WebP).');
        return;
      }

      setFileName(file.name);

      const reader = new FileReader();
      reader.onload = (e) => setPreview(e.target.result);
      reader.readAsDataURL(file);

      onUpload(file);
    },
    [onUpload]
  );

  const handleDrop = useCallback(
    (e) => {
      e.preventDefault();
      setDragOver(false);
      const file = e.dataTransfer.files[0];
      handleFile(file);
    },
    [handleFile]
  );

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    setDragOver(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setDragOver(false);
  }, []);

  const handleInputChange = useCallback(
    (e) => {
      const file = e.target.files[0];
      handleFile(file);
    },
    [handleFile]
  );

  return (
    <div className="space-y-4">
      
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => fileInputRef.current?.click()}
        className={`group relative flex min-h-[220px] cursor-pointer flex-col items-center justify-center rounded-3xl border-2 border-dashed p-6 text-center backdrop-blur-xl transition-all duration-300 ${
          dragOver
            ? 'border-white bg-zinc-900 shadow-[0_0_30px_rgba(255,255,255,0.2)]'
            : 'border-white/20 bg-zinc-950/70 hover:border-white/40 hover:bg-zinc-900/60 shadow-xl'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          onChange={handleInputChange}
          className="hidden"
        />

        {/* Tactical HUD Corner Brackets */}
        <div className="hud-corner-tl opacity-30 group-hover:opacity-100 transition-opacity"></div>
        <div className="hud-corner-tr opacity-30 group-hover:opacity-100 transition-opacity"></div>
        <div className="hud-corner-bl opacity-30 group-hover:opacity-100 transition-opacity"></div>
        <div className="hud-corner-br opacity-30 group-hover:opacity-100 transition-opacity"></div>

        {isLoading ? (
          <div className="flex flex-col items-center gap-3">
            <RefreshCw className="h-10 w-10 animate-spin text-white" />
            <div className="space-y-1">
              <p className="text-sm font-bold text-white font-mono uppercase tracking-wider">
                Computing Monocular Depth &amp; YOLOv8 Defect Contours...
              </p>
              <p className="text-xs text-zinc-500 font-mono">
                GPU Latency ~150ms
              </p>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl border border-white/15 bg-zinc-900 shadow-[0_0_20px_rgba(255,255,255,0.06)] group-hover:scale-105 group-hover:border-white/30 transition-all">
              <UploadCloud className="h-7 w-7 text-white" />
            </div>

            <div className="space-y-1">
              <p className="text-sm font-semibold text-white">
                Drag &amp; drop high-res road image, or <span className="underline underline-offset-4 decoration-white/40">browse files</span>
              </p>
              <p className="text-xs text-zinc-500 font-mono">
                Supports JPG, PNG, WEBP — Auto-Enhanced with MiDaS
              </p>
            </div>
          </div>
        )}

        {preview && !isLoading && (
          <div className="mt-4 flex items-center gap-2 rounded-lg border border-white/10 bg-zinc-900/80 px-3 py-1.5 text-xs text-zinc-300">
            <FileImage className="h-4 w-4 text-white" />
            <span className="font-mono">{fileName}</span>
          </div>
        )}
      </div>

    </div>
  );
}
