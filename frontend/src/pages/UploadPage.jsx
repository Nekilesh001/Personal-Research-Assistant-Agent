import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';

const API = 'http://localhost:8000/api';

export default function UploadPage() {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [useArxiv, setUseArxiv] = useState(false);
  const [query, setQuery] = useState('');
  const [mode, setMode] = useState('expert');
  const [isHovering, setIsHovering] = useState(false);
  const fileInputRef = useRef(null);
  const navigate = useNavigate();

  const handleDragOver = (e) => { e.preventDefault(); setIsHovering(true); };
  const handleDragLeave = (e) => { e.preventDefault(); setIsHovering(false); };
  const handleDrop = (e) => {
    e.preventDefault();
    setIsHovering(false);
    const dropped = Array.from(e.dataTransfer.files).filter(f => f.type === 'application/pdf');
    setFiles(prev => [...prev, ...dropped].slice(0, 5));
  };
  const handleFileSelect = (e) => {
    setFiles(prev => [...prev, ...Array.from(e.target.files)].slice(0, 5));
  };
  const removeFile = (i) => setFiles(prev => prev.filter((_, idx) => idx !== i));

  const handleUpload = async () => {
    if (!files.length) return;
    setUploading(true);
    const formData = new FormData();
    files.forEach(f => formData.append('files', f));
    try {
      const res = await fetch(`${API}/upload-papers`, { method: 'POST', body: formData });
      const data = await res.json();
      setUploadedFiles(data.filter(r => r.status === 'success'));
      setFiles([]);
    } catch (err) {
      alert('Upload failed. Ensure backend is running.');
    } finally {
      setUploading(false);
    }
  };

  const handleGenerate = () => {
    if (!query.trim() || !uploadedFiles.length) return;
    navigate('/research', {
      state: {
        query,
        mode,
        source: useArxiv ? 'both' : 'uploaded',
      }
    });
  };

  return (
    <div className="min-h-[calc(100vh-56px)] bg-slate-900 px-4 py-8">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-2xl font-bold text-white mb-2">Upload Research Papers</h1>
        <p className="text-slate-400 text-sm mb-8">Upload PDFs to analyze them with AI and generate custom reports.</p>

        {/* Drop Zone */}
        <div
          className={`border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer transition-all mb-6 ${
            isHovering
              ? 'border-indigo-500 bg-indigo-600/10'
              : 'border-slate-700 hover:border-slate-600 bg-slate-800/40'
          }`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <input type="file" ref={fileInputRef} onChange={handleFileSelect} multiple accept="application/pdf" className="hidden" />
          <div className="text-4xl mb-3">📄</div>
          <p className="text-white font-semibold mb-1">Click or drag & drop PDFs here</p>
          <p className="text-slate-400 text-sm">Up to 5 files, 10MB each</p>
        </div>

        {/* Pending files */}
        {files.length > 0 && (
          <div className="space-y-2 mb-4">
            {files.map((f, i) => (
              <div key={i} className="flex items-center justify-between bg-slate-800 border border-slate-700 rounded-xl px-4 py-3">
                <span className="text-sm text-white truncate">{f.name}</span>
                <button onClick={() => removeFile(i)} className="text-slate-400 hover:text-red-400 ml-2">✕</button>
              </div>
            ))}
            <button
              onClick={handleUpload}
              disabled={uploading}
              className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-xl font-medium text-sm transition-all"
            >
              {uploading ? 'Processing...' : `Process ${files.length} Paper${files.length > 1 ? 's' : ''}`}
            </button>
          </div>
        )}

        {/* Uploaded files */}
        {uploadedFiles.length > 0 && (
          <div className="bg-slate-800/50 border border-slate-700 rounded-2xl p-5 mb-6">
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
              ✅ {uploadedFiles.length} Paper{uploadedFiles.length > 1 ? 's' : ''} Ready
            </p>
            <div className="grid grid-cols-2 gap-2 mb-5">
              {uploadedFiles.map((f, i) => (
                <div key={i} className="bg-slate-700/50 rounded-lg p-3 text-xs">
                  <p className="text-white font-medium truncate">{f.filename}</p>
                  <p className="text-slate-400 mt-0.5">{f.page_count} pages extracted</p>
                </div>
              ))}
            </div>

            {/* Query input */}
            <div className="space-y-3">
              <label className="block text-sm text-slate-300 font-medium">
                What would you like to know about these papers?
              </label>
              <input
                type="text"
                value={query}
                onChange={e => setQuery(e.target.value)}
                placeholder="e.g. What are the main findings and limitations?"
                className="w-full bg-slate-900 border border-slate-600 rounded-xl px-4 py-2.5 text-white text-sm outline-none focus:border-indigo-500 placeholder:text-slate-500"
              />

              {/* Mode toggle */}
              <div className="flex items-center gap-2">
                <span className="text-sm text-slate-400">Mode:</span>
                {['expert', 'beginner'].map(m => (
                  <button
                    key={m}
                    onClick={() => setMode(m)}
                    className={`px-3 py-1 rounded-lg text-xs font-medium capitalize transition-all ${
                      mode === m ? 'bg-indigo-600 text-white' : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                    }`}
                  >
                    {m}
                  </button>
                ))}
              </div>

              {/* Arxiv toggle */}
              <label className="flex items-center gap-2 text-sm text-slate-400 cursor-pointer">
                <input
                  type="checkbox"
                  checked={useArxiv}
                  onChange={e => setUseArxiv(e.target.checked)}
                  className="rounded"
                />
                Combine with arXiv search (broader coverage)
              </label>

              <button
                onClick={handleGenerate}
                disabled={!query.trim()}
                className="w-full py-3 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white rounded-xl font-semibold text-sm transition-all"
              >
                Generate Report from {uploadedFiles.length} Paper{uploadedFiles.length > 1 ? 's' : ''} →
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
