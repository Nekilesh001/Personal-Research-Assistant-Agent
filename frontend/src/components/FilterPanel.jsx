import React, { useCallback, useEffect, useState } from 'react';

const API_BASE = 'http://localhost:8000/api';

/**
 * FilterPanel — Collapsible advanced search filter controls.
 * Accepts `filters` object and `setFilters` setter from parent.
 */
export default function FilterPanel({ filters, setFilters, mode }) {
  const [domains, setDomains] = useState([]);
  const [keywordInput, setKeywordInput] = useState('');

  // Safety guard — if setFilters is broken, render nothing
  if (typeof setFilters !== 'function') return null;

  // Ensure keywords is always an array even if parent didn't initialize correctly
  const keywords = Array.isArray(filters?.keywords) ? filters.keywords : [];

  /* ─── Fetch Available Domains ────────────────────── */
  useEffect(() => {
    const fetchDomains = async () => {
      try {
        const res = await fetch(`${API_BASE}/domains`);
        if (res.ok) {
          const data = await res.json();
          setDomains(Array.isArray(data) ? data : []);
        }
      } catch {
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
      if (!keywords.includes(kw)) {
        updateFilter('keywords', [...keywords, kw]);
      }
      setKeywordInput('');
    }
  }, [keywordInput, keywords, updateFilter]);

  const removeKeyword = useCallback((keyword) => {
    updateFilter('keywords', keywords.filter(k => k !== keyword));
  }, [keywords, updateFilter]);

  return (
    <div className="glass rounded-xl border border-border overflow-hidden" id="filter-panel">
      <div className="px-4 py-2.5 border-b border-border bg-bg-surface/30">
        <h3 className="text-xs font-semibold text-text-secondary uppercase tracking-wider">Search Filters</h3>
      </div>

      <div className="grid grid-cols-2 gap-3 p-3">
        {/* Domain Selector */}
        <div>
          <label className="block text-xs font-medium text-text-secondary mb-1">Research Domain</label>
          <select
            id="filter-domain"
            value={filters?.domain || ''}
            onChange={(e) => updateFilter('domain', e.target.value || null)}
            className="w-full px-2 py-1.5 rounded-lg bg-bg-primary border border-border text-text-primary text-xs focus:outline-none focus:border-accent-primary transition-colors"
          >
            <option value="">All Domains</option>
            {domains.map(d => (
              <option key={d} value={d}>{d}</option>
            ))}
          </select>
        </div>

        {/* Source Selector */}
        <div>
          <label className="block text-xs font-medium text-text-secondary mb-1">Source</label>
          <select
            id="filter-source"
            value={filters?.source || 'arxiv'}
            onChange={(e) => updateFilter('source', e.target.value)}
            className="w-full px-2 py-1.5 rounded-lg bg-bg-primary border border-border text-text-primary text-xs focus:outline-none focus:border-accent-primary"
          >
            <option value="arxiv">arXiv Only</option>
            <option value="both">Both Sources</option>
            <option value="uploaded">Uploaded Papers</option>
          </select>
        </div>

        {/* Keywords */}
        <div className="col-span-2">
          <label className="block text-xs font-medium text-text-secondary mb-1">Keywords</label>
          <div className="flex flex-wrap gap-1 p-1.5 rounded-lg bg-bg-primary border border-border min-h-[2rem] focus-within:border-accent-primary transition-colors">
            {keywords.map(kw => (
              <span key={kw} className="inline-flex items-center gap-1 px-2 py-0.5 bg-accent-primary/20 text-accent-primary text-xs rounded-full">
                {kw}
                <button onClick={() => removeKeyword(kw)} className="hover:text-red-400 leading-none">×</button>
              </span>
            ))}
            <div className="flex-1 flex items-center min-w-[120px]">
              <input
                id="filter-keywords-input"
                type="text"
                value={keywordInput}
                onChange={(e) => setKeywordInput(e.target.value)}
                onKeyDown={addKeyword}
                placeholder={keywords.length === 0 ? 'Type + Enter or click +' : ''}
                className="flex-1 bg-transparent border-none outline-none text-xs text-text-primary placeholder:text-text-muted"
              />
              {keywordInput.trim() && (
                <button
                  onClick={() => addKeyword({ key: 'Enter', preventDefault: () => { } })}
                  className="w-5 h-5 flex items-center justify-center bg-accent-primary text-white rounded-md hover:bg-accent-hover transition-colors"
                  title="Add keyword"
                >
                  +
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Year From */}
        <div>
          <label className="block text-xs font-medium text-text-secondary mb-1">Year From</label>
          <input
            id="filter-year-from"
            type="number"
            min="1990"
            max="2026"
            value={filters?.year_from || ''}
            onChange={(e) => updateFilter('year_from', e.target.value ? parseInt(e.target.value) : null)}
            placeholder="2021"
            className="w-full px-2 py-1.5 rounded-lg bg-bg-primary border border-border text-text-primary text-xs focus:outline-none focus:border-accent-primary"
          />
        </div>

        {/* Year To */}
        <div>
          <label className="block text-xs font-medium text-text-secondary mb-1">Year To</label>
          <input
            id="filter-year-to"
            type="number"
            min="1990"
            max="2026"
            value={filters?.year_to || ''}
            onChange={(e) => updateFilter('year_to', e.target.value ? parseInt(e.target.value) : null)}
            placeholder="2026"
            className="w-full px-2 py-1.5 rounded-lg bg-bg-primary border border-border text-text-primary text-xs focus:outline-none focus:border-accent-primary"
          />
        </div>

        {/* Sort By */}
        <div className="col-span-2">
          <label className="block text-xs font-medium text-text-secondary mb-1">Sort By</label>
          <select
            id="filter-sort"
            value={filters?.sort_by || 'relevance'}
            onChange={(e) => updateFilter('sort_by', e.target.value)}
            className="w-full px-2 py-1.5 rounded-lg bg-bg-primary border border-border text-text-primary text-xs focus:outline-none focus:border-accent-primary"
          >
            <option value="relevance">Relevance</option>
            <option value="most_recent">Most Recent</option>
            <option value="most_cited">Most Cited</option>
          </select>
        </div>
      </div>
    </div>
  );
}
