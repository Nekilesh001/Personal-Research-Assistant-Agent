import { useEffect, useRef } from 'react';

/**
 * AgentLogStream — Live streaming thought/action/observation feed.
 *
 * Displays the agent's reasoning steps in real-time via SSE events.
 * Each log type has a distinct color-coded left border.
 */
export default function AgentLogStream({ logs, isLoading }) {
  const scrollRef = useRef(null);

  /* Auto-scroll to bottom on new logs */
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  /**
   * Get the display label and CSS class for a log event type.
   */
  const getLogStyle = (type) => {
    switch (type) {
      case 'thought':
        return { label: '💭 Thought', className: 'log-thought' };
      case 'action':
        return { label: '⚡ Action', className: 'log-action' };
      case 'observation':
        return { label: '👁 Observation', className: 'log-observation' };
      case 'error':
        return { label: '❌ Error', className: 'log-error' };
      default:
        return { label: '📋 Info', className: 'log-thought' };
    }
  };

  return (
    <div
      ref={scrollRef}
      className="flex-1 overflow-y-auto p-3 space-y-2"
      id="agent-log-stream"
    >
      {logs.length === 0 && !isLoading ? (
        <div className="flex flex-col items-center justify-center h-full text-center text-text-muted text-xs">
          <svg className="w-8 h-8 mb-2 opacity-30" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
          Agent reasoning steps
          <br />
          will appear here.
        </div>
      ) : (
        <>
          {logs.map((log, index) => {
            const style = getLogStyle(log.type);
            return (
              <div
                key={index}
                className={`${style.className} px-3 py-2 rounded-r-lg text-xs animate-slide-up`}
              >
                <span className="font-semibold text-text-primary block mb-0.5">
                  {style.label}
                </span>
                <span className="text-text-secondary leading-relaxed whitespace-pre-wrap break-words">
                  {log.content}
                </span>
              </div>
            );
          })}

          {/* Loading indicator */}
          {isLoading && (
            <div className="flex items-center gap-2 px-3 py-2 text-xs text-text-muted animate-pulse">
              <div className="flex gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-accent-primary animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-1.5 h-1.5 rounded-full bg-accent-primary animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-1.5 h-1.5 rounded-full bg-accent-primary animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
              Agent is thinking…
            </div>
          )}
        </>
      )}
    </div>
  );
}
