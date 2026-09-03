'use client';
import { HeartPulse, Activity, Moon, Hourglass, PersonStanding } from 'lucide-react';
import { AgpChart } from '@/components/charts/AgpChart';
import type { RecoveryResponse, AnomaliesResponse, WorkoutResponse, AgpResponse, BioAgeResponse, Persona } from '@/types/api';

interface Props {
  recovery: RecoveryResponse | null;
  anomalies: AnomaliesResponse | null;
  workout: WorkoutResponse | null;
  agp: AgpResponse | null;
  bioAge: BioAgeResponse | null;
  persona: Persona | null;
  onAskOdin: () => void;
}

function StatCard({ label, value, unit, sub, color, Icon }: {
  label: string; value: string | number; unit?: string; sub?: string;
  color: string; Icon: React.ElementType;
}) {
  return (
    <div className="rounded-2xl p-4 transition" style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
      <div className="flex items-center justify-between text-xs mb-1" style={{ color: 'var(--text-muted)' }}>
        <span>{label}</span>
        <Icon className={`w-3.5 h-3.5 ${color}`} />
      </div>
      <div className="flex items-baseline space-x-1.5 my-1">
        <span className={`text-3xl font-black ${color}`}>{value}</span>
        {unit && <span className="text-xs" style={{ color: 'var(--text-muted)' }}>{unit}</span>}
      </div>
      {sub && <p className="text-[11px]" style={{ color: 'var(--text-muted)' }}>{sub}</p>}
    </div>
  );
}

export function OverviewTab({ recovery, workout, agp, bioAge, onAskOdin }: Props) {
  const bb = recovery?.biometric_breakdown;
  const plan = workout?.prescribed_plan;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* 4 Stat Cards */}
      <div id="tour-vitals" className="grid grid-cols-2 lg:grid-cols-4 gap-3.5">
        <StatCard
          label="Autonomic Recovery"
          value={recovery?.recovery_score ?? '--'}
          unit="/ 100"
          sub={recovery?.status ?? 'Calculating...'}
          color="text-emerald-400"
          Icon={HeartPulse}
        />
        <StatCard
          label="Overnight HRV"
          value={bb?.current_hrv_rmssd ?? '--'}
          unit="ms"
          sub={bb ? `z-score: ${bb.hrv_z_score > 0 ? '+' : ''}${bb.hrv_z_score}` : undefined}
          color="text-cyan-400"
          Icon={Activity}
        />
        <StatCard
          label="Sleep Efficiency"
          value={bb ? Math.round(bb.sleep_efficiency_pct) : '--'}
          unit="%"
          sub={bb ? `Deep: ${bb.deep_sleep_pct}% of sleep` : undefined}
          color="text-indigo-400"
          Icon={Moon}
        />
        <StatCard
          label="Biological Age"
          value={bioAge?.biological_age ?? '--'}
          unit="yrs"
          sub={bioAge ? `${bioAge.biological_age_delta_years} yrs decelerated` : undefined}
          color="text-teal-400"
          Icon={Hourglass}
        />
      </div>

      {/* CGM + Workout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* CGM */}
        <div className="lg:col-span-2 rounded-2xl p-5" style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
          <div className="flex items-center justify-between mb-3">
            <div>
              <h3 className="text-sm font-semibold flex items-center gap-2">
                <span className="text-amber-400">⚡</span>
                Continuous Glucose Profile (CGM 24h)
              </h3>
              <p className="text-[11px]" style={{ color: 'var(--text-muted)' }}>Target Range 70–140 mg/dL • Terra Graph API</p>
            </div>
            {agp && (
              <span className="text-xs font-semibold px-2 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/20">
                TIR: {agp.agp_metrics.time_in_range_pct}%
              </span>
            )}
          </div>
          {agp ? <AgpChart data={agp} compact /> : (
            <div className="h-44 flex items-center justify-center" style={{ color: 'var(--text-muted)' }}>Loading chart...</div>
          )}
        </div>

        {/* Workout */}
        <div className="rounded-2xl p-5 flex flex-col justify-between" style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-[11px] uppercase tracking-wider text-cyan-400 font-semibold flex items-center gap-1.5">
                <PersonStanding className="w-3.5 h-3.5" /> Today&apos;s Prescription
              </span>
              {plan && (
                <span className="text-[11px] font-medium px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-300 border border-cyan-500/20">
                  Strain {plan.target_strain}
                </span>
              )}
            </div>
            <h4 className="text-base font-bold mb-1.5">{plan?.workout_title ?? 'Loading...'}</h4>
            <p className="text-xs mb-3 leading-relaxed" style={{ color: 'var(--text-sub)' }}>
              {plan ? `${plan.category} (${plan.duration_minutes} mins)` : ''}
            </p>
            <div className="rounded-xl p-3 text-[11px]" style={{ background: 'var(--card-inner)', border: '1px solid var(--border)' }}>
              <strong className="block mb-0.5" style={{ color: 'var(--text-sub)' }}>Physiological Rationale:</strong>
              <span style={{ color: 'var(--text-muted)' }}>{plan?.rationale}</span>
            </div>
          </div>
          <div className="pt-4 mt-4 flex items-center justify-between" style={{ borderTop: '1px solid var(--border)' }}>
            <button onClick={onAskOdin} className="text-xs text-emerald-400 hover:text-emerald-300 font-medium flex items-center gap-1">
              Ask OdinAI for workout tweaks →
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
