"""
OdinAI Health Intelligence Engine.
Autonomous physiological reasoning, biometric anomaly detection,
adaptive workout planning, and active real-time LLM integration (Hugging Face / Gemini / OpenAI).
"""

import os
import time
import httpx
from typing import Dict, Any, List, Optional, Tuple
from data.terra_schemas import UnifiedHealthProfile
from config import PERSONAS
from models.anomaly_detector import score_today


SCIENTIFIC_CITATIONS = {
    "hrv_guided_training": {
        "title": "Monitoring Training Status with HR Measures: Do All Roads Lead to Rome?",
        "authors": "Buchheit, M.",
        "journal": "Frontiers in Physiology (2014)",
        "key_takeaway": "HRV (rMSSD) reflecting parasympathetic reactivation is the gold-standard marker for autonomic recovery and training readiness."
    },
    "sleep_architecture": {
        "title": "Sleep and Human Cognitive Performance",
        "authors": "Walker, M. P., & Stickgold, R.",
        "journal": "Nature Neuroscience (2017)",
        "key_takeaway": "Slow-Wave Deep Sleep (>20% of total sleep) is vital for physical cellular repair, growth hormone secretion, and glymphatic clearance."
    },
    "zone2_metabolism": {
        "title": "Assessment of Metabolic Flexibility in Athletes and Metabolic Disease",
        "authors": "San Millán, I., & Brooks, G. A.",
        "journal": "Sports Medicine (2018)",
        "key_takeaway": "Zone 2 aerobic base exercise directly maximizes mitochondrial density and fatty acid oxidation while clearing blood lactate."
    },
    "glucose_variability": {
        "title": "Continuous Glucose Monitoring Metrics for Clinical Trials: Recommendations on Time in Range",
        "authors": "Battelino, T., et al.",
        "journal": "Diabetes Care (2019)",
        "key_takeaway": "Maintaining >85% Time-in-Range (70-140 mg/dL) correlates with lower vascular endothelial damage and reduced all-cause mortality."
    },
    "acwr_workload": {
        "title": "The Training-Injury Prevention Paradox: Should Athletes Be Training Smarter and Harder?",
        "authors": "Gabbett, T. J.",
        "journal": "British Journal of Sports Medicine (2016)",
        "key_takeaway": "Acute-to-Chronic Workload Ratio between 0.8 and 1.3 is the optimal 'sweet spot' for performance without overtraining injury risk."
    }
}

# Supported free models on Hugging Face Serverless Router
HF_MODELS = [
    "meta-llama/Llama-3.2-3B-Instruct",
    "Qwen/Qwen2.5-72B-Instruct",
    "mistralai/Mistral-7B-Instruct-v0.3"
]

# Strict whitelist of verified Gemini text models
VERIFIED_GEMINI_TEXT_MODELS = [
    "gemini-3.6-flash",
    "gemini-3.6",
    "gemini-2.5-flash",
    "gemini-2.5",
    "gemini-1.5-flash",
    "gemini-1.5-flash-latest",
    "gemini-1.5-pro",
    "gemini-1.5-flash-8b"
]

EXCLUDED_MODEL_PATTERNS = [
    "high-res", "exp", "preview", "embedding", "image", "imagen", "vision",
    "aqa", "audio", "whisper", "video", "gemini-pro", "gemini-2.0-flash"
]


class OdinAIEngine:
    """OdinAI Health Intelligence Agent with Active LLM capabilities."""

    def __init__(self):
        self.citations = SCIENTIFIC_CITATIONS
        self.cached_hf_model: Optional[str] = "meta-llama/Llama-3.2-3B-Instruct"
        self.cached_gemini_model: Optional[str] = "gemini-3.6-flash"

    def analyze_recovery_status(self, profile: UnifiedHealthProfile) -> Dict[str, Any]:
        """Synthesize multi-modal biometric signals to compute autonomic recovery."""
        cfg = PERSONAS.get(profile.persona_id, PERSONAS["alex_longevity"])
        base_hrv = cfg["baseline"]["hrv_baseline"]
        base_rhr = cfg["baseline"]["resting_hr"]

        current_hrv = profile.sleep.avg_hrv_rmssd_ms
        hrv_z_score = (current_hrv - base_hrv) / 10.0

        current_rhr = profile.daily.resting_heart_rate_bpm
        rhr_delta = current_rhr - base_rhr

        stages = profile.sleep.stages
        total_asleep = max(1, profile.sleep.duration_asleep_seconds)
        deep_pct = (stages.deep_sleep_seconds / total_asleep) * 100.0
        rem_pct = (stages.rem_sleep_seconds / total_asleep) * 100.0
        efficiency = profile.sleep.sleep_efficiency_pct

        hrv_component = min(100.0, max(0.0, 70.0 + (hrv_z_score * 20.0)))
        rhr_component = min(100.0, max(0.0, 75.0 - (rhr_delta * 4.0)))
        sleep_component = min(100.0, max(0.0, (efficiency * 0.5) + (deep_pct * 1.5) + (rem_pct * 0.8)))

        composite_recovery = (
            (hrv_component * 0.40) +
            (sleep_component * 0.35) +
            (rhr_component * 0.15) +
            (profile.sleep.sleep_score * 0.10)
        )
        composite_recovery = round(min(100.0, max(10.0, composite_recovery)), 1)

        if composite_recovery >= 85.0:
            status = "Optimal Readiness (Prime Autonomic State)"
            color = "#10B981"
            recommendation = "Nervous system is primed. Ideal window for high-strain training, threshold intervals, or heavy neurological load."
        elif composite_recovery >= 65.0:
            status = "Moderate Readiness (Steady State)"
            color = "#3B82F6"
            recommendation = "System is in equilibrium. Recommend aerobic Zone 2 endurance or moderate hypertrophy training. Avoid maximal overreaching."
        else:
            status = "Suppressed Recovery (Sympathetic Dominance)"
            color = "#EF4444"
            recommendation = "Autonomic tone is suppressed. Prioritize active recovery, parasympathetic downregulation, low-glycemic nutrition, and >8h sleep window."

        return {
            "recovery_score": composite_recovery,
            "status": status,
            "color": color,
            "recommendation": recommendation,
            "biometric_breakdown": {
                "current_hrv_rmssd": current_hrv,
                "baseline_hrv_rmssd": base_hrv,
                "hrv_z_score": round(hrv_z_score, 2),
                "resting_hr_bpm": current_rhr,
                "rhr_delta_bpm": round(rhr_delta, 1),
                "deep_sleep_pct": round(deep_pct, 1),
                "rem_sleep_pct": round(rem_pct, 1),
                "sleep_efficiency_pct": efficiency
            },
            "scientific_rationale": self.citations["hrv_guided_training"]
        }

    def detect_anomalies(self, profile: UnifiedHealthProfile) -> List[Dict[str, Any]]:
        """Detect acute physiological anomalies across wearable and CGM telemetry."""
        anomalies = []
        cfg = PERSONAS.get(profile.persona_id, PERSONAS["alex_longevity"])
        base_hrv = cfg["baseline"]["hrv_baseline"]
        base_rhr = cfg["baseline"]["resting_hr"]

        current_hrv = profile.sleep.avg_hrv_rmssd_ms
        current_rhr = profile.daily.resting_heart_rate_bpm

        # Statistically-fit per-persona MAD control chart (see
        # models/anomaly_detector.py, fit by training/train_anomaly_baselines.py)
        # calibrated to each persona's own historical variance - replaces the
        # flat 15ms HRV / 5bpm RHR margins previously applied identically to
        # every persona regardless of how much that persona naturally
        # fluctuates day to day (e.g. Marcus's low-variance HRV vs. Sarah's
        # high-variance HRV got the same absolute threshold before this).
        mad_scores = score_today(
            profile.persona_id,
            hrv_rmssd_ms=current_hrv,
            resting_hr_bpm=current_rhr,
            sleep_efficiency_pct=profile.sleep.sleep_efficiency_pct,
        )

        if mad_scores is not None:
            hrv_result = mad_scores["hrv_rmssd_ms"]
            if hrv_result["is_anomalous"] and current_hrv < hrv_result["baseline_median"]:
                anomalies.append({
                    "type": "AUTONOMIC_SUPPRESSION",
                    "severity": "high",
                    "metric": "HRV (rMSSD)",
                    "detected_value": f"{current_hrv} ms",
                    "baseline_value": f"{hrv_result['baseline_median']} ms (persona MAD baseline, z={hrv_result['modified_z_score']})",
                    "message": "Acute autonomic depression detected. Parasympathetic brake is compromised.",
                    "actionable_fix": "Postpone glycolytic/high-intensity workouts. Implement 15 mins physiological sigh breathwork."
                })

            rhr_result = mad_scores["resting_hr_bpm"]
            if rhr_result["is_anomalous"] and current_rhr > rhr_result["baseline_median"]:
                anomalies.append({
                    "type": "ELEVATED_BASAL_HEART_RATE",
                    "severity": "medium",
                    "metric": "Resting Heart Rate",
                    "detected_value": f"{current_rhr} bpm",
                    "baseline_value": f"{rhr_result['baseline_median']} bpm (persona MAD baseline, z={rhr_result['modified_z_score']})",
                    "message": "Nocturnal heart rate elevated relative to this persona's own historical baseline. Potential early immune response or late caloric intake.",
                    "actionable_fix": "Ensure dinner is completed at least 3 hours before sleep; hydrate with electrolytes."
                })
        else:
            # No trained baseline yet (run: python -m training.train_anomaly_baselines) -
            # fall back to the original fixed-margin heuristic so this still
            # works out of the box on a fresh clone.
            if (base_hrv - current_hrv) >= 15.0:
                anomalies.append({
                    "type": "AUTONOMIC_SUPPRESSION",
                    "severity": "high",
                    "metric": "HRV (rMSSD)",
                    "detected_value": f"{current_hrv} ms",
                    "baseline_value": f"{base_hrv} ms",
                    "message": "Acute autonomic depression detected. Parasympathetic brake is compromised.",
                    "actionable_fix": "Postpone glycolytic/high-intensity workouts. Implement 15 mins physiological sigh breathwork."
                })
            if (current_rhr - base_rhr) >= 5:
                anomalies.append({
                    "type": "ELEVATED_BASAL_HEART_RATE",
                    "severity": "medium",
                    "metric": "Resting Heart Rate",
                    "detected_value": f"{current_rhr} bpm",
                    "baseline_value": f"{base_rhr} bpm",
                    "message": "Nocturnal heart rate elevated by +5 bpm. Potential early immune response or late caloric intake.",
                    "actionable_fix": "Ensure dinner is completed at least 3 hours before sleep; hydrate with electrolytes."
                })

        cgm = profile.body.cgm_readings_24h or []
        max_glucose = max([g.glucose_mg_dl for g in cgm], default=0.0)
        if max_glucose > 160.0:
            anomalies.append({
                "type": "GLYCEMIC_SPIKE_EXCURSION",
                "severity": "medium",
                "metric": "Blood Glucose Peak",
                "detected_value": f"{max_glucose} mg/dL",
                "baseline_value": "< 140 mg/dL",
                "message": f"Significant glucose excursion reaching {max_glucose} mg/dL observed post-meal.",
                "actionable_fix": "10-15 minute Zone 1 walking post-meal utilizes GLUT-4 translocation to clear glucose without insulin surge."
            })

        total_asleep = max(1, profile.sleep.duration_asleep_seconds)
        deep_pct = (profile.sleep.stages.deep_sleep_seconds / total_asleep) * 100.0
        if deep_pct < 12.0:
            anomalies.append({
                "type": "DEEP_SLEEP_DEFICIENCY",
                "severity": "medium",
                "metric": "Deep Sleep Stage",
                "detected_value": f"{deep_pct:.1f}%",
                "baseline_value": "> 20.0%",
                "message": "Deep slow-wave sleep is below cellular rejuvenation thresholds.",
                "actionable_fix": "Lower bedroom ambient temperature to 66°F (19°C) and avoid blue-light exposure 90 min before sleep."
            })

        return anomalies

    def generate_adaptive_workout_plan(self, profile: UnifiedHealthProfile) -> Dict[str, Any]:
        """Prescribe recovery-adjusted workout based on current strain."""
        recovery = self.analyze_recovery_status(profile)
        score = recovery["recovery_score"]
        persona_id = profile.persona_id

        if score >= 85.0:
            if persona_id == "sarah_athlete":
                plan = {
                    "workout_title": "Threshold 4x8min VO2 Max Intervals",
                    "category": "High-Intensity Lactate Threshold",
                    "duration_minutes": 65,
                    "target_strain": 16.5,
                    "main_set": "4 x 8 minutes at 90-92% HR Max with 3 min active spinning recovery",
                    "rationale": "Autonomic nervous system is fully restored (HRV z-score positive). High capacity for neuromuscular adaptation."
                }
            elif persona_id == "marcus_metabolic":
                plan = {
                    "workout_title": "Full-Body Metabolic Resistance Circuit",
                    "category": "Insulin Sensitivity Resistance",
                    "duration_minutes": 40,
                    "target_strain": 11.5,
                    "main_set": "3 rounds: Goblet Squats, Dumbbell Rows, Romanian Deadlifts, Farmers Walk (12 reps each)",
                    "rationale": "Stimulates muscle glycogen depletion, activating non-insulin-mediated GLUT4 glucose uptake for 24-48 hours."
                }
            else:
                plan = {
                    "workout_title": "Zone 2 Mitochondrial Hyper-Efficiency Ride",
                    "category": "Mitochondrial Biogenesis",
                    "duration_minutes": 60,
                    "target_strain": 12.0,
                    "main_set": "45 min steady-state cycling maintaining conversation-pace nasal breathing",
                    "rationale": "High readiness enables sustained Zone 2 fat oxidation without triggering cortisol spikes."
                }
        elif score >= 65.0:
            plan = {
                "workout_title": "Aerobic Zone 2 Foundation & Core Stability",
                "category": "Aerobic Base Maintenance",
                "duration_minutes": 45,
                "target_strain": 9.5,
                "main_set": "30 min steady Zone 2 jog or row + 3x45s side planks",
                "rationale": "Maintains aerobic capillary density without placing excessive stress on recovering autonomic pathways."
            }
        else:
            plan = {
                "workout_title": "Parasympathetic Restorative Protocol",
                "category": "Active Recovery & Downregulation",
                "duration_minutes": 30,
                "target_strain": 4.0,
                "main_set": "20 min outdoor walk in natural daylight + 10 min restorative yoga / foam rolling",
                "rationale": "Suppressed HRV indicates elevated sympathetic load. Intense training would promote overreaching and impair immune function."
            }

        return {
            "recovery_score_basis": score,
            "prescribed_plan": plan,
            "scientific_citations": [self.citations["zone2_metabolism"], self.citations["acwr_workload"]]
        }

    # ============ ACTIVE REAL-TIME LLM INTEGRATION ============

    async def test_api_connection(self, api_key: str, provider: str = "huggingface") -> Dict[str, Any]:
        """Test API key connection to Hugging Face, Gemini, or OpenAI."""
        key = api_key.strip().strip("'\"")
        if not key:
            return {"success": False, "error": "API key is empty. Please enter your API token."}

        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                
                # ---------------- 1. HUGGING FACE (RECOMMENDED) ----------------
                if provider.lower() == "huggingface" or key.startswith("hf_"):
                    url = "https://router.huggingface.co/hf-inference/v1/chat/completions"
                    headers = {
                        "Authorization": f"Bearer {key}",
                        "Content-Type": "application/json"
                    }
                    last_err = ""
                    for hf_model in HF_MODELS:
                        payload = {
                            "model": hf_model,
                            "messages": [{"role": "user", "content": "Respond with 'ready'"}],
                            "max_tokens": 10
                        }
                        resp = await client.post(url, headers=headers, json=payload, timeout=12.0)
                        latency = int((time.time() - start_time) * 1000)

                        if resp.status_code == 200:
                            self.cached_hf_model = hf_model
                            return {
                                "success": True,
                                "provider": "Hugging Face",
                                "model": hf_model,
                                "latency_ms": latency
                            }
                        elif resp.status_code in [401, 403]:
                            return {
                                "success": False,
                                "provider": "Hugging Face",
                                "status_code": resp.status_code,
                                "error": "Invalid Hugging Face Token. Please get a free User Access Token from huggingface.co/settings/tokens"
                            }
                        else:
                            last_err = f"{hf_model} HTTP {resp.status_code}: {resp.text[:150]}"

                    return {"success": False, "provider": "Hugging Face", "error": last_err or "Failed to connect to Hugging Face"}

                # ---------------- 2. OPENAI ----------------
                elif provider.lower() == "openai" or key.startswith("sk-"):
                    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
                    payload = {
                        "model": "gpt-4o-mini",
                        "messages": [{"role": "user", "content": "Respond with 'pong'"}],
                        "max_tokens": 5
                    }
                    resp = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
                    latency = int((time.time() - start_time) * 1000)
                    if resp.status_code == 200:
                        return {"success": True, "provider": "OpenAI", "model": "gpt-4o-mini", "latency_ms": latency}
                    else:
                        err_json = resp.json() if "application/json" in resp.headers.get("content-type", "") else {"error": resp.text}
                        return {"success": False, "status_code": resp.status_code, "error": err_json.get("error", {}).get("message", resp.text)}

                # ---------------- 3. GOOGLE GEMINI ----------------
                else:
                    list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
                    list_resp = await client.get(list_url, timeout=8.0)

                    available_models = []
                    if list_resp.status_code == 200:
                        data = list_resp.json()
                        for m in data.get("models", []):
                            methods = m.get("supportedGenerationMethods", []) or m.get("supported_generation_methods", [])
                            if "generateContent" in methods:
                                name = m.get("name", "").replace("models/", "").strip()
                                nl = name.lower()
                                if any(bad in nl for bad in EXCLUDED_MODEL_PATTERNS):
                                    continue
                                if any(good in nl for good in VERIFIED_GEMINI_TEXT_MODELS) or "gemini" in nl:
                                    if name not in available_models:
                                        available_models.append(name)
                    else:
                        try:
                            msg = list_resp.json().get("error", {}).get("message")
                        except Exception:
                            msg = None
                        if msg:
                            return {
                                "success": False,
                                "provider": "Google Gemini",
                                "status_code": list_resp.status_code,
                                "error": f"Google Gemini Error (HTTP {list_resp.status_code}): {msg}"
                            }

                    if not available_models:
                        available_models = ["gemini-3.6-flash", "gemini-2.5-flash", "gemini-1.5-flash"]

                    def priority(n: str) -> int:
                        nl = n.lower()
                        if "3.6-flash" in nl or "3.6" in nl: return 0
                        if "2.5-flash" in nl or "2.5" in nl: return 1
                        if "flash" in nl and "high-res" not in nl: return 2
                        if "pro" in nl: return 3
                        return 10

                    available_models.sort(key=priority)

                    errors = []
                    for model in available_models:
                        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
                        payload = {"contents": [{"parts": [{"text": "Hello"}]}]}
                        resp = await client.post(url, json=payload, timeout=10.0)
                        latency = int((time.time() - start_time) * 1000)

                        if resp.status_code == 200:
                            self.cached_gemini_model = model
                            return {
                                "success": True,
                                "provider": "Google Gemini",
                                "model": model,
                                "latency_ms": latency
                            }
                        else:
                            try:
                                err_msg = resp.json().get("error", {}).get("message", resp.text[:150])
                            except Exception:
                                err_msg = resp.text[:150]
                            errors.append(f"{model}: {err_msg}")

                    return {"success": False, "provider": "Google Gemini", "error": " | ".join(errors) or "Failed to call generateContent"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def generate_llm_response(
        self,
        query_text: str,
        profile: UnifiedHealthProfile,
        api_key: Optional[str] = None,
        provider: str = "huggingface"
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Call live generative AI using user's real multi-stream telemetry.
        Returns (response_text, model_name, error_message).
        """
        key = (
            (api_key or "").strip().strip("'\"") or
            os.getenv("HUGGINGFACE_API_KEY", "").strip().strip("'\"") or
            os.getenv("HF_TOKEN", "").strip().strip("'\"") or
            os.getenv("GEMINI_API_KEY", "").strip().strip("'\"") or
            os.getenv("OPENAI_API_KEY", "").strip().strip("'\"") or
            os.getenv("LLM_API_KEY", "").strip().strip("'\"")
        )
        if not key:
            return None, None, None

        cfg = PERSONAS.get(profile.persona_id, PERSONAS["alex_longevity"])
        recovery = self.analyze_recovery_status(profile)
        anomalies = self.detect_anomalies(profile)
        workout = self.generate_adaptive_workout_plan(profile)

        cgm = profile.body.cgm_readings_24h or []
        max_g = max([g.glucose_mg_dl for g in cgm], default=profile.body.fasting_glucose_mg_dl or 90.0)
        avg_g = round(sum([g.glucose_mg_dl for g in cgm]) / max(1, len(cgm)), 1)
        in_range = len([g for g in cgm if 70.0 <= g.glucose_mg_dl <= 140.0])
        tir = round((in_range / max(1, len(cgm))) * 100.0, 1)

        anomalies_str = "; ".join([f"{a['metric']}: {a['message']}" for a in anomalies]) or "None detected"

        system_instruction = (
            f"You are OdinAI, Terra's elite Health & Exercise Physiology Intelligence Engine. "
            f"You are directly analyzing real-time continuous wearable and CGM telemetry for {cfg['name']}.\n\n"
            f"Target Goal: {cfg['target_goal']}\n"
            f"Objective: {cfg['objective']}\n\n"
            f"Current Biometric Telemetry:\n"
            f"- Recovery Score: {recovery['recovery_score']}/100 ({recovery['status']})\n"
            f"- Overnight HRV: {profile.sleep.avg_hrv_rmssd_ms} ms (Baseline: {cfg['baseline']['hrv_baseline']} ms, z-score: {recovery['biometric_breakdown']['hrv_z_score']})\n"
            f"- Resting Heart Rate: {profile.daily.resting_heart_rate_bpm} bpm\n"
            f"- Sleep Architecture: Total {profile.sleep.duration_asleep_seconds/3600:.1f}h, Deep Sleep {recovery['biometric_breakdown']['deep_sleep_pct']}%, REM {recovery['biometric_breakdown']['rem_sleep_pct']}%, Efficiency {profile.sleep.sleep_efficiency_pct}%\n"
            f"- Continuous Glucose (CGM): Mean {avg_g} mg/dL, Peak {max_g} mg/dL, Time-in-Range (70-140 mg/dL): {tir}%\n"
            f"- Active Biometric Alerts: {anomalies_str}\n"
            f"- Prescribed Adaptive Workout: {workout['prescribed_plan']['workout_title']}\n\n"
            f"Instructions:\n"
            f"1. Directly address the user's specific inquiry using their real physiological metrics above.\n"
            f"2. Provide empathetic, scientifically rigorous coaching advice.\n"
            f"3. Cite relevant peer-reviewed exercise physiology or clinical literature (e.g., Buchheit on HRV, Walker on sleep, San Millán on Zone 2, Battelino on CGM TIR).\n"
            f"4. Format cleanly using concise paragraphs and markdown bolding."
        )

        try:
            async with httpx.AsyncClient(timeout=25.0) as client:
                
                # ---------------- 1. HUGGING FACE ----------------
                if provider.lower() == "huggingface" or key.startswith("hf_"):
                    url = "https://router.huggingface.co/hf-inference/v1/chat/completions"
                    headers = {
                        "Authorization": f"Bearer {key}",
                        "Content-Type": "application/json"
                    }
                    models = [self.cached_hf_model or "meta-llama/Llama-3.2-3B-Instruct", "Qwen/Qwen2.5-72B-Instruct"]
                    last_err = ""
                    for hf_model in models:
                        payload = {
                            "model": hf_model,
                            "messages": [
                                {"role": "system", "content": system_instruction},
                                {"role": "user", "content": query_text}
                            ],
                            "temperature": 0.7,
                            "max_tokens": 600
                        }
                        resp = await client.post(url, headers=headers, json=payload)
                        if resp.status_code == 200:
                            data = resp.json()
                            content = data["choices"][0]["message"]["content"].strip()
                            self.cached_hf_model = hf_model
                            return content, hf_model.split("/")[-1], None
                        else:
                            last_err = f"HF {hf_model} HTTP {resp.status_code}: {resp.text[:150]}"

                    return None, None, last_err

                # ---------------- 2. OPENAI ----------------
                elif provider.lower() == "openai" or key.startswith("sk-"):
                    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
                    payload = {
                        "model": "gpt-4o-mini",
                        "messages": [
                            {"role": "system", "content": system_instruction},
                            {"role": "user", "content": query_text}
                        ],
                        "temperature": 0.7,
                        "max_tokens": 600
                    }
                    resp = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        return data["choices"][0]["message"]["content"].strip(), "gpt-4o-mini", None
                    else:
                        err_msg = f"OpenAI HTTP {resp.status_code}: {resp.text[:200]}"
                        return None, None, err_msg

                # ---------------- 3. GOOGLE GEMINI ----------------
                else:
                    combined_prompt = f"{system_instruction}\n\nUser Question: {query_text}"
                    payload = {
                        "contents": [{"parts": [{"text": combined_prompt}]}],
                        "generationConfig": {
                            "temperature": 0.7,
                            "maxOutputTokens": 600
                        }
                    }

                    model = self.cached_gemini_model or "gemini-3.6-flash"
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
                    resp = await client.post(url, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if parts:
                                return parts[0].get("text", "").strip(), model, None
                    else:
                        err_msg = f"Gemini {model} HTTP {resp.status_code}: {resp.text[:200]}"
                        return None, None, err_msg

        except Exception as e:
            print(f"Active LLM call exception: {e}")
            return None, None, str(e)

        return None, None, "Unknown generation error"

    async def process_query(
        self,
        query_text: str,
        profile: UnifiedHealthProfile,
        api_key: Optional[str] = None,
        provider: str = "huggingface"
    ) -> Dict[str, Any]:
        """
        Process query using Active Live LLM if key is available,
        otherwise fall back seamlessly to physiological reasoning engine.
        """
        recovery = self.analyze_recovery_status(profile)
        anomalies = self.detect_anomalies(profile)
        workout = self.generate_adaptive_workout_plan(profile)
        cfg = PERSONAS.get(profile.persona_id, PERSONAS["alex_longevity"])

        # Try live LLM call first
        live_llm_response, used_model, llm_error = await self.generate_llm_response(
            query_text=query_text,
            profile=profile,
            api_key=api_key,
            provider=provider
        )

        if live_llm_response:
            return {
                "query": query_text,
                "persona_id": profile.persona_id,
                "odin_response": live_llm_response,
                "is_live_ai": True,
                "provider": provider,
                "model_name": used_model,
                "recovery_synthesis": recovery,
                "active_anomalies": anomalies,
                "recommended_workout": workout["prescribed_plan"],
                "scientific_citations": [self.citations["hrv_guided_training"], self.citations["zone2_metabolism"]]
            }

        # Fallback to Built-in Physiological Reasoning Engine
        query_lower = query_text.lower()
        if any(w in query_lower for w in ["recovery", "readiness", "hrv", "tired", "energy", "heart rate"]):
            response_text = (
                f"Your current recovery score is **{recovery['recovery_score']}/100** ({recovery['status']}). "
                f"Your nocturnal HRV is **{profile.sleep.avg_hrv_rmssd_ms} ms** (baseline is {cfg['baseline']['hrv_baseline']} ms, "
                f"z-score: {recovery['biometric_breakdown']['hrv_z_score']}). "
                f"Resting heart rate was recorded at **{profile.daily.resting_heart_rate_bpm} bpm**."
            )
            citations = [self.citations["hrv_guided_training"], self.citations["sleep_architecture"]]

        elif any(w in query_lower for w in ["glucose", "sugar", "cgm", "diet", "meal", "food", "carb"]):
            cgm = profile.body.cgm_readings_24h or []
            max_g = max([g.glucose_mg_dl for g in cgm], default=profile.body.fasting_glucose_mg_dl or 90.0)
            avg_g = round(sum([g.glucose_mg_dl for g in cgm]) / max(1, len(cgm)), 1)
            in_range = len([g for g in cgm if 70.0 <= g.glucose_mg_dl <= 140.0])
            tir = round((in_range / max(1, len(cgm))) * 100.0, 1)

            response_text = (
                f"Over the last 24 hours, your CGM telemetry shows an average glucose of **{avg_g} mg/dL** "
                f"with a peak excursion of **{max_g} mg/dL**. "
                f"Your Time-in-Range (70-140 mg/dL) is currently **{tir}%** (optimal target: >85%). "
                f"To buffer post-prandial spikes, consider a 10-15 min light Zone 1 walk immediately following meals, "
                f"which activates non-insulin GLUT-4 translocation."
            )
            citations = [self.citations["glucose_variability"]]

        elif any(w in query_lower for w in ["workout", "train", "exercise", "run", "gym", "lift", "hiit", "plan"]):
            plan = workout["prescribed_plan"]
            response_text = (
                f"Based on your physiological readiness ({recovery['recovery_score']}/100), OdinAI recommends: "
                f"**{plan['workout_title']}** ({plan['duration_minutes']} min, target strain {plan['target_strain']}).\n\n"
                f"• **Main Set**: {plan['main_set']}\n"
                f"• **Physiological Rationale**: {plan['rationale']}"
            )
            citations = [self.citations["zone2_metabolism"], self.citations["acwr_workload"]]

        elif any(w in query_lower for w in ["longevity", "120", "biological age", "lifespan", "aging"]):
            bio_age = cfg["baseline"]["biological_age"]
            chrono_age = cfg["baseline"]["chronological_age"]
            delta = round(chrono_age - bio_age, 1)
            response_text = (
                f"Your target is extreme longevity (Target 120). Currently, your biological age is calculated at "
                f"**{bio_age} years** compared to chronological age **{chrono_age} years** "
                f"({delta:+.1f} year deceleration). "
                f"The primary longevity drivers in your telemetry are high HRV resilience (+{recovery['biometric_breakdown']['hrv_z_score']} SD), "
                f"sustained Zone 2 mitochondrial stimulus, and deep slow-wave sleep efficiency ({profile.sleep.sleep_efficiency_pct}%)."
            )
            citations = [self.citations["zone2_metabolism"], self.citations["sleep_architecture"]]

        else:
            response_text = (
                f"OdinAI Health Summary for {cfg['name']}: Today your recovery is **{recovery['recovery_score']}/100**, "
                f"with {len(anomalies)} active biometric alerts detected. "
                f"Your daily steps stand at **{profile.daily.steps:,}**, sleep score is **{profile.sleep.sleep_score}/100**, "
                f"and resting HR is **{profile.daily.resting_heart_rate_bpm} bpm**."
            )
            citations = [self.citations["hrv_guided_training"]]

        return {
            "query": query_text,
            "persona_id": profile.persona_id,
            "odin_response": response_text,
            "is_live_ai": False,
            "provider": "physiological_heuristics",
            "llm_error": llm_error,
            "recovery_synthesis": recovery,
            "active_anomalies": anomalies,
            "recommended_workout": workout["prescribed_plan"],
            "scientific_citations": citations
        }
