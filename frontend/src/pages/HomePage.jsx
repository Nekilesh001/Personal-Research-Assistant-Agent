import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const API = 'http://localhost:8000/api';

const FEATURE_CARDS = [
  {
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
      </svg>
    ),
    title: 'Search Papers',
    desc: 'Fetch and synthesize from arXiv and Semantic Scholar automatically.',
    color: 'from-indigo-500 to-blue-500',
  },
  {
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>
        <line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/>
      </svg>
    ),
    title: 'Upload PDFs',
    desc: 'Analyze your own papers. Report generated from your documents only.',
    color: 'from-purple-500 to-pink-500',
  },
  {
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
      </svg>
    ),
    title: 'AI Chat',
    desc: 'Chat with an AI that understands your report. History persists across restarts.',
    color: 'from-teal-500 to-emerald-500',
  },
];

export default function HomePage() {
  const [query, setQuery] = useState('');
  const [mode, setMode] = useState('expert');
  const [recentHistory, setRecentHistory] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    fetch(`${API}/history`)
      .then(r => r.json())
      .then(data => setRecentHistory(data.slice(0, 3)))
      .catch(() => {});
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    navigate('/research', { state: { query, mode } });
  };

  return (
    <div className="min-h-[calc(100vh-56px)] bg-app flex flex-col items-center justify-start px-4 py-16 transition-colors duration-300">

      {/* Hero */}
      <div className="text-center mb-12 max-w-2xl animate-fade-in">
        <div
          className="inline-flex items-center gap-2 border px-4 py-1.5 rounded-full text-xs font-semibold mb-6 uppercase tracking-wider"
          style={{ backgroundColor: 'var(--accent-subtle)', borderColor: 'var(--accent-primary)', color: 'var(--accent-primary)' }}
        >
          ⚡ Powered by Groq LLaMA-3
        </div>
        <h1 className="text-5xl font-extrabold mb-4 leading-tight" style={{ color: 'var(--text-primary)' }}>
          Personal Research<br />
          <span className="text-gradient">Assistant</span>
        </h1>
        <p className="text-lg" style={{ color: 'var(--text-secondary)' }}>
          AI-powered academic research synthesis. Get comprehensive reports from arXiv papers in seconds.
        </p>
      </div>

      {/* Search bar */}
      <form onSubmit={handleSubmit} className="w-full max-w-2xl mb-5 animate-fade-in">
        <div
          className="border rounded-2xl p-2 flex gap-2"
          style={{ backgroundColor: 'var(--bg-surface)', borderColor: 'var(--border-color)', boxShadow: 'var(--shadow-lg)' }}
        >
          <input
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="e.g. transformer models for protein folding..."
            className="flex-1 bg-transparent outline-none text-base px-3 py-2"
            style={{ color: 'var(--text-primary)' }}
            autoFocus
          />
          <button
            type="submit"
            disabled={!query.trim()}
            className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white rounded-xl font-semibold text-sm transition-all shrink-0 shadow-sm"
          >
            Start Research →
          </button>
        </div>
      </form>

      {/* Mode toggle */}
      <div className="flex items-center gap-2 mb-14 animate-fade-in">
        <span className="text-sm" style={{ color: 'var(--text-muted)' }}>Mode:</span>
        {['expert', 'beginner'].map(m => (
          <button
            key={m}
            onClick={() => setMode(m)}
            className={`px-4 py-1.5 rounded-full text-sm font-medium transition-all capitalize ${
              mode === m
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'border'
            }`}
            style={mode !== m ? {
              backgroundColor: 'var(--bg-surface)',
              color: 'var(--text-secondary)',
              borderColor: 'var(--border-color)',
            } : {}}
          >
            {m}
          </button>
        ))}
      </div>

      {/* Feature cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 max-w-2xl w-full mb-12">
        {FEATURE_CARDS.map(card => (
          <div
            key={card.title}
            className="card rounded-2xl p-5 animate-fade-in"
          >
            <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${card.color} flex items-center justify-center text-white mb-3 shadow-sm`}>
              {card.icon}
            </div>
            <h3 className="font-semibold text-sm mb-1" style={{ color: 'var(--text-primary)' }}>{card.title}</h3>
            <p className="text-xs leading-relaxed" style={{ color: 'var(--text-secondary)' }}>{card.desc}</p>
          </div>
        ))}
      </div>

      {/* Recent searches */}
      {recentHistory.length > 0 && (
        <div className="max-w-2xl w-full animate-fade-in">
          <p className="text-xs uppercase tracking-wider mb-3 font-medium" style={{ color: 'var(--text-muted)' }}>
            Recent Searches
          </p>
          <div className="flex flex-wrap gap-2">
            {recentHistory.map(item => (
              <button
                key={item.query_id}
                onClick={() => navigate('/research', { state: { query: item.query, mode: item.mode } })}
                className="border text-sm px-3 py-1.5 rounded-lg truncate max-w-xs transition-all hover:border-indigo-500"
                style={{
                  backgroundColor: 'var(--bg-surface)',
                  color: 'var(--text-secondary)',
                  borderColor: 'var(--border-color)',
                }}
              >
                {item.query}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
