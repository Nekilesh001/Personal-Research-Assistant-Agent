import React from "react";

/**
 * Toast notification system.
 * Needs to be rendered via a portal or positioned absolute in a container.
 */
function Toast({ message, type = "info", onClose }) {
  if (!message) return null;

  const bgColors = {
    success: "bg-green-600",
    error: "bg-red-600",
    info: "bg-blue-600",
    warning: "bg-yellow-600",
  };

  const bgColor = bgColors[type] || bgColors.info;

  return (
    <div
      className={`fixed bottom-4 right-4 z-50 flex items-center gap-3 rounded-lg px-4 py-3 text-white shadow-lg transition-all animate-in fade-in slide-in-from-bottom-5 ${bgColor}`}
    >
      <span className="text-sm font-medium">{message}</span>
      <button
        onClick={onClose}
        className="ml-2 rounded-md p-1 opacity-80 hover:bg-white/20 hover:opacity-100 transition-colors"
        aria-label="Close"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M18 6 6 18" />
          <path d="m6 6 12 12" />
        </svg>
      </button>
    </div>
  );
}

export default Toast;
