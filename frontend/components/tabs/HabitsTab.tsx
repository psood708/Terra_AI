'use client';
import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { useAppStore } from '@/store/appStore';
import type { RewardsResponse, DigitalTwinsResponse, CausalImpactsResponse } from '@/types/api';

export function HabitsTab() {
  const { currentPersona, currentStreak, setStreak } = useAppStore();
  const [rewards, setRewards] = useState<RewardsResponse | null>(null);
  const [twins, setTwins] = useState<DigitalTwinsResponse | null>(null);
  const [causal, setCausal] = useState<CausalImpactsResponse | null>(null);

  useEffect(() => {
    Promise.all([
      api.getRewards(currentPersona, currentStreak),
      api.getDigitalTwins(currentPersona),
      api.getCausalImpacts(currentPersona),
    ]).then(([r, t, c]) => { setRewards(r); setTwins(t); setCausal(c); });
  }, [currentPersona, currentStreak]);

  const handleClaimStreak = async () => {
    const data = await api.claimStreak(currentPersona, currentStreak);
    if (data?.new_streak_days) { setStreak(data.new_streak_days); }
  };

  const ra = rewards?.retention_analytics;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Streak & Retention */}
      <div className="rounded-2xl p-5" style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
        <div className="flex items-center justify-between pb-3 mb-4" style={{ borderBottom: '1px solid var(--border)' }}>
          <div>
            <h3 className="text-sm font-bold flex items-center gap-2">
              🏆 Behavioral Retention & Streak Multiplier
            </h3>
            <p className="text-[11px]" style={{ color: 'var(--text-muted)' }}>RL-based micro-incentives sustaining Day-30 and Day-90 engagement</p>
          </div>
          <button onClick={handleClaimStreak}
            className="text-xs px-3 py-1.5 bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 light:text-amber-800 border border-amber-500/30 rounded-lg transition font-semibold flex items-center gap-1">
            🔥 Claim Streak
          </button>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
          {[{
            label: 'Active Streak', value: rewards?.streak_days ?? '--', unit: 'Days', sub: rewards ? `${rewards.streak_multiplier}x Multiplier` : '', subColor: 'text-emerald-400 light:text-emerald-700',
          }, {
            label: 'Daily Points', value: rewards?.daily_points_earned ?? '--', unit: 'pts', sub: rewards ? `${rewards.achieved_habits_count} habits met` : '', subColor: 'text-[color:var(--text-muted)]',
          }, {
            label: 'Retention Index', value: rewards ? Math.round(ra!.retention_index_score) : '--', unit: '/ 100', sub: ra?.churn_risk_level ?? '', subColor: 'text-emerald-400 light:text-emerald-700',
          }, {
            label: 'Best Nudge Window', value: ra?.best_notification_window ?? '--', unit: '', sub: ra?.recommended_nudge_strategy ?? '', subColor: 'text-[color:var(--text-muted)]',
          }].map((item, i) => (
            <div key={i} className="rounded-xl p-3" style={{ background: 'var(--card-inner)', border: '1px solid var(--border)' }}>
              <span className="text-[10px] block" style={{ color: 'var(--text-muted)' }}>{item.label}</span>
              <div className="flex items-baseline space-x-1 mt-0.5">
                <span className="text-xl font-bold text-amber-400 light:text-amber-700">{item.value}</span>
                {item.unit && <span style={{ color: 'var(--text-muted)' }}>{item.unit}</span>}
              </div>
              {item.sub && <span className={`text-[10px] ${item.subColor} block`}>{item.sub}</span>}
            </div>
          ))}
        </div>
      </div>

      {/* Causal + Twins */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Causal Pathways */}
        <div className="rounded-2xl p-5" style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
          <h4 className="text-xs font-bold flex items-center gap-2 mb-3">
            🔘 Biometric Causal Graph Pathways
          </h4>
          <div className="space-y-2 max-h-72 overflow-y-auto text-xs pr-1">
            {causal?.causal_impacts.length === 0 && (
              <p style={{ color: 'var(--text-muted)' }}>No behavioral impacts logged for today.</p>
            )}
            {causal?.causal_impacts.map((impact, i) => (
              <div key={i} className="rounded-xl p-2.5 space-y-1" style={{ border: `1px solid ${impact.direction === 'positive' ? 'rgba(16,185,129,0.3)' : 'rgba(244,63,94,0.3)'}`, background: 'var(--card-inner)' }}>
                <div className="flex items-center justify-between">
                  <span className="font-semibold flex items-center gap-1">
                    {impact.direction === 'positive' ? '↗️' : '↘️'} {impact.behavior}
                  </span>
                  <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-semibold ${
                    impact.direction === 'positive' ? 'bg-emerald-500/10 text-emerald-400 light:text-emerald-700' : 'bg-rose-500/10 text-rose-400 light:text-rose-700'
                  }`}>{impact.net_impact_score > 0 ? '+' : ''}{impact.net_impact_score} net</span>
                </div>
                <div className="text-[11px]" style={{ color: 'var(--text-sub)' }}>
                  Path: <strong>{impact.affected_biomarker}</strong> → {impact.target_outcome}
                </div>
                <p className="text-[10px] leading-normal" style={{ color: 'var(--text-muted)' }}>{impact.physiological_mechanism}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Digital Twins */}
        <div className="rounded-2xl p-5" style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
          <h4 className="text-xs font-bold flex items-center gap-2 mb-3">
            👥 Digital Health Twins (Cosine Similarity)
          </h4>
          <div className="space-y-2 max-h-72 overflow-y-auto text-xs pr-1">
            {twins?.digital_twins.map((twin, i) => (
              <div key={i} className="rounded-xl p-3 flex items-center justify-between" style={{ background: 'var(--card-inner)', border: '1px solid var(--border)' }}>
                <div>
                  <div className="flex items-center gap-2">
                    <h5 className="font-semibold">{twin.name}</h5>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 light:text-indigo-700">{twin.target_goal}</span>
                  </div>
                  <div className="text-[10px] mt-1 space-x-2" style={{ color: 'var(--text-muted)' }}>
                    {twin.shared_traits.map((t, j) => <span key={j}>• {t}</span>)}
                  </div>
                </div>
                <div className="text-right">
                  <span className="text-base font-black text-indigo-400 light:text-indigo-700">{twin.similarity_score_pct}%</span>
                  <span className="text-[9px] block" style={{ color: 'var(--text-muted)' }}>Cosine Match</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
