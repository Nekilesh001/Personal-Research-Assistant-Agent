import { useState } from 'react'

export default function PaperCard({ paper, isSelected, onToggle }) {
  const [expanded, setExpanded] = useState(false)

  const authors = Array.isArray(paper.authors)
    ? paper.authors.slice(0, 3).join(', ') +
      (paper.authors.length > 3 ? ' et al.' : '')
    : paper.authors || 'Unknown'

  const abstract = paper.abstract || ''
  const preview = abstract.slice(0, 200)
  const hasMore = abstract.length > 200

  return (
    <div className={`
      rounded-xl border transition-all duration-200
      ${isSelected
        ? 'border-l-4 border-indigo-500 bg-indigo-950/30'
        : 'border-slate-700 bg-slate-800/50 hover:border-slate-600'
      }
    `}>
      <div className="p-4">
        <div className="flex items-start gap-3">

          <input
            type="checkbox"
            checked={isSelected}
            onChange={() => onToggle(paper)}
            className="mt-1 w-4 h-4 rounded accent-indigo-500 flex-shrink-0 cursor-pointer"
          />

          <div className="flex-1 min-w-0">

            <h3 className="text-sm font-semibold text-white leading-snug mb-1">
              {paper.title}
            </h3>

            <div className="flex flex-wrap items-center gap-2 mb-2">
              <span className="text-xs text-slate-400">
                {authors}
              </span>
              {paper.year && (
                <span className="text-xs text-slate-500">
                  · {paper.year}
                </span>
              )}
              {paper.source && (
                <span className="text-xs px-2 py-0.5 rounded-full bg-slate-700 text-slate-300">
                  {paper.source === 'arxiv'
                    ? 'arXiv'
                    : paper.source === 'semantic_scholar'
                    ? 'Semantic Scholar'
                    : paper.source}
                </span>
              )}
              {paper.citation_count > 0 && (
                <span className="text-xs text-amber-400">
                  {paper.citation_count} citations
                </span>
              )}
            </div>

            {abstract && (
              <div className="text-xs text-slate-400 leading-relaxed">
                <span>
                  {expanded ? abstract : preview}
                  {!expanded && hasMore && '...'}
                </span>
                {hasMore && (
                  <button
                    onClick={() => setExpanded(!expanded)}
                    className="ml-1 text-indigo-400 hover:text-indigo-300 underline"
                  >
                    {expanded ? 'Show less' : 'Show more'}
                  </button>
                )}
              </div>
            )}

            {paper.url && !paper.url.startsWith('uploaded://') && (
              <a
                href={paper.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 mt-2 text-xs text-indigo-400 hover:text-indigo-300 hover:underline"
              >
                Read Paper →
              </a>
            )}

          </div>
        </div>
      </div>
    </div>
  )
}
