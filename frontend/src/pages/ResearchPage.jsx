import React, { useState, useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import FilterPanel from '../components/FilterPanel';
import QueryHistory from '../components/QueryHistory';
import ReportViewer from '../components/ReportViewer';
import AgentLogStream from '../components/AgentLogStream';
import PaperUpload from '../components/PaperUpload';
import ChatBot from '../components/ChatBot';
import Toast from '../components/Toast';
import PaperResultsList from '../components/PaperResultsList';
import FloatingGenerateButton from '../components/FloatingGenerateButton';

const API = 'http://localhost:8000';

export default function ResearchPage() {
  const location = useLocation();

  const [query, setQuery] = useState('');
  const [filters, setFilters] = useState({
    domain: '',
    keywords: [],
    year_from: null,
    year_to: null,
    sort_by: 'relevance',
    source: 'arxiv',
  });

  const [history, setHistory] = useState([]);
  const [currentReport, setCurrentReport] = useState(null);
  const [currentQueryId, setCurrentQueryId] = useState(null);
  const [currentPapers, setCurrentPapers] = useState([]);

  const [isStreaming, setIsStreaming] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [logs, setLogs] = useState([]);

  const [toast, setToast] = useState(null);
  const abortControllerRef = useRef(null);

  // Two-step search flow state
  const [searchResults, setSearchResults] = useState([]);
  const [selectedPapers, setSelectedPapers] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [paperCount, setPaperCount] = useState(10);
  const [hasSearched, setHasSearched] = useState(false);

  // Follow-up questions state
  const [followups, setFollowups] = useState([]);

  // Guard to prevent double auto-search
  const autoSearchDone = useRef(false);

  // On mount: auto-populate query from location state AND auto-trigger search
  useEffect(() => {
    if (location.state?.query && !autoSearchDone.current) {
      autoSearchDone.current = true;
      setQuery(location.state.query);
      // Auto-trigger search after state is set
      setTimeout(() => {
        searchPapers(null, location.state.query, 10);
      }, 300);
    }
    if (location.state?.source) {
      setFilters(prev => ({ ...prev, source: location.state.source }));
    }
    if (location.state?.queryId) {
      loadPastQuery(location.state.queryId);
    }
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const res = await fetch(`${API}/api/history`);
      if (res.ok) setHistory(await res.json());
    } catch { }
  };

  const showToast = (message, type = 'info') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 5000);
  };

  const handleUploadComplete = (results, useUploadedOnly = true) => {
    const successResults = results.filter(r => r.status === 'success');
    const count = successResults.length;
    if (count > 0) {
      showToast(`${count} document(s) embedded. Starting analysis...`, 'success');
      const newSource = useUploadedOnly ? 'uploaded' : 'both';
      setFilters(prev => ({ ...prev, source: newSource }));

      // Build a specific query using the uploaded paper titles/filenames
      const paperNames = successResults
        .map(r => r.title || r.filename || 'uploaded document')
        .join(', ');
      const promptQuery = query.trim()
        || `Please provide a detailed analysis of the uploaded paper(s): ${paperNames}. Summarize the key findings, methodology, results, and conclusions.`;
      if (!query.trim()) setQuery(promptQuery);
      generateReport(null, promptQuery, { ...filters, source: newSource });
    }
  };

  const loadPastQuery = async (queryId) => {
    setLogs([]);
    setSearchResults([]);
    setSelectedPapers([]);
    setHasSearched(false);
    setFollowups([]);
    try {
      const res = await fetch(`${API}/api/history/${queryId}`);
      if (res.ok) {
        const data = await res.json();
        setCurrentQueryId(data.query_id);
        setQuery(data.query);
        setCurrentReport(data.report);
        if (data.papers) setCurrentPapers(data.papers);
        setIsComplete(true);
        setIsStreaming(false);
      }
    } catch {
      showToast('Error loading past report', 'error');
    }
  };

  const deleteQuery = async (queryId) => {
    try {
      const res = await fetch(`${API}/api/history/${queryId}`, { method: 'DELETE' });
      if (res.ok) {
        showToast('Report deleted', 'success');
        fetchHistory();
        if (currentQueryId === queryId) {
          setCurrentReport(null);
          setCurrentQueryId(null);
          setQuery('');
          setCurrentPapers([]);
          setIsComplete(false);
          setLogs([]);
          setFollowups([]);
        }
      }
    } catch {
      showToast('Failed to delete report', 'error');
    }
  };

  // ────────────────────────────────────────────────
  // Step 1: Search papers (zero tokens)
  // ────────────────────────────────────────────────
  const searchPapers = async (e, queryOverride = null, countOverride = null) => {
    if (e) e.preventDefault();
    const activeQuery = queryOverride || query;
    const activeCount = countOverride || paperCount;
    if (!activeQuery.trim() || isSearching) return;

    setIsSearching(true);
    setSearchResults([]);
    setSelectedPapers([]);
    setCurrentReport(null);
    setCurrentQueryId(null);
    setCurrentPapers([]);
    setHasSearched(false);
    setFollowups([]);

    try {
      const res = await fetch(`${API}/api/search-papers`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: activeQuery,
          filters: { ...filters, paper_count: activeCount },
          mode: 'expert',
        }),
      });
      if (res.ok) {
        const papers = await res.json();
        setSearchResults(papers);
        setHasSearched(true);
      } else {
        showToast('Search failed', 'error');
      }
    } catch (err) {
      showToast('Search connection failed', 'error');
    } finally {
      setIsSearching(false);
    }
  };

  // ────────────────────────────────────────────────
  // Paper selection handlers
  // ────────────────────────────────────────────────
  const togglePaper = (paper) => {
    const id = paper.url || paper.title;
    setSelectedPapers(prev => {
      const exists = prev.find(p => (p.url || p.title) === id);
      return exists
        ? prev.filter(p => (p.url || p.title) !== id)
        : [...prev, paper];
    });
  };

  const selectAllPapers = () => setSelectedPapers([...searchResults]);
  const clearAllPapers = () => setSelectedPapers([]);

  // ────────────────────────────────────────────────
  // Step 2: Generate report (LLM tokens only here)
  // ────────────────────────────────────────────────
  const generateReport = async (e, overrideQuery = null, overrideFilters = null, papersToUse = []) => {
    if (e) e.preventDefault();

    const activeQuery = overrideQuery || query;
    const activeFilters = overrideFilters || filters;

    if (!activeQuery.trim() || isStreaming) return;

    setCurrentReport('');
    setCurrentQueryId(null);
    setCurrentPapers([]);
    setLogs([]);
    setIsStreaming(true);
    setIsComplete(false);
    setSearchResults([]);
    setHasSearched(false);
    setFollowups([]);

    if (abortControllerRef.current) abortControllerRef.current.abort();
    abortControllerRef.current = new AbortController();

    try {
      const endpoint = activeFilters.source === 'uploaded' ? '/api/query-uploaded' : '/api/query';
      const response = await fetch(`${API}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: activeQuery,
          filters: activeFilters,
          mode: 'expert',
          selected_papers: papersToUse,
        }),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let reportText = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        const lines = decoder.decode(value, { stream: true }).split('\n\n').filter(Boolean);
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          try {
            const data = JSON.parse(line.substring(6));
            if (data.type === 'metadata') {
              const qid = data.query_id || data.id || data.content;
              if (qid) setCurrentQueryId(qid);
            }
            else if (data.type === 'chunk') {
              reportText += data.content;
              setCurrentReport(reportText);
            }
            else if (data.type === 'report') {
              reportText = data.content;
              setCurrentReport(reportText);
            }
            else if (data.type === 'papers') {
              if (Array.isArray(data.content)) {
                setCurrentPapers(data.content);
              }
            }
            else if (data.type === 'followups') {
              if (Array.isArray(data.content)) {
                setFollowups(data.content);
              }
            }
            else if (data.type === 'thought' ||
              data.type === 'action' ||
              data.type === 'observation') {
              setLogs(prev => [...prev,
              `[${data.type.toUpperCase()}] ${data.content}`
              ]);
            }
            else if (data.type === 'log') {
              setLogs(prev => [...prev, data.content]);
            }
            else if (data.type === 'error') {
              showToast(`Agent Error: ${data.content}`, 'error');
              setLogs(prev => [...prev, `[ERROR] ${data.content}`]);
            }
            else if (data.type === 'done') {
              setIsComplete(true);
              setSelectedPapers([]);
              fetchHistory();
            }
          } catch { }
        }
      }
    } catch (err) {
      if (err.name !== 'AbortError') {
        showToast('Connection to agent failed', 'error');
      }
    } finally {
      setIsStreaming(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-56px)] bg-slate-900 text-slate-100 text-sm font-sans">
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}

      <main className="max-w-[1600px] mx-auto p-4 md:p-6 grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Sidebar */}
        <aside className="lg:col-span-3 space-y-4 flex flex-col h-[calc(100vh-7rem)] sticky top-20">
          <div className="flex-shrink-0 space-y-4">
            <PaperUpload onUploadComplete={handleUploadComplete} />
            <FilterPanel filters={filters} setFilters={setFilters} />
          </div>
          <div className="flex-1 min-h-[200px] overflow-y-auto">
            <QueryHistory
              history={history}
              currentQueryId={currentQueryId}
              onSelectQuery={loadPastQuery}
              onDeleteQuery={deleteQuery}
            />
          </div>
        </aside>

        {/* Center: Search + Papers + Report */}
        <div className="lg:col-span-6 flex flex-col gap-4 h-[calc(100vh-7rem)]">
          {/* Search bar */}
          <div className="bg-slate-800 border border-slate-700 rounded-2xl p-2 shadow-sm">
            <form onSubmit={searchPapers} className="flex relative">
              <input
                type="text"
                value={query}
                onChange={e => setQuery(e.target.value)}
                placeholder={filters.source === 'uploaded' ? 'Synthesize uploaded PDFs...' : 'Search for research papers...'}
                className="flex-1 bg-transparent border-none py-3 pl-4 pr-40 text-base text-white placeholder:text-slate-500 outline-none"
                disabled={isSearching || isStreaming}
              />
              <button
                type="submit"
                disabled={isSearching || isStreaming || !query.trim()}
                className="absolute right-2 top-1/2 -translate-y-1/2 px-5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl font-semibold text-sm disabled:opacity-40 transition-all flex items-center gap-2"
              >
                {isSearching ? (
                  <>
                    <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Searching...
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                    Search Papers
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Content area */}
          <div className="flex-1 overflow-y-auto">
            {/* Show paper results after search */}
            {(hasSearched || isSearching) && !currentReport && (
              <PaperResultsList
                papers={searchResults}
                selectedPapers={selectedPapers}
                onToggle={togglePaper}
                onSelectAll={selectAllPapers}
                onClearAll={clearAllPapers}
                paperCount={paperCount}
                onPaperCountChange={(n) => {
                  setPaperCount(n);
                  searchPapers(null, null, n);
                }}
                isLoading={isSearching}
              />
            )}

            {/* Show report after generation */}
            {currentReport && (
              <ReportViewer
                report={currentReport}
                queryId={currentQueryId}
                isStreaming={isStreaming}
                isComplete={isComplete}
                papers={currentPapers}
              />
            )}

            {/* Follow-up questions */}
            {followups.length > 0 && (
              <div className="mt-4 p-4 bg-slate-800 border border-slate-700 rounded-xl">
                <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-3">
                  Explore Further
                </p>
                <div className="flex flex-wrap gap-2">
                  {followups.map((q, i) => (
                    <button
                      key={i}
                      onClick={() => {
                        setQuery(q);
                        searchPapers(null, q, paperCount);
                      }}
                      className="text-xs px-3 py-1.5 rounded-full border border-slate-600 text-slate-300 hover:border-indigo-500 hover:text-indigo-300 transition-colors text-left"
                    >
                      → {q}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Empty state */}
            {!hasSearched && !isSearching && !currentReport && (
              <div className="flex flex-col items-center justify-center h-64 text-slate-500">
                <svg className="w-12 h-12 mb-3 opacity-30" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                <p className="text-sm">Search for papers to begin</p>
                <p className="text-xs mt-1 opacity-60">Select papers then generate your report</p>
              </div>
            )}
          </div>
        </div>

        {/* Right Sidebar — Agent Logs only (ChatBot is now floating) */}
        <aside className="lg:col-span-3 flex flex-col gap-4 h-[calc(100vh-7rem)] sticky top-20">
          <div className="flex-1">
            <AgentLogStream logs={logs} isLoading={isStreaming} />
          </div>
        </aside>
      </main>

      {/* Floating generate button */}
      <FloatingGenerateButton
        selectedCount={selectedPapers.length}
        onGenerate={() => generateReport(null, null, null, selectedPapers)}
        isGenerating={isStreaming}
        onSelectAll={selectAllPapers}
        onClearAll={clearAllPapers}
      />

      {/* Floating chat bubble */}
      <ChatBot queryId={currentQueryId} />
    </div>
  );
}
