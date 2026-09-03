'use client';
import { useCallback, useEffect, useState } from 'react';
import { Compass, X, ChevronRight, ChevronLeft } from 'lucide-react';
import type { TabId } from '@/types/api';

interface TourStep {
  targetId: string;
  tabId?: TabId;
  icon: string;
  title: string;
  description: string;
}

const TOUR_STEPS: TourStep[] = [
  {
    targetId: 'tour-brand',
    icon: '🧬',
    title: 'Terra Infrastructure & AI Layer',
    description: 'Terra connects over 500+ wearable sources into one normalized platform. This project implements the AI intelligence layer on top: autonomous health reasoning, trajectory forecasting, and extreme personalization.',
  },
  {
    targetId: 'tour-tabs',
    icon: '📊',
    title: 'Minimalist Modular Navigation',
    description: 'Switch between focused studios: Overview, OdinAI Health Assistant, Terra Graph API (AGP & hypnograms), 10-Year Longevity Simulator, and Habits & Retention.',
  },
  {
    targetId: 'tour-persona',
    icon: '👤',
    title: 'Multi-Goal Persona Switcher',
    description: 'Switch between personas to see extreme personalization in action: Alex Vance (Target 120 Longevity), Sarah Chen (Olympic Triathlon), Marcus Sterling (Metabolic Reversal), or Elena Rostova (Cognitive Stamina).',
  },
  {
    targetId: 'tour-vitals',
    icon: '❤️',
    title: 'Synthesized Biometric Vitals',
    description: 'Live cards displaying composite autonomic recovery, overnight HRV (rMSSD) z-scores, sleep architecture, and phenotypic biological age computed across multi-stream sensors.',
  },
  {
    targetId: 'tour-odin',
    icon: '🧠',
    title: 'OdinAI Health Intelligence Studio',
    description: 'Converse with OdinAI. Ask about recovery, training readiness, or glycemic excursions. Powered by active LLMs (Hugging Face / Gemini / OpenAI) with peer-reviewed sports science citations.',
  },
  {
    targetId: 'tour-whatif',
    tabId: 'longevity',
    icon: '🎛️',
    title: 'Counterfactual What-If Simulator',
    description: 'Drag sliders for sleep, Zone 2 cardio, dinner timing, and glucose stability to simulate real-time shifts in biological age and 10-year mortality reduction.',
  },
];

interface TourProps {
  isActive: boolean;
  onClose: () => void;
  onSwitchTab?: (tab: TabId) => void;
}

interface Rect { top: number; left: number; width: number; height: number; }

export function GuidedTour({ isActive, onClose, onSwitchTab }: TourProps) {
  const [step, setStep] = useState(0);
  const [spotRect, setSpotRect] = useState<Rect>({ top: 0, left: 0, width: 0, height: 0 });
  const [popoverPos, setPopoverPos] = useState({ top: 0, left: 0 });
  const [arrowLeft, setArrowLeft] = useState(20);
  const [isAbove, setIsAbove] = useState(false);

  const measure = useCallback(() => {
    const s = TOUR_STEPS[step];
    const el = document.getElementById(s.targetId);
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const pad = 8;
    const sTop = Math.max(4, rect.top - pad);
    const sLeft = Math.max(4, rect.left - pad);
    const sW = Math.min(window.innerWidth - 8, rect.width + pad * 2);
    const sH = rect.height + pad * 2;
    setSpotRect({ top: sTop, left: sLeft, width: sW, height: sH });

    const pw = Math.min(360, window.innerWidth - 32);
    let pLeft = sLeft + sW / 2 - pw / 2;
    pLeft = Math.max(16, Math.min(window.innerWidth - pw - 16, pLeft));

    const spaceBelow = window.innerHeight - (sTop + sH);
    const spaceAbove = sTop;
    let pTop: number;
    let above = false;
    if (spaceBelow >= 230 || spaceBelow >= spaceAbove) {
      pTop = sTop + sH + 14;
    } else {
      pTop = Math.max(12, sTop - 250);
      above = true;
    }
    setPopoverPos({ top: pTop, left: pLeft });
    const arrowX = Math.max(20, Math.min(pw - 28, (sLeft + sW / 2) - pLeft - 6));
    setArrowLeft(arrowX);
    setIsAbove(above);
  }, [step]);

  useEffect(() => {
    if (!isActive) return;
    const current = TOUR_STEPS[step];
    if (current.tabId && onSwitchTab) onSwitchTab(current.tabId);
    const el = document.getElementById(current.targetId);
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    const timer = setTimeout(measure, 150);
    return () => clearTimeout(timer);
  }, [isActive, step, measure, onSwitchTab]);

  useEffect(() => {
    if (!isActive) return;
    const onResize = () => measure();
    window.addEventListener('resize', onResize);
    window.addEventListener('scroll', onResize);
    return () => { window.removeEventListener('resize', onResize); window.removeEventListener('scroll', onResize); };
  }, [isActive, measure]);

  if (!isActive) return null;

  const current = TOUR_STEPS[step];
  const popoverWidth = Math.min(360, window.innerWidth - 32);

  return (
    <div className="fixed inset-0 z-50 pointer-events-none">
      {/* Dark overlay with cutout */}
      <div
        className="fixed inset-0 pointer-events-auto"
        style={{
          background: 'rgba(0,0,0,0.7)',
          clipPath: `polygon(
            0% 0%, 100% 0%, 100% 100%, 0% 100%, 0% 0%,
            ${spotRect.left}px ${spotRect.top}px,
            ${spotRect.left}px ${spotRect.top + spotRect.height}px,
            ${spotRect.left + spotRect.width}px ${spotRect.top + spotRect.height}px,
            ${spotRect.left + spotRect.width}px ${spotRect.top}px,
            ${spotRect.left}px ${spotRect.top}px
          )`,
        }}
        onClick={onClose}
      />

      {/* Spotlight border */}
      <div
        className="fixed rounded-xl pointer-events-none"
        style={{
          top: spotRect.top,
          left: spotRect.left,
          width: spotRect.width,
          height: spotRect.height,
          border: '2px solid rgba(16,185,129,0.6)',
          boxShadow: '0 0 0 4px rgba(16,185,129,0.15)',
          transition: 'all 0.2s ease',
        }}
      />

      {/* Popover */}
      <div
        className="fixed z-50 rounded-2xl p-5 shadow-2xl space-y-3 pointer-events-auto"
        style={{
          top: popoverPos.top,
          left: popoverPos.left,
          width: popoverWidth,
          background: 'var(--bg-card)',
          border: '1px solid rgba(16,185,129,0.4)',
          transition: 'all 0.2s ease',
        }}
      >
        {/* Arrow */}
        <div
          className="absolute w-3 h-3"
          style={{
            left: arrowLeft,
            [isAbove ? 'bottom' : 'top']: -7,
            background: 'var(--bg-card)',
            border: `1px solid rgba(16,185,129,0.4)`,
            borderRight: isAbove ? undefined : 'none',
            borderBottom: isAbove ? 'none' : undefined,
            transform: 'rotate(45deg)',
          }}
        />

        {/* Step indicator */}
        <div className="flex items-center justify-between text-[11px] pb-2" style={{ borderBottom: '1px solid var(--border)', color: 'var(--text-muted)' }}>
          <span className="flex items-center gap-1.5 text-emerald-400 font-semibold">
            <Compass className="w-3 h-3" /> Step {step + 1} of {TOUR_STEPS.length}
          </span>
          <button onClick={onClose} className="flex items-center gap-0.5 hover:text-white transition font-medium">
            Skip Tour <X className="w-3 h-3" />
          </button>
        </div>

        {/* Content */}
        <div className="space-y-1.5 py-1">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-lg bg-emerald-500/20 flex items-center justify-center text-sm shrink-0">
              {current.icon}
            </div>
            <h4 className="text-sm font-bold">{current.title}</h4>
          </div>
          <p className="text-xs leading-relaxed" style={{ color: 'var(--text-sub)' }}>{current.description}</p>
        </div>

        {/* Navigation */}
        <div className="flex items-center justify-between pt-2" style={{ borderTop: '1px solid var(--border)' }}>
          {/* Dots */}
          <div className="flex items-center gap-1">
            {TOUR_STEPS.map((_, i) => (
              <span key={i} className={`rounded-full transition-all ${
                i === step ? 'w-4 h-1.5 bg-emerald-400' : 'w-1.5 h-1.5 bg-gray-700'
              }`} />
            ))}
          </div>
          <div className="flex items-center gap-1.5">
            {step > 0 && (
              <button onClick={() => setStep(s => s - 1)}
                className="text-xs px-2.5 py-1 rounded-lg font-medium transition flex items-center gap-0.5"
                style={{ background: 'var(--card-inner)', border: '1px solid var(--border)', color: 'var(--text-sub)' }}>
                <ChevronLeft className="w-3 h-3" /> Back
              </button>
            )}
            <button
              onClick={() => { if (step < TOUR_STEPS.length - 1) { setStep(s => s + 1); } else { onClose(); } }}
              className="text-xs px-3.5 py-1 rounded-lg bg-emerald-500 hover:bg-emerald-600 text-black font-bold transition shadow flex items-center gap-0.5"
            >
              {step === TOUR_STEPS.length - 1 ? 'Finish Tour' : 'Next'}
              {step < TOUR_STEPS.length - 1 && <ChevronRight className="w-3 h-3" />}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
