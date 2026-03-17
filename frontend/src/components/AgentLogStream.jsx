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
  // Parse a log string to determine its ReAct type for color coding
  const getLogStyle = (text) => {
    const lower = text.toLowerCase();
    if (lower.includes("thought:") || lower.includes("thinking:")) {
      return {
        bg: "bg-purple-50 dark:bg-purple-900/10",
        border: "border-purple-200 dark:border-purple-800",
        text: "text-purple-800 dark:text-purple-300",
        icon: (
          <svg className="w-3.5 h-3.5 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
        )
      };
    }
    if (lower.includes("action:") || lower.includes("invoking:")) {
      return {
        bg: "bg-blue-50 dark:bg-blue-900/10",
        border: "border-blue-200 dark:border-blue-800",
        text: "text-blue-800 dark:text-blue-300",
        icon: (
          <svg className="w-3.5 h-3.5 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        )
      };
    }
    if (lower.includes("observation:") || lower.includes("results:")) {
      return {
        bg: "bg-emerald-50 dark:bg-emerald-900/10",
        border: "border-emerald-200 dark:border-emerald-800",
        text: "text-emerald-800 dark:text-emerald-300",
        icon: (
          <svg className="w-3.5 h-3.5 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
          </svg>
        )
      };
    }
    if (lower.includes("error") || lower.includes("failed")) {
      return {
        bg: "bg-red-50 dark:bg-red-900/10",
        border: "border-red-200 dark:border-red-800",
        text: "text-red-800 dark:text-red-300",
        icon: (
          <svg className="w-3.5 h-3.5 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        )
      };
    }
    // Default info log
    return {
      bg: "bg-slate-50 dark:bg-slate-800/50",
      border: "border-slate-200 dark:border-slate-700",
      text: "text-slate-700 dark:text-slate-300",
      icon: (
        <svg className="w-3.5 h-3.5 mt-0.5 shrink-0 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      )
    };
  };

  return (
    <div className="glass rounded-xl p-5 border border-border flex flex-col min-h-[200px] text-text-tertiary">
      {logs.length === 0 && !isLoading ? (
        <div className="flex flex-col items-center justify-center h-full">
          <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="mb-2 opacity-50">
            <path d="M12 20h9" />
            <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z" />
          </svg>
          <p className="text-sm">Agent reasoning will appear here</p>
        </div>
      ) : (
        <>
          <div ref={scrollRef} className="flex-grow overflow-y-auto text-sm pr-2">
            {logs.map((log, index) => {
              const { bg, border, text, icon } = getLogStyle(log);
              return (
                <div key={index} className={`flex items-start gap-2 p-2 rounded-md mb-1 ${bg} border-l-4 ${border}`}>
                  <div className={`pt-0.5 ${text}`}>
                    {icon}
                  </div>
                  <pre className={`font-mono whitespace-pre-wrap break-words ${text}`}>
                    {log}
                  </pre>
                </div>
              );
            })}
          </div>

          {/* Loading indicator */}
          {isLoading && (
            <div className="flex items-center gap-2 px-3 py-2 text-xs text-text-secondary animate-pulse">
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
