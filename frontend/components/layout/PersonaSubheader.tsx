'use client';
import { RefreshCw } from 'lucide-react';
import type { Persona, AnomaliesResponse } from '@/types/api';
import { useAppStore } from '@/store/appStore';

interface Props {
  persona: Persona | null;
  anomalies: AnomaliesResponse | null;
  onAskOdin: () => void;
}

export function PersonaSubheader({ persona, anomalies, onAskOdin }: Props) {
  return (
    <div className="space-y-2">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 rounded-xl px-4 py-3 text-xs transition-colors"
        style={{ background: 'rgba(17,24,39,0.4)', border: '1px solid var(--border-subtle)' }}>
        <div className="flex items-center space-x-3">
          <div className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
          <div>
            <span style={{ color: 'var(--text-muted)' }}>Active Profile:</span>
            <strong className="ml-1 font-semibold">{persona?.name ?? '—'}</strong>
            <span className="mx-1.5" style={{ color: 'var(--text-muted)' }}>•</span>
            <span className="text-emerald-400 font-medium">{persona?.target_goal ?? '—'}</span>
          </div>
        </div>
        <div className="flex items-center space-x-2" style={{ color: 'var(--text-muted)' }}>
          <span>Sensors:</span>
          <span className="font-medium" style={{ color: 'var(--text-sub)' }}>{persona?.primary_sensors.join(', ') ?? '—'}</span>
        </div>
      </div>

      {anomalies && anomalies.anomalies_count > 0 && (
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-xs text-amber-200 flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <span className="text-amber-400 text-sm">⚠</span>
            <span>{anomalies.anomalies_count} Biometric Alert(s): {anomalies.anomalies[0]?.message}</span>
          </div>
          <button onClick={onAskOdin} className="text-amber-300 underline hover:text-white font-medium">Ask OdinAI</button>
        </div>
      )}
    </div>
  );
}
