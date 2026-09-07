'use client';
import {
  ComposedChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import { useTheme } from 'next-themes';
import type { CorrelationResponse } from '@/types/api';

interface Props { data: CorrelationResponse; }

export function CorrelationChart({ data }: Props) {
  const { resolvedTheme } = useTheme();
  const isDark = resolvedTheme !== 'light';
  const grid = isDark ? '#161e2e' : '#e2e8f0';
  const tick = '#64748b';

  const chartData = data.dates.map((d, i) => ({
    date: d.slice(5),
    hrv: data.series.hrv_rmssd_ms[i],
    sleep: data.series.sleep_hours[i],
    strain: data.series.workout_strain[i],
  }));

  return (
    <ResponsiveContainer width="100%" height={240}>
      <ComposedChart data={chartData} margin={{ top: 4, right: 16, left: -16, bottom: 0 }}>
        <CartesianGrid stroke={grid} strokeDasharray="3 3" />
        <XAxis dataKey="date" tick={{ fontSize: 10, fill: tick }} />
        <YAxis yAxisId="hrv" orientation="left" tick={{ fontSize: 10, fill: '#10b981' }} label={{ value: 'HRV ms', angle: -90, position: 'insideLeft', fontSize: 9, fill: '#10b981' }} />
        <YAxis yAxisId="sleep" orientation="right" tick={{ fontSize: 10, fill: '#6366f1' }} />
        <Tooltip
          contentStyle={{ background: isDark ? '#0e1320' : '#fff', border: isDark ? '1px solid #1a2234' : '1px solid #e2e8f0', borderRadius: 8, fontSize: 11 }}
        />
        <Legend wrapperStyle={{ fontSize: 11, color: isDark ? '#cbd5e1' : '#334155' }} iconSize={10} />
        <Line yAxisId="hrv" type="monotone" dataKey="hrv" name="HRV (ms)" stroke="#10b981" strokeWidth={2} dot={false} />
        <Line yAxisId="sleep" type="monotone" dataKey="sleep" name="Sleep (hrs)" stroke="#6366f1" strokeWidth={2} strokeDasharray="4 4" dot={false} />
        <Line yAxisId="sleep" type="monotone" dataKey="strain" name="Strain" stroke="#f59e0b" strokeWidth={2} dot={false} />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
