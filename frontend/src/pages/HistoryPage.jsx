import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const API = 'http://localhost:8000/api';

const S = {
  wrap:      { backgroundColor: 'var(--bg-primary)' },
  card:      { backgroundColor: 'var(--bg-surface)', borderColor: 'var(--border-color)' },
  txt:       { color: 'var(--text-primary)' },
  txtSub:    { color: 'var(--text-secondary)' },
  txtMuted:  { color: 'var(--text-muted)' },
  input:     { backgroundColor: 'var(--bg-surface)', borderColor: 'var(--border-color)', color: 'var(--text-primary)' },
  msgUser:   { backgroundColor: 'var(--accent-primary)', color: '#fff' },
  msgBot:    { backgroundColor: 'var(--bg-surface-2)', color: 'var(--text-secondary)' },
};

function ChatTranscript({ queryId }) {
  const [messages, setMessages] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API}/chat/${queryId}/history`)
      .then(r => r.json())
      .then(data => { setMessages(data); setLoading(false); })
      .catch(() => setLoading(false));
  }, [queryId]);

  if (loading) return <p className="text-xs mt-2 px-1" style={S.txtMuted}>Loading chat…</p>;
  if (!messages || messages.length === 0)
    return <p className="text-xs mt-2 px-1 italic" style={S.txtMuted}>No chat messages for this report yet.</p>;

  return (
    <div className="mt-3 pt-3 border-t" style={{ borderColor: 'var(--border-color)' }}>
      <p className="text-[10px] font-semibold uppercase tracking-wider mb-2 flex items-center gap-1" style={S.txtMuted}>
        <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-3 3v-3z" />
        </svg>
        Chat History ({messages.length} messages)
      </p>
      <div className="space-y-2 max-h-52 overflow-y-auto pr-1">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className="max-w-[85%] px-3 py-1.5 rounded-xl text-xs leading-relaxed"
              style={msg.role === 'user'
                ? { ...S.msgUser, borderBottomRightRadius: '4px' }
                : { ...S.msgBot, borderBottomLeftRadius: '4px' }
              }
            >
              {msg.content}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function HistoryPage() {
  const [history, setHistory]       = useState([]);
  const [search, setSearch]         = useState('');
  const [loading, setLoading]       = useState(true);
  const [expandedChat, setExpanded] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetch(`${API}/history`)
      .then(r => r.json())
      .then(data => { setHistory(data); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  const handleDelete = async (qid) => {
    await fetch(`${API}/history/${qid}`, { method: 'DELETE' });
    setHistory(prev => prev.filter(h => h.query_id !== qid));
    if (expandedChat === qid) setExpanded(null);
  };

  const filtered = history.filter(h => h.query.toLowerCase().includes(search.toLowerCase()));

  const groupByDate = (items) => {
    const groups = { Today: [], Yesterday: [], 'This Week': [], Older: [] };
    const now = new Date();
    items.forEach(item => {
      const diff = Math.floor((now - new Date(item.created_at)) / 86400000);
      if (diff === 0)      groups.Today.push(item);
      else if (diff === 1) groups.Yesterday.push(item);
      else if (diff < 7)   groups['This Week'].push(item);
      else                 groups.Older.push(item);
    });
    return groups;
  };

  const groups = groupByDate(filtered);
  const fmt = (s) => new Date(s).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });

  return (
    <div className="min-h-[calc(100vh-56px)] px-4 py-8 transition-colors duration-300" style={S.wrap}>
      <div className="max-w-3xl mx-auto">

        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold" style={S.txt}>Research History</h1>
            <p className="text-sm mt-1" style={S.txtMuted}>{history.length} saved queries</p>
          </div>
          <button
            onClick={() => navigate('/research')}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-medium transition-colors"
          >
            New Research
          </button>
        </div>

        {/* Search */}
        <input
          type="text"
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Filter by query text…"
          className="w-full border rounded-xl px-4 py-2.5 text-sm outline-none mb-6 transition-all focus:border-indigo-500"
          style={S.input}
        />

        {loading && <div className="text-center py-16" style={S.txtMuted}>Loading history…</div>}

        {!loading && filtered.length === 0 && (
          <div className="text-center py-16">
            <div className="text-4xl mb-4">📋</div>
            <p style={S.txtMuted}>No research history yet.</p>
            <button
              onClick={() => navigate('/research')}
              className="mt-4 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-medium"
            >
              Start your first research
            </button>
          </div>
        )}

        {Object.entries(groups).map(([group, items]) => {
          if (!items.length) return null;
          return (
            <div key={group} className="mb-8">
              <p className="text-xs font-semibold uppercase tracking-wider mb-3" style={S.txtMuted}>{group}</p>
              <div className="space-y-3">
                {items.map(item => (
                  <div
                    key={item.query_id}
                    className="rounded-xl p-4 border transition-all group"
                    style={S.card}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <p className="font-semibold text-sm truncate" style={S.txt}>{item.query}</p>
                        <div className="flex items-center gap-3 mt-2 flex-wrap">
                          <span className="text-xs" style={S.txtMuted}>{fmt(item.created_at)}</span>
                          <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${
                            item.mode === 'expert' ? 'bg-indigo-600/20 text-indigo-400' : 'bg-teal-600/20 text-teal-400'
                          }`}>
                            {item.mode}
                          </span>
                          {item.paper_count > 0 && (
                            <span className="text-xs" style={S.txtMuted}>{item.paper_count} papers</span>
                          )}
                          <button
                            onClick={() => setExpanded(expandedChat === item.query_id ? null : item.query_id)}
                            className="text-[10px] px-2 py-0.5 rounded-full font-medium border transition-colors hover:border-indigo-500 hover:text-indigo-400 flex items-center gap-1"
                            style={{ borderColor: 'var(--border-color)', color: 'var(--text-muted)' }}
                          >
                            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-3 3v-3z"/>
                            </svg>
                            {expandedChat === item.query_id ? 'Hide Chat' : 'View Chat'}
                          </button>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button
                          onClick={() => navigate('/research', { state: { queryId: item.query_id, query: item.query } })}
                          className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-medium transition-colors"
                        >
                          View Report →
                        </button>
                        <button
                          onClick={() => handleDelete(item.query_id)}
                          className="p-1.5 rounded-lg transition-colors hover:text-red-400"
                          style={{ color: 'var(--text-muted)' }}
                          title="Delete"
                        >
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                              d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                          </svg>
                        </button>
                      </div>
                    </div>

                    {expandedChat === item.query_id && <ChatTranscript queryId={item.query_id} />}
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
