import { useState } from 'react';

/**
 * QueryHistory — Sidebar list of past queries.
 *
 * Displays a scrollable list of previous research queries with
 * timestamps. Clicking loads the saved report; delete button removes it.
 */
export default function QueryHistory({ history, currentQueryId, onSelectQuery, onDeleteQuery }) {
  const [hoveredId, setHoveredId] = useState(null);

  /**
   * Format a timestamp into a relative or short date string.
   */
  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    
    const d = new Date(dateStr);
    const today = new Date();
    
    // If today, show time. Otherwise, show short date.
    if (d.toDateString() === today.toDateString()) {
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    return d.toLocaleDateString([], { month: 'short', day: 'numeric' });
  };

  return (
    <div className="glass rounded-xl border border-border overflow-hidden flex flex-col max-h-[400px]">
      <div className="px-4 py-3 border-b border-border bg-bg-surface/50 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-text-primary flex items-center gap-2">
          <svg className="w-4 h-4 text-accent-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Previous Research
        </h3>
        <span className="text-[10px] font-medium text-text-tertiary uppercase tracking-wider bg-bg-surface px-2 py-0.5 rounded-full border border-border">
          {history.length} Saved
        </span>
      </div>

      <div className="overflow-y-auto p-2 space-y-1">
        {history.map((item) => {
          const isActive = currentQueryId === item.query_id;
          
          return (
            <div
              key={item.query_id}
              className={`group flex items-center justify-between p-3 rounded-lg cursor-pointer transition-all ${
                isActive 
                  ? "bg-accent-primary/10 border border-accent-primary/20 shadow-sm" 
                  : "hover:bg-bg-surface border border-transparent"
              }`}
              onClick={() => onSelectQuery(item.query_id)}
              onMouseEnter={() => setHoveredId(item.query_id)}
              onMouseLeave={() => setHoveredId(null)}
            >
              <div className="flex-1 min-w-0 pr-2">
                <p className={`text-sm truncate font-medium ${isActive ? "text-accent-primary" : "text-text-primary group-hover:text-accent-primary transition-colors"}`}>
                  {item.query}
                </p>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-[10px] text-text-tertiary">
                    {formatDate(item.created_at)}
                  </span>
                  <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                    item.mode === "expert" 
                      ? "bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300" 
                      : "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300"
                  }`}>
                    {item.mode}
                  </span>
                </div>
              </div>
              
              {/* Delete button (shown on hover) */}
              {hoveredId === item.query_id && (
                <button
                  onClick={(e) => { e.stopPropagation(); onDeleteQuery(item.query_id); }}
                  className="absolute right-3 top-1/2 -translate-y-1/2 p-1.5 rounded-md text-text-muted hover:text-error hover:bg-error/10 transition-colors bg-bg-surface shadow-sm"
                  title="Delete query"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
