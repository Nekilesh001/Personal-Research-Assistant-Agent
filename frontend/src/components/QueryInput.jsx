import { useCallback } from 'react';

/**
 * QueryInput — Search bar with mode toggle switch.
 *
 * Features:
 *   - Full-width search input with submit button
 *   - Expert / Beginner mode toggle pill
 *   - Loading state with spinner
 */
export default function QueryInput({ query, setQuery, mode, setMode, onSubmit, isLoading }) {

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSubmit();
    }
  }, [onSubmit]);

  return (
    <div id="query-input-container">
      {/* Search Bar */}
      <div className="flex gap-3 items-center">
        <div className="flex-1 relative glow-border rounded-xl">
          <input
            id="query-input"
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Enter a research topic… e.g., 'transformer architectures for NLP'"
            disabled={isLoading}
            className="w-full px-4 py-3 pr-12 rounded-xl bg-bg-primary border-none text-text-primary placeholder:text-text-muted focus:outline-none text-sm"
          />
          {/* Search icon inside input */}
          <div className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
        </div>

        {/* Submit Button */}
        <button
          id="submit-query-btn"
          onClick={() => onSubmit()}
          disabled={isLoading || !query.trim()}
          className={`px-6 py-3 rounded-xl font-medium text-sm transition-all duration-200 flex items-center gap-2 ${
            isLoading || !query.trim()
              ? 'bg-accent-primary/30 text-text-muted cursor-not-allowed'
              : 'bg-accent-primary hover:bg-accent-hover text-white shadow-lg shadow-accent-primary/25 hover:shadow-accent-primary/40'
          }`}
        >
          {isLoading ? (
            <>
              <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Researching…
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              Research
            </>
          )}
        </button>
      </div>

      {/* Mode Toggle */}
      <div className="flex items-center gap-3 mt-3">
        <span className="text-xs text-text-secondary">Mode:</span>
        <div className="flex rounded-lg overflow-hidden border border-border bg-bg-primary">
          <button
            id="mode-expert-btn"
            onClick={() => setMode('expert')}
            className={`px-3 py-1.5 text-xs font-medium transition-all duration-200 ${
              mode === 'expert'
                ? 'bg-accent-primary text-white'
                : 'text-text-secondary hover:text-text-primary'
            }`}
          >
            🔬 Expert
          </button>
          <button
            id="mode-beginner-btn"
            onClick={() => setMode('beginner')}
            className={`px-3 py-1.5 text-xs font-medium transition-all duration-200 ${
              mode === 'beginner'
                ? 'bg-success text-white'
                : 'text-text-secondary hover:text-text-primary'
            }`}
          >
            📖 Beginner
          </button>
        </div>
        <span className="text-xs text-text-muted">
          {mode === 'expert'
            ? 'Technical language with citations'
            : 'Simple language with analogies'}
        </span>
      </div>
    </div>
  );
}
