import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const API = 'http://localhost:8000/api';

const FEATURE_CARDS = [
  {
    icon: '🔬',
    title: 'Search Papers',
    desc: 'Automatically fetches and synthesizes papers from arXiv and Semantic Scholar.',
  },
  {
    icon: '📄',
    title: 'Upload PDFs',
    desc: 'Analyze your own research papers and generate reports from uploaded documents.',
  },
  {
    icon: '💬',
    title: 'AI Chat',
    desc: 'Discuss findings with an AI assistant that understands your report context.',
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
    <div className="min-h-[calc(100vh-56px)] bg-slate-900 flex flex-col items-center justify-start px-4 py-16">
      {/* Hero */}
      <div className="text-center mb-12 max-w-2xl">
        <div className="inline-flex items-center gap-2 bg-indigo-600/20 border border-indigo-600/40 text-indigo-400 px-4 py-1.5 rounded-full text-xs font-semibold mb-6 uppercase tracking-wider">
          ⚡ Powered by Groq LLaMA-3
        </div>
        <h1 className="text-5xl font-extrabold text-white mb-4 leading-tight">
          Personal Research<br />
          <span className="bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
            Assistant
          </span>
        </h1>
        <p className="text-lg text-slate-400">
          AI-powered academic research synthesis. Get comprehensive reports from arXiv
          papers in seconds.
        </p>
      </div>

      {/* Search */}
      <form onSubmit={handleSubmit} className="w-full max-w-2xl mb-6">
        <div className="bg-slate-800 border border-slate-700 rounded-2xl p-2 flex gap-2 shadow-2xl">
          <input
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="e.g. transformer models for protein folding..."
            className="flex-1 bg-transparent outline-none text-white placeholder:text-slate-500 px-3 py-2 text-base"
            autoFocus
          />
          <button
            type="submit"
            disabled={!query.trim()}
            className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white rounded-xl font-semibold text-sm transition-all shrink-0"
          >
            Start Research →
          </button>
        </div>
      </form>

      {/* Mode toggle */}
      <div className="flex items-center gap-2 mb-14">
        <span className="text-slate-500 text-sm">Mode:</span>
        {['expert', 'beginner'].map(m => (
          <button
            key={m}
            onClick={() => setMode(m)}
            className={`px-4 py-1.5 rounded-full text-sm font-medium transition-all capitalize ${
              mode === m
                ? 'bg-indigo-600 text-white'
                : 'bg-slate-800 text-slate-400 hover:text-white border border-slate-700'
            }`}
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
            className="bg-slate-800/60 border border-slate-700 rounded-2xl p-5 hover:border-indigo-600/50 transition-all"
          >
            <div className="text-3xl mb-3">{card.icon}</div>
            <h3 className="font-semibold text-white text-sm mb-1">{card.title}</h3>
            <p className="text-slate-400 text-xs leading-relaxed">{card.desc}</p>
          </div>
        ))}
      </div>

      {/* Recent searches */}
      {recentHistory.length > 0 && (
        <div className="max-w-2xl w-full">
          <p className="text-slate-500 text-xs uppercase tracking-wider mb-3 font-medium">Recent Searches</p>
          <div className="flex flex-wrap gap-2">
            {recentHistory.map(item => (
              <button
                key={item.query_id}
                onClick={() => navigate('/research', { state: { query: item.query, mode: item.mode } })}
                className="bg-slate-800 border border-slate-700 hover:border-indigo-600/50 text-slate-300 text-sm px-3 py-1.5 rounded-lg truncate max-w-xs transition-all hover:text-white"
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
