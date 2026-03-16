/**
 * FollowUpSuggestions — 3 clickable pill buttons for next questions.
 *
 * After every report, this component shows 3 follow-up research
 * questions. Clicking one fires a new query automatically.
 */
export default function FollowUpSuggestions({ followups, onSelect }) {
  if (!followups || followups.length === 0) return null;

  return (
    <div className="rounded-xl glass overflow-hidden" id="followup-suggestions">
      {/* Header */}
      <div className="flex items-center gap-2 px-5 py-3 border-b border-border">
        <svg className="w-4 h-4 text-accent-secondary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span className="text-sm font-semibold text-text-primary">Explore Further</span>
      </div>

      {/* Question Pills */}
      <div className="p-4 flex flex-wrap gap-2">
        {followups.map((question, index) => (
          <button
            key={index}
            onClick={() => onSelect(question)}
            className="group flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm text-left transition-all duration-200 border border-accent-secondary/20 bg-accent-secondary/5 hover:bg-accent-secondary/15 hover:border-accent-secondary/40 text-text-secondary hover:text-text-primary animate-slide-up"
            style={{ animationDelay: `${index * 100}ms` }}
            id={`followup-${index}`}
          >
            <span className="text-accent-secondary group-hover:text-accent-primary transition-colors flex-shrink-0">
              →
            </span>
            <span className="leading-snug">{question}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
