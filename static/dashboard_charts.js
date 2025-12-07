// Helper to render simple charts using Chart.js (loaded via CDN).
// Expects summary payload { total_balance, categories: [{name, budget, spend}] }
async function loadSummaryAndRender() {
  const res = await fetch('/api/summary');
  if (!res.ok) throw new Error(await res.text());
  const summary = await res.json();
  renderCharts(summary);
  const totalEl = document.getElementById('total-balance');
  if (totalEl && typeof summary.total_balance !== 'undefined') {
    totalEl.textContent = Number(summary.total_balance || 0).toFixed(2);
  }
}

function renderCharts(summary) {
  const ctxPie = document.getElementById('pie-spend')?.getContext('2d');
  const ctxBar = document.getElementById('bar-budgets')?.getContext('2d');
  const labels = summary.categories.map(c => c.name);
  const spend = summary.categories.map(c => Number(c.spend || 0));
  const budgets = summary.categories.map(c => Number(c.budget || 0));

  if (ctxPie) {
    new Chart(ctxPie, {
      type: 'pie',
      data: { labels, datasets: [{ data: spend, backgroundColor: labels.map(() => randomColor()) }] },
      options: { plugins: { legend: { labels: { color: '#e2e8f0' } } } }
    });
  }

  if (ctxBar) {
    new Chart(ctxBar, {
      type: 'bar',
      data: {
        labels,
        datasets: [
          { label: 'Budget', data: budgets, backgroundColor: 'rgba(59,130,246,0.6)' },
          { label: 'Spend', data: spend, backgroundColor: 'rgba(248,113,113,0.7)' },
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
}

function randomColor() {
  const r = Math.floor(Math.random() * 150) + 50;
  const g = Math.floor(Math.random() * 150) + 50;
  const b = Math.floor(Math.random() * 150) + 50;
  return `rgba(${r},${g},${b},0.8)`;
}
