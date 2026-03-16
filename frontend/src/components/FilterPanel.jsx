import { useState, useEffect, useCallback } from 'react';

const API_BASE = '/api';

/**
 * FilterPanel — Collapsible advanced search filter controls.
 *
 * Provides 6 filter controls: domain, keywords, date range,
 * paper count, sort by, and source selector.
 */
export default function FilterPanel({ filters, setFilters, mode }) {
  const [domains, setDomains] = useState([]);
  const [keywordInput, setKeywordInput] = useState('');

  /* ─── Fetch Available Domains ────────────────────── */
  useEffect(() => {
    const fetchDomains = async () => {
      try {
        const res = await fetch(`${API_BASE}/domains`);
        if (res.ok) {
          const data = await res.json();
          setDomains(data);
        }
      } catch (err) {
        console.error('Failed to fetch domains:', err);
        setDomains([
          'Computer Science', 'Artificial Intelligence', 'Machine Learning',
          'Biology', 'Physics', 'Medicine', 'Economics', 'Mathematics',
        ]);
      }
    };
    fetchDomains();
  }, []);

  /* ─── Update Filter Helper ──────────────────────── */
  const updateFilter = useCallback((key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  }, [setFilters]);

  /* ─── Keyword Chip Handlers ─────────────────────── */
  const addKeyword = useCallback((e) => {
    if (e.key === 'Enter' && keywordInput.trim()) {
      e.preventDefault();
      const kw = keywordInput.trim();
      if (!filters.keywords.includes(kw)) {
        updateFilter('keywords', [...filters.keywords, kw]);
      }
      setKeywordInput('');
    }
  }, [keywordInput, filters.keywords, updateFilter]);

  const removeKeyword = useCallback((keyword) => {
    updateFilter('keywords', filters.keywords.filter(k => k !== keyword));
  }, [filters.keywords, updateFilter]);

  /* ─── Render ─────────────────────────────────────── */
  return (
    <div className="grid grid-cols-2 lg:grid-cols-3 gap-4 p-4 rounded-xl glass" id="filter-panel">
      {/* Domain Selector */}
      <div>
        <label className="block text-xs font-medium text-text-secondary mb-1.5">
          Research Domain
        </label>
        <select
          id="filter-domain"
          value={filters.domain || ''}
          onChange={(e) => updateFilter('domain', e.target.value || null)}
          className="w-full px-3 py-2 rounded-lg bg-bg-primary border border-border text-text-primary text-sm focus:outline-none focus:border-accent-primary transition-colors"
        >
          <option value="">All Domains</option>
          {domains.map(d => (
            <option key={d} value={d}>{d}</option>
          ))}
        </select>
      </div>

      {/* Keywords */}
      <div className="col-span-2 lg:col-span-1">
        <label className="block text-xs font-medium text-text-secondary mb-1.5">
          Keywords
        </label>
        <div className="flex flex-wrap gap-1.5 p-2 rounded-lg bg-bg-primary border border-border min-h-[2.5rem] focus-within:border-accent-primary transition-colors">
          {filters.keywords.map(kw => (
            <span key={kw} className="keyword-chip">
              {kw}
              <button onClick={() => removeKeyword(kw)} aria-label={`Remove ${kw}`}>×</button>
            </span>
          ))}
          <input
            id="filter-keywords-input"
            type="text"
            value={keywordInput}
            onChange={(e) => setKeywordInput(e.target.value)}
            onKeyDown={addKeyword}
            placeholder={filters.keywords.length === 0 ? 'Type + Enter' : ''}
            className="flex-1 min-w-[80px] bg-transparent border-none outline-none text-sm text-text-primary placeholder:text-text-muted"
          />
        </div>
      </div>

      {/* Year From */}
      <div>
        <label className="block text-xs font-medium text-text-secondary mb-1.5">
          Year From
        </label>
        <input
          id="filter-year-from"
          type="number"
          min="1990"
          max="2026"
          value={filters.year_from || ''}
          onChange={(e) => updateFilter('year_from', e.target.value ? parseInt(e.target.value) : null)}
          placeholder={mode === 'beginner' ? '2024' : '2021'}
          className="w-full px-3 py-2 rounded-lg bg-bg-primary border border-border text-text-primary text-sm focus:outline-none focus:border-accent-primary transition-colors"
        />
      </div>

      {/* Year To */}
      <div>
        <label className="block text-xs font-medium text-text-secondary mb-1.5">
          Year To
        </label>
        <input
          id="filter-year-to"
          type="number"
          min="1990"
          max="2026"
          value={filters.year_to || ''}
          onChange={(e) => updateFilter('year_to', e.target.value ? parseInt(e.target.value) : null)}
          placeholder="2026"
          className="w-full px-3 py-2 rounded-lg bg-bg-primary border border-border text-text-primary text-sm focus:outline-none focus:border-accent-primary transition-colors"
        />
      </div>

      {/* Paper Count */}
      <div>
        <label className="block text-xs font-medium text-text-secondary mb-1.5">
          Paper Count
        </label>
        <select
          id="filter-paper-count"
          value={filters.paper_count}
          onChange={(e) => updateFilter('paper_count', parseInt(e.target.value))}
          className="w-full px-3 py-2 rounded-lg bg-bg-primary border border-border text-text-primary text-sm focus:outline-none focus:border-accent-primary transition-colors"
        >
          {[3, 5, 10, 20].map(n => (
            <option key={n} value={n}>{n} papers</option>
          ))}
        </select>
      </div>

      {/* Sort By */}
      <div>
        <label className="block text-xs font-medium text-text-secondary mb-1.5">
          Sort By
        </label>
        <select
          id="filter-sort-by"
          value={filters.sort_by}
          onChange={(e) => updateFilter('sort_by', e.target.value)}
          className="w-full px-3 py-2 rounded-lg bg-bg-primary border border-border text-text-primary text-sm focus:outline-none focus:border-accent-primary transition-colors"
        >
          <option value="relevance">Relevance</option>
          <option value="most_recent">Most Recent</option>
          <option value="most_cited">Most Cited</option>
        </select>
      </div>

      {/* Source */}
      <div>
        <label className="block text-xs font-medium text-text-secondary mb-1.5">
          Source
        </label>
        <select
          id="filter-source"
          value={filters.source}
          onChange={(e) => updateFilter('source', e.target.value)}
          className="w-full px-3 py-2 rounded-lg bg-bg-primary border border-border text-text-primary text-sm focus:outline-none focus:border-accent-primary transition-colors"
        >
          <option value="both">Both Sources</option>
          <option value="arxiv">arXiv Only</option>
          <option value="semantic_scholar">Semantic Scholar Only</option>
        </select>
      </div>
    </div>
  );
}
