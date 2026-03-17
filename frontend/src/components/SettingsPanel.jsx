import React, { useState } from "react";
import Toast from "./Toast";

export default function SettingsPanel({ isOpen, onClose }) {
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);

  if (!isOpen) return null;

  const handleTestLLM = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const res = await fetch("http://localhost:8000/api/test-llm");
      const data = await res.json();
      setTestResult(data);
    } catch (err) {
      setTestResult({
        status: "error",
        error: "Failed to connect to backend test endpoint",
      });
    } finally {
      setTesting(false);
    }
  };

  return (
    <>
      <div 
        className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-40 animate-in fade-in"
        onClick={onClose}
      />
      
      <div className="fixed right-0 top-0 h-full w-[400px] max-w-[90vw] bg-white dark:bg-slate-900 shadow-2xl z-50 p-6 flex flex-col border-l border-slate-200 dark:border-slate-800 animate-in slide-in-from-right">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold flex items-center gap-2">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            Settings
          </h2>
          <button onClick={onClose} className="p-2 rounded-full hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto space-y-6">
          <div className="space-y-3">
            <h3 className="font-semibold text-slate-900 dark:text-white border-b border-slate-200 dark:border-slate-800 pb-2">LLM Connection</h3>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Verify that your API keys are valid and the backend can successfully connect to the LLM provider configured in `.env`.
            </p>
            
            <button
              onClick={handleTestLLM}
              disabled={testing}
              className="w-full flex justify-center items-center gap-2 px-4 py-2 bg-slate-900 dark:bg-white text-white dark:text-slate-900 rounded-lg hover:opacity-90 disabled:opacity-50 transition-opacity font-medium"
            >
              {testing ? (
                <>
                  <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Testing Connection...
                </>
              ) : (
                "Test LLM Connection"
              )}
            </button>

            {testResult && (
              <div className={`mt-4 p-4 rounded-lg border ${
                testResult.status === "ok" 
                  ? "bg-green-50/50 border-green-200 dark:bg-green-900/10 dark:border-green-800" 
                  : "bg-red-50/50 border-red-200 dark:bg-red-900/10 dark:border-red-800"
              }`}>
                {testResult.status === "ok" ? (
                  <>
                    <h4 className="flex items-center gap-2 text-sm font-semibold text-green-800 dark:text-green-400 mb-2">
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                      Connection Successful
                    </h4>
                    <div className="grid grid-cols-2 gap-2 text-xs text-green-700 dark:text-green-300">
                      <div><span className="opacity-70">Provider:</span> {testResult.provider}</div>
                      <div><span className="opacity-70">Model:</span> {testResult.model}</div>
                      <div className="col-span-2"><span className="opacity-70">Latency:</span> {testResult.latency_ms?.toFixed(2)} ms</div>
                    </div>
                  </>
                ) : (
                  <>
                    <h4 className="flex items-center gap-2 text-sm font-semibold text-red-800 dark:text-red-400 mb-2">
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                      Connection Failed
                    </h4>
                    <p className="text-sm text-red-700 dark:text-red-300 break-words font-mono text-xs bg-red-100/50 dark:bg-red-900/30 p-2 rounded">
                      {testResult.error || "Unknown error"}
                    </p>
                    <p className="text-xs text-red-600 dark:text-red-400 mt-2">
                      Please check your API keys and provider settings in the backend `.env` file.
                    </p>
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
