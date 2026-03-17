import React, { useState, useRef } from 'react';

export default function PaperUpload({ onUploadComplete }) {
  const [isHovering, setIsHovering] = useState(false);
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [results, setResults] = useState(null);
  const [useUploadedOnly, setUseUploadedOnly] = useState(false);
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => { e.preventDefault(); setIsHovering(true); };
  const handleDragLeave = (e) => { e.preventDefault(); setIsHovering(false); };
  const handleDrop = (e) => {
    e.preventDefault();
    setIsHovering(false);
    const dropped = Array.from(e.dataTransfer.files).filter(f => f.type === 'application/pdf');
    if (dropped.length + files.length > 5) { alert('Maximum 5 files allowed.'); return; }
    setFiles(prev => [...prev, ...dropped].slice(0, 5));
    setResults(null);
  };
  const handleFileSelect = (e) => {
    const selected = Array.from(e.target.files);
    if (selected.length + files.length > 5) { alert('Maximum 5 files allowed.'); return; }
    setFiles(prev => [...prev, ...selected].slice(0, 5));
    setResults(null);
  };
  const removeFile = (i) => setFiles(prev => prev.filter((_, idx) => idx !== i));

  const uploadFiles = async () => {
    if (files.length === 0) return;
    setUploading(true);
    setResults(null);
    const formData = new FormData();
    files.forEach(f => formData.append('files', f));
    try {
      const res = await fetch('http://localhost:8000/api/upload-papers', { method: 'POST', body: formData });
      const data = await res.json();
      setResults(data);
      const hasSuccess = data.some(r => r.status === 'success');
      if (hasSuccess && onUploadComplete) onUploadComplete(data);
    } catch {
      alert('Error uploading files.');
    } finally {
      setUploading(false);
      setFiles([]);
    }
  };

  const successResults = results ? results.filter(r => r.status === 'success') : [];

  return (
    <div className="glass rounded-xl p-4 mb-4">
      <h3 className="text-sm font-semibold text-text-primary mb-3 flex items-center gap-2">
        <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-accent-primary">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
        </svg>
        Upload Papers
      </h3>

      {/* Drop Zone */}
      <div
        className={`border-2 border-dashed rounded-lg p-5 text-center transition-all cursor-pointer ${
          isHovering ? 'border-accent-primary bg-accent-primary/5' : 'border-border hover:bg-bg-surface'
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <input type="file" ref={fileInputRef} onChange={handleFileSelect} multiple accept="application/pdf" className="hidden" />
        <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="mx-auto text-text-tertiary mb-2">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="12" y1="18" x2="12" y2="12"/><line x1="9" y1="15" x2="15" y2="15"/>
        </svg>
        <p className="text-xs font-medium text-text-primary mb-0.5">Click to upload or drag & drop PDFs</p>
        <p className="text-xs text-text-secondary">Max 5 PDF files, up to 10MB each</p>
      </div>

      {/* Pending files */}
      {files.length > 0 && (
        <div className="mt-3 space-y-1.5">
          {files.map((f, i) => (
            <div key={i} className="flex items-center justify-between bg-bg-surface rounded border border-border px-3 py-1.5 text-xs">
              <span className="truncate max-w-[160px] text-text-primary">{f.name}</span>
              <button onClick={(e) => { e.stopPropagation(); removeFile(i); }} className="text-text-tertiary hover:text-red-400 ml-2">×</button>
            </div>
          ))}
          <button
            onClick={uploadFiles}
            disabled={uploading}
            className="w-full mt-2 py-2 bg-accent-primary text-white rounded-lg hover:bg-accent-primary/90 transition-colors disabled:opacity-50 text-xs font-medium"
          >
            {uploading ? 'Extracting & Embedding...' : 'Process Papers'}
          </button>
        </div>
      )}

      {/* Upload Results + Generate Button */}
      {results && results.length > 0 && (
        <div className="mt-3 pt-3 border-t border-border space-y-2">
          <h4 className="text-xs font-semibold text-text-secondary uppercase">Upload Results</h4>
          {results.map((res, i) => (
            <div key={i} className={`flex items-start gap-2 p-2 rounded text-xs border ${
              res.status === 'success'
                ? 'bg-state-success/10 border-state-success/20 text-state-success'
                : 'bg-state-error/10 border-state-error/20 text-state-error'
            }`}>
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="mt-0.5 shrink-0">
                {res.status === 'success' ? <polyline points="20 6 9 17 4 12"/> : <><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></>}
              </svg>
              <div>
                <span className="font-medium block truncate max-w-[170px]">{res.filename}</span>
                {res.status === 'success'
                  ? <span className="opacity-80">Extracted {res.page_count} pages • Ready for analysis</span>
                  : <span className="opacity-80">{res.message}</span>}
              </div>
            </div>
          ))}

          {/* Generate Report button — only shown after successful upload */}
          {successResults.length > 0 && (
            <div className="mt-3 space-y-2">
              <label className="flex items-center gap-2 text-xs text-text-secondary cursor-pointer">
                <input
                  type="checkbox"
                  checked={useUploadedOnly}
                  onChange={e => setUseUploadedOnly(e.target.checked)}
                  className="rounded"
                />
                Use ONLY uploaded papers (skip arXiv search)
              </label>
              <button
                onClick={() => {
                  if (onUploadComplete) onUploadComplete(successResults, useUploadedOnly);
                }}
                className="w-full py-2 px-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-medium transition-colors"
              >
                Generate Report from {successResults.length} Uploaded Paper{successResults.length > 1 ? 's' : ''}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
