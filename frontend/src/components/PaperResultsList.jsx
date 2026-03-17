import PaperCard from './PaperCard'

export default function PaperResultsList({
  papers,
  selectedPapers,
  onToggle,
  onSelectAll,
  onClearAll,
  paperCount,
  onPaperCountChange,
  isLoading,
}) {
  const selectedIds = new Set(
    selectedPapers.map(p => p.url || p.title)
  )

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[...Array(5)].map((_, i) => (
          <div
            key={i}
            className="h-28 rounded-xl bg-slate-800 animate-pulse"
          />
        ))}
      </div>
    )
  }

  if (!papers || papers.length === 0) return null

  return (
    <div className="space-y-3">

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-sm text-slate-400">
            {papers.length} papers found
          </span>
          <span className="text-slate-600">·</span>
          <button
            onClick={onSelectAll}
            className="text-xs text-indigo-400 hover:text-indigo-300"
          >
            Select all
          </button>
          {selectedPapers.length > 0 && (
            <>
              <span className="text-slate-600">·</span>
              <button
                onClick={onClearAll}
                className="text-xs text-slate-400 hover:text-slate-300"
              >
                Clear
              </button>
            </>
          )}
        </div>

        <div className="flex items-center gap-1">
          <span className="text-xs text-slate-500 mr-1">
            Show:
          </span>
          {[3, 5, 10, 15].map(n => (
            <button
              key={n}
              onClick={() => onPaperCountChange(n)}
              className={`
                text-xs px-2.5 py-1 rounded-full transition-colors
                ${paperCount === n
                  ? 'bg-indigo-600 text-white'
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                }
              `}
            >
              {n}
            </button>
          ))}
        </div>
      </div>

      {papers.map((paper, idx) => (
        <PaperCard
          key={paper.url || paper.title || idx}
          paper={paper}
          isSelected={selectedIds.has(paper.url || paper.title)}
          onToggle={onToggle}
        />
      ))}

    </div>
  )
}
