import { useState, useEffect } from 'react';

const API = 'http://localhost:8000/api';

const PROVIDERS = [
  {
    id: 'groq',
    name: 'Groq',
    initial: 'G',
    color: 'from-orange-500 to-red-500',
    envKey: 'GROQ_API_KEY',
    model: 'llama-3.3-70b-versatile',
    keyLink: 'https://console.groq.com',
  },
  {
    id: 'openai',
    name: 'OpenAI',
    initial: 'O',
    color: 'from-emerald-500 to-teal-500',
    envKey: 'OPENAI_API_KEY',
    model: 'gpt-4o-mini',
    keyLink: 'https://platform.openai.com/api-keys',
  },
  {
    id: 'ollama',
    name: 'Ollama (Local)',
    initial: 'L',
    color: 'from-blue-500 to-indigo-500',
    envKey: 'OLLAMA_BASE_URL',
    model: 'llama3',
    keyLink: 'https://ollama.ai',
  },
];

export default function SettingsPage() {
  const [testResult, setTestResult] = useState(null);
  const [testing, setTesting] = useState(false);
  const [defaultMode, setDefaultMode] = useState(
    () => localStorage.getItem('defaultMode') || 'expert'
  );
  const [defaultCount, setDefaultCount] = useState(
    () => parseInt(localStorage.getItem('defaultCount') || '5')
  );
  const [saved, setSaved] = useState(false);

  const testConnection = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const res = await fetch(`${API}/test-llm`);
      const data = await res.json();
      setTestResult(data);
    } catch {
      setTestResult({ status: 'error', error_message: 'Could not reach backend' });
    } finally {
      setTesting(false);
    }
  };

  const savePreferences = () => {
    localStorage.setItem('defaultMode', defaultMode);
    localStorage.setItem('defaultCount', String(defaultCount));
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="min-h-[calc(100vh-56px)] bg-slate-900 px-4 py-8">
      <div className="max-w-2xl mx-auto space-y-8">
        <div>
          <h1 className="text-2xl font-bold text-white mb-1">Settings</h1>
          <p className="text-slate-400 text-sm">Configure LLM providers and preferences.</p>
        </div>

        {/* LLM Providers */}
        <section>
          <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400 mb-4">
            LLM Providers
          </h2>
          <div className="space-y-3">
            {PROVIDERS.map(p => (
              <div
                key={p.id}
                className="bg-slate-800 border border-slate-700 rounded-2xl p-4 flex items-center justify-between gap-4"
              >
                <div className="flex items-center gap-3">
                  <div className={`w-9 h-9 rounded-xl bg-gradient-to-br ${p.color} flex items-center justify-center text-white font-bold text-sm shadow`}>
                    {p.initial}
                  </div>
                  <div>
                    <p className="text-white font-semibold text-sm">{p.name}</p>
                    <p className="text-slate-500 text-xs">{p.model}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <a
                    href={p.keyLink}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-indigo-400 hover:underline"
                  >
                    Get API Key →
                  </a>
                </div>
              </div>
            ))}
          </div>

          {/* Test Connection */}
          <div className="mt-4">
            <button
              onClick={testConnection}
              disabled={testing}
              className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-xl text-sm font-medium transition-all"
            >
              {testing ? 'Testing...' : 'Test Active Connection'}
            </button>
            {testResult && (
              <div className={`mt-3 p-3 rounded-xl text-sm ${
                testResult.status === 'ok'
                  ? 'bg-emerald-900/30 border border-emerald-700 text-emerald-300'
                  : 'bg-red-900/30 border border-red-700 text-red-300'
              }`}>
                {testResult.status === 'ok' ? (
                  <>✅ <strong>{testResult.provider}</strong> ({testResult.model}) — {testResult.latency_seconds}s latency</>
                ) : (
                  <>❌ {testResult.error_message || testResult.error_type}</>
                )}
              </div>
            )}
          </div>
        </section>

        {/* Default Preferences */}
        <section>
          <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400 mb-4">
            Default Preferences
          </h2>
          <div className="bg-slate-800 border border-slate-700 rounded-2xl p-5 space-y-6">
            <div>
              <label className="text-sm text-white font-medium block mb-2">Default Mode</label>
              <div className="flex gap-2">
                {['expert', 'beginner'].map(m => (
                  <button
                    key={m}
                    onClick={() => setDefaultMode(m)}
                    className={`px-4 py-2 rounded-lg text-sm font-medium capitalize transition-all ${
                      defaultMode === m ? 'bg-indigo-600 text-white' : 'bg-slate-700 text-slate-300'
                    }`}
                  >
                    {m}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="text-sm text-white font-medium block mb-2">Default Paper Count</label>
              <div className="flex gap-2">
                {[3, 5, 10, 20].map(n => (
                  <button
                    key={n}
                    onClick={() => setDefaultCount(n)}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                      defaultCount === n ? 'bg-indigo-600 text-white' : 'bg-slate-700 text-slate-300'
                    }`}
                  >
                    {n}
                  </button>
                ))}
              </div>
            </div>
            <button
              onClick={savePreferences}
              className={`px-5 py-2.5 rounded-xl text-sm font-medium transition-all ${
                saved ? 'bg-emerald-600 text-white' : 'bg-indigo-600 hover:bg-indigo-500 text-white'
              }`}
            >
              {saved ? '✓ Saved!' : 'Save Preferences'}
            </button>
          </div>
        </section>

        {/* About */}
        <section>
          <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400 mb-4">About</h2>
          <div className="bg-slate-800 border border-slate-700 rounded-2xl p-5 space-y-2 text-sm text-slate-400">
            <p><span className="text-white">Version:</span> 2.0.0</p>
            <p>
              <span className="text-white">GitHub: </span>
              <a
                href="https://github.com/Nekilesh001/Personal-Research-Assistant-Agent"
                target="_blank"
                rel="noopener noreferrer"
                className="text-indigo-400 hover:underline"
              >
                Personal-Research-Assistant-Agent
              </a>
            </p>
            <p><span className="text-white">LLM Provider: </span> Groq (llama-3.3-70b-versatile)</p>
          </div>
        </section>
      </div>
    </div>
  );
}
