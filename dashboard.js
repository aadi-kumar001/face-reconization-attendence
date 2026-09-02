let trendChart, deptChart;

function tickClock() {
  document.getElementById('clock').textContent = new Date().toLocaleString();
}
setInterval(tickClock, 1000);
tickClock();

async function authedFetch(url) {
  const res = await fetch(url, { credentials: 'same-origin' });
  if (res.status === 401) {
    window.location.href = '/login';
    throw new Error('unauthenticated');
  }
  return res;
}

async function loadLiveResults() {
  try {
    const res = await fetch('/api/live_results');
    const rows = await res.json();
    const list = document.getElementById('liveList');
    list.innerHTML = rows.length
      ? rows.map(r => `
          <div class="live-row">
            <span>${r.employee_name || 'Unknown'}</span>
            <span>${r.liveness_passed ? '✅ live' : '⏳ verifying'}
              ${r.just_marked ? ' · marked' : ''}
              ${r.confidence ? ' · ' + Math.round(r.confidence * 100) + '%' : ''}
            </span>
          </div>`).join('')
      : '<div class="live-row"><span>No faces in frame</span></div>';
  } catch (e) { /* camera may be unavailable in this environment */ }
}

async function loadStats() {
  try {
    const res = await authedFetch('/api/attendance/today');
    const s = await res.json();
    document.getElementById('statCards').innerHTML = `
      <div class="stat-card"><div class="value">${s.present + s.late}</div><div class="label">Marked</div></div>
      <div class="stat-card"><div class="value">${s.late}</div><div class="label">Late</div></div>
      <div class="stat-card"><div class="value">${s.absent}</div><div class="label">Absent</div></div>
      <div class="stat-card"><div class="value">${Math.round(s.attendance_rate * 100)}%</div><div class="label">Rate</div></div>
    `;
  } catch (e) { /* not logged in yet */ }
}

async function loadTrend() {
  try {
    const res = await authedFetch('/api/attendance/trend?days=7');
    const data = await res.json();
    const ctx = document.getElementById('trendChart');
    const labels = data.map(d => d.date.slice(5));
    const marked = data.map(d => d.marked);
    if (trendChart) trendChart.destroy();
    trendChart = new Chart(ctx, {
      type: 'line',
      data: { labels, datasets: [{ label: 'Marked', data: marked, borderColor: '#ff7a3d', tension: .3 }] },
      options: { plugins: { legend: { labels: { color: '#9598b3' } } },
        scales: { x: { ticks: { color: '#9598b3' } }, y: { ticks: { color: '#9598b3' }, beginAtZero: true } } }
    });
  } catch (e) { /* not logged in yet */ }
}

async function loadDept() {
  try {
    const res = await authedFetch('/api/attendance/departments');
    const data = await res.json();
    const ctx = document.getElementById('deptChart');
    if (deptChart) deptChart.destroy();
    deptChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: data.map(d => d.department),
        datasets: [{ label: 'Present', data: data.map(d => d.count), backgroundColor: '#ff4d6d' }]
      },
      options: { plugins: { legend: { display: false } },
        scales: { x: { ticks: { color: '#9598b3' } }, y: { ticks: { color: '#9598b3' }, beginAtZero: true } } }
    });
  } catch (e) { /* not logged in yet */ }
}

function loadAll() {
  loadStats();
  loadTrend();
  loadDept();
}

loadAll();
setInterval(loadLiveResults, 1500);
setInterval(loadAll, 30000);
