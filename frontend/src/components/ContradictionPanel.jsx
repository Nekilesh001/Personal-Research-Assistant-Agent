/**
 * ContradictionPanel — Displays detected paper contradictions.
 *
 * Shows amber-highlighted conflict cards with severity badges.
 * Each card names the two conflicting papers and explains the disagreement.
 */
export default function ContradictionPanel({ contradictions }) {
  if (!contradictions || contradictions.length === 0) return null;

  /**
   * Get severity badge styling.
   */
  const getSeverityStyle = (severity) => {
    switch (severity) {
      case 'major':
        return 'bg-error/15 text-error border-error/30';
      case 'moderate':
        return 'bg-warning/15 text-warning border-warning/30';
      case 'minor':
        return 'bg-yellow-500/15 text-yellow-400 border-yellow-500/30';
      default:
        return 'bg-warning/15 text-warning border-warning/30';
    }
  };

  return (
    <div className="rounded-xl glass overflow-hidden" id="contradiction-panel">
      {/* Header */}
      <div className="flex items-center gap-2 px-5 py-3 border-b border-warning/20 bg-warning/5">
        <svg className="w-4 h-4 text-warning" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
        </svg>
        <span className="text-sm font-semibold text-warning">
          Contradictions Detected ({contradictions.length})
        </span>
      </div>

      {/* Contradiction Cards */}
      <div className="p-4 space-y-3">
        {contradictions.map((c, index) => (
          <div
            key={index}
            className="p-4 rounded-lg border border-warning/20 bg-warning/5 animate-slide-up"
            style={{ animationDelay: `${index * 100}ms` }}
            id={`contradiction-${index}`}
          >
            {/* Severity Badge */}
            <div className="flex items-center justify-between mb-2">
              <span className={`text-xs px-2 py-0.5 rounded-full border ${getSeverityStyle(c.severity)}`}>
                {c.severity?.toUpperCase() || 'MODERATE'}
              </span>
            </div>

            {/* Paper Names */}
            <div className="flex items-start gap-2 mb-2">
              <div className="flex-1">
                <p className="text-xs text-text-muted mb-0.5">Paper A:</p>
                <p className="text-sm text-text-primary font-medium">
                  {c.url_a ? (
                    <a href={c.url_a} target="_blank" rel="noopener noreferrer" className="hover:text-accent-primary transition-colors">
                      {c.paper_a}
                    </a>
                  ) : c.paper_a}
                </p>
              </div>
              <div className="text-warning text-lg mt-3">⚡</div>
              <div className="flex-1">
                <p className="text-xs text-text-muted mb-0.5">Paper B:</p>
                <p className="text-sm text-text-primary font-medium">
                  {c.url_b ? (
                    <a href={c.url_b} target="_blank" rel="noopener noreferrer" className="hover:text-accent-primary transition-colors">
                      {c.paper_b}
                    </a>
                  ) : c.paper_b}
                </p>
              </div>
            </div>

            {/* Description */}
            <p className="text-xs text-text-secondary leading-relaxed mt-2 pt-2 border-t border-warning/10">
              {c.description}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
