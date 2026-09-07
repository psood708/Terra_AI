'use client';
import { AgpChart } from '@/components/charts/AgpChart';
import { HypnogramChart } from '@/components/charts/HypnogramChart';
import { CorrelationChart } from '@/components/charts/CorrelationChart';
import type { AgpResponse, HypnogramResponse, CorrelationResponse } from '@/types/api';

interface Props {
  agp: AgpResponse | null;
  hypnogram: HypnogramResponse | null;
  correlation: CorrelationResponse | null;
}

export function GraphsTab({ agp, hypnogram, correlation }: Props) {
  return (
    <div className="space-y-6 animate-fade-in">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* AGP */}
        <div className="rounded-2xl p-5" style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold flex items-center gap-2">
                <span className="text-amber-400 light:text-amber-700">📊</span> Ambulatory Glucose Profile (AGP) 24h
              </h3>
              <p className="text-[11px]" style={{ color: 'var(--text-muted)' }}>Clinical Target: 70–140 mg/dL</p>
            </div>
            {agp && <div className="text-xs font-semibold px-2.5 py-1 rounded bg-amber-500/10 text-amber-400 light:text-amber-700 border border-amber-500/20">TIR: {agp.agp_metrics.time_in_range_pct}%</div>}
          </div>
          {agp ? <AgpChart data={agp} /> : <div className="h-60 flex items-center justify-center" style={{ color: 'var(--text-muted)' }}>Loading...</div>}
          {agp && (
            <div className="grid grid-cols-3 gap-2 mt-4 pt-3 text-center text-xs" style={{ borderTop: '1px solid var(--border)' }}>
              <div><span className="text-[10px] block" style={{ color: 'var(--text-muted)' }}>Mean Glucose</span><strong>{agp.agp_metrics.mean_glucose_mg_dl} mg/dL</strong></div>
              <div><span className="text-[10px] block" style={{ color: 'var(--text-muted)' }}>Est. A1c (GMI)</span><strong className="text-emerald-400 light:text-emerald-700">{agp.agp_metrics.gmi_estimated_a1c}%</strong></div>
              <div><span className="text-[10px] block" style={{ color: 'var(--text-muted)' }}>Variability (CV)</span><strong>{agp.agp_metrics.glycemic_variability_cv_pct}%</strong></div>
            </div>
          )}
        </div>

        {/* Hypnogram */}
        <div className="rounded-2xl p-5" style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold flex items-center gap-2">
                <span className="text-indigo-400 light:text-indigo-700">🛀</span> Sleep Architecture & Hypnogram
              </h3>
              <p className="text-[11px]" style={{ color: 'var(--text-muted)' }}>Deep, REM, Light, and Awake breakdown</p>
            </div>
            {hypnogram && <div className="text-xs font-semibold px-2.5 py-1 rounded bg-indigo-500/10 text-indigo-400 light:text-indigo-700 border border-indigo-500/20">Score: {hypnogram.sleep_score}</div>}
          </div>
          {hypnogram ? <HypnogramChart data={hypnogram} /> : <div className="h-60 flex items-center justify-center" style={{ color: 'var(--text-muted)' }}>Loading...</div>}
          {hypnogram && (
            <div className="grid grid-cols-4 gap-2 mt-4 pt-3 text-center text-xs" style={{ borderTop: '1px solid var(--border)' }}>
              <div><span className="text-[10px] block" style={{ color: 'var(--text-muted)' }}>Deep</span><strong className="text-indigo-300 light:text-indigo-700">{hypnogram.stage_breakdown_minutes.deep}m</strong></div>
              <div><span className="text-[10px] block" style={{ color: 'var(--text-muted)' }}>REM</span><strong className="text-cyan-300 light:text-cyan-700">{hypnogram.stage_breakdown_minutes.rem}m</strong></div>
              <div><span className="text-[10px] block" style={{ color: 'var(--text-muted)' }}>Light</span><strong style={{ color: 'var(--text-muted)' }}>{hypnogram.stage_breakdown_minutes.light}m</strong></div>
              <div><span className="text-[10px] block" style={{ color: 'var(--text-muted)' }}>Awake</span><strong className="text-rose-400 light:text-rose-700">{hypnogram.stage_breakdown_minutes.awake}m</strong></div>
            </div>
          )}
        </div>
      </div>

      {/* 14-day Correlation */}
      <div className="rounded-2xl p-5" style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-semibold flex items-center gap-2">
              <span className="text-teal-400 light:text-teal-700">🔗</span> 14-Day Multi-Stream Longitudinal Coupling
            </h3>
            <p className="text-[11px]" style={{ color: 'var(--text-muted)' }}>Overlaying Daily Workout Strain vs Sleep Duration vs Overnight HRV</p>
          </div>
        </div>
        {correlation ? <CorrelationChart data={correlation} /> : <div className="h-60 flex items-center justify-center" style={{ color: 'var(--text-muted)' }}>Loading...</div>}
      </div>
    </div>
  );
}
