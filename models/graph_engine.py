"""
Terra Graph API & Knowledge Engine.
1. Formats visual chart data compliant with Terra's Graph API (AGP, Hypnogram, Multi-metric overlay).
2. NetworkX-powered Biometric Causal Graph for behavioral impact discovery and Digital Twin cohort matching.
"""

from typing import Dict, Any, List, Optional
import networkx as nx
import numpy as np
from data.terra_schemas import UnifiedHealthProfile
from data.mock_generator import generate_longitudinal_series
from config import PERSONAS


class TerraGraphEngine:
    """Combines Terra visual chart specs with causal network graph analytics."""

    def __init__(self):
        self.knowledge_graph = self._build_health_knowledge_graph()

    def _build_health_knowledge_graph(self) -> nx.DiGraph:
        """
        Build a directed weighted causal health graph connecting
        Behaviors -> Biomarkers -> Health Goals.
        Edge weights represent normalized impact coefficients (-1.0 to +1.0).
        """
        G = nx.DiGraph()

        # Behavior Nodes
        behaviors = [
            ("late_dinner", {"type": "behavior", "label": "Late Dinner (<2h to bed)"}),
            ("sauna_session", {"type": "behavior", "label": "Sauna (20m @ 80°C)"}),
            ("zone2_cardio", {"type": "behavior", "label": "Zone 2 Cardio (45m)"}),
            ("caffeine_late", {"type": "behavior", "label": "Caffeine After 2 PM"}),
            ("breathwork", {"type": "behavior", "label": "Box Breathing (10m)"}),
            ("tart_cherry", {"type": "behavior", "label": "Tart Cherry Extract"}),
            ("post_meal_walk", {"type": "behavior", "label": "Post-Meal Walk (15m)"}),
        ]
        for node_id, attrs in behaviors:
            G.add_node(node_id, **attrs)

        # Biomarker Nodes
        biomarkers = [
            ("deep_sleep", {"type": "biomarker", "label": "Deep Sleep Duration"}),
            ("hrv_rmssd", {"type": "biomarker", "label": "HRV (rMSSD)"}),
            ("resting_hr", {"type": "biomarker", "label": "Resting Heart Rate"}),
            ("glucose_variability", {"type": "biomarker", "label": "Glycemic Variability (TIR)"}),
            ("vo2_max", {"type": "biomarker", "label": "Cardiorespiratory VO2 Max"}),
        ]
        for node_id, attrs in biomarkers:
            G.add_node(node_id, **attrs)

        # Health Outcome Nodes
        outcomes = [
            ("longevity_120", {"type": "outcome", "label": "Longevity & Biological Age Deceleration"}),
            ("peak_athletic", {"type": "outcome", "label": "Peak Athletic Output & Recovery"}),
            ("metabolic_health", {"type": "outcome", "label": "Insulin Sensitivity & Disease Reversal"}),
            ("cognitive_acuity", {"type": "outcome", "label": "Executive Mental Acuity & Stress Resilience"}),
        ]
        for node_id, attrs in outcomes:
            G.add_node(node_id, **attrs)

        # Behavioral Edges -> Biomarkers (weight, mechanism)
        G.add_edge("late_dinner", "deep_sleep", weight=-0.42, mechanism="Elevated nocturnal core body temperature impairs slow-wave delta sleep.")
        G.add_edge("late_dinner", "resting_hr", weight=0.35, mechanism="Ongoing digestion requires elevated cardiac output during sleep.")
        G.add_edge("sauna_session", "hrv_rmssd", weight=0.38, mechanism="Heat shock proteins and subsequent parasympathetic rebound.")
        G.add_edge("sauna_session", "resting_hr", weight=-0.25, mechanism="Improves endothelial compliance and arterial elasticity.")
        G.add_edge("zone2_cardio", "vo2_max", weight=0.65, mechanism="Increases left ventricular stroke volume and capillary bed density.")
        G.add_edge("zone2_cardio", "glucose_variability", weight=0.45, mechanism="Enhances mitochondrial fat oxidation and muscle insulin sensitivity.")
        G.add_edge("caffeine_late", "deep_sleep", weight=-0.50, mechanism="Adenosine A1/A2A receptor antagonism blocks sleep pressure.")
        G.add_edge("breathwork", "hrv_rmssd", weight=0.40, mechanism="Stimulates vagal nerve efferent activity and baroreceptor sensitivity.")
        G.add_edge("tart_cherry", "deep_sleep", weight=0.28, mechanism="Natural exogenous melatonin and phytochemical anti-inflammatory effect.")
        G.add_edge("post_meal_walk", "glucose_variability", weight=0.60, mechanism="GLUT-4 receptor translocation facilitates direct muscular glucose uptake.")

        # Biomarker Edges -> Outcomes
        G.add_edge("deep_sleep", "longevity_120", weight=0.55, mechanism="Glymphatic clearance of beta-amyloid and nocturnal growth hormone release.")
        G.add_edge("deep_sleep", "cognitive_acuity", weight=0.60, mechanism="Synaptic pruning and consolidation of working memory.")
        G.add_edge("hrv_rmssd", "peak_athletic", weight=0.65, mechanism="Autonomic capacity for explosive neuromuscular strain.")
        G.add_edge("hrv_rmssd", "longevity_120", weight=0.50, mechanism="Strong all-cause mortality protective biomarker.")
        G.add_edge("glucose_variability", "metabolic_health", weight=0.75, mechanism="Minimizes advanced glycation end-products (AGEs) and beta-cell exhaustion.")
        G.add_edge("vo2_max", "longevity_120", weight=0.80, mechanism="Highest correlated single metric for 10-year survival hazard ratio.")
        G.add_edge("vo2_max", "peak_athletic", weight=0.85, mechanism="Rate-limiting ceiling for aerobic ATP generation.")

        return G

    # ------------ Terra Visual Graph API Formats ------------

    def get_agp_graph_data(self, profile: UnifiedHealthProfile) -> Dict[str, Any]:
        """
        Generates Ambulatory Glucose Profile (AGP) compliant with Terra Graph API standard.
        Produces continuous glucose trajectory, Time-in-Range (TIR) metrics, and target bands.
        """
        cgm = profile.body.cgm_readings_24h or []
        timestamps = [g.timestamp.split("T")[1][:5] for g in cgm]
        values = [g.glucose_mg_dl for g in cgm]

        if not values:
            values = [90.0] * 144
            timestamps = [f"{h:02d}:{m:02d}" for h in range(24) for m in (0, 10, 20, 30, 40, 50)]

        # Calculate clinical AGP summary metrics
        total = len(values)
        very_low = round((len([v for v in values if v < 54.0]) / total) * 100.0, 1)
        low = round((len([v for v in values if 54.0 <= v < 70.0]) / total) * 100.0, 1)
        in_range = round((len([v for v in values if 70.0 <= v <= 140.0]) / total) * 100.0, 1)
        high = round((len([v for v in values if 140.0 < v <= 180.0]) / total) * 100.0, 1)
        very_high = round((len([v for v in values if v > 180.0]) / total) * 100.0, 1)

        mean_val = float(np.mean(values))
        std_val = float(np.std(values))
        cv = round((std_val / mean_val) * 100.0, 1) if mean_val > 0 else 0.0

        return {
            "chart_type": "ambulatory_glucose_profile",
            "title": f"Ambulatory Glucose Profile (AGP) - {profile.persona_id}",
            "units": "mg/dL",
            "target_range": {"min": 70, "max": 140},
            "time_series": {
                "timestamps": timestamps,
                "glucose_values": values
            },
            "agp_metrics": {
                "time_in_range_pct": in_range,
                "time_above_range_pct": round(high + very_high, 1),
                "time_below_range_pct": round(low + very_low, 1),
                "mean_glucose_mg_dl": round(mean_val, 1),
                "glycemic_variability_cv_pct": cv,
                "gmi_estimated_a1c": round((mean_val + 46.7) / 28.7, 1)
            }
        }

    def get_sleep_hypnogram(self, profile: UnifiedHealthProfile) -> Dict[str, Any]:
        """
        Generates Sleep Hypnogram stage breakdown for Terra Graph API visualizer.
        """
        stages = profile.sleep.stages
        total = max(1, profile.sleep.duration_total_seconds)
        
        deep_min = stages.deep_sleep_seconds // 60
        rem_min = stages.rem_sleep_seconds // 60
        light_min = stages.light_sleep_seconds // 60
        awake_min = stages.awake_seconds // 60

        return {
            "chart_type": "sleep_hypnogram",
            "title": "Sleep Architecture & Hypnogram",
            "sleep_score": profile.sleep.sleep_score,
            "efficiency_pct": profile.sleep.sleep_efficiency_pct,
            "total_sleep_hours": round(profile.sleep.duration_asleep_seconds / 3600.0, 2),
            "stage_breakdown_minutes": {
                "deep": deep_min,
                "rem": rem_min,
                "light": light_min,
                "awake": awake_min
            },
            "stage_percentages": {
                "deep": round((stages.deep_sleep_seconds / total) * 100.0, 1),
                "rem": round((stages.rem_sleep_seconds / total) * 100.0, 1),
                "light": round((stages.light_sleep_seconds / total) * 100.0, 1),
                "awake": round((stages.awake_seconds / total) * 100.0, 1)
            },
            "overnight_hrv_rmssd": profile.sleep.avg_hrv_rmssd_ms,
            "lowest_heart_rate": profile.sleep.lowest_heart_rate_bpm
        }

    def get_longitudinal_correlation_series(self, persona_id: str, days: int = 14) -> Dict[str, Any]:
        """
        Generates 14-day overlay of Daily Strain vs Sleep Duration vs Overnight HRV.
        Demonstrates Terra Graph API multi-metric correlation capabilities.
        """
        history = generate_longitudinal_series(persona_id, days)
        dates = [p.date for p in history]
        hrvs = [p.sleep.avg_hrv_rmssd_ms for p in history]
        sleep_hours = [round(p.sleep.duration_asleep_seconds / 3600.0, 2) for p in history]
        strains = [p.activities[0].strain_score if p.activities else 5.0 for p in history]

        return {
            "chart_type": "multi_metric_correlation",
            "title": "14-Day Longitudinal Biomarker Coupling",
            "dates": dates,
            "series": {
                "hrv_rmssd_ms": hrvs,
                "sleep_hours": sleep_hours,
                "workout_strain": strains
            }
        }

    # ------------ Causal Knowledge Graph Traversal & Twins ------------

    def get_knowledge_graph_summary(self) -> Dict[str, Any]:
        """Export serialized nodes and edges for UI visualization."""
        nodes = []
        for n, d in self.knowledge_graph.nodes(data=True):
            nodes.append({"id": n, "label": d.get("label", n), "type": d.get("type", "node")})

        edges = []
        for u, v, d in self.knowledge_graph.edges(data=True):
            edges.append({
                "source": u,
                "target": v,
                "weight": d.get("weight", 0.0),
                "mechanism": d.get("mechanism", "")
            })

        return {"nodes": nodes, "edges": edges}

    def analyze_behavioral_impacts(self, profile: UnifiedHealthProfile) -> List[Dict[str, Any]]:
        """
        Given the persona's recent logged behaviors, trace downstream causal impacts
        on biomarkers and health goals via graph paths.
        """
        impacts = []
        for b in profile.recent_behaviors:
            behavior_key = b["behavior"]
            # Map simplified behavior strings to graph nodes
            node_candidates = [n for n in self.knowledge_graph.nodes if n in behavior_key or behavior_key in n]
            if not node_candidates:
                continue
            b_node = node_candidates[0]

            out_edges = self.knowledge_graph.out_edges(b_node, data=True)
            for _, biomarker, data in out_edges:
                # Find outcome that this biomarker feeds into
                downstream = self.knowledge_graph.out_edges(biomarker, data=True)
                for _, outcome, out_data in downstream:
                    compound_effect = round(data["weight"] * out_data["weight"], 2)
                    impacts.append({
                        "behavior": self.knowledge_graph.nodes[b_node]["label"],
                        "affected_biomarker": self.knowledge_graph.nodes[biomarker]["label"],
                        "target_outcome": self.knowledge_graph.nodes[outcome]["label"],
                        "direction": "positive" if compound_effect > 0 else "negative",
                        "net_impact_score": compound_effect,
                        "physiological_mechanism": data["mechanism"]
                    })
        return impacts

    def find_digital_twins(self, profile: UnifiedHealthProfile) -> List[Dict[str, Any]]:
        """
        Compute Digital Twin cohort similarity using cosine distance across
        standardized biometric feature vectors (HRV, Sleep, VO2, Resting HR, Glucose TIR).
        """
        # Current user vector
        cgm = profile.body.cgm_readings_24h or []
        in_range = len([g for g in cgm if 70.0 <= g.glucose_mg_dl <= 140.0])
        tir = (in_range / max(1, len(cgm))) * 100.0 if cgm else 85.0

        user_vec = np.array([
            profile.sleep.avg_hrv_rmssd_ms / 100.0,
            (profile.sleep.duration_asleep_seconds / 3600.0) / 10.0,
            (profile.daily.estimated_vo2_max or 45.0) / 70.0,
            profile.daily.resting_heart_rate_bpm / 100.0,
            tir / 100.0
        ])

        twins = []
        for p_id, p_data in PERSONAS.items():
            if p_id == profile.persona_id:
                continue
            b = p_data["baseline"]
            twin_vec = np.array([
                b["hrv_baseline"] / 100.0,
                b["avg_sleep_hours"] / 10.0,
                b["vo2_max"] / 70.0,
                b["resting_hr"] / 100.0,
                b["time_in_range_pct"] / 100.0
            ])

            # Cosine similarity
            cosine_sim = np.dot(user_vec, twin_vec) / (np.linalg.norm(user_vec) * np.linalg.norm(twin_vec))
            sim_pct = round(float(cosine_sim) * 100.0, 1)

            twins.append({
                "twin_persona_id": p_id,
                "name": p_data["name"],
                "target_goal": p_data["target_goal"],
                "similarity_score_pct": sim_pct,
                "shared_traits": [
                    f"Baseline HRV: {b['hrv_baseline']} ms",
                    f"VO2 Max: {b['vo2_max']} mL/kg/min",
                    f"Sleep Duration: {b['avg_sleep_hours']} hrs"
                ]
            })

        twins.sort(key=lambda x: x["similarity_score_pct"], reverse=True)
        return twins
