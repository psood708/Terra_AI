'use client';
import { useState, useCallback, useEffect } from 'react';
import { api } from '@/lib/api';
import { useAppStore } from '@/store/appStore';
import type { BioAgeResponse, WhatIfResponse } from '@/types/api';

interface Props {
  bioAge: BioAgeResponse | null;
}

function Slider({ label, min, max, step, value, onChange, displayFn }: {
  label: string; min: number; max: number; step: number; value: number;
  onChange: (v: number) => void; displayFn: (v: number) => string;
}) {
  return (
    <div>
      <div className="flex justify-between font-medium mb-1">
        <span className="text-xs" style={{ color: 'var(--text-sub)' }}>{label}</span>
        <span className="text-xs text-emerald-400 font-bold">{displayFn(value)}</span>
      </div>
      <input
        type="range" min={min} max={max} step={step} value={value}
        onChange={e => onChange(Number(e.target.value))}
        className="w-full h-1.5 rounded-lg appearance-none cursor-pointer accent-emerald-500"
        style={{ background: 'var(--border)' }}
      />
    </div>
  );
}

export function LongevityTab({ bioAge }: Props) {
  const { currentPersona } = useAppStore();
  const [sleep, setSleep] = useState(30);
  const [cardio, setCardio] = useState(60);
  const [dinner, setDinner] = useState(2.0);
  const [tir, setTir] = useState(8);
  const [result, setResult] = useState<WhatIfResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const runSim = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.whatIf({
        persona_id: currentPersona,
        added_sleep_minutes: sleep,
        added_zone2_minutes_weekly: cardio,
        earlier_dinner_shift_hours: dinner,
        improved_glucose_tir_pct: tir,
      });
      setResult(res);
    } catch {}
    setLoading(false);
  }, [currentPersona, sleep, cardio, dinner, tir]);

  useEffect(() => { runSim(); }, [runSim]);

  const outcome = result?.simulated_outcome;

  return (
    <div id="tour-whatif" className="animate-fade-in">
      <div className="rounded-2xl p-6 space-y-6" style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4" style={{ borderBottom: '1px solid var(--border)' }}>
          <div>
            <h3 className="text-base font-bold flex items-center gap-2">
              🎛️ 10-Year Health Forecasting & What-If Simulator
            </h3>
            <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>
              Test counterfactual lifestyle interventions to simulate shifts in Biological Age
            </p>
          </div>
          <div className="text-xs" style={{ color: 'var(--text-muted)' }}>
            Chrono Age: <strong>{bioAge?.chronological_age ?? '--'}</strong> yrs • Current Bio-Age: <strong className="text-teal-400">{bioAge?.biological_age ?? '--'}</strong> yrs
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
          {/* Sliders */}
          <div className="space-y-4">
            <Slider label="🛌 Additional Sleep / Night" min={0} max={120} step={15} value={sleep} onChange={setSleep} displayFn={v => `+${v} minutes`} />
            <Slider label="❤️ Additional Zone 2 Cardio / Week" min={0} max={180} step={15} value={cardio} onChange={setCardio} displayFn={v => `+${v} minutes`} />
            <Slider label="🍽️ Shift Dinner Earlier" min={0} max={4} step={0.5} value={dinner} onChange={setDinner} displayFn={v => `${v.toFixed(1)} hrs before bed`} />
            <Slider label="📊 Glucose Time-in-Range Gain" min={0} max={25} step={1} value={tir} onChange={setTir} displayFn={v => `+${v}% TIR`} />
          </div>

          {/* Result */}
          <div className="rounded-2xl p-6" style={{ background: 'linear-gradient(to bottom right, var(--card-inner), var(--bg-page))', border: '1px solid rgba(16,185,129,0.3)' }}>
            <span className="text-[10px] uppercase tracking-wider text-emerald-400 font-semibold mb-2 flex items-center gap-1.5">
              ✨ Counterfactual Simulation Result
            </span>
            <div className="flex items-baseline space-x-3 my-3">
              <span className="text-4xl font-black">{loading ? '...' : (outcome?.projected_biological_age ?? '--')}</span>
              <span className="text-xs" style={{ color: 'var(--text-muted)' }}>Projected Bio-Age</span>
              {outcome && (
                <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                  -{outcome.net_biological_years_saved} yrs saved
                </span>
              )}
            </div>
            <p className="text-xs leading-relaxed pt-3" style={{ borderTop: '1px solid var(--border)', color: 'var(--text-sub)' }}>
              {result?.clinical_verdict ?? 'Running simulation...'}
            </p>
            {outcome && (
              <div className="grid grid-cols-3 gap-2 mt-4 text-center text-xs">
                <div className="rounded-lg p-2" style={{ background: 'var(--card-inner)', border: '1px solid var(--border)' }}>
                  <span className="text-[10px] block" style={{ color: 'var(--text-muted)' }}>HRV Boost</span>
                  <strong className="text-cyan-400">+{outcome.projected_hrv_improvement_ms} ms</strong>
                </div>
                <div className="rounded-lg p-2" style={{ background: 'var(--card-inner)', border: '1px solid var(--border)' }}>
                  <span className="text-[10px] block" style={{ color: 'var(--text-muted)' }}>VO2 Max Gain</span>
                  <strong className="text-emerald-400">+{outcome.projected_vo2_max_gain} ml/kg</strong>
                </div>
                <div className="rounded-lg p-2" style={{ background: 'var(--card-inner)', border: '1px solid var(--border)' }}>
                  <span className="text-[10px] block" style={{ color: 'var(--text-muted)' }}>Resting HR Drop</span>
                  <strong className="text-indigo-400">-{outcome.projected_rhr_reduction_bpm} bpm</strong>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
