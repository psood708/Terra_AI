'use client';
import { useState, useRef, useEffect } from 'react';
import { Brain, Dna, Sparkles, Cpu, BookMarked, Send } from 'lucide-react';
import ReactMarkdown, { type Components } from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useOdinChat } from '@/hooks/useOdinChat';
import { useAppStore } from '@/store/appStore';
import type { AnomaliesResponse } from '@/types/api';

const PROMPT_CHIPS = [
  { label: 'Why is my recovery at this score?', query: 'Why is my recovery score at this level today?', color: 'text-emerald-400 light:text-emerald-700' },
  { label: 'What workout should I do?', query: 'What is my recommended adaptive workout today?', color: 'text-cyan-400 light:text-cyan-700' },
  { label: 'Analyze my glucose & CGM', query: 'Analyze my blood glucose excursions and post-meal response.', color: 'text-amber-400 light:text-amber-700' },
  { label: 'Tracking for Target 120', query: 'How am I tracking towards extreme longevity and Target 120?', color: 'text-teal-400 light:text-teal-700' },
];

const CITATIONS = [
  { title: 'HRV Autonomic Readiness', cite: 'Buchheit, M. (2014) • Frontiers in Physiology', color: 'border-emerald-500/40' },
  { title: 'Slow-Wave Sleep Delta Repair', cite: 'Walker & Stickgold (2017) • Nature Neuroscience', color: 'border-indigo-500/40' },
  { title: 'Mitochondrial Zone 2 Fat Oxidation', cite: 'San Millán & Brooks (2018) • Sports Medicine', color: 'border-amber-500/40' },
];

// Some models emit a plain "•" bullet character instead of standard "-"/"*"
// markdown syntax; normalize it so remark-gfm actually recognizes it as a list
// instead of leaving it as inline text.
function normalizeMarkdown(text: string): string {
  return text.replace(/^[ \t]*•[ \t]+/gm, '- ');
}

const ODIN_MARKDOWN_COMPONENTS: Components = {
  p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
  strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
  em: ({ children }) => <em className="italic">{children}</em>,
  ul: ({ children }) => <ul className="list-disc pl-4 space-y-1 marker:text-emerald-400 light:marker:text-emerald-700">{children}</ul>,
  ol: ({ children }) => <ol className="list-decimal pl-4 space-y-1 marker:text-emerald-400 light:marker:text-emerald-700">{children}</ol>,
  li: ({ children }) => <li className="pl-0.5">{children}</li>,
  a: ({ href, children }) => (
    <a href={href} target="_blank" rel="noopener noreferrer" className="text-emerald-400 light:text-emerald-700 underline">
      {children}
    </a>
  ),
  code: ({ children }) => (
    <code className="rounded px-1 py-0.5 text-[11px]" style={{ background: 'var(--card-inner)' }}>{children}</code>
  ),
};

function OdinMarkdown({ content }: { content: string }) {
  return (
    <div className="leading-relaxed" style={{ color: 'var(--text-sub)' }}>
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={ODIN_MARKDOWN_COMPONENTS}>
        {normalizeMarkdown(content)}
      </ReactMarkdown>
    </div>
  );
}

interface Props { anomalies: AnomaliesResponse | null; onOpenAiModal: () => void; }

export function OdinAITab({ anomalies, onOpenAiModal }: Props) {
  const { currentPersona, activeApiKey, activeProvider } = useAppStore();
  const { messages, isLoading, sendMessage } = useOdinChat(currentPersona, activeApiKey, activeProvider);
  const [input, setInput] = useState('');
  const chatRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (chatRef.current) chatRef.current.scrollTop = chatRef.current.scrollHeight;
  }, [messages, isLoading]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    sendMessage(input);
    setInput('');
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-fade-in">
      {/* Chat Console */}
      <div id="tour-odin" className="lg:col-span-2 rounded-2xl p-5 flex flex-col" style={{ height: '580px', background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
        {/* Header */}
        <div className="flex items-center justify-between pb-3" style={{ borderBottom: '1px solid var(--border)' }}>
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-full bg-emerald-500/20 text-emerald-400 light:text-emerald-700 flex items-center justify-center">
              <Brain className="w-3.5 h-3.5" />
            </div>
            <div>
              <h3 className="text-sm font-bold">OdinAI Health Intelligence</h3>
              <p className="text-[10px]" style={{ color: 'var(--text-muted)' }}>Multi-sensor telemetry reasoning + Peer-Reviewed Sports Science</p>
            </div>
          </div>
          <button onClick={onOpenAiModal}
            className="text-[10px] text-emerald-400 light:text-emerald-700 bg-emerald-500/10 hover:bg-emerald-500/20 px-2.5 py-1 rounded-full border border-emerald-500/20 flex items-center gap-1.5 transition">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            <span>Active AI: {activeApiKey ? activeProvider : 'Auto'}</span>
          </button>
        </div>

        {/* Messages */}
        <div ref={chatRef} className="flex-1 overflow-y-auto py-4 space-y-4 pr-1 text-xs">
          {messages.map(msg => (
            <div key={msg.id}>
              {msg.role === 'user' ? (
                <div className="flex items-start justify-end">
                  <div className="bg-emerald-600 text-black font-medium rounded-xl rounded-tr-none p-3 max-w-md shadow text-xs">
                    {msg.content}
                  </div>
                </div>
              ) : (
                <div className="flex items-start gap-3">
                  <div className="w-7 h-7 rounded-full bg-emerald-600/30 text-emerald-400 light:text-emerald-700 flex items-center justify-center text-xs shrink-0 mt-0.5">
                    <Dna className="w-3.5 h-3.5" />
                  </div>
                  <div className="rounded-xl rounded-tl-none p-3.5 text-xs space-y-2 max-w-xl shadow" style={{ background: 'var(--card-inner)', border: '1px solid var(--border)' }}>
                    {msg.isLiveAi !== undefined && (
                      <div className="flex items-center mb-1">
                        {msg.isLiveAi ? (
                          <span className="text-[10px] bg-emerald-500/10 text-emerald-400 light:text-emerald-700 border border-emerald-500/20 px-2 py-0.5 rounded-full font-semibold flex items-center gap-1">
                            <Sparkles className="w-2.5 h-2.5" /> Live AI ({msg.modelName || msg.provider?.toUpperCase()})
                          </span>
                        ) : (
                          <button onClick={onOpenAiModal} className="text-[10px] bg-indigo-500/10 text-indigo-400 light:text-indigo-700 border border-indigo-500/20 px-2 py-0.5 rounded-full font-semibold flex items-center gap-1">
                            <Cpu className="w-2.5 h-2.5" /> Local Engine (Click to Connect Live LLM)
                          </button>
                        )}
                      </div>
                    )}
                    {msg.llmError && (
                      <div className="text-[10px] text-amber-400 light:text-amber-800 bg-amber-500/10 border border-amber-500/25 rounded-lg p-2 leading-relaxed">
                        ⚠️ <strong>AI Provider Note:</strong> {msg.llmError}. Fallback physiological engine activated.
                      </div>
                    )}
                    <OdinMarkdown content={msg.content} />
                    {msg.citations && msg.citations.length > 0 && (
                      <div className="mt-3 pt-2.5 text-[10px] space-y-1" style={{ borderTop: '1px solid var(--border)', color: 'var(--text-muted)' }}>
                        <strong className="text-emerald-400 light:text-emerald-700 block">📚 Scientific Grounding:</strong>
                        {msg.citations.map((c, i) => (
                          <div key={i}>• <strong>{c.authors}</strong> ({c.journal}) – <em>&quot;{c.key_takeaway}&quot;</em></div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))}
          {isLoading && (
            <div className="flex items-start gap-3">
              <div className="w-7 h-7 rounded-full bg-emerald-600/30 text-emerald-400 light:text-emerald-700 flex items-center justify-center text-xs shrink-0">
                <Dna className="w-3.5 h-3.5 animate-spin" />
              </div>
              <div className="rounded-xl rounded-tl-none p-3 text-xs italic" style={{ background: 'var(--card-inner)', border: '1px solid var(--border)', color: 'var(--text-muted)' }}>
                OdinAI is synthesizing multi-sensor telemetry & sports science
                <span className="ml-1"><span className="dot-1">.</span><span className="dot-2">.</span><span className="dot-3">.</span></span>
              </div>
            </div>
          )}
        </div>

        {/* Prompt Chips */}
        <div className="py-2.5 flex flex-wrap gap-1.5 text-xs" style={{ borderTop: '1px solid var(--border)' }}>
          {PROMPT_CHIPS.map(chip => (
            <button key={chip.query} onClick={() => sendMessage(chip.query)}
              className="rounded-lg px-2.5 py-1 text-[11px] transition"
              style={{ background: 'var(--card-inner)', border: '1px solid var(--border)', color: 'var(--text-sub)' }}
            >
              <span className={`${chip.color} mr-1`}>•</span>{chip.label}
            </button>
          ))}
        </div>

        {/* Input */}
        <form onSubmit={handleSubmit} className="flex items-center gap-2 pt-2" style={{ borderTop: '1px solid var(--border)' }}>
          <input
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder="Ask OdinAI about your biometrics, recovery, or training..."
            className="flex-1 rounded-xl px-3.5 py-2 text-xs focus:outline-none focus:border-emerald-500 transition"
            style={{ background: 'var(--card-inner)', border: '1px solid var(--border)', color: 'var(--text-primary)' }}
          />
          <button type="submit" disabled={isLoading}
            className="bg-emerald-500 hover:bg-emerald-600 text-black px-4 py-2 rounded-xl font-bold text-xs transition flex items-center gap-1 disabled:opacity-50">
            <span>Ask</span> <Send className="w-3 h-3" />
          </button>
        </form>
      </div>

      {/* Right Panel */}
      <div className="space-y-6">
        {/* Alerts */}
        <div className="rounded-2xl p-5" style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-xs font-bold flex items-center gap-2">
              ⚠️ Biometric Alerts
            </h4>
            <span className={`text-[10px] px-2 py-0.5 rounded-full font-semibold border ${
              anomalies && anomalies.anomalies_count > 0
                ? 'bg-rose-500/10 text-rose-400 light:text-rose-700 border-rose-500/20'
                : 'bg-emerald-500/10 text-emerald-400 light:text-emerald-700 border-emerald-500/20'
            }`}>{anomalies?.anomalies_count ?? 0} Active</span>
          </div>
          <div className="space-y-2 text-xs">
            {(!anomalies || anomalies.anomalies_count === 0) ? (
              <p className="text-[11px] italic" style={{ color: 'var(--text-muted)' }}>All biomarkers in physiological equilibrium.</p>
            ) : (
              anomalies.anomalies.map((a, i) => (
                <div key={i} className="rounded-lg p-2.5 space-y-1" style={{ border: '1px solid rgba(244,63,94,0.3)', background: 'var(--card-inner)' }}>
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-rose-400 light:text-rose-700 uppercase text-[10px]">{a.metric}</span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-rose-950 text-rose-300 light:bg-rose-100 light:text-rose-700">{a.detected_value}</span>
                  </div>
                  <p style={{ color: 'var(--text-sub)' }}>{a.message}</p>
                  <div className="text-[10px] text-emerald-400 light:text-emerald-700">💡 {a.actionable_fix}</div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Scientific Grounding */}
        <div className="rounded-2xl p-5 text-xs" style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
          <h4 className="text-xs font-bold flex items-center gap-2 mb-3">
            <BookMarked className="w-3.5 h-3.5 text-emerald-400 light:text-emerald-700" /> Scientific Grounding
          </h4>
          <div className="space-y-2.5 text-[11px]" style={{ color: 'var(--text-muted)' }}>
            {CITATIONS.map((c, i) => (
              <div key={i} className={`border-l-2 ${c.color} pl-2.5`}>
                <strong className="block" style={{ color: 'var(--text-sub)' }}>{c.title}</strong>
                {c.cite}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
