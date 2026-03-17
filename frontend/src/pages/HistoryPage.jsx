import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const API = 'http://localhost:8000/api';

export default function HistoryPage() {
  const [history, setHistory] = useState([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetch(`${API}/history`)
      .then(r => r.json())
      .then(data => { setHistory(data); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  const handleDelete = async (queryId) => {
    await fetch(`${API}/history/${queryId}`, { method: 'DELETE' });
    setHistory(prev => prev.filter(h => h.query_id !== queryId));
  };

  const filtered = history.filter(h =>
    h.query.toLowerCase().includes(search.toLowerCase())
  );

  const groupByDate = (items) => {
    const groups = { Today: [], Yesterday: [], 'This Week': [], Older: [] };
    const now = new Date();
    items.forEach(item => {
      const d = new Date(item.created_at);
      const diffDays = Math.floor((now - d) / 86400000);
      if (diffDays === 0) groups['Today'].push(item);
      else if (diffDays === 1) groups['Yesterday'].push(item);
      else if (diffDays < 7) groups['This Week'].push(item);
      else groups['Older'].push(item);
    });
    return groups;
  };

  const groups = groupByDate(filtered);

  const formatDate = (str) => new Date(str).toLocaleString([], {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
  });

  return (
    <div className="min-h-[calc(100vh-56px)] bg-slate-900 px-4 py-8">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-white">Research History</h1>
            <p className="text-slate-400 text-sm mt-1">{history.length} saved queries</p>
          </div>
          <button
            onClick={() => navigate('/research')}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-medium"
          >
            New Research
          </button>
        </div>

        {/* Search */}
        <input
          type="text"
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Filter by query text..."
          className="w-full bg-slate-800 border border-slate-700 text-white rounded-xl px-4 py-2.5 text-sm outline-none focus:border-indigo-600 mb-6 placeholder:text-slate-500"
        />

        {loading && (
          <div className="text-slate-400 text-center py-16">Loading history...</div>
        )}

        {!loading && filtered.length === 0 && (
          <div className="text-center py-16">
            <div className="text-4xl mb-4">📋</div>
            <p className="text-slate-400">No research history yet.</p>
            <button
              onClick={() => navigate('/research')}
              className="mt-4 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-medium"
            >
              Start your first research
            </button>
          </div>
        )}

        {Object.entries(groups).map(([group, items]) => {
          if (items.length === 0) return null;
          return (
            <div key={group} className="mb-8">
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-3">{group}</p>
              <div className="space-y-3">
                {items.map(item => (
                  <div
                    key={item.query_id}
                    className="bg-slate-800 border border-slate-700 rounded-xl p-4 hover:border-indigo-600/50 transition-all group"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <p className="font-semibold text-white text-sm truncate">{item.query}</p>
                        <div className="flex items-center gap-3 mt-2">
                          <span className="text-xs text-slate-500">{formatDate(item.created_at)}</span>
                          <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${
                            item.mode === 'expert'
                              ? 'bg-indigo-900/50 text-indigo-300'
                              : 'bg-teal-900/50 text-teal-300'
                          }`}>
                            {item.mode}
                          </span>
                          {item.paper_count > 0 && (
                            <span className="text-xs text-slate-500">{item.paper_count} papers</span>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        <button
                          onClick={() => navigate('/research', { state: { queryId: item.query_id, query: item.query } })}
                          className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-medium opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                          View Report →
                        </button>
                        <button
                          onClick={() => handleDelete(item.query_id)}
                          className="p-1.5 text-slate-500 hover:text-red-400 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity"
                          title="Delete"
                        >
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
