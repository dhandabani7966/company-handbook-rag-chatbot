import React, { useRef, useState } from 'react';
import { UploadCloud, FileCheck, RefreshCw, AlertCircle, Layers, CheckCircle2, FileText } from 'lucide-react';

export default function PdfUpload({
  backendReady,
  indexedChunks,
  currentDocument,
  onUploadSuccess,
  isUploading,
  setIsUploading
}) {
  const [errorMsg, setErrorMsg] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleUpload(e.target.files[0]);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleUpload(e.dataTransfer.files[0]);
    }
  };

  const handleUpload = async (file) => {
    setErrorMsg(null);

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setErrorMsg("Please select a valid PDF (.pdf) file.");
      return;
    }

    if (file.size > 25 * 1024 * 1024) {
      setErrorMsg("File exceeds 25 MB size limit.");
      return;
    }

    setIsUploading(true);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://127.0.0.1:8000/upload', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || `Upload failed with status ${response.status}`);
      }

      onUploadSuccess({
        filename: data.filename,
        chunks: data.chunks_indexed
      });
    } catch (err) {
      setErrorMsg(err.message || "Failed to upload and index document.");
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  return (
    <div className="pdf-upload-card">
      <div className="panel-section-title">
        <FileText size={18} className="panel-title-icon" />
        <h3>Handbook Management</h3>
      </div>

      <div
        className={`dropzone ${dragActive ? 'dropzone-active' : ''} ${isUploading ? 'dropzone-busy' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => !isUploading && fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          style={{ display: 'none' }}
          onChange={handleFileChange}
          disabled={isUploading}
        />

        <div className="dropzone-content">
          {isUploading ? (
            <div className="upload-progress-state">
              <RefreshCw size={32} className="spin-icon text-accent" />
              <p className="upload-prompt">Parsing pages & generating embeddings...</p>
              <span className="upload-subtext">Indexing chunks into local ChromaDB</span>
            </div>
          ) : (
            <>
              <div className="upload-icon-wrapper">
                <UploadCloud size={30} />
              </div>
              <p className="upload-prompt">
                <span className="upload-link">Click to browse</span> or drag PDF here
              </p>
              <span className="upload-subtext">Text-based PDF up to 25 MB</span>
            </>
          )}
        </div>
      </div>

      {errorMsg && (
        <div className="alert-banner alert-error">
          <AlertCircle size={16} />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Index Status Card */}
      <div className="index-status-box">
        <div className="status-row">
          <span className="status-label">Active Handbook:</span>
          <span className="status-value text-truncate" title={currentDocument || "No document loaded"}>
            {currentDocument ? (
              <span className="flex-row items-center gap-1">
                <FileCheck size={14} className="text-emerald" />
                {currentDocument}
              </span>
            ) : (
              <span className="text-muted">None uploaded</span>
            )}
          </span>
        </div>

        <div className="status-row">
          <span className="status-label">Indexed Chunks:</span>
          <span className="status-value font-mono">
            <span className="chunk-badge">
              <Layers size={13} />
              {indexedChunks} {indexedChunks === 1 ? 'chunk' : 'chunks'}
            </span>
          </span>
        </div>

        <div className="status-row">
          <span className="status-label">RAG Engine:</span>
          <span className="status-value">
            {indexedChunks > 0 ? (
              <span className="status-pill status-ready">
                <CheckCircle2 size={12} />
                Ready to Query
              </span>
            ) : (
              <span className="status-pill status-waiting">
                Awaiting PDF
              </span>
            )}
          </span>
        </div>
      </div>
    </div>
  );
}
