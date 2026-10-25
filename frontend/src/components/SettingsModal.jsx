import React, { useRef, useState } from 'react';
import {
  X,
  UploadCloud,
  FileCheck,
  RefreshCw,
  AlertCircle,
  Layers,
  CheckCircle2,
  Settings,
  Cpu,
  Database,
  FileText
} from 'lucide-react';

export default function SettingsModal({
  isOpen,
  onClose,
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

  if (!isOpen) return null;

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
      onClose();
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
    <div className="modal-overlay" onClick={onClose}>
      <div className="settings-modal-card" onClick={(e) => e.stopPropagation()}>
        {/* Modal Header */}
        <div className="modal-header">
          <div className="modal-title-row">
            <Settings size={20} className="text-orange" />
            <h2 className="modal-heading">Handbook Settings &amp; Management</h2>
          </div>
          <button type="button" className="modal-close-btn" onClick={onClose} aria-label="Close modal">
            <X size={18} />
          </button>
        </div>

        <div className="modal-content">
          {/* Active Handbook Status */}
          <div className="settings-section">
            <h3 className="section-label">Active Document</h3>
            <div className="active-doc-box">
              <div className="active-doc-row">
                <span className="doc-prop-label">Indexed File:</span>
                <span className="doc-prop-value font-mono">
                  {currentDocument ? (
                    <span className="flex-inline items-center gap-1 text-orange">
                      <FileCheck size={14} />
                      {currentDocument}
                    </span>
                  ) : (
                    <span className="text-muted">No handbook currently loaded</span>
                  )}
                </span>
              </div>
              <div className="active-doc-row">
                <span className="doc-prop-label">Vector Storage:</span>
                <span className="doc-prop-value">
                  <span className="badge-pill">
                    <Layers size={13} />
                    {indexedChunks} Chunks (ChromaDB)
                  </span>
                </span>
              </div>
              <div className="active-doc-row">
                <span className="doc-prop-label">Backend Status:</span>
                <span className="doc-prop-value">
                  {backendReady ? (
                    <span className="badge-pill text-emerald">
                      <CheckCircle2 size={13} />
                      Online &amp; Ready
                    </span>
                  ) : (
                    <span className="badge-pill text-danger">
                      <AlertCircle size={13} />
                      Disconnected
                    </span>
                  )}
                </span>
              </div>
            </div>
          </div>

          {/* Upload New PDF Dropzone */}
          <div className="settings-section">
            <h3 className="section-label">Upload New Handbook PDF</h3>
            <div
              className={`modal-dropzone ${dragActive ? 'dropzone-active' : ''} ${isUploading ? 'dropzone-busy' : ''}`}
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
                  <div className="uploading-state">
                    <RefreshCw size={28} className="spin-icon text-orange" />
                    <p className="upload-prompt">Parsing pages &amp; building embeddings...</p>
                    <span className="upload-subtext">Indexing chunks into local ChromaDB</span>
                  </div>
                ) : (
                  <>
                    <div className="upload-icon-circle">
                      <UploadCloud size={24} className="text-orange" />
                    </div>
                    <p className="upload-prompt">
                      <span className="upload-link-text">Click to browse</span> or drag PDF here
                    </p>
                    <span className="upload-subtext">Text-based PDF up to 25 MB</span>
                  </>
                )}
              </div>
            </div>

            {errorMsg && (
              <div className="alert-banner alert-error mt-2">
                <AlertCircle size={16} />
                <span>{errorMsg}</span>
              </div>
            )}
          </div>

          {/* System Architecture Specifications */}
          <div className="settings-section">
            <h3 className="section-label">System Architecture</h3>
            <div className="specs-grid">
              <div className="spec-card">
                <span className="spec-title">Extraction</span>
                <span className="spec-detail">PyPDF (Page Metadata Preserved)</span>
              </div>
              <div className="spec-card">
                <span className="spec-title">Embedding Model</span>
                <span className="spec-detail font-mono">all-MiniLM-L6-v2 (384-dim)</span>
              </div>
              <div className="spec-card">
                <span className="spec-title">Vector Database</span>
                <span className="spec-detail">Persistent ChromaDB</span>
              </div>
              <div className="spec-card">
                <span className="spec-title">Grounding Policy</span>
                <span className="spec-detail text-emerald">Strict Context-Only Refusal</span>
              </div>
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="modal-footer">
          <button type="button" className="btn-secondary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
