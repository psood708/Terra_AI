'use client';
import { useState } from 'react';
import { X, Sparkles, Zap, Trash2 } from 'lucide-react';
import { useAppStore } from '@/store/appStore';
import { api } from '@/lib/api';
import type { Provider } from '@/types/api';

const PROVIDER_CONFIG: Record<Provider, { label: string; placeholder: string; hint: string; hintLink?: string }> = {
  huggingface: {
    label: 'Hugging Face (Recommended – Free Serverless Token)',
    placeholder: 'Enter hf_... (Free at huggingface.co/settings/tokens)',
    hint: 'Get a free User Access Token at ',
    hintLink: 'https://huggingface.co/settings/tokens',
  },
  gemini: {
    label: 'Google Gemini (gemini-3.6-flash)',
    placeholder: 'Enter AIza... Google API key',
    hint: 'Get a key at ',
    hintLink: 'https://aistudio.google.com/apikey',
  },
  openai: {
    label: 'OpenAI (GPT-4o-mini)',
    placeholder: 'Enter sk-... OpenAI API key',
    hint: 'Get a key at platform.openai.com',
  },
};

interface Props { open: boolean; onClose: () => void; }

export function AiConfigModal({ open, onClose }: Props) {
  const { activeApiKey, activeProvider, setAiConfig, clearAiConfig } = useAppStore();
  const [provider, setProvider] = useState<Provider>(activeProvider);
  const [apiKey, setApiKey] = useState(activeApiKey);
  const [testStatus, setTestStatus] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  const [testing, setTesting] = useState(false);
  // Track the previous `open` value to re-sync local form state from the store
  // the moment the modal transitions closed -> open, without an effect (avoids
  // a stale-content flash and the cascading-render footgun effects can cause).
  const [prevOpen, setPrevOpen] = useState(open);
  if (open !== prevOpen) {
    setPrevOpen(open);
    if (open) {
      setProvider(activeProvider);
      setApiKey(activeApiKey);
      setTestStatus(null);
    }
  }

  if (!open) return null;

  const config = PROVIDER_CONFIG[provider];

  const handleTest = async () => {
    if (!apiKey.trim()) { setTestStatus({ type: 'error', message: 'Please enter an API key first.' }); return; }
    setTesting(true);
    setTestStatus(null);
    try {
      const res = await api.testConnection({ api_key: apiKey.trim(), provider });
      if (res.success) {
        setTestStatus({ type: 'success', message: `✔ Connected! Model: ${res.model} • Latency: ${res.latency_ms}ms` });
      } else {
        setTestStatus({ type: 'error', message: `✖ ${res.error}` });
      }
    } catch (e) {
      setTestStatus({ type: 'error', message: `Connection error: ${e}` });
    }
    setTesting(false);
  };

  const handleSave = () => {
    setAiConfig(apiKey.trim(), provider);
    onClose();
  };

  const handleClear = () => {
    clearAiConfig();
    setApiKey('');
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4" style={{ background: 'var(--bg-card)', border: '1px solid rgba(16,185,129,0.3)' }}>
        {/* Header */}
        <div className="flex items-center justify-between pb-3" style={{ borderBottom: '1px solid var(--border)' }}>
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-emerald-500/20 text-emerald-400 light:text-emerald-700 flex items-center justify-center">
              <Sparkles className="w-3.5 h-3.5" />
            </div>
            <div>
              <h3 className="text-sm font-bold">Active AI Configuration</h3>
              <p className="text-[10px]" style={{ color: 'var(--text-muted)' }}>Connect live LLM generative reasoning to OdinAI</p>
            </div>
          </div>
          <button onClick={onClose} style={{ color: 'var(--text-muted)' }} className="hover:text-[color:var(--text-primary)] transition"><X className="w-4 h-4" /></button>
        </div>

        {/* Fields */}
        <div className="space-y-3 text-xs">
          <div>
            <label className="block font-medium mb-1" style={{ color: 'var(--text-sub)' }}>AI Provider:</label>
            <select value={provider} onChange={e => setProvider(e.target.value as Provider)}
              className="w-full rounded-lg p-2 text-xs focus:outline-none focus:border-emerald-500"
              style={{ background: 'var(--card-inner)', border: '1px solid var(--border)', color: 'var(--text-primary)' }}>
              {(Object.keys(PROVIDER_CONFIG) as Provider[]).map(p => (
                <option key={p} value={p}>{PROVIDER_CONFIG[p].label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block font-medium mb-1" style={{ color: 'var(--text-sub)' }}>API Token / Key:</label>
            <input type="password" value={apiKey} onChange={e => setApiKey(e.target.value)}
              placeholder={config.placeholder}
              className="w-full rounded-lg p-2 text-xs focus:outline-none focus:border-emerald-500"
              style={{ background: 'var(--card-inner)', border: '1px solid var(--border)', color: 'var(--text-primary)' }}
            />
            {config.hintLink ? (
              <p className="text-[10px] mt-1" style={{ color: 'var(--text-muted)' }}>
                {config.hint}<a href={config.hintLink} target="_blank" className="text-emerald-400 light:text-emerald-700 underline">{config.hintLink.replace('https://', '')}</a>. Powers small open models (Qwen, Gemma, Llama) via the HF router.
              </p>
            ) : (
              <p className="text-[10px] mt-1" style={{ color: 'var(--text-muted)' }}>{config.hint}</p>
            )}
          </div>

          <div className="rounded-xl p-3 text-[11px] leading-relaxed" style={{ background: 'var(--card-inner)', border: '1px solid var(--border)', color: 'var(--text-muted)' }}>
            <strong className="text-emerald-400 light:text-emerald-700 block mb-1">ℹ️ How this works:</strong>
            When an API key is connected, OdinAI dynamically injects real-time biometric streams (HRV z-scores, CGM readings, sleep hypnogram stages) into the LLM system prompt.
          </div>

          {testStatus && (
            <div className={`text-[11px] rounded-lg p-2.5 ${
              testStatus.type === 'success' ? 'bg-emerald-500/10 text-emerald-300 light:text-emerald-800 border border-emerald-500/20' : 'bg-rose-500/10 text-rose-300 light:text-rose-800 border border-rose-500/20'
            }`}>{testStatus.message}</div>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center justify-between pt-3" style={{ borderTop: '1px solid var(--border)' }}>
          <button onClick={handleClear} className="text-xs text-rose-400 light:text-rose-700 hover:text-rose-300 light:hover:text-rose-800 transition flex items-center gap-1">
            <Trash2 className="w-3 h-3" /> Clear Key
          </button>
          <div className="flex items-center gap-2">
            <button onClick={handleTest} disabled={testing}
              className="text-xs px-3 py-1.5 rounded-lg bg-gray-800 hover:bg-gray-700 light:bg-slate-100 light:hover:bg-slate-200 text-cyan-300 light:text-cyan-700 border border-cyan-500/30 transition flex items-center gap-1 disabled:opacity-50">
              <Zap className="w-3 h-3" />{testing ? 'Testing...' : 'Test Connection'}
            </button>
            <button onClick={handleSave}
              className="text-xs px-4 py-1.5 rounded-lg bg-emerald-500 hover:bg-emerald-600 text-black font-bold transition shadow">
              Save & Activate
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
