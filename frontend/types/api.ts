// Terra Intelligence Engine – TypeScript API Types

export type PersonaId = 'alex_longevity' | 'sarah_athlete' | 'marcus_metabolic' | 'elena_cognitive';
export type Provider = 'huggingface' | 'gemini' | 'openai';
export type TabId = 'overview' | 'odin' | 'graphs' | 'longevity' | 'habits';

export interface PersonaBaseline {
  chronological_age: number;
  biological_age: number;
  hrv_baseline: number;
  resting_hr: number;
}

export interface Persona {
  id: PersonaId;
  name: string;
  target_goal: string;
  objective: string;
  primary_sensors: string[];
  baseline: PersonaBaseline;
}

export interface BiometricBreakdown {
  current_hrv_rmssd: number;
  baseline_hrv_rmssd: number;
  hrv_z_score: number;
  resting_hr_bpm: number;
  rhr_delta_bpm: number;
  deep_sleep_pct: number;
  rem_sleep_pct: number;
  sleep_efficiency_pct: number;
}

export interface Citation {
  title: string;
  authors: string;
  journal: string;
  key_takeaway: string;
}

export interface RecoveryResponse {
  recovery_score: number;
  status: string;
  color: string;
  recommendation: string;
  biometric_breakdown: BiometricBreakdown;
  scientific_rationale: Citation;
}

export interface Anomaly {
  type: string;
  severity: 'high' | 'medium' | 'low';
  metric: string;
  detected_value: string;
  baseline_value: string;
  message: string;
  actionable_fix: string;
}

export interface AnomaliesResponse {
  persona_id: string;
  anomalies_count: number;
  anomalies: Anomaly[];
}

export interface WorkoutPlan {
  workout_title: string;
  category: string;
  duration_minutes: number;
  target_strain: number;
  main_set: string;
  rationale: string;
}

export interface WorkoutResponse {
  recovery_score_basis: number;
  prescribed_plan: WorkoutPlan;
  scientific_citations: Citation[];
}

export interface AgpMetrics {
  time_in_range_pct: number;
  mean_glucose_mg_dl: number;
  gmi_estimated_a1c: number;
  glycemic_variability_cv_pct: number;
}

export interface AgpTimeSeries {
  timestamps: string[];
  glucose_values: number[];
}

export interface AgpResponse {
  persona_id: string;
  agp_metrics: AgpMetrics;
  time_series: AgpTimeSeries;
}

export interface StageBreakdownMinutes {
  deep: number;
  rem: number;
  light: number;
  awake: number;
}

export interface HypnogramEntry {
  time: string;
  stage: string;
  stage_numeric: number;
}

export interface HypnogramResponse {
  persona_id: string;
  sleep_score: number;
  total_sleep_hours: number;
  stage_breakdown_minutes: StageBreakdownMinutes;
  hypnogram_series: HypnogramEntry[];
}

export interface CorrelationSeries {
  hrv_rmssd_ms: number[];
  sleep_hours: number[];
  workout_strain: number[];
}

export interface CorrelationResponse {
  persona_id: string;
  dates: string[];
  series: CorrelationSeries;
}

export interface BioAgeResponse {
  persona_id: string;
  chronological_age: number;
  biological_age: number;
  biological_age_delta_years: number;
  longevity_score: number;
  primary_drivers: string[];
}

export interface WhatIfInput {
  persona_id: PersonaId;
  added_sleep_minutes: number;
  added_zone2_minutes_weekly: number;
  earlier_dinner_shift_hours: number;
  improved_glucose_tir_pct: number;
}

export interface SimulatedOutcome {
  projected_biological_age: number;
  net_biological_years_saved: number;
  projected_hrv_improvement_ms: number;
  projected_vo2_max_gain: number;
  projected_rhr_reduction_bpm: number;
}

export interface WhatIfResponse {
  simulated_outcome: SimulatedOutcome;
  clinical_verdict: string;
}

export interface OdinQueryRequest {
  persona_id: PersonaId;
  query: string;
  api_key?: string;
  provider?: Provider;
}

export interface OdinQueryResponse {
  query: string;
  persona_id: string;
  odin_response: string;
  is_live_ai: boolean;
  provider: string;
  model_name?: string;
  llm_error?: string;
  recovery_synthesis: RecoveryResponse;
  active_anomalies: Anomaly[];
  recommended_workout: WorkoutPlan;
  scientific_citations: Citation[];
}

export interface TestConnectionRequest {
  api_key: string;
  provider: Provider;
}

export interface TestConnectionResponse {
  success: boolean;
  provider?: string;
  model?: string;
  latency_ms?: number;
  error?: string;
}

export interface RetentionAnalytics {
  retention_index_score: number;
  churn_risk_level: string;
  best_notification_window: string;
  recommended_nudge_strategy: string;
}

export interface RewardsResponse {
  streak_days: number;
  streak_multiplier: number;
  daily_points_earned: number;
  achieved_habits_count: number;
  retention_analytics: RetentionAnalytics;
}

export interface DigitalTwin {
  name: string;
  target_goal: string;
  similarity_score_pct: number;
  shared_traits: string[];
}

export interface DigitalTwinsResponse {
  persona_id: string;
  digital_twins: DigitalTwin[];
}

export interface CausalImpact {
  behavior: string;
  direction: 'positive' | 'negative';
  net_impact_score: number;
  affected_biomarker: string;
  target_outcome: string;
  physiological_mechanism: string;
}

export interface CausalImpactsResponse {
  persona_id: string;
  logged_behaviors: string[];
  causal_impacts: CausalImpact[];
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'odin';
  content: string;
  isLiveAi?: boolean;
  modelName?: string;
  provider?: string;
  llmError?: string;
  citations?: Citation[];
  timestamp: Date;
}
