export default function FloatingGenerateButton({
  selectedCount,
  onGenerate,
  isGenerating,
  onSelectAll,
  onClearAll,
}) {
  if (selectedCount === 0 || isGenerating) return null

  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 flex items-center gap-3 bg-slate-900/95 backdrop-blur-sm border border-slate-700 rounded-2xl px-4 py-3 shadow-2xl">

      <button
        onClick={onClearAll}
        className="text-xs text-slate-400 hover:text-slate-200 transition-colors"
      >
        Clear
      </button>

      <button
        onClick={onGenerate}
        className="flex items-center gap-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl font-semibold text-sm transition-all shadow-lg shadow-indigo-900/50"
      >
        <svg
          className="w-4 h-4"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
        Generate Report ({selectedCount} selected)
      </button>

      <button
        onClick={onSelectAll}
        className="text-xs text-slate-400 hover:text-slate-200 transition-colors"
      >
        Select all
      </button>

    </div>
  )
}
