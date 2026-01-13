// Helper to render simple charts using Chart.js (loaded via CDN).
// Expects summary payload { total_balance, categories: [{name, budget, spend}] }
let pieChart = null;
let barChart = null;
let subCharts = {};

async function loadSummaryAndRender(query = "") {
  const res = await fetch('/api/summary' + query);
  if (!res.ok) throw new Error(await res.text());
  const summary = await res.json();
  renderCharts(summary);
  const totalEl = document.getElementById('total-balance');
  if (totalEl && typeof summary.total_balance !== 'undefined') {
    const amt = Number(summary.total_balance || 0);
    totalEl.textContent = `${amt < 0 ? '-' : ''}£${Math.abs(amt).toFixed(2)}`;
  }
  const uncatEl = document.getElementById('uncat-count');
  if (uncatEl && typeof summary.uncategorized_count !== 'undefined') {
    uncatEl.textContent = summary.uncategorized_count;
  }
}

function renderCharts(summary) {
  const ctxPie = document.getElementById('pie-spend')?.getContext('2d');
  const ctxBar = document.getElementById('bar-budgets')?.getContext('2d');
  const palette = ["#ef4444", "#f97316", "#f59e0b", "#eab308", "#22c55e", "#14b8a6", "#06b6d4", "#3b82f6", "#6366f1", "#8b5cf6", "#ec4899", "#f973ab"];
  const labels = (summary.categories || []).map(c => c.name);
  const spend = (summary.categories || []).map(c => Math.abs(Number(c.spend || 0)));
  const colors = (summary.categories || []).map((c, idx) => c.color || palette[idx % palette.length]);

  const budgetItems = [
    ...(summary.categories || []).filter(c => Number(c.budget || 0) > 0).map((c, idx) => ({
      name: c.name,
      budget: Number(c.budget || 0),
      spend: Math.abs(Number(c.spend || 0)),
      color: c.color || palette[idx % palette.length],
    })),
    ...(summary.subcategories || []).filter(s => Number(s.budget || 0) > 0).map((s, idx) => ({
      name: s.name,
      budget: Number(s.budget || 0),
      spend: Math.abs(Number(s.spend || 0)),
      color: palette[(idx + 5) % palette.length],
    })),
  ];

  if (ctxPie) {
    if (pieChart) pieChart.destroy();
    pieChart = new Chart(ctxPie, {
      type: 'pie',
      data: { labels, datasets: [{ data: spend, backgroundColor: colors }] },
      options: { plugins: { legend: { labels: { color: '#e2e8f0' } } } }
    });
  }

  if (ctxBar) {
    if (barChart) barChart.destroy();
    const barLabels = budgetItems.map(b => b.name);
    const budgets = budgetItems.map(b => b.budget);
    const barSpend = budgetItems.map(b => b.spend);
    const barColors = budgetItems.map((b, idx) => b.color || palette[idx % palette.length]);
    barChart = new Chart(ctxBar, {
      type: 'bar',
      data: {
        labels: barLabels,
        datasets: [
          { label: 'Budget', data: budgets, backgroundColor: barColors },
          { label: 'Spend', data: barSpend, backgroundColor: 'rgba(248,113,113,0.7)' },
        ],
      },
      options: {
        plugins: { legend: { labels: { color: '#e2e8f0' } } },
        scales: {
          x: { ticks: { color: '#e2e8f0' } },
          y: { ticks: { color: '#e2e8f0' } }
        }
      }
    });
  }

  // Per-category subcategory pies
  const piesContainer = document.getElementById('subcategory-pies');
  if (piesContainer && summary.subcategories) {
    Object.values(subCharts).forEach(chart => chart.destroy());
    subCharts = {};
    piesContainer.innerHTML = '';
    const catSpendMap = {};
    (summary.categories || []).forEach(c => { catSpendMap[c.id] = Math.abs(Number(c.spend || 0)); });
    const subsByCat = {};
    summary.subcategories.forEach(s => {
      subsByCat[s.category_id] = subsByCat[s.category_id] || [];
      subsByCat[s.category_id].push(s);
    });
    summary.categories.forEach(cat => {
      const subs = subsByCat[cat.id] || [];
      if (!subs.length) return;
      const baseColor = cat.color || palette[0];
      const canvasId = `pie-sub-${cat.id}`;
      const card = document.createElement('div');
      card.className = 'card';
      card.innerHTML = `
        <div style="font-size:14px; font-weight:600; margin-bottom:6px;">${cat.name} subcategories</div>
        <canvas id="${canvasId}"></canvas>
      `;
      piesContainer.appendChild(card);
      const ctx = document.getElementById(canvasId)?.getContext('2d');
      if (!ctx) return;
      const subLabels = subs.map(s => s.name);
      const subSpend = subs.map(s => Math.abs(Number(s.spend || 0)));
      const subColors = subs.map((s, idx) => tweakColor(baseColor, idx));
      const totalSpend = catSpendMap[cat.id] || subSpend.reduce((a, b) => a + b, 0);
      const subtotal = subSpend.reduce((a, b) => a + b, 0);
      const noneSlice = Math.max(totalSpend - subtotal, 0);
      if (noneSlice > 0) {
        subLabels.push('None');
        subSpend.push(noneSlice);
        subColors.push(baseColor);
      }
      subCharts[cat.id] = new Chart(ctx, {
        type: 'pie',
        data: { labels: subLabels, datasets: [{ data: subSpend, backgroundColor: subColors }] },
        options: { plugins: { legend: { labels: { color: '#e2e8f0' } } } }
      });
    });
  }
}

function randomColor() {
  const r = Math.floor(Math.random() * 150) + 50;
  const g = Math.floor(Math.random() * 150) + 50;
  const b = Math.floor(Math.random() * 150) + 50;
  return `rgba(${r},${g},${b},0.8)`;
}

// Simple lighter variation generator
function tweakColor(hex, step = 0) {
  if (!hex || !hex.startsWith('#') || hex.length !== 7) return hex || '#3b82f6';
  const num = parseInt(hex.slice(1), 16);
  let r = (num >> 16) & 0xff;
  let g = (num >> 8) & 0xff;
  let b = num & 0xff;
  const factor = 1 + (step + 1) * 0.06;
  r = Math.min(255, Math.floor(r * factor));
  g = Math.min(255, Math.floor(g * factor));
  b = Math.min(255, Math.floor(b * factor));
  return `rgb(${r},${g},${b})`;
}
