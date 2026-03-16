import { useState } from 'react';

/**
 * QueryHistory — Sidebar list of past queries.
 *
 * Displays a scrollable list of previous research queries with
 * timestamps. Clicking loads the saved report; delete button removes it.
 */
export default function QueryHistory({ history, onSelect, onDelete }) {
  const [hoveredId, setHoveredId] = useState(null);

  /**
   * Format a timestamp into a relative or short date string.
   */
  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    try {
      const date = new Date(dateStr);
      const now = new Date();
      const diffMs = now - date;
      const diffMins = Math.floor(diffMs / 60000);
      const diffHours = Math.floor(diffMs / 3600000);
      const diffDays = Math.floor(diffMs / 86400000);

      if (diffMins < 1) return 'Just now';
      if (diffMins < 60) return `${diffMins}m ago`;
      if (diffHours < 24) return `${diffHours}h ago`;
      if (diffDays < 7) return `${diffDays}d ago`;
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    } catch {
      return '';
    }
  };

  return (
    <div className="flex-1 overflow-y-auto" id="query-history-panel">
      {history.length === 0 ? (
        <div className="p-4 text-center text-text-muted text-sm">
          <svg className="w-8 h-8 mx-auto mb-2 opacity-30" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          No queries yet.
          <br />
          <span className="text-xs">Your research history will appear here.</span>
        </div>
      ) : (
        <div className="p-2 space-y-1">
          {history.map((item) => (
            <div
              key={item.query_id}
              className="group relative p-3 rounded-lg cursor-pointer transition-all duration-200 hover:bg-bg-hover border border-transparent hover:border-border"
              onMouseEnter={() => setHoveredId(item.query_id)}
              onMouseLeave={() => setHoveredId(null)}
              onClick={() => onSelect(item)}
              id={`history-item-${item.query_id}`}
            >
              {/* Query text */}
              <p className="text-sm text-text-primary font-medium truncate pr-6">
                {item.query}
              </p>

              {/* Meta info */}
              <div className="flex items-center gap-2 mt-1.5">
                <span className={`text-xs px-1.5 py-0.5 rounded-full ${
                  item.mode === 'expert'
                    ? 'bg-accent-primary/15 text-accent-primary'
                    : 'bg-success/15 text-success'
                }`}>
                  {item.mode}
                </span>
                {item.paper_count > 0 && (
                  <span className="text-xs text-text-muted">
                    {item.paper_count} papers
                  </span>
                )}
                <span className="text-xs text-text-muted ml-auto">
                  {formatDate(item.created_at)}
                </span>
              </div>

              {/* Report indicator */}
              {item.has_report && (
                <div className="absolute top-3 right-3">
                  <div className="w-2 h-2 rounded-full bg-success" title="Report available" />
                </div>
              )}

              {/* Delete button (shown on hover) */}
              {hoveredId === item.query_id && (
                <button
                  onClick={(e) => { e.stopPropagation(); onDelete(item.query_id); }}
                  className="absolute top-2 right-2 p-1 rounded-md text-text-muted hover:text-error hover:bg-error/10 transition-colors"
                  title="Delete"
                  id={`delete-history-${item.query_id}`}
                >
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
