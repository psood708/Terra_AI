/**
 * Terra Intelligence Engine - Minimalist Client Application
 * Features: Active AI Integration (Gemini/OpenAI), Dark/Light Theme, Spotlight Guided Tour
 */

let currentPersona = 'alex_longevity';
let currentStreak = 12;

// Active AI Configuration
let activeApiKey = localStorage.getItem('tie_llm_api_key') || '';
let activeProvider = localStorage.getItem('tie_llm_provider') || 'gemini';

// Global chart instances
let overviewAgpChartInstance = null;
let agpChartInstance = null;
let sleepChartInstance = null;
let correlationChartInstance = null;

// Debounce utility
function debounce(func, wait) {
  let timeout;
  return function(...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), wait);
  };
}

// Format markdown text with bolding and bullet list items
function formatOdinText(text) {
  if (!text) return '';
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold">$1</strong>')
    .replace(/\n\n/g, '<br/><br/>')
    .replace(/• (.*?)(?=(•|<br\/>|$))/g, '<div class="flex items-start my-1"><span class="text-emerald-400 mr-2">•</span><span>$1</span></div>');
}

// ---------------- THEME MANAGEMENT (DARK / LIGHT) ----------------

function getEffectiveTheme() {
  return localStorage.getItem('terra_theme') || 'dark';
}

function applyTheme(theme) {
  const html = document.documentElement;
  const sunIcon = document.getElementById('themeSunIcon');
  const moonIcon = document.getElementById('themeMoonIcon');

  if (theme === 'light') {
    html.classList.remove('dark');
    if (sunIcon) sunIcon.classList.remove('hidden');
    if (moonIcon) moonIcon.classList.add('hidden');
  } else {
    html.classList.add('dark');
    if (sunIcon) sunIcon.classList.add('hidden');
    if (moonIcon) moonIcon.classList.remove('hidden');
  }

  localStorage.setItem('terra_theme', theme);
  updateChartsTheme(theme);
}

function toggleTheme() {
  const current = getEffectiveTheme();
  applyTheme(current === 'dark' ? 'light' : 'dark');
}

function updateChartsTheme(theme) {
  const isDark = theme === 'dark';
  const gridColor = isDark ? '#161e2e' : '#e2e8f0';
  const tickColor = isDark ? '#64748b' : '#64748b';

  [overviewAgpChartInstance, agpChartInstance, correlationChartInstance].forEach(chart => {
    if (chart && chart.options && chart.options.scales) {
      if (chart.options.scales.x) {
        chart.options.scales.x.grid.color = gridColor;
        chart.options.scales.x.ticks.color = tickColor;
      }
      if (chart.options.scales.y) {
        chart.options.scales.y.grid.color = gridColor;
        chart.options.scales.y.ticks.color = tickColor;
      }
      if (chart.options.scales.yHrv) {
        chart.options.scales.yHrv.grid.color = gridColor;
      }
      chart.update();
    }
  });

  if (sleepChartInstance && sleepChartInstance.options && sleepChartInstance.options.plugins) {
    sleepChartInstance.options.plugins.legend.labels.color = isDark ? '#cbd5e1' : '#334155';
    sleepChartInstance.update();
  }
}

// ---------------- ACTIVE AI CONFIGURATION ----------------

function updateAiStatusBadge() {
  const statusLabel = document.getElementById('aiStatusLabel');
  const activeTag = document.getElementById('activeAiModelTag');
  
  if (activeApiKey && activeApiKey.trim()) {
    let provName = 'Hugging Face';
    if (activeProvider === 'gemini') provName = 'Gemini';
    else if (activeProvider === 'openai') provName = 'GPT-4o';
    
    if (statusLabel) statusLabel.textContent = `AI: ${provName}`;
    if (activeTag) activeTag.textContent = `Active AI: ${provName}`;
  } else {
    if (statusLabel) statusLabel.textContent = 'AI: Local';
    if (activeTag) activeTag.textContent = 'Active AI: Local (Heuristic)';
  }
}

function updateProviderInputs() {
  const provider = document.getElementById('aiProviderSelect').value;
  const input = document.getElementById('aiApiKeyInput');
  const hint = document.getElementById('aiTokenHint');

  if (provider === 'huggingface') {
    input.placeholder = 'Enter hf_... (Free at huggingface.co/settings/tokens)';
    if (hint) hint.innerHTML = 'Get a free User Access Token at <a href="https://huggingface.co/settings/tokens" target="_blank" class="text-emerald-400 underline">huggingface.co/settings/tokens</a>. Powers Llama-3.2-3B-Instruct.';
  } else if (provider === 'gemini') {
    input.placeholder = 'Enter AIzaSy... from Google AI Studio';
    if (hint) hint.innerHTML = 'Google Gemini API key. Powers gemini-3.6-flash and gemini-2.5-flash.';
  } else {
    input.placeholder = 'Enter sk-... from OpenAI Platform';
    if (hint) hint.innerHTML = 'OpenAI API key. Powers GPT-4o-mini and GPT-4o.';
  }
}

function openAiModal() {
  document.getElementById('aiProviderSelect').value = activeProvider;
  document.getElementById('aiApiKeyInput').value = activeApiKey;
  updateProviderInputs();
  const resultDiv = document.getElementById('aiTestResult');
  if (resultDiv) {
    resultDiv.classList.add('hidden');
    resultDiv.innerHTML = '';
  }
  document.getElementById('aiModal').classList.remove('hidden');
}

function closeAiModal() {
  document.getElementById('aiModal').classList.add('hidden');
}

async function testAiConnection() {
  const provider = document.getElementById('aiProviderSelect').value;
  const key = document.getElementById('aiApiKeyInput').value.trim();
  const resultDiv = document.getElementById('aiTestResult');

  if (!key) {
    resultDiv.className = 'text-[11px] rounded-lg p-2.5 bg-rose-500/10 border border-rose-500/30 text-rose-400 block';
    resultDiv.innerHTML = '<i class="fa-solid fa-circle-exclamation mr-1.5"></i> Please enter an API token first.';
    return;
  }

  let providerLabel = 'Hugging Face';
  if (provider === 'gemini') providerLabel = 'Google Gemini';
  else if (provider === 'openai') providerLabel = 'OpenAI';

  resultDiv.className = 'text-[11px] rounded-lg p-2.5 bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 block';
  resultDiv.innerHTML = `<i class="fa-solid fa-spinner animate-spin mr-1.5"></i> Testing connection to ${providerLabel}...`;

  try {
    const res = await fetch('/api/odin/test-connection', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ api_key: key, provider: provider })
    });
    const data = await res.json();

    if (data.success) {
      resultDiv.className = 'text-[11px] rounded-lg p-2.5 bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 block';
      resultDiv.innerHTML = `<i class="fa-solid fa-check mr-1.5"></i> <strong>Connected!</strong> Model: <code>${data.model}</code> • Latency: ${data.latency_ms}ms`;
    } else {
      resultDiv.className = 'text-[11px] rounded-lg p-2.5 bg-rose-500/10 border border-rose-500/30 text-rose-400 block';
      resultDiv.innerHTML = `<i class="fa-solid fa-triangle-exclamation mr-1.5"></i> <strong>Connection Failed:</strong> ${data.error || 'Check API Token'}`;
    }
  } catch (err) {
    resultDiv.className = 'text-[11px] rounded-lg p-2.5 bg-rose-500/10 border border-rose-500/30 text-rose-400 block';
    resultDiv.innerHTML = `<i class="fa-solid fa-triangle-exclamation mr-1.5"></i> Request error: ${err.message}`;
  }
}

function saveAiKey() {
  const provider = document.getElementById('aiProviderSelect').value;
  const key = document.getElementById('aiApiKeyInput').value.trim();
  
  activeProvider = provider;
  activeApiKey = key;

  localStorage.setItem('tie_llm_provider', provider);
  if (key) {
    localStorage.setItem('tie_llm_api_key', key);
  } else {
    localStorage.removeItem('tie_llm_api_key');
  }

  updateAiStatusBadge();
  closeAiModal();
}

function clearAiKey() {
  document.getElementById('aiApiKeyInput').value = '';
  activeApiKey = '';
  localStorage.removeItem('tie_llm_api_key');
  updateAiStatusBadge();
  closeAiModal();
}

// ---------------- TAB NAVIGATION ----------------

function switchTab(tabId) {
  document.querySelectorAll('.tab-content').forEach(tab => {
    tab.classList.add('hidden');
  });

  const activeTab = document.getElementById(tabId);
  if (activeTab) {
    activeTab.classList.remove('hidden');
    activeTab.classList.add('animate-fade-in');
  }

  document.querySelectorAll('.nav-tab').forEach(btn => {
    if (btn.dataset.tab === tabId) {
      btn.classList.add('active-tab');
      btn.classList.remove('text-gray-400');
    } else {
      btn.classList.remove('active-tab');
      btn.classList.add('text-gray-400');
    }
  });

  setTimeout(() => {
    if (overviewAgpChartInstance) overviewAgpChartInstance.resize();
    if (agpChartInstance) agpChartInstance.resize();
    if (sleepChartInstance) sleepChartInstance.resize();
    if (correlationChartInstance) correlationChartInstance.resize();
  }, 100);
}

// ---------------- DATA LOADING & METRICS ----------------

async function loadDashboard(personaId) {
  currentPersona = personaId;

  try {
    const personasRes = await fetch('/api/health-score/personas');
    const personas = await personasRes.json();
    const persona = personas.find(p => p.id === personaId) || personas[0];

    document.getElementById('personaName').textContent = persona.name;
    document.getElementById('personaGoal').textContent = persona.target_goal;
    document.getElementById('personaSensors').textContent = persona.primary_sensors.join(', ');
    document.getElementById('simChronoAge').textContent = persona.baseline.chronological_age;
    document.getElementById('simCurrentBioAge').textContent = persona.baseline.biological_age;

    const [recoveryRes, anomaliesRes, workoutRes] = await Promise.all([
      fetch(`/api/odin/recovery/${personaId}`).then(r => r.json()),
      fetch(`/api/odin/anomalies/${personaId}`).then(r => r.json()),
      fetch(`/api/odin/adaptive-workout/${personaId}`).then(r => r.json())
    ]);

    const score = recoveryRes.recovery_score;
    const scoreElem = document.getElementById('metricRecovery');
    scoreElem.textContent = score;
    scoreElem.style.color = recoveryRes.color || '#10B981';
    document.getElementById('metricRecoveryStatus').textContent = recoveryRes.status;

    document.getElementById('metricHrv').textContent = recoveryRes.biometric_breakdown.current_hrv_rmssd;
    document.getElementById('metricHrvZ').textContent = `z-score: ${recoveryRes.biometric_breakdown.hrv_z_score > 0 ? '+' : ''}${recoveryRes.biometric_breakdown.hrv_z_score}`;

    document.getElementById('metricSleep').textContent = Math.round(recoveryRes.biometric_breakdown.sleep_efficiency_pct);
    document.getElementById('metricDeepSleep').textContent = `Deep: ${recoveryRes.biometric_breakdown.deep_sleep_pct}% of sleep`;

    const anomalyBanner = document.getElementById('anomalyBanner');
    const anomalyBannerText = document.getElementById('anomalyBannerText');
    if (anomaliesRes.anomalies_count > 0) {
      anomalyBanner.classList.remove('hidden');
      anomalyBannerText.textContent = `${anomaliesRes.anomalies_count} Biometric Alert(s): ${anomaliesRes.anomalies[0].message}`;
    } else {
      anomalyBanner.classList.add('hidden');
    }

    const alertsContainer = document.getElementById('alertsContainer');
    const alertsCount = document.getElementById('alertsCount');
    alertsCount.textContent = `${anomaliesRes.anomalies_count} Active`;
    if (anomaliesRes.anomalies_count === 0) {
      alertsCount.className = 'text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded-full font-semibold';
      alertsContainer.innerHTML = '<p class="text-gray-400 card-muted text-[11px] italic">All biomarkers in physiological equilibrium.</p>';
    } else {
      alertsCount.className = 'text-[10px] bg-rose-500/10 text-rose-400 border border-rose-500/20 px-2 py-0.5 rounded-full font-semibold';
      alertsContainer.innerHTML = anomaliesRes.anomalies.map(a => `
        <div class="inner-card border border-rose-500/30 rounded-lg p-2.5 space-y-1">
          <div class="flex items-center justify-between">
            <span class="font-bold text-rose-400 uppercase text-[10px]">${a.metric}</span>
            <span class="text-[10px] px-1.5 py-0.2 rounded bg-rose-950 text-rose-300">${a.detected_value}</span>
          </div>
          <p class="card-sub text-[11px]">${a.message}</p>
          <div class="text-[10px] text-emerald-400"><i class="fa-solid fa-lightbulb mr-1"></i> ${a.actionable_fix}</div>
        </div>
      `).join('');
    }

    const plan = workoutRes.prescribed_plan;
    document.getElementById('overviewWorkoutTitle').textContent = plan.workout_title;
    document.getElementById('overviewWorkoutDesc').textContent = `${plan.category} (${plan.duration_minutes} mins) • Target Strain ${plan.target_strain}`;
    document.getElementById('overviewWorkoutRationale').textContent = plan.rationale;
    document.getElementById('overviewWorkoutStrain').textContent = `Strain ${plan.target_strain}`;

    await Promise.all([
      loadAGPChart(personaId),
      loadSleepChart(personaId),
      loadCorrelationChart(personaId)
    ]);

    await loadBioAgeData(personaId);
    triggerWhatIfSimulation();

    await Promise.all([
      loadCausalImpacts(personaId),
      loadDigitalTwins(personaId),
      loadRewards(personaId)
    ]);

  } catch (err) {
    console.error('Error loading dashboard:', err);
  }
}

// ---------------- TERRA GRAPH API CHARTS ----------------

async function loadAGPChart(personaId) {
  const res = await fetch(`/api/graph/agp/${personaId}`);
  const data = await res.json();

  const tir = data.agp_metrics.time_in_range_pct;
  document.getElementById('agpBadge').textContent = `TIR: ${tir}%`;
  document.getElementById('overviewTirBadge').textContent = `TIR: ${tir}%`;
  document.getElementById('agpMean').textContent = `${data.agp_metrics.mean_glucose_mg_dl} mg/dL`;
  document.getElementById('agpGmi').textContent = `${data.agp_metrics.gmi_estimated_a1c}%`;
  document.getElementById('agpCv').textContent = `${data.agp_metrics.glycemic_variability_cv_pct}%`;

  const isDark = getEffectiveTheme() === 'dark';
  const gridColor = isDark ? '#161e2e' : '#e2e8f0';

  const labels = data.time_series.timestamps.map((t, idx) => (idx % 12 === 0 ? t : ''));
  const vals = data.time_series.glucose_values;

  const chartConfig = {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'Glucose (mg/dL)',
        data: vals,
        borderColor: '#f59e0b',
        backgroundColor: 'rgba(245, 158, 11, 0.08)',
        borderWidth: 2,
        pointRadius: 0,
        pointHoverRadius: 4,
        fill: true,
        tension: 0.3
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { color: gridColor }, ticks: { color: '#64748b', maxRotation: 0, autoSkip: false } },
        y: { min: 50, max: 220, grid: { color: gridColor }, ticks: { color: '#64748b' } }
      }
    }
  };

  const ctxOverview = document.getElementById('overviewAgpChart').getContext('2d');
  if (overviewAgpChartInstance) overviewAgpChartInstance.destroy();
  overviewAgpChartInstance = new Chart(ctxOverview, chartConfig);

  const ctxFull = document.getElementById('agpChart').getContext('2d');
  if (agpChartInstance) agpChartInstance.destroy();
  agpChartInstance = new Chart(ctxFull, chartConfig);
}

async function loadSleepChart(personaId) {
  const res = await fetch(`/api/graph/hypnogram/${personaId}`);
  const data = await res.json();

  document.getElementById('sleepScoreBadge').textContent = `Sleep Score: ${data.sleep_score}`;
  document.getElementById('hypnoDeep').textContent = `${data.stage_breakdown_minutes.deep}m`;
  document.getElementById('hypnoRem').textContent = `${data.stage_breakdown_minutes.rem}m`;
  document.getElementById('hypnoLight').textContent = `${data.stage_breakdown_minutes.light}m`;
  document.getElementById('hypnoAwake').textContent = `${data.stage_breakdown_minutes.awake}m`;

  const isDark = getEffectiveTheme() === 'dark';
  const ctx = document.getElementById('sleepChart').getContext('2d');
  if (sleepChartInstance) sleepChartInstance.destroy();

  sleepChartInstance = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Deep Sleep', 'REM Sleep', 'Light Sleep', 'Awake'],
      datasets: [{
        data: [
          data.stage_breakdown_minutes.deep,
          data.stage_breakdown_minutes.rem,
          data.stage_breakdown_minutes.light,
          data.stage_breakdown_minutes.awake
        ],
        backgroundColor: ['#6366f1', '#06b6d4', '#475569', '#f43f5e'],
        borderWidth: 0,
        hoverOffset: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'right', labels: { color: isDark ? '#cbd5e1' : '#334155', boxWidth: 10, padding: 12, font: { size: 11 } } }
      },
      cutout: '72%'
    }
  });
}

async function loadCorrelationChart(personaId) {
  const res = await fetch(`/api/graph/correlation/${personaId}?days=14`);
  const data = await res.json();

  const isDark = getEffectiveTheme() === 'dark';
  const gridColor = isDark ? '#161e2e' : '#e2e8f0';

  const ctx = document.getElementById('correlationChart').getContext('2d');
  if (correlationChartInstance) correlationChartInstance.destroy();

  correlationChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: data.dates.map(d => d.slice(5)),
      datasets: [
        {
          label: 'HRV (ms)',
          data: data.series.hrv_rmssd_ms,
          borderColor: '#10b981',
          borderWidth: 2,
          yAxisID: 'yHrv',
          tension: 0.3
        },
        {
          label: 'Sleep (hrs)',
          data: data.series.sleep_hours,
          borderColor: '#6366f1',
          borderWidth: 2,
          borderDash: [4, 4],
          yAxisID: 'ySleep',
          tension: 0.3
        },
        {
          label: 'Strain',
          data: data.series.workout_strain,
          borderColor: '#f59e0b',
          borderWidth: 2,
          yAxisID: 'yStrain',
          tension: 0.3
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { labels: { color: isDark ? '#cbd5e1' : '#334155', boxWidth: 10, font: { size: 11 } } } },
      scales: {
        x: { grid: { color: gridColor }, ticks: { color: '#64748b' } },
        yHrv: { type: 'linear', position: 'left', grid: { color: gridColor }, ticks: { color: '#10b981' } },
        ySleep: { type: 'linear', position: 'right', grid: { drawOnChartArea: false }, ticks: { color: '#6366f1' } },
        yStrain: { type: 'linear', position: 'right', grid: { drawOnChartArea: false }, ticks: { display: false } }
      }
    }
  });
}

// ---------------- BIOLOGICAL AGE & COUNTERFACTUAL SIMULATOR ----------------

async function loadBioAgeData(personaId) {
  const res = await fetch(`/api/health-score/bio-age/${personaId}`);
  const data = await res.json();

  document.getElementById('metricBioAge').textContent = data.biological_age;
  const deltaText = data.biological_age_delta_years < 0
    ? `${data.biological_age_delta_years} yrs (Decelerated)`
    : `+${data.biological_age_delta_years} yrs (Accelerated)`;

  const deltaElem = document.getElementById('metricBioDelta');
  deltaElem.textContent = deltaText;
  deltaElem.className = data.biological_age_delta_years < 0
    ? 'text-[11px] text-emerald-400 font-medium'
    : 'text-[11px] text-rose-400 font-medium';
}

async function triggerWhatIfSimulation() {
  const sleepVal = parseInt(document.getElementById('sleepSlider').value);
  const cardioVal = parseInt(document.getElementById('cardioSlider').value);
  const dinnerVal = parseFloat(document.getElementById('dinnerSlider').value);
  const tirVal = parseFloat(document.getElementById('tirSlider').value);

  document.getElementById('sleepSliderVal').textContent = `+${sleepVal} minutes`;
  document.getElementById('cardioSliderVal').textContent = `+${cardioVal} minutes`;
  document.getElementById('dinnerSliderVal').textContent = `${dinnerVal.toFixed(1)} hours before bed`;
  document.getElementById('tirSliderVal').textContent = `+${tirVal}% TIR`;

  const res = await fetch('/api/health-score/what-if', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      persona_id: currentPersona,
      added_sleep_minutes: sleepVal,
      added_zone2_minutes_weekly: cardioVal,
      earlier_dinner_shift_hours: dinnerVal,
      improved_glucose_tir_pct: tirVal
    })
  });
  const data = await res.json();

  document.getElementById('simNewBioAge').textContent = data.simulated_outcome.projected_biological_age;
  document.getElementById('simAdvantageBadge').textContent = `-${data.simulated_outcome.net_biological_years_saved} yrs saved`;
  document.getElementById('simVerdict').textContent = data.clinical_verdict;
  document.getElementById('simHrvGain').textContent = `+${data.simulated_outcome.projected_hrv_improvement_ms} ms`;
  document.getElementById('simVo2Gain').textContent = `+${data.simulated_outcome.projected_vo2_max_gain} ml/kg`;
  document.getElementById('simRhrDrop').textContent = `-${data.simulated_outcome.projected_rhr_reduction_bpm} bpm`;
}

// ---------------- KNOWLEDGE GRAPH & DIGITAL TWINS ----------------

async function loadCausalImpacts(personaId) {
  const res = await fetch(`/api/graph/behavioral-impacts/${personaId}`);
  const data = await res.json();
  const container = document.getElementById('causalImpactsContainer');

  if (!data.causal_impacts || data.causal_impacts.length === 0) {
    container.innerHTML = '<p class="card-muted text-xs">No behavioral impacts logged for today.</p>';
    return;
  }

  container.innerHTML = data.causal_impacts.map(impact => {
    const isPositive = impact.direction === 'positive';
    const borderCol = isPositive ? 'border-emerald-500/30' : 'border-rose-500/30';
    const icon = isPositive ? 'fa-arrow-trend-up text-emerald-400' : 'fa-arrow-trend-down text-rose-400';
    return `
      <div class="inner-card border ${borderCol} rounded-xl p-2.5 space-y-1">
        <div class="flex items-center justify-between">
          <span class="font-semibold card-title flex items-center text-xs">
            <i class="fa-solid ${icon} mr-1.5 text-[11px]"></i>
            ${impact.behavior}
          </span>
          <span class="text-[10px] px-1.5 py-0.5 rounded-full ${isPositive ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-400'} font-semibold">
            ${impact.net_impact_score > 0 ? '+' : ''}${impact.net_impact_score} net
          </span>
        </div>
        <div class="text-[11px] card-sub">
          Path: <strong class="card-title">${impact.affected_biomarker}</strong> → <span class="card-muted">${impact.target_outcome}</span>
        </div>
        <p class="text-[10px] card-muted leading-normal">${impact.physiological_mechanism}</p>
      </div>
    `;
  }).join('');
}

async function loadDigitalTwins(personaId) {
  const res = await fetch(`/api/graph/digital-twins/${personaId}`);
  const data = await res.json();
  const container = document.getElementById('digitalTwinsContainer');

  container.innerHTML = data.digital_twins.map(twin => `
    <div class="inner-card border border-gray-800 card-divider rounded-xl p-3 flex items-center justify-between">
      <div>
        <div class="flex items-center space-x-2">
          <h5 class="font-semibold card-title text-xs">${twin.name}</h5>
          <span class="text-[10px] px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400">${twin.target_goal}</span>
        </div>
        <div class="text-[10px] card-muted mt-1 space-x-2">
          ${twin.shared_traits.map(t => `<span>• ${t}</span>`).join('')}
        </div>
      </div>
      <div class="text-right">
        <span class="text-base font-black text-indigo-400">${twin.similarity_score_pct}%</span>
        <span class="text-[9px] card-muted block">Cosine Match</span>
      </div>
    </div>
  `).join('');
}

// ---------------- REWARDS & RETENTION ----------------

async function loadRewards(personaId) {
  const res = await fetch(`/api/rewards/${personaId}?streak_days=${currentStreak}`);
  const data = await res.json();

  document.getElementById('rewardStreak').textContent = data.streak_days;
  document.getElementById('rewardMultiplier').textContent = `${data.streak_multiplier}x Multiplier`;
  document.getElementById('rewardPoints').textContent = data.daily_points_earned;
  document.getElementById('rewardHabitsMet').textContent = `${data.achieved_habits_count} habits completed`;
  document.getElementById('retentionScore').textContent = Math.round(data.retention_analytics.retention_index_score);
  document.getElementById('churnRisk').textContent = `Churn: ${data.retention_analytics.churn_risk_level}`;
  document.getElementById('nudgeWindow').textContent = data.retention_analytics.best_notification_window;
  document.getElementById('nudgeStrategy').textContent = data.retention_analytics.recommended_nudge_strategy;
}

// ---------------- ODINAI CHAT (WITH ACTIVE LLM INTEGRATION) ----------------

async function handleOdinQuery(query) {
  if (!query || !query.trim()) return;

  const chatHistory = document.getElementById('chatHistory');

  // Append user message
  const userMsg = document.createElement('div');
  userMsg.className = 'flex items-start justify-end space-x-2';
  userMsg.innerHTML = `
    <div class="bg-emerald-600 text-black font-medium rounded-xl rounded-tr-none p-3 text-xs max-w-md shadow">
      ${query}
    </div>
  `;
  chatHistory.appendChild(userMsg);
  chatHistory.scrollTop = chatHistory.scrollHeight;

  // Append typing indicator
  const typingMsg = document.createElement('div');
  typingMsg.className = 'flex items-start space-x-3';
  typingMsg.innerHTML = `
    <div class="w-7 h-7 rounded-full bg-emerald-600/30 text-emerald-400 flex items-center justify-center text-xs shrink-0 mt-0.5">
      <i class="fa-solid fa-dna animate-spin"></i>
    </div>
    <div class="inner-card border border-gray-700/60 rounded-xl rounded-tl-none p-3 text-xs card-muted italic">
      OdinAI is synthesizing multi-sensor telemetry & sports science...
    </div>
  `;
  chatHistory.appendChild(typingMsg);
  chatHistory.scrollTop = chatHistory.scrollHeight;

  try {
    const res = await fetch('/api/odin/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        persona_id: currentPersona,
        query: query,
        api_key: activeApiKey || undefined,
        provider: activeProvider || 'gemini'
      })
    });
    const data = await res.json();
    chatHistory.removeChild(typingMsg);

    // Live AI badge vs local fallback notice
    let modelBadge = '';
    if (data.is_live_ai) {
      modelBadge = `
        <span class="text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded-full font-semibold inline-flex items-center mr-2">
          <i class="fa-solid fa-sparkles mr-1 text-[9px]"></i> Live AI (${data.model_name || data.provider.toUpperCase()})
        </span>
      `;
    } else {
      modelBadge = `
        <span class="text-[10px] bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 px-2 py-0.5 rounded-full font-semibold inline-flex items-center mr-2 cursor-pointer" onclick="openAiModal()">
          <i class="fa-solid fa-microchip mr-1 text-[9px]"></i> Local Engine (Click to Connect Live LLM)
        </span>
      `;
    }

    // Diagnostic Notice if LLM reported an error
    let errorNotice = '';
    if (data.llm_error) {
      errorNotice = `
        <div class="text-[10px] text-amber-400 bg-amber-500/10 border border-amber-500/25 rounded-lg p-2 my-1 leading-relaxed">
          <i class="fa-solid fa-triangle-exclamation mr-1"></i>
          <strong>AI Provider Note:</strong> ${data.llm_error}. Fallback physiological engine activated.
        </div>
      `;
    }

    // Citations
    const citationsHtml = data.scientific_citations && data.scientific_citations.length > 0
      ? `
        <div class="mt-3 pt-2.5 border-t border-gray-700/60 card-divider text-[10px] space-y-1 card-muted">
          <strong class="text-emerald-400 block"><i class="fa-solid fa-book-bookmark mr-1"></i> Scientific Grounding:</strong>
          ${data.scientific_citations.map(c => `
            <div>• <strong class="card-title">${c.authors}</strong> (${c.journal}) - <em>"${c.key_takeaway}"</em></div>
          `).join('')}
        </div>
      `
      : '';

    const odinMsg = document.createElement('div');
    odinMsg.className = 'flex items-start space-x-3';
    odinMsg.innerHTML = `
      <div class="w-7 h-7 rounded-full bg-emerald-600/30 text-emerald-400 flex items-center justify-center text-xs shrink-0 mt-0.5">
        <i class="fa-solid fa-brain"></i>
      </div>
      <div class="inner-card border border-gray-700/80 rounded-xl rounded-tl-none p-3.5 text-xs card-sub space-y-2 max-w-xl shadow">
        <div class="flex items-center mb-1">${modelBadge}</div>
        ${errorNotice}
        <div class="leading-relaxed">${formatOdinText(data.odin_response)}</div>
        ${citationsHtml}
      </div>
    `;
    chatHistory.appendChild(odinMsg);
    chatHistory.scrollTop = chatHistory.scrollHeight;

  } catch (err) {
    chatHistory.removeChild(typingMsg);
    console.error('Odin query failed:', err);
  }
}

// ---------------- SPOTLIGHT CUTOUT & DIRECTIONAL POPOVER TOUR ----------------

const TOUR_STEPS = [
  {
    targetId: 'tour-brand',
    tabId: 'tab-overview',
    icon: 'fa-dna',
    title: 'Terra Infrastructure & AI Layer',
    description: 'Terra connects over 500+ wearable sources into one normalized platform. This project implements the AI intelligence layer on top: autonomous health reasoning, trajectory forecasting, and extreme personalization.'
  },
  {
    targetId: 'tour-tabs',
    tabId: 'tab-overview',
    icon: 'fa-gauge-high',
    title: 'Minimalist Modular Navigation',
    description: 'Switch between focused studios: Overview, OdinAI Health Assistant, Terra Graph API (AGP & hypnograms), 10-Year Longevity Simulator, and Habits & Retention.'
  },
  {
    targetId: 'tour-persona',
    tabId: 'tab-overview',
    icon: 'fa-user-astronaut',
    title: 'Multi-Goal Persona Switcher',
    description: 'Switch between personas to see extreme personalization in action: Alex Vance (Target 120 Longevity), Sarah Chen (Olympic Triathlon), Marcus Sterling (Metabolic Reversal), or Elena Rostova (Cognitive Stamina).'
  },
  {
    targetId: 'tour-vitals',
    tabId: 'tab-overview',
    icon: 'fa-heart-pulse',
    title: 'Synthesized Biometric Vitals',
    description: 'Live cards displaying composite autonomic recovery, overnight HRV (rMSSD) z-scores, sleep architecture, and phenotypic biological age computed across multi-stream sensors.'
  },
  {
    targetId: 'tour-odin',
    tabId: 'tab-odin',
    icon: 'fa-brain',
    title: 'OdinAI Health Intelligence Studio',
    description: 'Converse with OdinAI. Ask about recovery, training readiness, or glycemic excursions. Powered by active LLMs (Gemini / OpenAI) with peer-reviewed sports science citations.'
  },
  {
    targetId: 'tour-whatif',
    tabId: 'tab-longevity',
    icon: 'fa-sliders',
    title: 'Counterfactual What-If Simulator',
    description: 'Drag sliders for sleep, Zone 2 cardio, dinner timing, and glucose stability to simulate real-time shifts in biological age and 10-year mortality reduction.'
  }
];

let currentTourIndex = 0;

function positionSpotlightAndPopover() {
  const step = TOUR_STEPS[currentTourIndex];
  const targetEl = document.getElementById(step.targetId);
  const spotlight = document.getElementById('tourSpotlight');
  const popover = document.getElementById('tourPopover');
  const arrow = document.getElementById('tourArrow');

  if (!targetEl || !spotlight || !popover) return;

  const rect = targetEl.getBoundingClientRect();
  const pad = 8;
  const spotTop = Math.max(4, rect.top - pad);
  const spotLeft = Math.max(4, rect.left - pad);
  const spotWidth = Math.min(window.innerWidth - 8, rect.width + pad * 2);
  const spotHeight = rect.height + pad * 2;

  spotlight.style.top = `${spotTop}px`;
  spotlight.style.left = `${spotLeft}px`;
  spotlight.style.width = `${spotWidth}px`;
  spotlight.style.height = `${spotHeight}px`;

  const popoverWidth = Math.min(360, window.innerWidth - 32);
  popover.style.width = `${popoverWidth}px`;

  const spaceBelow = window.innerHeight - (spotTop + spotHeight);
  const spaceAbove = spotTop;

  let popoverLeft = (spotLeft + spotWidth / 2) - (popoverWidth / 2);
  popoverLeft = Math.max(16, Math.min(window.innerWidth - popoverWidth - 16, popoverLeft));

  let popoverTop = 0;
  let isBelow = true;

  if (spaceBelow >= 230 || spaceBelow >= spaceAbove) {
    popoverTop = spotTop + spotHeight + 14;
    isBelow = true;
  } else {
    popoverTop = Math.max(12, spotTop - 250);
    isBelow = false;
  }

  popover.style.top = `${popoverTop}px`;
  popover.style.left = `${popoverLeft}px`;

  const targetCenterX = spotLeft + spotWidth / 2;
  const arrowRelX = Math.max(20, Math.min(popoverWidth - 28, targetCenterX - popoverLeft - 6));
  arrow.style.left = `${arrowRelX}px`;

  if (isBelow) {
    arrow.className = 'absolute w-3 h-3 modal-themed border-emerald-500/40 rotate-45 pointer-events-none arrow-up';
  } else {
    arrow.className = 'absolute w-3 h-3 modal-themed border-emerald-500/40 rotate-45 pointer-events-none arrow-down';
  }
}

function updateTourStep() {
  const step = TOUR_STEPS[currentTourIndex];

  if (step.tabId) {
    switchTab(step.tabId);
  }

  const targetEl = document.getElementById(step.targetId);
  if (targetEl) {
    targetEl.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'center' });
  }

  document.getElementById('tourStepIndicator').textContent = `Step ${currentTourIndex + 1} of ${TOUR_STEPS.length}`;
  document.getElementById('tourTitle').textContent = step.title;
  document.getElementById('tourDescription').textContent = step.description;

  const iconElem = document.getElementById('tourIcon');
  iconElem.className = `fa-solid ${step.icon}`;

  const prevBtn = document.getElementById('tourPrevBtn');
  if (currentTourIndex > 0) {
    prevBtn.classList.remove('hidden');
  } else {
    prevBtn.classList.add('hidden');
  }

  const nextBtn = document.getElementById('tourNextBtn');
  if (currentTourIndex === TOUR_STEPS.length - 1) {
    nextBtn.textContent = 'Finish Tour';
  } else {
    nextBtn.textContent = 'Next';
  }

  const dotsContainer = document.getElementById('tourDots');
  dotsContainer.innerHTML = TOUR_STEPS.map((_, idx) => `
    <span class="w-1.5 h-1.5 rounded-full transition ${idx === currentTourIndex ? 'bg-emerald-400 w-3' : 'bg-gray-700'}"></span>
  `).join('');

  setTimeout(positionSpotlightAndPopover, 120);
}

function startTour(stepIndex = 0) {
  currentTourIndex = stepIndex;
  const container = document.getElementById('tourContainer');
  container.classList.remove('hidden');
  updateTourStep();
}

function closeTour() {
  const container = document.getElementById('tourContainer');
  container.classList.add('hidden');
  localStorage.setItem('terra_tour_completed', 'true');
  switchTab('tab-overview');
}

function nextTourStep() {
  if (currentTourIndex < TOUR_STEPS.length - 1) {
    currentTourIndex++;
    updateTourStep();
  } else {
    closeTour();
  }
}

function prevTourStep() {
  if (currentTourIndex > 0) {
    currentTourIndex--;
    updateTourStep();
  }
}

// ---------------- INITIALIZATION ----------------

document.addEventListener('DOMContentLoaded', () => {
  // 1. Initial Theme Setup
  applyTheme(getEffectiveTheme());

  // 2. Initial AI Status Setup
  updateAiStatusBadge();

  // 3. Initial Dashboard Data Load
  loadDashboard(currentPersona);

  // 4. Tab Navigation clicks
  document.querySelectorAll('.nav-tab').forEach(tabBtn => {
    tabBtn.addEventListener('click', () => {
      switchTab(tabBtn.dataset.tab);
    });
  });

  // 5. Persona Selector
  document.getElementById('personaSelect').addEventListener('change', (e) => {
    loadDashboard(e.target.value);
  });

  // 6. Refresh Button
  document.getElementById('refreshDataBtn').addEventListener('click', () => {
    loadDashboard(currentPersona);
  });

  // 7. Theme Toggle Button
  document.getElementById('themeToggleBtn').addEventListener('click', toggleTheme);

  // 8. AI Settings Modal Listeners
  document.getElementById('navAiSettingsBtn').addEventListener('click', openAiModal);
  const openAiBtn = document.getElementById('openAiModalBtn');
  if (openAiBtn) openAiBtn.addEventListener('click', openAiModal);

  document.getElementById('closeAiModalBtn').addEventListener('click', closeAiModal);
  document.getElementById('aiProviderSelect').addEventListener('change', updateProviderInputs);
  document.getElementById('testAiKeyBtn').addEventListener('click', testAiConnection);
  document.getElementById('saveAiKeyBtn').addEventListener('click', saveAiKey);
  document.getElementById('clearAiKeyBtn').addEventListener('click', clearAiKey);

  // 9. Odin Chat Submit
  const chatForm = document.getElementById('chatForm');
  const chatInput = document.getElementById('chatInput');
  chatForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const query = chatInput.value;
    chatInput.value = '';
    handleOdinQuery(query);
  });

  // 10. Odin Prompt Chips
  document.querySelectorAll('.prompt-chip').forEach(btn => {
    btn.addEventListener('click', () => {
      handleOdinQuery(btn.dataset.query);
    });
  });

  // 11. What-If Sliders (debounced)
  const debouncedWhatIf = debounce(triggerWhatIfSimulation, 100);
  ['sleepSlider', 'cardioSlider', 'dinnerSlider', 'tirSlider'].forEach(id => {
    document.getElementById(id).addEventListener('input', debouncedWhatIf);
  });

  // 12. Claim Streak Button
  document.getElementById('claimStreakBtn').addEventListener('click', async () => {
    const res = await fetch('/api/rewards/claim-streak', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        persona_id: currentPersona,
        current_streak_days: currentStreak
      })
    });
    const data = await res.json();
    currentStreak = data.new_streak_days;
    loadRewards(currentPersona);
  });

  // 13. Tour Event Listeners
  document.getElementById('startTourBtn').addEventListener('click', () => startTour(0));
  document.getElementById('tourSkipBtn').addEventListener('click', closeTour);
  document.getElementById('tourNextBtn').addEventListener('click', nextTourStep);
  document.getElementById('tourPrevBtn').addEventListener('click', prevTourStep);

  window.addEventListener('resize', debounce(positionSpotlightAndPopover, 50));
  window.addEventListener('scroll', debounce(positionSpotlightAndPopover, 50));

  // 14. First-Time Tour Trigger (if not previously completed)
  if (!localStorage.getItem('terra_tour_completed')) {
    setTimeout(() => {
      startTour(0);
    }, 600);
  }
});
