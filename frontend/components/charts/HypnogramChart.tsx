'use client';
import { PieChart, Pie, Cell, Legend, ResponsiveContainer, Tooltip } from 'recharts';
import { useTheme } from 'next-themes';
import type { HypnogramResponse } from '@/types/api';

interface Props { data: HypnogramResponse; }

export function HypnogramChart({ data }: Props) {
  const { resolvedTheme } = useTheme();
  const isDark = resolvedTheme !== 'light';

  const stages = [
    { name: 'Deep Sleep', value: data.stage_breakdown_minutes.deep, color: '#6366f1' },
    { name: 'REM Sleep', value: data.stage_breakdown_minutes.rem, color: '#06b6d4' },
    { name: 'Light Sleep', value: data.stage_breakdown_minutes.light, color: '#475569' },
    { name: 'Awake', value: data.stage_breakdown_minutes.awake, color: '#f43f5e' },
  ];

  return (
    <ResponsiveContainer width="100%" height={240}>
      <PieChart>
        <Pie
          data={stages}
          cx="50%" cy="50%"
          innerRadius={60} outerRadius={90}
          paddingAngle={2}
          dataKey="value"
        >
          {stages.map((s, i) => <Cell key={i} fill={s.color} />)}
        </Pie>
        <Tooltip
          contentStyle={{ background: isDark ? '#0e1320' : '#fff', border: isDark ? '1px solid #1a2234' : '1px solid #e2e8f0', borderRadius: 8, fontSize: 11 }}
          formatter={(v) => [`${v} min`]}
        />
        <Legend
          wrapperStyle={{ fontSize: 11, color: isDark ? '#cbd5e1' : '#334155' }}
          iconSize={10}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}
