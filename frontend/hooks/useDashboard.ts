'use client';
import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';
import type { PersonaId, RecoveryResponse, AnomaliesResponse, WorkoutResponse, BioAgeResponse, AgpResponse, HypnogramResponse, CorrelationResponse, Persona } from '@/types/api';

interface DashboardData {
  persona: Persona | null;
  recovery: RecoveryResponse | null;
  anomalies: AnomaliesResponse | null;
  workout: WorkoutResponse | null;
  bioAge: BioAgeResponse | null;
  agp: AgpResponse | null;
  hypnogram: HypnogramResponse | null;
  correlation: CorrelationResponse | null;
  loading: boolean;
  error: string | null;
}

export function useDashboard(personaId: PersonaId) {
  const [data, setData] = useState<DashboardData>({
    persona: null, recovery: null, anomalies: null, workout: null,
    bioAge: null, agp: null, hypnogram: null, correlation: null,
    loading: true, error: null,
  });

  const load = useCallback(async () => {
    setData(d => ({ ...d, loading: true, error: null }));
    try {
      const [personas, recovery, anomalies, workout, bioAge, agp, hypnogram, correlation] = await Promise.all([
        api.getPersonas(),
        api.getRecovery(personaId),
        api.getAnomalies(personaId),
        api.getWorkout(personaId),
        api.getBioAge(personaId),
        api.getAgp(personaId),
        api.getHypnogram(personaId),
        api.getCorrelation(personaId),
      ]);
      const persona = personas.find(p => p.id === personaId) ?? personas[0];
      setData({ persona, recovery, anomalies, workout, bioAge, agp, hypnogram, correlation, loading: false, error: null });
    } catch (err) {
      setData(d => ({ ...d, loading: false, error: String(err) }));
    }
  }, [personaId]);

  useEffect(() => { load(); }, [load]);

  return { ...data, refresh: load };
}
