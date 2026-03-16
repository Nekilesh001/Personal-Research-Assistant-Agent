import { useState, useCallback, useEffect } from 'react';
import QueryInput from './components/QueryInput';
import FilterPanel from './components/FilterPanel';
import AgentLogStream from './components/AgentLogStream';
import ReportViewer from './components/ReportViewer';
import ContradictionPanel from './components/ContradictionPanel';
import FollowUpSuggestions from './components/FollowUpSuggestions';
import QueryHistory from './components/QueryHistory';

const API_BASE = '/api';

/**
 * Main application component — orchestrates the research assistant UI.
 *
 * Layout: Left sidebar (history) | Main area (query + report) | Right panel (agent logs)
 */
export default function App() {
  /* ─── State ──────────────────────────────────────── */
  const [query, setQuery] = useState('');
  const [mode, setMode] = useState('expert');
  const [filters, setFilters] = useState({
    domain: null,
    keywords: [],
    year_from: null,
    year_to: null,
    paper_count: 5,
    sort_by: 'relevance',
    source: 'both',
  });
  const [isLoading, setIsLoading] = useState(false);
  const [agentLogs, setAgentLogs] = useState([]);
  const [report, setReport] = useState('');
  const [contradictions, setContradictions] = useState([]);
  const [followups, setFollowups] = useState([]);
  const [papers, setPapers] = useState([]);
  const [history, setHistory] = useState([]);
  const [showFilters, setShowFilters] = useState(false);
  const [error, setError] = useState(null);

  /* ─── Fetch History on Mount ─────────────────────── */
  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const res = await fetch(`${API_BASE}/history`);
      if (res.ok) {
        const data = await res.json();
        setHistory(data);
      }
    } catch (err) {
      console.error('Failed to fetch history:', err);
    }
  };

  /* ─── Run Query via SSE ──────────────────────────── */
  const handleSubmit = useCallback(async (queryText) => {
    const searchQuery = queryText || query;
    if (!searchQuery.trim()) return;

    setIsLoading(true);
    setAgentLogs([]);
    setReport('');
    setContradictions([]);
    setFollowups([]);
    setPapers([]);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: searchQuery,
          filters,
          mode,
        }),
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const event = JSON.parse(line.slice(6));
              handleSSEEvent(event);
            } catch (parseErr) {
              // Skip malformed events
            }
          }
        }
      }
    } catch (err) {
      setError(err.message);
      setAgentLogs(prev => [...prev, { type: 'error', content: err.message }]);
    } finally {
      setIsLoading(false);
      fetchHistory();
    }
  }, [query, filters, mode]);

  /* ─── Handle Individual SSE Events ───────────────── */
  const handleSSEEvent = useCallback((event) => {
    switch (event.type) {
      case 'thought':
      case 'action':
      case 'observation':
      case 'error':
        setAgentLogs(prev => [...prev, event]);
        break;
      case 'report':
        setReport(event.content);
        break;
      case 'contradictions':
        setContradictions(event.content || []);
        break;
      case 'followups':
        setFollowups(event.content || []);
        break;
      case 'papers':
        setPapers(event.content || []);
        break;
      case 'done':
        break;
      default:
        break;
    }
  }, []);

  /* ─── Load Report from History ───────────────────── */
  const handleHistoryClick = useCallback(async (item) => {
    try {
      const res = await fetch(`${API_BASE}/report/${item.query_id}`);
      if (res.ok) {
        const data = await res.json();
        setQuery(data.query || item.query);
        setReport(data.report || '');
        setContradictions(data.contradictions || []);
        setFollowups(data.followups || []);
        setPapers(data.papers || []);
        setAgentLogs([{ type: 'observation', content: 'Loaded from history' }]);
        setError(null);
      }
    } catch (err) {
      console.error('Failed to load report:', err);
    }
  }, []);

  /* ─── Delete History Entry ───────────────────────── */
  const handleHistoryDelete = useCallback(async (queryId) => {
    try {
      await fetch(`${API_BASE}/history/${queryId}`, { method: 'DELETE' });
      fetchHistory();
    } catch (err) {
      console.error('Failed to delete history entry:', err);
    }
  }, []);

  /* ─── Follow-up Click ───────────────────────────── */
  const handleFollowupClick = useCallback((followupQuery) => {
    setQuery(followupQuery);
    handleSubmit(followupQuery);
  }, [handleSubmit]);

  /* ─── Render ─────────────────────────────────────── */
  return (
    <div className="min-h-screen bg-bg-primary flex">
      {/* ─── Left Sidebar: Query History ─── */}
      <aside className="w-72 border-r border-border bg-bg-surface flex-shrink-0 flex flex-col h-screen sticky top-0">
        <div className="p-4 border-b border-border">
          <h1 className="text-lg font-bold gradient-text">Research Assistant</h1>
          <p className="text-xs text-text-muted mt-1">AI-Powered Paper Analysis</p>
        </div>
        <QueryHistory
          history={history}
          onSelect={handleHistoryClick}
          onDelete={handleHistoryDelete}
        />
      </aside>

      {/* ─── Main Content Area ─── */}
      <main className="flex-1 flex flex-col h-screen overflow-hidden">
        {/* Query Input Header */}
        <header className="p-4 border-b border-border bg-bg-surface/50 backdrop-blur-sm">
          <QueryInput
            query={query}
            setQuery={setQuery}
            mode={mode}
            setMode={setMode}
            onSubmit={handleSubmit}
            isLoading={isLoading}
          />
          <div className="mt-3">
            <button
              id="filter-toggle-btn"
              onClick={() => setShowFilters(!showFilters)}
              className="text-sm text-text-secondary hover:text-accent-primary transition-colors flex items-center gap-1.5"
            >
              <svg className={`w-4 h-4 transition-transform ${showFilters ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
              {showFilters ? 'Hide Filters' : 'Show Advanced Filters'}
            </button>
            {showFilters && (
              <div className="mt-3 animate-fade-in">
                <FilterPanel filters={filters} setFilters={setFilters} mode={mode} />
              </div>
            )}
          </div>
        </header>

        {/* Results Area */}
        <div className="flex-1 overflow-y-auto p-6">
          {error && (
            <div className="mb-4 p-4 rounded-lg border border-error/30 bg-error/5 text-error animate-fade-in">
              <p className="font-medium">⚠ Error</p>
              <p className="text-sm mt-1">{error}</p>
            </div>
          )}

          {report ? (
            <div className="animate-fade-in space-y-6">
              <ReportViewer report={report} />

              {contradictions.length > 0 && (
                <ContradictionPanel contradictions={contradictions} />
              )}

              {followups.length > 0 && (
                <FollowUpSuggestions
                  followups={followups}
                  onSelect={handleFollowupClick}
                />
              )}
            </div>
          ) : !isLoading ? (
            /* Empty State */
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="w-20 h-20 rounded-2xl bg-accent-primary/10 flex items-center justify-center mb-6">
                <svg className="w-10 h-10 text-accent-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
              </div>
              <h2 className="text-xl font-semibold text-text-primary mb-2">Start Your Research</h2>
              <p className="text-text-secondary max-w-md">
                Enter a research topic above to fetch and analyze academic papers from arXiv and Semantic Scholar.
              </p>
              <div className="flex gap-2 mt-6 flex-wrap justify-center">
                {['Transformer architectures', 'CRISPR gene editing 2024', 'Quantum error correction'].map(example => (
                  <button
                    key={example}
                    onClick={() => { setQuery(example); handleSubmit(example); }}
                    className="px-3 py-1.5 rounded-full text-sm bg-bg-surface border border-border text-text-secondary hover:text-accent-primary hover:border-accent-primary/50 transition-all duration-200"
                  >
                    {example}
                  </button>
                ))}
              </div>
            </div>
          ) : null}
        </div>
      </main>

      {/* ─── Right Panel: Agent Log Stream ─── */}
      <aside className="w-80 border-l border-border bg-bg-surface flex-shrink-0 h-screen sticky top-0 flex flex-col">
        <div className="p-4 border-b border-border flex items-center gap-2">
          <div className={`${isLoading ? 'pulse-dot' : 'w-2 h-2 rounded-full bg-text-muted'}`} />
          <h2 className="text-sm font-semibold text-text-primary">Agent Reasoning</h2>
        </div>
        <AgentLogStream logs={agentLogs} isLoading={isLoading} />
      </aside>
    </div>
  );
}
