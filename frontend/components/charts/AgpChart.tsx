'use client';
import {
  ComposedChart, Area, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ReferenceLine, ResponsiveContainer
} from 'recharts';
import { useTheme } from 'next-themes';
import type { AgpResponse } from '@/types/api';

interface Props { data: AgpResponse; compact?: boolean; }

export function AgpChart({ data, compact }: Props) {
  const { resolvedTheme } = useTheme();
  const isDark = resolvedTheme !== 'light';
  const grid = isDark ? '#161e2e' : '#e2e8f0';
  const tick = '#64748b';

  const chartData = data.time_series.timestamps.map((t, i) => ({
    time: i % 12 === 0 ? t : '',
    fullTime: t,
    glucose: data.time_series.glucose_values[i],
    low: 70,
    high: 140,
  }));

  return (
    <ResponsiveContainer width="100%" height={compact ? 180 : 240}>
      <ComposedChart data={chartData} margin={{ top: 4, right: 8, left: -16, bottom: 0 }}>
        <CartesianGrid stroke={grid} strokeDasharray="3 3" />
        <XAxis dataKey="time" tick={{ fontSize: 10, fill: tick }} />
        <YAxis domain={[50, 220]} tick={{ fontSize: 10, fill: tick }} />
        <Tooltip
          contentStyle={{ background: isDark ? '#0e1320' : '#fff', border: isDark ? '1px solid #1a2234' : '1px solid #e2e8f0', borderRadius: 8, fontSize: 11 }}
          formatter={(v) => [`${v} mg/dL`, 'Glucose']}
          labelFormatter={(l) => l}
        />
        {/* TIR band */}
        <Area type="monotone" dataKey="high" stroke="none" fill="rgba(16,185,129,0.08)" fillOpacity={1} legendType="none" />
        {/* Glucose line */}
        <Line type="monotone" dataKey="glucose" stroke="#f59e0b" strokeWidth={2} dot={false} activeDot={{ r: 4 }} />
        <ReferenceLine y={70} stroke="#ef4444" strokeDasharray="4 4" strokeWidth={1} label={{ value: '70', fontSize: 9, fill: '#ef4444' }} />
        <ReferenceLine y={140} stroke="#10b981" strokeDasharray="4 4" strokeWidth={1} label={{ value: '140', fontSize: 9, fill: '#10b981' }} />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
