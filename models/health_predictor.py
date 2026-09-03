"""
Longitudinal Health Trajectory & Biological Age Predictor.
Powers 10-Year Health Forecasting and Counterfactual "What-If" Simulations
as envisioned by Terra for Extreme Personalization and Longevity.
"""

from typing import Dict, Any, List, Optional
import math
from data.terra_schemas import UnifiedHealthProfile
from config import PERSONAS


class HealthPredictor:
    """Predictive health forecasting and biological age modeling."""

    def compute_biological_age(self, profile: UnifiedHealthProfile) -> Dict[str, Any]:
        """
        Calculate phenotypic biological age based on multi-system wearable biomarkers:
        1. Cardiorespiratory fitness (VO2 max) - primary all-cause mortality marker
        2. Autonomic tone (HRV rMSSD & Resting HR)
        3. Sleep architecture (Deep sleep % and Sleep efficiency)
        4. Glycemic stability (Time-in-Range)
        """
        cfg = PERSONAS.get(profile.persona_id, PERSONAS["alex_longevity"])
        chrono_age = float(cfg["baseline"]["chronological_age"])

        # 1. VO2 Max modifier (Every 3.5 ml/kg/min above age norm ~ -1.5 years bio-age)
        vo2 = profile.daily.estimated_vo2_max or cfg["baseline"]["vo2_max"]
        # Expected normative VO2 max for 40yo ~ 38 mL/kg/min
        vo2_norm = 45.0 - (chrono_age - 30.0) * 0.35
        vo2_delta = vo2 - vo2_norm
        vo2_age_mod = -1.2 * (vo2_delta / 3.5)

        # 2. HRV (rMSSD) modifier
        hrv = profile.sleep.avg_hrv_rmssd_ms
        # Normal HRV at age 40 ~ 45 ms
        hrv_norm = 60.0 - (chrono_age - 25.0) * 0.5
        hrv_delta = hrv - hrv_norm
        hrv_age_mod = -0.8 * (hrv_delta / 10.0)

        # 3. Resting HR modifier
        rhr = profile.daily.resting_heart_rate_bpm
        rhr_age_mod = 0.5 * ((rhr - 60.0) / 5.0)

        # 4. Sleep Efficiency modifier
        eff = profile.sleep.sleep_efficiency_pct
        sleep_age_mod = -0.5 * ((eff - 85.0) / 5.0)

        # 5. Glucose Time-in-Range modifier
        cgm = profile.body.cgm_readings_24h or []
        if cgm:
            in_range = len([g for g in cgm if 70.0 <= g.glucose_mg_dl <= 140.0])
            tir = (in_range / len(cgm)) * 100.0
        else:
            tir = cfg["baseline"]["time_in_range_pct"]
        glucose_age_mod = -1.0 * ((tir - 80.0) / 10.0)

        # Total biological age delta
        total_delta = vo2_age_mod + hrv_age_mod + rhr_age_mod + sleep_age_mod + glucose_age_mod
        # Bound delta reasonably within [-12, +15] years
        total_delta = max(-12.0, min(15.0, total_delta))
        biological_age = round(chrono_age + total_delta, 1)

        # Rate of biological aging (years aged per calendar year)
        rate_of_aging = round(1.0 + (total_delta / max(1.0, chrono_age)), 2)

        return {
            "chronological_age": chrono_age,
            "biological_age": biological_age,
            "biological_age_delta_years": round(total_delta, 1),
            "rate_of_aging": rate_of_aging,
            "aging_speed_category": "Decelerated" if total_delta < -1.0 else ("Accelerated" if total_delta > 1.0 else "Normal"),
            "biomarker_contributions": {
                "vo2_max_years_impact": round(vo2_age_mod, 1),
                "hrv_autonomic_impact": round(hrv_age_mod, 1),
                "resting_hr_impact": round(rhr_age_mod, 1),
                "sleep_quality_impact": round(sleep_age_mod, 1),
                "glucose_stability_impact": round(glucose_age_mod, 1)
            }
        }

    def forecast_trajectory(self, profile: UnifiedHealthProfile) -> Dict[str, Any]:
        """
        Forecast 3-month, 6-month, 1-year, and 5-year trajectories for Health Score,
        assuming status quo lifestyle vs optimized trajectory.
        """
        bio_age_res = self.compute_biological_age(profile)
        rate = bio_age_res["rate_of_aging"]
        chrono_age = bio_age_res["chronological_age"]
        current_bio_age = bio_age_res["biological_age"]

        # Health score baseline (0-100)
        base_score = max(20.0, min(98.0, 100.0 - (bio_age_res["biological_age_delta_years"] * 2.5)))

        horizons = [
            {"months": 3, "label": "3 Months"},
            {"months": 6, "label": "6 Months"},
            {"months": 12, "label": "1 Year"},
            {"months": 60, "label": "5 Years"},
        ]

        trajectory_points = []
        for h in horizons:
            t_years = h["months"] / 12.0
            
            # Status quo: continue at current aging rate
            projected_bio_age_status_quo = round(current_bio_age + (rate * t_years), 1)
            score_status_quo = round(max(10.0, min(100.0, base_score - (rate - 1.0) * t_years * 5.0)), 1)
            
            # Optimized: with full Terra AI guided interventions (rate drops to 0.82)
            projected_bio_age_optimized = round(current_bio_age + (0.82 * t_years), 1)
            score_optimized = round(min(99.0, base_score + (t_years * 2.2)), 1)

            trajectory_points.append({
                "timeframe": h["label"],
                "months": h["months"],
                "status_quo": {
                    "health_score": score_status_quo,
                    "projected_biological_age": projected_bio_age_status_quo
                },
                "optimized_terra": {
                    "health_score": score_optimized,
                    "projected_biological_age": projected_bio_age_optimized
                }
            })

        return {
            "current_health_score": round(base_score, 1),
            "biological_age": current_bio_age,
            "chronological_age": chrono_age,
            "rate_of_aging": rate,
            "trajectory_forecast": trajectory_points,
            "10_year_outlook": (
                f"Under status-quo telemetry, biological age will reach {current_bio_age + (rate * 10):.1f} in 10 years. "
                f"With OdinAI-guided autonomic recovery and Zone 2 optimization, biological age can be held to {current_bio_age + (0.80 * 10):.1f}."
            )
        }

    def simulate_what_if_counterfactual(
        self,
        profile: UnifiedHealthProfile,
        added_sleep_minutes: int = 30,
        added_zone2_minutes_weekly: int = 60,
        earlier_dinner_shift_hours: float = 2.0,
        improved_glucose_tir_pct: float = 8.0
    ) -> Dict[str, Any]:
        """
        Counterfactual "What-If" Lifestyle Intervention Simulator.
        Enables user to see real-time shifts in Biological Age and 1-Year Longevity Forecast.
        """
        base_calc = self.compute_biological_age(profile)
        curr_bio = base_calc["biological_age"]

        # Interventions calculate physiological shifts
        # 1. Added sleep -> increases HRV by ~4ms and deep sleep
        hrv_gain = (added_sleep_minutes / 30.0) * 4.2
        # 2. Added Zone 2 -> increases VO2 max over 6 months
        vo2_gain = (added_zone2_minutes_weekly / 60.0) * 1.4
        # 3. Earlier dinner -> improves nocturnal resting HR by ~2 bpm
        rhr_drop = min(4.0, (earlier_dinner_shift_hours / 2.0) * 2.2)
        # 4. Improved TIR
        tir_gain = improved_glucose_tir_pct

        # Shift biological age
        bio_age_reduction = (
            (vo2_gain / 3.5 * 1.2) +
            (hrv_gain / 10.0 * 0.8) +
            (rhr_drop / 5.0 * 0.5) +
            (tir_gain / 10.0 * 1.0)
        )
        bio_age_reduction = round(bio_age_reduction, 1)
        simulated_bio_age = round(curr_bio - bio_age_reduction, 1)
        new_delta = round(base_calc["chronological_age"] - simulated_bio_age, 1)

        return {
            "inputs": {
                "added_sleep_minutes": added_sleep_minutes,
                "added_zone2_minutes_weekly": added_zone2_minutes_weekly,
                "earlier_dinner_shift_hours": earlier_dinner_shift_hours,
                "improved_glucose_tir_pct": improved_glucose_tir_pct
            },
            "baseline": {
                "chronological_age": base_calc["chronological_age"],
                "biological_age": curr_bio
            },
            "simulated_outcome": {
                "projected_biological_age": simulated_bio_age,
                "net_biological_years_saved": bio_age_reduction,
                "new_biological_advantage_years": new_delta,
                "projected_hrv_improvement_ms": round(hrv_gain, 1),
                "projected_vo2_max_gain": round(vo2_gain, 1),
                "projected_rhr_reduction_bpm": round(rhr_drop, 1)
            },
            "clinical_verdict": (
                f"Implementing these 4 lifestyle shifts is projected to decelerate biological aging by {bio_age_reduction} years, "
                f"reducing 10-year all-cause mortality hazard ratio by an estimated {bio_age_reduction * 7.5:.0f}%."
            )
        }
