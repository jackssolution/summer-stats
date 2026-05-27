/* ── Filtering ───────────────────────────────────────────────────────────── */

let activeTeam = 'all';
let activePos  = 'all';

function filterTeam(team, btn) {
  activeTeam = team;
  document.querySelectorAll('.filter-bar .filter-btn').forEach(b => {
    if (['all', 'Kenosha Kingfish', 'St. Cloud Rox', 'Willmar Stingers'].includes(b.textContent.trim()) ||
        b.textContent.trim() === 'All Players') {
      b.classList.remove('active');
    }
  });
  btn.classList.add('active');
  applyFilters();
}

function filterPos(pos, btn) {
  activePos = pos;
  ['posAll', ...document.querySelectorAll('.filter-bar .filter-btn')]
    .forEach(b => b && b.classList.remove('active'));
  btn.classList.add('active');
  applyFilters();
}

function applyFilters() {
  document.querySelectorAll('.player-card').forEach(card => {
    const team = card.dataset.team;
    const pos  = card.dataset.pos;
    const teamOk = activeTeam === 'all' || team === activeTeam;
    const posOk  = activePos  === 'all' || pos  === activePos;
    card.classList.toggle('hidden', !(teamOk && posOk));
  });

  // Hide section headings if all cards in that section are hidden
  document.querySelectorAll('.position-section').forEach(sec => {
    const visible = [...sec.querySelectorAll('.player-card')].some(c => !c.classList.contains('hidden'));
    sec.style.display = visible ? '' : 'none';
  });
}


/* ── Modals ──────────────────────────────────────────────────────────────── */

function openAddModal() {
  // Show player pick list
  fetch('/api/players')
    .then(r => r.json())
    .then(players => {
      const list = document.getElementById('playerPickList');
      list.innerHTML = players.map(p => `
        <div class="player-pick-item">
          <div>
            <div class="pick-name">${p.name}</div>
            <div class="pick-meta">${p.team} · ${p.position}</div>
          </div>
          <div class="pick-actions">
            ${p.position !== 'pitcher' ? `<button class="btn btn-add" onclick="openBattingModal(${p.id}, '${p.name.replace(/'/g,"\\'")}'); event.stopPropagation();">Batting</button>` : ''}
            ${p.position !== 'hitter'  ? `<button class="btn btn-scrape" onclick="openPitchingModal(${p.id}, '${p.name.replace(/'/g,"\\'")}'); event.stopPropagation();">Pitching</button>` : ''}
          </div>
        </div>
      `).join('');
      showModal('chooseModal');
    });
}

function openBattingModal(playerId, playerName) {
  document.getElementById('bPlayerId').value = playerId;
  document.getElementById('bModalName').textContent = playerName;
  // Set today as default date
  const today = new Date().toISOString().split('T')[0];
  document.getElementById('bDate').value = today;
  // Reset all number inputs
  document.querySelectorAll('#battingForm input[type="number"]').forEach(i => i.value = 0);
  showModal('battingModal');
}

function openPitchingModal(playerId, playerName) {
  document.getElementById('pPlayerId').value = playerId;
  document.getElementById('pModalName').textContent = playerName;
  const today = new Date().toISOString().split('T')[0];
  document.getElementById('pDate').value = today;
  document.querySelectorAll('#pitchingForm input[type="number"]').forEach(i => i.value = 0);
  document.querySelector('#pitchingForm input[name="IP"]').value = '0.0';
  showModal('pitchingModal');
}

function showModal(id) {
  document.querySelectorAll('.modal').forEach(m => m.classList.add('hidden'));
  document.getElementById(id).classList.remove('hidden');
  document.getElementById('modalOverlay').classList.remove('hidden');
}

function closeModals(event) {
  if (event.target === document.getElementById('modalOverlay')) {
    closeAllModals();
  }
}

function closeAllModals() {
  document.getElementById('modalOverlay').classList.add('hidden');
  document.querySelectorAll('.modal').forEach(m => m.classList.add('hidden'));
}


/* ── Form submission ─────────────────────────────────────────────────────── */

function formToJson(form) {
  const data = {};
  new FormData(form).forEach((v, k) => { data[k] = v; });
  return data;
}

function submitBatting(event) {
  event.preventDefault();
  const data = formToJson(event.target);
  // Convert numeric strings
  ['AB','PA','H','doubles','triples','HR','BB','HBP'].forEach(k => {
    data[k] = parseInt(data[k]) || 0;
  });
  data.player_id = parseInt(data.player_id);
  if (!data.PA) data.PA = data.AB + data.BB + data.HBP;

  fetch('/api/batting', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  .then(r => r.json())
  .then(res => {
    if (res.ok) {
      closeAllModals();
      showToast('Game saved!', 'success');
      setTimeout(() => location.reload(), 600);
    } else {
      showToast('Error: ' + res.error, 'error');
    }
  });
}

function submitPitching(event) {
  event.preventDefault();
  const data = formToJson(event.target);
  ['BF','K','BB','HBP','strikes','balls','total_pitches',
   'R','ER','H_allowed','HR_allowed','doubles_allowed','triples_allowed'].forEach(k => {
    data[k] = parseInt(data[k]) || 0;
  });
  data.player_id = parseInt(data.player_id);
  if (!data.total_pitches) data.total_pitches = data.strikes + data.balls;

  fetch('/api/pitching', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  .then(r => r.json())
  .then(res => {
    if (res.ok) {
      closeAllModals();
      showToast('Game saved!', 'success');
      setTimeout(() => location.reload(), 600);
    } else {
      showToast('Error: ' + res.error, 'error');
    }
  });
}


/* ── Delete line ─────────────────────────────────────────────────────────── */

function deleteLine(type, id) {
  if (!confirm('Remove this game line?')) return;
  fetch(`/api/${type}/${id}`, { method: 'DELETE' })
    .then(r => r.json())
    .then(res => {
      if (res.ok) {
        showToast('Removed.', 'success');
        setTimeout(() => location.reload(), 400);
      }
    });
}


/* ── Scrape trigger ──────────────────────────────────────────────────────── */

function triggerScrape() {
  const btn = document.getElementById('scrapeBtn');
  btn.classList.add('loading');
  btn.textContent = '↻ Scraping…';
  btn.disabled = true;

  fetch('/api/scrape', { method: 'POST' })
    .then(r => r.json())
    .then(res => {
      if (res.ok) {
        showToast('Scrape started — page will refresh in 30s', 'success');
        setTimeout(() => location.reload(), 30000);
      } else {
        showToast('Scrape error: ' + (res.error || 'unknown'), 'error');
        btn.classList.remove('loading');
        btn.textContent = '↻ Refresh Stats';
        btn.disabled = false;
      }
    })
    .catch(() => {
      btn.classList.remove('loading');
      btn.textContent = '↻ Refresh Stats';
      btn.disabled = false;
    });
}


/* ── Toast ───────────────────────────────────────────────────────────────── */

let _toastTimer = null;
function showToast(msg, type = 'success') {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.className = `toast ${type}`;
  clearTimeout(_toastTimer);
  _toastTimer = setTimeout(() => { el.classList.add('hidden'); }, 2800);
}


/* ── Keyboard shortcuts ──────────────────────────────────────────────────── */

document.addEventListener('keydown', e => {
  if (e.key === 'Escape') closeAllModals();
});
