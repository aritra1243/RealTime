// =============================================================================
// PotholeVision — Image Uploader Component
// =============================================================================

import { useState, useRef, useCallback } from 'react';

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

      // Create preview
      const reader = new FileReader();
      reader.onload = (e) => setPreview(e.target.result);
      reader.readAsDataURL(file);

      // Trigger analysis
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
    <div className="uploader" id="image-uploader">
      <div className="section-title">
        <span className="icon">📷</span>
        Upload Road Image
      </div>

      <div
        className={`drop-zone ${dragOver ? 'drag-over' : ''}`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => fileInputRef.current?.click()}
        id="drop-zone"
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          onChange={handleInputChange}
          style={{ display: 'none' }}
        />

        {isLoading ? (
          <>
            <div className="loading-spinner lg"></div>
            <p className="loading-text" style={{ marginTop: '16px' }}>
              Analyzing road surface & computing depth...
            </p>
          </>
        ) : (
          <>
            <div className="drop-zone-icon">📁</div>
            <p className="drop-zone-text">
              Drag & drop a road image here, or click to browse
            </p>
            <p className="drop-zone-hint">
              Supports: JPG, PNG, WebP
            </p>
          </>
        )}

        {preview && !isLoading && (
          <img
            src={preview}
            alt={`Preview: ${fileName}`}
            className="preview-image"
          />
        )}
      </div>

      {fileName && !isLoading && (
        <p style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)', textAlign: 'center' }}>
          📄 {fileName}
        </p>
      )}
    </div>
  );
}
