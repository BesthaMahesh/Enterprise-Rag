import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import { DocumentItem, DocumentChunkItem } from '../types';
import {
  FileText,
  Search,
  Filter,
  Upload,
  RefreshCw,
  Trash2,
  Lock,
  Layers,
  CheckCircle2,
  X,
  AlertCircle,
  Eye,
} from 'lucide-react';

export const DocumentsPage: React.FC = () => {
  const { user, hasRole } = useAuth();
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [classificationFilter, setClassificationFilter] = useState('');
  
  // Modals
  const [selectedDoc, setSelectedDoc] = useState<DocumentItem | null>(null);
  const [chunks, setChunks] = useState<DocumentChunkItem[]>([]);
  const [chunksLoading, setChunksLoading] = useState(false);
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  
  // Upload Form
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadClassification, setUploadClassification] = useState('INTERNAL');
  const [uploadRoles, setUploadRoles] = useState('EMPLOYEE,HR,FINANCE,ADMIN');
  const [uploading, setUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState<string | null>(null);

  useEffect(() => {
    loadDocuments();
  }, [classificationFilter]);

  const loadDocuments = async () => {
    setLoading(true);
    try {
      const data = await api.getDocuments({
        classification: classificationFilter || undefined,
        search: search || undefined,
      });
      setDocuments(data);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    loadDocuments();
  };

  const openChunkInspector = async (doc: DocumentItem) => {
    setSelectedDoc(doc);
    setChunksLoading(true);
    try {
      const data = await api.getDocumentChunks(doc.document_id);
      setChunks(data);
    } catch {
      setChunks([]);
    } finally {
      setChunksLoading(false);
    }
  };

  const handleReindex = async (docId: string) => {
    try {
      await api.reindexDocument(docId);
      loadDocuments();
    } catch (err: any) {
      alert(`Reindex error: ${err.message}`);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) return;

    setUploading(true);
    setUploadMessage(null);
    try {
      const formData = new FormData();
      formData.append('file', uploadFile);
      formData.append('classification', uploadClassification);
      formData.append('allowed_roles', uploadRoles);

      await api.uploadDocument(formData);
      setIsUploadOpen(false);
      setUploadFile(null);
      loadDocuments();
    } catch (err: any) {
      setUploadMessage(err.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const getClassificationBadge = (cls: string) => {
    switch (cls) {
      case 'INTERNAL':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'CONFIDENTIAL':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'RESTRICTED':
        return 'bg-orange-50 text-orange-700 border-orange-200';
      case 'HIGHLY_RESTRICTED':
        return 'bg-red-50 text-red-700 border-red-200';
      default:
        return 'bg-slate-50 text-slate-700 border-slate-200';
    }
  };

  return (
    <div className="p-4 sm:p-6 md:p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900">
            Knowledge Base Documents
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Manage enterprise knowledge files, index statuses, and document properties.
          </p>
        </div>

        {hasRole(['HR', 'ADMIN']) && (
          <button
            onClick={() => setIsUploadOpen(true)}
            className="flex items-center justify-center gap-1.5 px-3.5 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-sm transition-colors cursor-pointer w-full sm:w-auto"
          >
            <Upload className="w-3.5 h-3.5" />
            Upload Document
          </button>
        )}
      </div>

      {/* Filter & Search Bar */}
      <div className="bg-white border border-slate-200 rounded-xl p-3 sm:p-4 flex flex-col sm:flex-row gap-3 shadow-2xs">
        <form onSubmit={handleSearch} className="flex-1 relative">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search document title or keywords..."
            className="w-full pl-9 pr-3 py-2 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </form>

        <div className="flex items-center gap-2">
          <Filter className="w-3.5 h-3.5 text-slate-400 shrink-0" />
          <select
            value={classificationFilter}
            onChange={(e) => setClassificationFilter(e.target.value)}
            className="w-full sm:w-auto px-3 py-2 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-700 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="">All Classifications</option>
            <option value="INTERNAL">Internal</option>
            <option value="CONFIDENTIAL">Confidential</option>
            <option value="RESTRICTED">Restricted</option>
            <option value="HIGHLY_RESTRICTED">Highly Restricted</option>
          </select>
        </div>
      </div>

      {/* Document Table */}
      <div className="bg-white border border-slate-200 rounded-xl shadow-2xs overflow-x-auto">
        {loading ? (
          <div className="py-12 text-center text-xs text-slate-400">Loading documents...</div>
        ) : documents.length === 0 ? (
          <div className="py-12 text-center text-xs text-slate-400">No authorized documents found</div>
        ) : (
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase font-semibold text-[10px]">
              <tr>
                <th className="px-5 py-3">Document Title</th>
                <th className="px-4 py-3">Classification</th>
                <th className="px-4 py-3">Allowed Roles</th>
                <th className="px-4 py-3">Chunks</th>
                <th className="px-4 py-3">Effective Date</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {documents.map((doc) => (
                <tr key={doc.id} className="hover:bg-slate-50/70 transition-colors">
                  <td className="px-5 py-3 font-medium text-slate-900 flex items-center gap-2">
                    <FileText className="w-4 h-4 text-blue-600 shrink-0" />
                    <div>
                      <div className="font-semibold text-slate-800">{doc.title}</div>
                      <div className="text-[10px] text-slate-400 font-mono">{doc.file_name}</div>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`px-2 py-0.5 rounded border text-[10px] font-semibold ${getClassificationBadge(
                        doc.classification
                      )}`}
                    >
                      {doc.classification}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {doc.allowed_roles?.map((role, idx) => (
                        <span
                          key={idx}
                          className="px-1.5 py-0.2 rounded bg-slate-100 text-slate-700 text-[10px] font-medium"
                        >
                          {role}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-slate-600 font-mono">
                    {doc.chunk_count} chunks
                  </td>
                  <td className="px-4 py-3 text-slate-500">
                    {doc.effective_date || '2026-01-01'}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center justify-end gap-1.5">
                      <button
                        onClick={() => openChunkInspector(doc)}
                        className="p-1.5 rounded hover:bg-slate-100 text-slate-500 hover:text-blue-600 transition-colors"
                        title="View Chunks & ACL"
                      >
                        <Eye className="w-3.5 h-3.5" />
                      </button>

                      {hasRole(['HR', 'ADMIN']) && (
                        <button
                          onClick={() => handleReindex(doc.document_id)}
                          className="p-1.5 rounded hover:bg-slate-100 text-slate-500 hover:text-emerald-600 transition-colors"
                          title="Re-Index"
                        >
                          <RefreshCw className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Chunk Inspector Modal */}
      {selectedDoc && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-3xl w-full max-h-[85vh] flex flex-col shadow-2xl border border-slate-200">
            <div className="p-4 border-b border-slate-100 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-slate-900">{selectedDoc.title}</h3>
                <p className="text-[11px] text-slate-500">
                  Document ID: <span className="font-mono">{selectedDoc.document_id}</span> &bull; {chunks.length} Indexed Chunks
                </p>
              </div>
              <button
                onClick={() => setSelectedDoc(null)}
                className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-600"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-4 overflow-y-auto space-y-3 flex-1">
              {chunksLoading ? (
                <div className="py-12 text-center text-xs text-slate-400">Loading chunk details...</div>
              ) : chunks.length === 0 ? (
                <div className="py-12 text-center text-xs text-slate-400">No chunks found</div>
              ) : (
                chunks.map((chk) => (
                  <div key={chk.id} className="p-3 bg-slate-50 border border-slate-200 rounded-xl space-y-2">
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="font-bold text-slate-800">
                        Chunk #{chk.chunk_index + 1} &bull; {chk.section || 'Overview'}
                      </span>
                      <div className="flex items-center gap-1.5">
                        <span className="text-[10px] text-slate-400">Tokens: {chk.token_count}</span>
                        <span className={`px-1.5 py-0.2 rounded border text-[9px] font-semibold ${getClassificationBadge(chk.classification)}`}>
                          {chk.classification}
                        </span>
                      </div>
                    </div>
                    <p className="text-xs text-slate-600 whitespace-pre-wrap font-sans bg-white p-2.5 rounded-lg border border-slate-100">
                      {chk.content}
                    </p>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* Upload Document Modal */}
      {isUploadOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-900">Upload Enterprise Document</h3>
              <button
                onClick={() => setIsUploadOpen(false)}
                className="p-1 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-600"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {uploadMessage && (
              <div className="p-2.5 rounded-lg bg-red-50 text-red-600 text-xs border border-red-200">
                {uploadMessage}
              </div>
            )}

            <form onSubmit={handleUpload} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Select File (.md, .txt, .pdf, .docx)</label>
                <input
                  type="file"
                  required
                  onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                  className="w-full text-xs text-slate-600 file:mr-3 file:py-2 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Data Classification</label>
                <select
                  value={uploadClassification}
                  onChange={(e) => setUploadClassification(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-800"
                >
                  <option value="INTERNAL">INTERNAL (Employee Accessible)</option>
                  <option value="CONFIDENTIAL">CONFIDENTIAL (HR / Finance)</option>
                  <option value="RESTRICTED">RESTRICTED (HR / Finance / Admin)</option>
                  <option value="HIGHLY_RESTRICTED">HIGHLY_RESTRICTED (Admin Only)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Allowed Roles (Comma Separated)</label>
                <input
                  type="text"
                  value={uploadRoles}
                  onChange={(e) => setUploadRoles(e.target.value)}
                  placeholder="e.g. EMPLOYEE,HR,FINANCE,ADMIN"
                  className="w-full px-3 py-2 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-800"
                />
              </div>

              <div className="pt-2 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setIsUploadOpen(false)}
                  className="px-3 py-2 rounded-lg text-xs font-medium text-slate-600 hover:bg-slate-100"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={uploading || !uploadFile}
                  className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold disabled:opacity-50"
                >
                  {uploading ? 'Ingesting & Indexing...' : 'Ingest & Index'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
