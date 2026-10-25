import React, { useState, useEffect } from 'react';
import {
  FileText,
  Upload,
  Trash2,
  Download,
  CheckCircle2,
  Clock,
  AlertCircle,
  FileBox,
  Search,
  ArrowLeft,
  X,
  RefreshCw
} from 'lucide-react';

export default function DocumentsPage({ apiBase, token, onBackToChat, userRole }) {
  const [documents, setDocuments] = useState([]);
  const [metrics, setMetrics] = useState({ total: 0, indexed: 0, processing: 0, failed: 0 });
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadFile, setUploadFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState('');
  const [actionMsg, setActionMsg] = useState('');

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${apiBase}/api/documents`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setDocuments(data.documents || []);
        setMetrics(data.metrics || { total: 0, indexed: 0, processing: 0, failed: 0 });
      }
    } catch (err) {
      console.error('Failed to load documents', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, [token]);

  const handleUploadSubmit = async (e) => {
    e.preventDefault();
    if (!uploadFile) return;

    try {
      setUploading(true);
      setUploadProgress('Extracting and chunking policy sections...');
      const formData = new FormData();
      formData.append('file', uploadFile);

      const res = await fetch(`${apiBase}/api/documents/upload`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Upload failed');

      setActionMsg(`Success: "${data.filename}" indexed with ${data.chunks_indexed} chunks!`);
      setShowUploadModal(false);
      setUploadFile(null);
      fetchDocuments();
    } catch (err) {
      setActionMsg(`Error: ${err.message}`);
    } finally {
      setUploading(false);
      setUploadProgress('');
    }
  };

  const handleDelete = async (docId, filename) => {
    if (!window.confirm(`Are you sure you want to delete "${filename}"? All associated ChromaDB chunks will be purged.`)) {
      return;
    }

    try {
      const res = await fetch(`${apiBase}/api/documents/${docId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        setActionMsg(`Document "${filename}" and its vector chunks deleted successfully.`);
        fetchDocuments();
      } else {
        const err = await res.json();
        alert(err.detail || 'Delete failed');
      }
    } catch (err) {
      alert(`Delete error: ${err.message}`);
    }
  };

  const handleDownload = (docId) => {
    window.open(`${apiBase}/api/documents/${docId}/download`, '_blank');
  };

  const formatBytes = (bytes) => {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const filteredDocs = documents.filter(d =>
    (d.filename || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
    (d.original_name || '').toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="enterprise-page-container">
      {/* Page Header */}
      <div className="page-header-row">
        <div>
          <button className="back-breadcrumb-btn" onClick={onBackToChat}>
            <ArrowLeft size={16} />
            <span>Back to Chat</span>
          </button>
          <h2>Documents & Knowledge Base</h2>
          <p className="page-subtitle">
            Manage company handbooks and policy PDFs indexed in persistent ChromaDB.
          </p>
        </div>

        <div className="page-header-actions">
          <button className="secondary-action-btn" onClick={fetchDocuments} title="Refresh">
            <RefreshCw size={16} />
            <span>Refresh</span>
          </button>
          <button className="primary-action-btn" onClick={() => setShowUploadModal(true)}>
            <Upload size={16} />
            <span>+ Upload PDF</span>
          </button>
        </div>
      </div>

      {actionMsg && (
        <div className="status-toast-bar">
          <span>{actionMsg}</span>
          <button onClick={() => setActionMsg('')}>✕</button>
        </div>
      )}

      {/* 4 Stat Metric Cards matching Screen 5 */}
      <div className="stats-cards-grid">
        <div className="stat-card">
          <div className="stat-card-icon-wrap total">
            <FileBox size={22} color="#F97316" />
          </div>
          <div className="stat-card-info">
            <span className="stat-card-label">Total Documents</span>
            <h3 className="stat-card-value">{metrics.total}</h3>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-card-icon-wrap indexed">
            <CheckCircle2 size={22} color="#16A34A" />
          </div>
          <div className="stat-card-info">
            <span className="stat-card-label">Indexed & Searchable</span>
            <h3 className="stat-card-value">{metrics.indexed}</h3>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-card-icon-wrap processing">
            <Clock size={22} color="#EAB308" />
          </div>
          <div className="stat-card-info">
            <span className="stat-card-label">Processing</span>
            <h3 className="stat-card-value">{metrics.processing}</h3>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-card-icon-wrap failed">
            <AlertCircle size={22} color="#DC2626" />
          </div>
          <div className="stat-card-info">
            <span className="stat-card-label">Failed</span>
            <h3 className="stat-card-value">{metrics.failed}</h3>
          </div>
        </div>
      </div>

      {/* Search Toolbar */}
      <div className="table-toolbar-row">
        <div className="table-search-input">
          <Search size={18} className="search-icon" />
          <input
            type="text"
            placeholder="Search documents by filename..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <div className="table-meta-counts">
          <span>Showing {filteredDocs.length} of {documents.length} document{documents.length !== 1 ? 's' : ''}</span>
        </div>
      </div>

      {/* Documents Table */}
      <div className="enterprise-table-card">
        {loading ? (
          <div className="table-loading-spinner">
            <RefreshCw size={28} className="spin-icon" />
            <p>Loading indexed knowledge base...</p>
          </div>
        ) : filteredDocs.length === 0 ? (
          <div className="empty-table-state">
            <FileText size={42} color="#9CA3AF" />
            <h3>No documents found</h3>
            <p>Upload a company handbook or policy PDF to index it into ChromaDB.</p>
            <button className="primary-action-btn" onClick={() => setShowUploadModal(true)}>
              Upload First PDF
            </button>
          </div>
        ) : (
          <table className="enterprise-data-table">
            <thead>
              <tr>
                <th>Document Name</th>
                <th>File Size</th>
                <th>Chunks</th>
                <th>Status</th>
                <th>Uploaded On</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredDocs.map((doc) => (
                <tr key={doc.id}>
                  <td>
                    <div className="document-name-cell">
                      <div className="pdf-mini-badge">
                        <FileText size={16} color="#DC2626" />
                      </div>
                      <div>
                        <span className="doc-primary-name">{doc.original_name || doc.filename}</span>
                        <span className="doc-sub-path">{doc.filename}</span>
                      </div>
                    </div>
                  </td>
                  <td>{formatBytes(doc.file_size)}</td>
                  <td>
                    <span className="chunks-pill">{doc.chunks_count || 0} chunks</span>
                  </td>
                  <td>
                    <span className={`status-pill ${doc.status}`}>
                      <span className="status-dot"></span>
                      {doc.status.charAt(0).toUpperCase() + doc.status.slice(1)}
                    </span>
                  </td>
                  <td className="timestamp-cell">
                    {doc.uploaded_at ? new Date(doc.uploaded_at).toLocaleDateString() : 'System'}
                  </td>
                  <td>
                    <div className="table-actions-cell">
                      <button
                        className="table-icon-btn"
                        title="Download / View Original PDF"
                        onClick={() => handleDownload(doc.id)}
                      >
                        <Download size={16} />
                      </button>
                      <button
                        className="table-icon-btn danger"
                        title="Delete Document & Chroma Chunks"
                        onClick={() => handleDelete(doc.id, doc.filename)}
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="modal-backdrop" onClick={() => !uploading && setShowUploadModal(false)}>
          <div className="modal-content-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div className="title-with-icon">
                <Upload size={20} color="#EA580C" />
                <h3>Upload Company Policy PDF</h3>
              </div>
              <button
                className="modal-close-btn"
                disabled={uploading}
                onClick={() => setShowUploadModal(false)}
              >
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleUploadSubmit} className="modal-body-form">
              <div className="dropzone-area">
                <input
                  type="file"
                  id="pdf-file-input"
                  accept=".pdf"
                  className="hidden-file-input"
                  onChange={(e) => setUploadFile(e.target.files[0] || null)}
                />
                <label htmlFor="pdf-file-input" className="dropzone-label">
                  <FileText size={40} color="#EA580C" />
                  <span className="dropzone-title">
                    {uploadFile ? uploadFile.name : 'Click to select or drag PDF handbook'}
                  </span>
                  <span className="dropzone-subtitle">
                    {uploadFile ? `${formatBytes(uploadFile.size)} selected` : 'Supports searchable PDF handbooks up to 50MB'}
                  </span>
                </label>
              </div>

              {uploadProgress && (
                <div className="upload-progress-box">
                  <RefreshCw size={16} className="spin-icon" />
                  <span>{uploadProgress}</span>
                </div>
              )}

              <div className="modal-confirm-actions">
                <button
                  type="button"
                  className="secondary-action-btn"
                  disabled={uploading}
                  onClick={() => setShowUploadModal(false)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="primary-action-btn"
                  disabled={!uploadFile || uploading}
                >
                  {uploading ? 'Indexing into ChromaDB...' : 'Upload & Index'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
