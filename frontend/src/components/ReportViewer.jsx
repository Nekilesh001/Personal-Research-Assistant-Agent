import { useCallback, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import SkeletonLoader from './SkeletonLoader';

/**
 * ReportViewer — Renders the markdown research report with a download button.
 *
 * Uses react-markdown with remark-gfm for GitHub Flavored Markdown
 * (tables, strikethrough, task lists, etc.).
 */
export default function ReportViewer({ report, queryId, isStreaming, isComplete, papers = [] }) {
  const [downloading, setDownloading] = useState(false);

  /**
   * Download the report as a PDF using the backend generator.
   */
  const handleDownloadPdf = useCallback(async () => {
    if (!queryId) return;
    setDownloading(true);
    try {
      const res = await fetch(`http://localhost:8000/api/report/${queryId}/pdf`);
      if (!res.ok) throw new Error("Failed to download PDF");

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `Research_Report_${queryId.slice(0, 8)}.pdf`;
      document.body.appendChild(link);
      link.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(link);
    } catch (err) {
      console.error(err);
      alert("Failed to download PDF. Please try again.");
    } finally {
      setDownloading(false);
    }
  }, [queryId]);

  if (!report && isStreaming) {
    return (
      <div className="glass rounded-xl overflow-hidden min-h-[400px]">
        <SkeletonLoader />
      </div>
    );
  }

  if (!report) {
    return (
      <div className="glass rounded-xl overflow-hidden min-h-[400px] flex flex-col items-center justify-center text-text-secondary">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="48"
          height="48"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="mb-4 opacity-50"
        >
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
          <polyline points="14 2 14 8 20 8" />
          <line x1="16" y1="13" x2="8" y2="13" />
          <line x1="16" y1="17" x2="8" y2="17" />
          <polyline points="10 9 9 9 8 9" />
        </svg>
        <p className="text-lg font-medium">No report generated yet</p>
        <p className="text-sm opacity-70">Enter a query on the left to begin research</p>
      </div>
    );
  }

  return (
    <div className="glass rounded-xl overflow-hidden relative" id="report-viewer">
      {/* Header Bar */}
      <div className="flex items-center justify-between px-5 py-3 border-b border-border bg-bg-surface/50">
        <div className="flex items-center gap-2">
          <svg className="w-4 h-4 text-accent-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <span className="text-sm font-semibold text-text-primary">Research Report</span>
        </div>
        
        <div className="flex gap-2">
          {isStreaming && (
            <span className="flex items-center gap-2 rounded-full bg-accent-primary/10 px-3 py-1 text-xs font-semibold text-accent-primary">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-accent-secondary opacity-75"></span>
                <span className="relative inline-flex h-2 w-2 rounded-full bg-accent-primary"></span>
              </span>
              Generating...
            </span>
          )}

          {!isStreaming && queryId && (
            <button
              onClick={handleDownloadPdf}
              disabled={downloading}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-accent-primary/10 text-accent-primary hover:bg-accent-primary/20 transition-colors disabled:opacity-50"
            >
              {downloading ? (
                <svg className="h-3.5 w-3.5 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              ) : (
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
              )}
              Download PDF
            </button>
          )}
        </div>
      </div>

      {/* Report Content — white document panel */}
      <div 
        className="p-8 bg-white rounded-b-xl min-h-[300px]"
        style={{ backgroundColor: '#ffffff', color: '#1e293b' }}
      >
        <div 
          className="prose prose-slate max-w-none prose-headings:text-slate-900 prose-p:text-slate-700 prose-strong:text-slate-900 prose-a:text-indigo-600 prose-code:text-indigo-700 prose-code:bg-indigo-50 prose-code:rounded prose-code:px-1 prose-code:py-0.5 prose-pre:bg-slate-900 prose-pre:text-slate-100 prose-blockquote:border-indigo-400 prose-blockquote:text-slate-600"
          style={{ color: '#1e293b' }}
        >
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {report}
          </ReactMarkdown>

          {papers && papers.length > 0 && (
            <div 
              className="mt-8 pt-6 border-t border-slate-200"
              style={{ color: '#1e293b' }}
            >
              <h3 
                className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-3"
                style={{ color: '#64748b' }}
              >
                Sources Analyzed ({papers.length} papers)
              </h3>
              <div className="space-y-2">
                {papers.map((paper, idx) => (
                  <div key={idx} className="flex items-start gap-3 text-sm">
                    <span className="text-slate-400 font-mono text-xs mt-0.5 w-5 flex-shrink-0">
                      {idx + 1}.
                    </span>
                    <div>
                      <a
                        href={paper.url || '#'}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-indigo-600 hover:underline font-medium"
                        style={{ color: '#4f46e5' }}
                      >
                        {paper.title}
                      </a>
                      <p 
                        className="text-slate-500 text-xs mt-0.5"
                        style={{ color: '#64748b' }}
                      >
                        {Array.isArray(paper.authors)
                          ? paper.authors
                              .slice(0, 3)
                              .join(', ')
                          : paper.authors}
                        {paper.authors?.length > 3 
                          ? ' et al.' : ''}
                        {paper.year 
                          ? ` (${paper.year})` : ''}
                        {paper.citation_count
                          ? ` · ${paper.citation_count} citations`
                          : ''}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
