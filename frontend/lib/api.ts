import type {
  RecoveryResponse, AnomaliesResponse, WorkoutResponse,
  AgpResponse, HypnogramResponse, CorrelationResponse,
  BioAgeResponse, WhatIfInput, WhatIfResponse,
  OdinQueryRequest, OdinQueryResponse,
  TestConnectionRequest, TestConnectionResponse,
  RewardsResponse, StreakClaimResponse, DigitalTwinsResponse, CausalImpactsResponse,
  Persona, PersonaId
} from '@/types/api';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  getPersonas: () => apiFetch<Persona[]>('/api/health-score/personas'),
  getRecovery: (id: PersonaId) => apiFetch<RecoveryResponse>(`/api/odin/recovery/${id}`),
  getAnomalies: (id: PersonaId) => apiFetch<AnomaliesResponse>(`/api/odin/anomalies/${id}`),
  getWorkout: (id: PersonaId) => apiFetch<WorkoutResponse>(`/api/odin/adaptive-workout/${id}`),
  getAgp: (id: PersonaId) => apiFetch<AgpResponse>(`/api/graph/agp/${id}`),
  getHypnogram: (id: PersonaId) => apiFetch<HypnogramResponse>(`/api/graph/hypnogram/${id}`),
  getCorrelation: (id: PersonaId, days = 14) => apiFetch<CorrelationResponse>(`/api/graph/correlation/${id}?days=${days}`),
  getBioAge: (id: PersonaId) => apiFetch<BioAgeResponse>(`/api/health-score/bio-age/${id}`),
  getRewards: (id: PersonaId, streak: number) => apiFetch<RewardsResponse>(`/api/rewards/${id}?streak_days=${streak}`),
  getDigitalTwins: (id: PersonaId) => apiFetch<DigitalTwinsResponse>(`/api/graph/digital-twins/${id}`),
  getCausalImpacts: (id: PersonaId) => apiFetch<CausalImpactsResponse>(`/api/graph/behavioral-impacts/${id}`),
  whatIf: (body: WhatIfInput) => apiFetch<WhatIfResponse>('/api/health-score/what-if', {
    method: 'POST', body: JSON.stringify(body),
  }),
  askOdin: (body: OdinQueryRequest) => apiFetch<OdinQueryResponse>('/api/odin/query', {
    method: 'POST', body: JSON.stringify(body),
  }),
  testConnection: (body: TestConnectionRequest) => apiFetch<TestConnectionResponse>('/api/odin/test-connection', {
    method: 'POST', body: JSON.stringify(body),
  }),
  claimStreak: (personaId: PersonaId, streak: number) => apiFetch<StreakClaimResponse>('/api/rewards/claim-streak', {
    method: 'POST',
    body: JSON.stringify({ persona_id: personaId, current_streak_days: streak }),
  }),
};

export function cn(...classes: (string | undefined | false | null)[]) {
  return classes.filter(Boolean).join(' ');
}
