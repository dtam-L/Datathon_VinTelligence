/* ═══════════════════════════════════════════════════════════════════════════
   VinTelligence Revenue Forecasting — Frontend Logic
   ════════════════════════════════════════════════════════════════════════════ */

const API_BASE = 'http://localhost:5000';

// ──────────────────────────────────────────────────────────────────────────────
// State
// ──────────────────────────────────────────────────────────────────────────────
let state = {
  model: 'XGBoost',
  target: 'Revenue',
  featureInfo: {},
  topFeatures: [],
  defaults: {}
};

// ──────────────────────────────────────────────────────────────────────────────
// Feature metadata (fallback if API is unavailable)
// ──────────────────────────────────────────────────────────────────────────────
const FEATURE_INFO = {
  total_orders: {
    label: 'Total Orders', description: 'Tổng số đơn hàng trong ngày', unit: 'đơn', correlation: 0.9358, default: 1200
  },
  cancelled_orders: {
    label: 'Cancelled Orders', description: 'Số đơn hàng bị huỷ trong ngày', unit: 'đơn', correlation: 0.8795, default: 50
  },
  Revenue_lag_1: {
    label: 'Revenue (Hôm qua)', description: 'Doanh thu ngày hôm qua (lag 1 ngày)', unit: 'VND', correlation: 0.8657, default: 5_000_000_000
  },
  returned_orders: {
    label: 'Returned Orders', description: 'Số đơn hàng bị trả lại', unit: 'đơn', correlation: 0.8376, default: 30
  },
  COGS_lag_1: {
    label: 'COGS (Hôm qua)', description: 'Giá vốn hàng bán ngày hôm qua', unit: 'VND', correlation: 0.8368, default: 3_500_000_000
  },
  Revenue_roll_mean_7: {
    label: 'Revenue TB 7 ngày', description: 'Doanh thu trung bình 7 ngày gần nhất', unit: 'VND', correlation: 0.6956, default: 4_800_000_000
  },
  Revenue_roll_mean_30: {
    label: 'Revenue TB 30 ngày', description: 'Doanh thu trung bình 30 ngày gần nhất', unit: 'VND', correlation: 0.6833, default: 4_600_000_000
  },
  Revenue_roll_mean_14: {
    label: 'Revenue TB 14 ngày', description: 'Doanh thu trung bình 14 ngày gần nhất', unit: 'VND', correlation: 0.6705, default: 4_700_000_000
  },
  COGS_roll_mean_30: {
    label: 'COGS TB 30 ngày', description: 'Giá vốn trung bình 30 ngày gần nhất', unit: 'VND', correlation: 0.6632, default: 3_200_000_000
  },
  COGS_roll_mean_7: {
    label: 'COGS TB 7 ngày', description: 'Giá vốn trung bình 7 ngày gần nhất', unit: 'VND', correlation: 0.6589, default: 3_300_000_000
  },
};

const TOP_10_FEATURES = [
  'total_orders', 'cancelled_orders', 'Revenue_lag_1', 'returned_orders', 'COGS_lag_1',
  'Revenue_roll_mean_7', 'Revenue_roll_mean_30', 'Revenue_roll_mean_14',
  'COGS_roll_mean_30', 'COGS_roll_mean_7',
];

// ──────────────────────────────────────────────────────────────────────────────
// Init
// ──────────────────────────────────────────────────────────────────────────────
async function init() {
  try {
    const res = await fetch(`${API_BASE}/api/features`);
    if (res.ok) {
      const data = await res.json();
      state.featureInfo = data.feature_info || FEATURE_INFO;
      state.topFeatures = data.top_features || TOP_10_FEATURES;
    } else {
      throw new Error('API not available');
    }
  } catch {
    state.featureInfo = FEATURE_INFO;
    state.topFeatures = TOP_10_FEATURES;
  }

  renderFeatures();
  renderCorrChart();
  setupSelectors();
  setupButtons();
}

// ──────────────────────────────────────────────────────────────────────────────
// Render feature inputs
// ──────────────────────────────────────────────────────────────────────────────
function renderFeatures() {
  const grid = document.getElementById('features-grid');
  grid.innerHTML = '';

  TOP_10_FEATURES.forEach((feat, idx) => {
    const info = state.featureInfo[feat] || FEATURE_INFO[feat] || { label: feat, description: '', unit: '', correlation: 0, default: 0 };
    const corrPct = (info.correlation * 100).toFixed(1);
    const isVND = info.unit === 'VND';

    const item = document.createElement('div');
    item.className = 'feature-item';
    item.innerHTML = `
      <div class="feature-header">
        <div class="feature-label">${idx + 1}. ${info.label}</div>
        <div class="corr-badge">r = +${info.correlation.toFixed(4)}</div>
      </div>
      <div class="feature-desc">${info.description}</div>
      <div class="feature-input-wrap">
        <input
          class="feature-input"
          id="input-${feat}"
          type="number"
          value="${info.default}"
          placeholder="${info.default}"
          step="${isVND ? 1000000 : 1}"
          min="0"
        />
        <span class="feature-unit">${info.unit}</span>
      </div>
    `;
    grid.appendChild(item);
  });
}

// ──────────────────────────────────────────────────────────────────────────────
// Render correlation bar chart
// ──────────────────────────────────────────────────────────────────────────────
function renderCorrChart() {
  const wrap = document.getElementById('corr-chart');
  wrap.innerHTML = '';

  const maxCorr = 0.9358;
  const gradients = [
    'linear-gradient(90deg,#6c63ff,#9c88ff)',
    'linear-gradient(90deg,#6c63ff,#00d9a3)',
    'linear-gradient(90deg,#00d9a3,#38ef7d)',
  ];

  TOP_10_FEATURES.forEach((feat, idx) => {
    const info = state.featureInfo[feat] || FEATURE_INFO[feat] || {};
    const corr = info.correlation || 0;
    const pct = (corr / maxCorr) * 100;
    const grad = gradients[Math.floor(idx / 4)] || gradients[2];

    const row = document.createElement('div');
    row.className = 'chart-row';
    row.innerHTML = `
      <div class="chart-label" title="${info.label || feat}">${info.label || feat}</div>
      <div class="chart-bar-track">
        <div class="chart-bar" style="width:0%;background:${grad};" data-target="${pct.toFixed(1)}">
          <span class="chart-bar-val">+${corr.toFixed(4)}</span>
        </div>
      </div>
    `;
    wrap.appendChild(row);
  });

  // Animate bars
  requestAnimationFrame(() => {
    document.querySelectorAll('.chart-bar').forEach(bar => {
      bar.style.width = bar.dataset.target + '%';
    });
  });
}

// ──────────────────────────────────────────────────────────────────────────────
// Selectors
// ──────────────────────────────────────────────────────────────────────────────
function setupSelectors() {
  document.querySelectorAll('#model-selector .pill').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('#model-selector .pill').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.model = btn.dataset.value;
    });
  });

  document.querySelectorAll('#target-selector .pill').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('#target-selector .pill').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.target = btn.dataset.value;
    });
  });
}

// ──────────────────────────────────────────────────────────────────────────────
// Buttons
// ──────────────────────────────────────────────────────────────────────────────
function setupButtons() {
  document.getElementById('btn-reset').addEventListener('click', resetInputs);
  document.getElementById('btn-predict').addEventListener('click', predict);
}

function resetInputs() {
  TOP_10_FEATURES.forEach(feat => {
    const info = state.featureInfo[feat] || FEATURE_INFO[feat] || {};
    const el = document.getElementById(`input-${feat}`);
    if (el) el.value = info.default || 0;
  });
  document.getElementById('result-card').style.display = 'none';
}

// ──────────────────────────────────────────────────────────────────────────────
// Prediction
// ──────────────────────────────────────────────────────────────────────────────
async function predict() {
  const btn = document.getElementById('btn-predict');
  const btnText = btn.querySelector('.btn-text');
  const btnLoader = btn.querySelector('.btn-loader');

  // Gather inputs
  const inputs = {};
  TOP_10_FEATURES.forEach(feat => {
    const el = document.getElementById(`input-${feat}`);
    inputs[feat] = el ? parseFloat(el.value) || 0 : 0;
  });

  // Show loading
  btn.disabled = true;
  btnText.style.display = 'none';
  btnLoader.style.display = 'inline';

  try {
    const res = await fetch(`${API_BASE}/api/predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: state.model,
        target: state.target,
        inputs
      })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.error || 'Prediction failed');
    }

    const data = await res.json();
    showResult(data, inputs);
  } catch (e) {
    alert('❌ Lỗi: ' + e.message);
  } finally {
    btn.disabled = false;
    btnText.style.display = 'inline';
    btnLoader.style.display = 'none';
  }
}

// ──────────────────────────────────────────────────────────────────────────────
// Show result
// ──────────────────────────────────────────────────────────────────────────────
function showResult(data, inputs) {
  const card = document.getElementById('result-card');
  card.style.display = 'block';

  // Scroll to result
  card.scrollIntoView({ behavior: 'smooth', block: 'center' });

  // Meta
  document.getElementById('result-meta').textContent = `${data.model} · ${data.target}`;

  // Amount
  const amount = document.getElementById('result-amount');
  animateNumber(amount, 0, data.prediction, 1200);

  // Gauge – mức độ tự tin
  const confidencePct = 99.55;
  setTimeout(() => {
    document.getElementById('gauge-fill').style.width = confidencePct + '%';
    document.getElementById('gauge-pct').textContent = confidencePct.toFixed(1) + '%';
  }, 100);

  // Insight chips
  const chipsEl = document.getElementById('insight-chips');
  chipsEl.innerHTML = '';
  const chips = generateInsights(inputs, data);
  chips.forEach(c => {
    const el = document.createElement('div');
    el.className = `insight-chip ${c.type}`;
    el.textContent = c.text;
    chipsEl.appendChild(el);
  });
}

// ──────────────────────────────────────────────────────────────────────────────
// Animate number counter
// ──────────────────────────────────────────────────────────────────────────────
function animateNumber(el, from, to, duration) {
  const start = performance.now();
  const diff = to - from;

  function step(now) {
    const elapsed = now - start;
    const progress = Math.min(elapsed / duration, 1);
    const ease = 1 - Math.pow(1 - progress, 3); // ease-out cubic
    const current = from + diff * ease;
    el.textContent = formatVND(current);
    if (progress < 1) requestAnimationFrame(step);
  }

  requestAnimationFrame(step);
}

function formatVND(n) {
  if (n >= 1_000_000_000) return (n / 1_000_000_000).toFixed(2) + ' tỷ';
  if (n >= 1_000_000)     return (n / 1_000_000).toFixed(1) + ' triệu';
  return n.toLocaleString('vi-VN');
}

// ──────────────────────────────────────────────────────────────────────────────
// Generate insight chips
// ──────────────────────────────────────────────────────────────────────────────
function generateInsights(inputs, data) {
  const chips = [];
  const { total_orders, cancelled_orders, Revenue_lag_1 } = inputs;

  if (total_orders > 1000) chips.push({ type: 'positive', text: `📦 ${total_orders.toLocaleString()} đơn hàng (cao)` });
  else chips.push({ type: 'neutral', text: `📦 ${total_orders.toLocaleString()} đơn hàng` });

  const cancelRate = total_orders > 0 ? (cancelled_orders / total_orders * 100).toFixed(1) : 0;
  chips.push({ type: parseFloat(cancelRate) < 5 ? 'positive' : 'neutral', text: `❌ Tỷ lệ huỷ: ${cancelRate}%` });

  if (Revenue_lag_1 > 0) {
    const growthPct = ((data.prediction - Revenue_lag_1) / Revenue_lag_1 * 100).toFixed(1);
    const sign = parseFloat(growthPct) >= 0 ? '+' : '';
    chips.push({ type: parseFloat(growthPct) >= 0 ? 'positive' : 'neutral', text: `📈 So hôm qua: ${sign}${growthPct}%` });
  }

  chips.push({ type: 'neutral', text: `🤖 Model: ${data.model}` });
  return chips;
}

// ──────────────────────────────────────────────────────────────────────────────
// Bootstrap
// ──────────────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', init);
