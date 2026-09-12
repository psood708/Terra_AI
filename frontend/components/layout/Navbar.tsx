'use client';
import { useTheme } from 'next-themes';
import { useEffect, useState } from 'react';
import { Dna, Gauge, Brain, ChartLine, Hourglass, Trophy, Sparkles, Compass, Code, Sun, Moon, ChevronDown, RefreshCw } from 'lucide-react';
import { useAppStore } from '@/store/appStore';
import { API_BASE } from '@/lib/api';
import type { TabId, PersonaId } from '@/types/api';

const TABS: { id: TabId; label: string; Icon: React.ElementType; color: string }[] = [
  { id: 'overview', label: 'Overview', Icon: Gauge, color: 'text-emerald-400 light:text-emerald-700' },
  { id: 'odin', label: 'OdinAI Studio', Icon: Brain, color: 'text-cyan-400 light:text-cyan-700' },
  { id: 'graphs', label: 'Terra Graph API', Icon: ChartLine, color: 'text-amber-400 light:text-amber-700' },
  { id: 'longevity', label: 'Longevity Sim', Icon: Hourglass, color: 'text-teal-400 light:text-teal-700' },
  { id: 'habits', label: 'Habits & Cohorts', Icon: Trophy, color: 'text-indigo-400 light:text-indigo-700' },
];

const PERSONAS: { id: PersonaId; label: string }[] = [
  { id: 'alex_longevity', label: 'Alex Vance (Target 120)' },
  { id: 'sarah_athlete', label: 'Sarah Chen (Triathlon)' },
  { id: 'marcus_metabolic', label: 'Marcus Sterling (Metabolic)' },
  { id: 'elena_cognitive', label: 'Elena Rostova (Cognitive)' },
];

interface NavbarProps {
  onOpenAiModal: () => void;
  onStartTour: () => void;
  onRefresh: () => void;
}

export function Navbar({ onOpenAiModal, onStartTour, onRefresh }: NavbarProps) {
  const { resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  const { selectedTab, setSelectedTab, currentPersona, setCurrentPersona, activeApiKey, activeProvider } = useAppStore();

  // next-themes' documented hydration-safe pattern: resolvedTheme is unknown
  // during SSR, so we only render the theme icon after client mount to avoid
  // a hydration mismatch. Single mount-only setState, not a cascading render.
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => setMounted(true), []);

  const providerLabel = activeApiKey ? (activeProvider === 'openai' ? 'GPT-4o' : activeProvider === 'gemini' ? 'Gemini' : 'HF') : 'Local';

  return (
    <header style={{ borderBottom: '1px solid var(--border-subtle)', background: 'var(--bg-nav)' }}
      className="backdrop-blur-md sticky top-0 z-40 transition-colors duration-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-4">

        {/* Brand */}
        <div id="tour-brand" className="flex items-center space-x-3 shrink-0">
          <div className="w-8 h-8 rounded-lg bg-emerald-500 flex items-center justify-center shadow-lg shadow-emerald-500/20">
            <Dna className="w-4 h-4 text-black" />
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-base font-bold tracking-tight">TERRA</span>
            <span className="text-[10px] uppercase px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 light:text-emerald-700 border border-emerald-500/20 font-semibold tracking-wider">AI Engine</span>
          </div>
        </div>

        {/* Segmented Nav — desktop */}
        <nav id="tour-tabs" className="hidden md:flex items-center rounded-xl p-1 text-xs font-medium space-x-1"
          style={{ background: 'var(--card-inner)', border: '1px solid var(--border-subtle)' }}>
          {TABS.map(({ id, label, Icon, color }) => (
            <button
              key={id}
              onClick={() => setSelectedTab(id)}
              className={`px-3 py-1.5 rounded-lg transition flex items-center gap-1.5 ${
                selectedTab === id
                  ? 'bg-emerald-500/15 text-white light:text-emerald-800'
                  : 'text-[color:var(--text-muted)] hover:text-[color:var(--text-primary)]'
              }`}
            >
              <Icon className={`w-3 h-3 ${color}`} />
              {label}
            </button>
          ))}
        </nav>

        {/* Right cluster */}
        <div className="flex items-center space-x-2 shrink-0">
          {/* Persona */}
          <div id="tour-persona" className="relative">
            <select
              value={currentPersona}
              onChange={e => setCurrentPersona(e.target.value as PersonaId)}
              className="h-9 rounded-lg px-2.5 pr-7 text-xs font-medium focus:outline-none focus:border-emerald-500 cursor-pointer appearance-none transition"
              style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', color: 'var(--text-primary)' }}
            >
              {PERSONAS.map(p => <option key={p.id} value={p.id}>{p.label}</option>)}
            </select>
            <ChevronDown className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 w-3 h-3 text-[color:var(--text-muted)]" />
          </div>

          {/* Refresh */}
          <button onClick={onRefresh} className="h-9 w-9 rounded-lg transition flex items-center justify-center"
            style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', color: 'var(--text-muted)' }}
            title="Refresh Live Stream">
            <RefreshCw className="w-3.5 h-3.5" />
          </button>

          {/* Theme */}
          <button
            onClick={() => setTheme(resolvedTheme === 'dark' ? 'light' : 'dark')}
            className="h-9 w-9 rounded-lg transition flex items-center justify-center"
            style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', color: 'var(--text-muted)' }}
            title="Toggle theme"
          >
            {mounted && (resolvedTheme === 'dark' ? <Sun className="w-3.5 h-3.5" /> : <Moon className="w-3.5 h-3.5" />)}
          </button>

          {/* AI Settings */}
          <button onClick={onOpenAiModal}
            className="h-9 px-2.5 rounded-lg transition flex items-center space-x-1.5"
            style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', color: 'var(--text-muted)' }}
          >
            <Sparkles className="w-3 h-3 text-emerald-400 light:text-emerald-700" />
            <span className="text-xs hidden lg:inline">AI: {providerLabel}</span>
          </button>

          {/* Tour */}
          <button onClick={onStartTour}
            className="h-9 px-2.5 rounded-lg transition flex items-center space-x-1.5"
            style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', color: 'var(--text-muted)' }}
          >
            <Compass className="w-3 h-3 text-emerald-400 light:text-emerald-700" />
            <span className="text-xs hidden sm:inline">Tour</span>
          </button>

          {/* Swagger */}
          <a href={`${API_BASE}/docs`} target="_blank"
            className="h-9 w-9 rounded-lg transition flex items-center justify-center"
            style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', color: 'var(--text-muted)' }}
            title="OpenAPI Docs"
          >
            <Code className="w-3.5 h-3.5" />
          </a>
        </div>
      </div>

      {/* Mobile tab bar */}
      <div className="md:hidden flex overflow-x-auto px-4 py-2 space-x-1 text-xs"
        style={{ borderTop: '1px solid var(--border-subtle)' }}>
        {TABS.map(({ id, label }) => (
          <button key={id} onClick={() => setSelectedTab(id)}
            className={`whitespace-nowrap px-3 py-1 rounded-md transition ${
              selectedTab === id ? 'bg-emerald-500/15 text-emerald-400 light:text-emerald-700' : 'text-[color:var(--text-muted)]'
            }`}>
            {label}
          </button>
        ))}
      </div>
    </header>
  );
}
