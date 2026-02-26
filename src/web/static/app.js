/* EVE Arbitrage Bot — Dashboard Logic */

let _opportunities = [];
let _sortKey = 'total_profit_potential';
let _sortAsc = false;
let _refreshTimer = null;

// ── Bootstrap ─────────────────────────────────────────────────────────────

function init(autoRefreshMs) {
  // Load based on what's enabled
  if (typeof HAS_CHARACTER !== 'undefined' && HAS_CHARACTER) {
    loadCharacterStatus();
  }
  if (typeof HAS_WORMHOLES !== 'undefined' && HAS_WORMHOLES) {
    loadWormholes();
  }
  if (typeof HAS_TWITCH !== 'undefined' && HAS_TWITCH) {
    updateTwitchStatus();
  }
  
  loadOpportunities();
  loadInventory();
  updateScanStatus();

  if (autoRefreshMs > 0) {
    setInterval(() => {
      if (HAS_CHARACTER) loadCharacterStatus();
      if (HAS_WORMHOLES) loadWormholes();
      if (HAS_TWITCH) updateTwitchStatus();
      loadOpportunities();
      updateScanStatus();
    }, autoRefreshMs);
  }
}

// ── Tab switching ─────────────────────────────────────────────────────────

function showTab(name) {
  document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
  document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
  document.getElementById('tab-' + name).classList.remove('hidden');
  event.target.classList.add('active');

  if (name === 'inventory') loadInventory();
  if (name === 'character') loadCharacterStatus();
  if (name === 'wormholes') loadWormholes();
}

// ── Opportunities ─────────────────────────────────────────────────────────

async function loadOpportunities() {
  try {
    const res = await fetch('/api/opportunities?limit=500');
    const data = await res.json();
    _opportunities = data.results || [];
    populatePairFilter();
    renderOpportunities();
  } catch (e) {
    document.getElementById('opp-tbody').innerHTML =
      '<tr><td colspan="9" class="muted center">Error loading data</td></tr>';
  }
}

function populatePairFilter() {
  const sel = document.getElementById('filter-pair');
  const current = sel.value;
  const pairs = new Set(_opportunities.map(o => `${o.buy_region} → ${o.sell_region}`));
  sel.innerHTML = '<option value="">All routes</option>';
  pairs.forEach(p => {
    const opt = document.createElement('option');
    opt.value = p; opt.textContent = p;
    sel.appendChild(opt);
  });
  sel.value = current;
}

function filterOpportunities() {
  renderOpportunities();
}

function sortBy(key) {
  if (_sortKey === key) {
    _sortAsc = !_sortAsc;
  } else {
    _sortKey = key;
    _sortAsc = false;
  }
  renderOpportunities();
}

function renderOpportunities() {
  const nameFilter = document.getElementById('filter-item').value.toLowerCase();
  const pairFilter = document.getElementById('filter-pair').value;

  let items = _opportunities.filter(o => {
    if (nameFilter && !o.item_name.toLowerCase().includes(nameFilter)) return false;
    if (pairFilter && `${o.buy_region} → ${o.sell_region}` !== pairFilter) return false;
    return true;
  });

  items.sort((a, b) => {
    const av = a[_sortKey], bv = b[_sortKey];
    if (typeof av === 'string') {
      return _sortAsc ? av.localeCompare(bv) : bv.localeCompare(av);
    }
    return _sortAsc ? av - bv : bv - av;
  });

  document.getElementById('opp-count').textContent = `${items.length} opportunities`;

  const tbody = document.getElementById('opp-tbody');
  if (!items.length) {
    tbody.innerHTML = '<tr><td colspan="9" class="muted center">No opportunities found — run a scan first</td></tr>';
    return;
  }

  tbody.innerHTML = items.map(o => {
    const marginClass = o.profit_margin_pct >= 25 ? 'margin-high'
                      : o.profit_margin_pct >= 15 ? 'margin-mid'
                      : 'margin-low';
    return `
      <tr>
        <td>${escHtml(o.item_name)}</td>
        <td>${escHtml(o.buy_region)}</td>
        <td>${escHtml(o.sell_region)}</td>
        <td class="num">${fmtIsk(o.buy_price)}</td>
        <td class="num">${fmtIsk(o.sell_price)}</td>
        <td class="num profit-pos">${fmtIsk(o.net_profit_per_unit)}</td>
        <td class="num ${marginClass}">${o.profit_margin_pct.toFixed(1)}%</td>
        <td class="num">${fmtNum(o.volume_available)}</td>
        <td class="num profit-pos">${fmtIsk(o.total_profit_potential)}</td>
      </tr>`;
  }).join('');
}

// ── Scan control ──────────────────────────────────────────────────────────

async function triggerScan() {
  const btn = document.getElementById('btn-scan');
  btn.disabled = true;
  btn.textContent = 'Scanning…';
  btn.classList.add('scanning');

  try {
    const res = await fetch('/api/scan/run', { method: 'POST' });
    if (res.status === 409) {
      alert('A scan is already running.');
      return;
    }
    // Poll for completion
    pollScanStatus(btn);
  } catch (e) {
    btn.disabled = false;
    btn.textContent = 'Run Scan';
    btn.classList.remove('scanning');
  }
}

function pollScanStatus(btn) {
  const interval = setInterval(async () => {
    const status = await updateScanStatus();
    if (!status.scan_running) {
      clearInterval(interval);
      btn.disabled = false;
      btn.textContent = 'Run Scan';
      btn.classList.remove('scanning');
      loadOpportunities();
      loadInventory();
    }
  }, 2000);
}

async function updateScanStatus() {
  try {
    const res = await fetch('/api/scan/status');
    const data = await res.json();
    const label = document.getElementById('last-scan-label');
    if (data.last_scan) {
      const d = new Date(data.last_scan + 'Z');
      label.textContent = `Last scan: ${d.toLocaleTimeString()} · ${data.opportunities_count} opps`;
    } else {
      label.textContent = 'No scan yet';
    }
    return data;
  } catch (e) {
    return {};
  }
}

// ── Inventory ─────────────────────────────────────────────────────────────

async function loadInventory() {
  try {
    const res = await fetch('/api/inventory');
    const data = await res.json();
    renderInventory(data.inventory || []);
  } catch (e) {
    document.getElementById('inv-tbody').innerHTML =
      '<tr><td colspan="8" class="muted center">Error loading inventory</td></tr>';
  }
}

function renderInventory(items) {
  const tbody = document.getElementById('inv-tbody');
  if (!items.length) {
    tbody.innerHTML = '<tr><td colspan="8" class="muted center">No inventory items — add some!</td></tr>';
    document.getElementById('inv-summary').textContent = '';
    return;
  }

  let totalCost = 0, totalPnl = 0;
  tbody.innerHTML = items.map(item => {
    const cost = item.cost_basis_isk * item.quantity;
    totalCost += cost;
    const pnl = item.unrealized_pnl;
    if (pnl !== null) totalPnl += pnl;
    const pnlClass = pnl === null ? '' : pnl >= 0 ? 'profit-pos' : 'profit-neg';
    const mktPrice = item.current_market_price !== null ? fmtIsk(item.current_market_price) : '—';
    const pnlStr = pnl !== null ? fmtIsk(pnl) : '—';
    return `
      <tr>
        <td>${escHtml(item.item_name)}</td>
        <td class="num">${fmtNum(item.quantity)}</td>
        <td class="num">${fmtIsk(item.cost_basis_isk)}</td>
        <td class="num">${fmtIsk(cost)}</td>
        <td class="num">${mktPrice}</td>
        <td class="num ${pnlClass}">${pnlStr}</td>
        <td>${escHtml(item.station || '—')}</td>
        <td>
          <button class="btn btn-sm" aria-label="Update quantity for ${escHtml(item.item_name)}" onclick="updateInventoryQty(${item.id}, ${item.quantity})">Update Qty</button>
          <button class="btn btn-danger" onclick="deleteInventoryItem(${item.id})">Remove</button>
        </td>
      </tr>`;
  }).join('');

  const pnlClass = totalPnl >= 0 ? 'profit-pos' : 'profit-neg';
  document.getElementById('inv-summary').innerHTML =
    `Total cost: <strong>${fmtIsk(totalCost)}</strong> &nbsp;·&nbsp; ` +
    `Unrealized P&L: <strong class="${pnlClass}">${fmtIsk(totalPnl)}</strong>`;
}

async function deleteInventoryItem(id) {
  if (!confirm('Remove this item from inventory?')) return;
  await fetch(`/api/inventory/${id}`, { method: 'DELETE' });
  loadInventory();
}

async function updateInventoryQty(id, currentQty) {
  const input = prompt('New quantity:', currentQty);
  if (input === null) return;
  const qty = parseInt(input, 10);
  if (isNaN(qty) || qty <= 0) { alert('Quantity must be a positive integer.'); return; }
  const res = await fetch(`/api/inventory/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ quantity: qty }),
  });
  if (!res.ok) {
    const d = await res.json().catch(() => ({}));
    alert(d.description || `Error ${res.status}`);
  }
  loadInventory();
}

// ── Add inventory modal ───────────────────────────────────────────────────

function openAddModal() {
  document.getElementById('add-modal').classList.remove('hidden');
  document.getElementById('add-name').focus();
}
function closeAddModal() {
  document.getElementById('add-modal').classList.add('hidden');
  ['add-name','add-qty','add-cost','add-station'].forEach(id => document.getElementById(id).value = '');
  const err = document.getElementById('add-error');
  err.textContent = '';
  err.classList.add('hidden');
}

async function submitAddItem() {
  const name = document.getElementById('add-name').value.trim();
  const qty  = parseInt(document.getElementById('add-qty').value, 10);
  const cost = parseFloat(document.getElementById('add-cost').value);
  const station = document.getElementById('add-station').value.trim();
  const err  = document.getElementById('add-error');

  if (!name || !qty || isNaN(cost)) {
    err.textContent = 'Item name, quantity, and cost basis are required.';
    err.classList.remove('hidden');
    return;
  }

  try {
    const res = await fetch('/api/inventory', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ item_name: name, quantity: qty, cost_basis_isk: cost, station }),
    });
    if (!res.ok) {
      const d = await res.json();
      err.textContent = d.description || `Error ${res.status}`;
      err.classList.remove('hidden');
      return;
    }
    closeAddModal();
    loadInventory();
  } catch (e) {
    err.textContent = 'Network error — is the server running?';
    err.classList.remove('hidden');
  }
}

// ── Price Lookup ──────────────────────────────────────────────────────────

document.addEventListener('keydown', e => {
  if (e.key === 'Enter' && document.getElementById('lookup-input') === document.activeElement) {
    doLookup();
  }
});

async function doLookup() {
  const query = document.getElementById('lookup-input').value.trim();
  if (!query) return;

  const out = document.getElementById('lookup-result');
  out.innerHTML = '<p class="muted">Searching…</p>';

  try {
    const res = await fetch(`/api/prices/${encodeURIComponent(query)}`);
    if (!res.ok) {
      out.innerHTML = `<p class="muted">Item not found: "${escHtml(query)}"</p>`;
      return;
    }
    const data = await res.json();

    const rows = data.hubs.map(h => {
      if (h.error) return `<tr><td>${h.region}</td><td colspan="4" class="muted">Error: ${escHtml(h.error)}</td></tr>`;
      return `<tr>
        <td>${h.region}</td>
        <td class="num">${h.lowest_sell !== null ? fmtIsk(h.lowest_sell) : '—'}</td>
        <td class="num muted">${h.sell_volume !== null ? fmtNum(h.sell_volume) : '—'}</td>
        <td class="num">${h.highest_buy !== null ? fmtIsk(h.highest_buy) : '—'}</td>
        <td class="num muted">${h.buy_volume !== null ? fmtNum(h.buy_volume) : '—'}</td>
      </tr>`;
    }).join('');

    out.innerHTML = `
      <div class="lookup-card">
        <h2>${escHtml(data.item_name)}</h2>
        <p class="lookup-meta">Type ID: ${data.type_id} &nbsp;·&nbsp; Volume: ${data.volume_m3} m³</p>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Hub</th>
                <th class="num">Lowest Sell</th>
                <th class="num">Sell Vol</th>
                <th class="num">Highest Buy</th>
                <th class="num">Buy Vol</th>
              </tr>
            </thead>
            <tbody>${rows}</tbody>
          </table>
        </div>
      </div>`;
  } catch (e) {
    out.innerHTML = '<p class="muted">Error contacting server.</p>';
  }
}

// ── Utilities ─────────────────────────────────────────────────────────────

function fmtIsk(n) {
  if (n === null || n === undefined) return '—';
  const abs = Math.abs(n);
  let str;
  if (abs >= 1e12)      str = (n / 1e12).toFixed(2) + ' T';
  else if (abs >= 1e9)  str = (n / 1e9).toFixed(2) + ' B';
  else if (abs >= 1e6)  str = (n / 1e6).toFixed(2) + ' M';
  else if (abs >= 1e3)  str = (n / 1e3).toFixed(1) + ' K';
  else                  str = n.toFixed(2);
  return str + ' ISK';
}

function fmtNum(n) {
  if (n === null || n === undefined) return '—';
  return n.toLocaleString();
}

function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// ── Character Tracking ────────────────────────────────────────────────────

async function loadCharacterStatus() {
  try {
    const res = await fetch('/api/character/status');
    if (!res.ok) return;
    const data = await res.json();
    
    // Update header badge
    const badge = document.getElementById('char-status');
    if (badge) {
      const online = data.online?.online ? '🟢' : '🔴';
      badge.textContent = `${online} ${data.character_name}`;
    }
    
    // Update location
    const loc = data.location;
    document.getElementById('char-location').innerHTML = `
      <strong>${escHtml(loc.solar_system_name)}</strong><br>
      ${loc.station_name || loc.structure_name || 'In space'}
    `;
    
    // Update ship
    const ship = data.ship;
    document.getElementById('char-ship').innerHTML = `
      <strong>${escHtml(ship.ship_type_name)}</strong><br>
      ${escHtml(ship.ship_name)}
    `;
    
    // Update wallet
    document.getElementById('char-wallet').innerHTML = `
      <strong>${fmtIsk(data.wallet.balance)}</strong>
    `;
    
    // Update online
    const lastLogin = data.online?.last_login ? new Date(data.online.last_login).toLocaleString() : '—';
    document.getElementById('char-online').innerHTML = `
      ${data.online?.online ? '<span style="color: green">● Online</span>' : '<span style="color: gray">○ Offline</span>'}<br>
      Last login: ${lastLogin}
    `;
    
    // Load transactions and orders
    loadCharacterTransactions();
    loadCharacterOrders();
  } catch (e) {
    console.error('Failed to load character status:', e);
  }
}

async function loadCharacterTransactions() {
  try {
    const res = await fetch('/api/character/transactions?limit=20');
    if (!res.ok) return;
    const data = await res.json();
    
    const tbody = document.getElementById('char-transactions-tbody');
    if (!data.transactions || !data.transactions.length) {
      tbody.innerHTML = '<tr><td colspan="6" class="muted center">No recent transactions</td></tr>';
      return;
    }
    
    tbody.innerHTML = data.transactions.map(t => {
      const date = new Date(t.date).toLocaleString();
      const type = t.is_buy ? 'BUY' : 'SELL';
      const typeClass = t.is_buy ? 'profit-neg' : 'profit-pos';
      return `
        <tr>
          <td>${date}</td>
          <td>${escHtml(t.item_name)}</td>
          <td class="${typeClass}">${type}</td>
          <td class="num">${fmtNum(t.quantity)}</td>
          <td class="num">${fmtIsk(t.unit_price)}</td>
          <td class="num">${fmtIsk(t.total_value)}</td>
        </tr>`;
    }).join('');
  } catch (e) {
    console.error('Failed to load transactions:', e);
  }
}

async function loadCharacterOrders() {
  try {
    const res = await fetch('/api/character/orders');
    if (!res.ok) return;
    const data = await res.json();
    
    const tbody = document.getElementById('char-orders-tbody');
    if (!data.orders || !data.orders.length) {
      tbody.innerHTML = '<tr><td colspan="7" class="muted center">No active orders</td></tr>';
      return;
    }
    
    tbody.innerHTML = data.orders.map(o => {
      const type = o.is_buy_order ? 'BUY' : 'SELL';
      const typeClass = o.is_buy_order ? 'profit-neg' : 'profit-pos';
      return `
        <tr>
          <td>${escHtml(o.item_name)}</td>
          <td class="${typeClass}">${type}</td>
          <td class="num">${fmtIsk(o.price)}</td>
          <td class="num">${fmtNum(o.volume_remain)}</td>
          <td class="num">${fmtNum(o.volume_total)}</td>
          <td>${o.duration} days</td>
          <td>${escHtml(o.state)}</td>
        </tr>`;
    }).join('');
  } catch (e) {
    console.error('Failed to load orders:', e);
  }
}

// ── Wormhole Tracking ─────────────────────────────────────────────────────

async function loadWormholes() {
  loadWHConnections();
  loadWHHistory();
}

async function loadWHConnections() {
  try {
    const res = await fetch('/api/wormholes/connections');
    if (!res.ok) return;
    const data = await res.json();
    
    const tbody = document.getElementById('wh-connections-tbody');
    if (!data.connections || !data.connections.length) {
      tbody.innerHTML = '<tr><td colspan="8" class="muted center">No active connections</td></tr>';
      return;
    }
    
    tbody.innerHTML = data.connections.map(c => {
      const lastSeen = new Date(c.last_seen * 1000).toLocaleString();
      return `
        <tr>
          <td>${escHtml(c.source_system_name)}</td>
          <td>→</td>
          <td>${escHtml(c.dest_system_name)}</td>
          <td>${escHtml(c.wh_type)}</td>
          <td>${escHtml(c.mass_remaining)}</td>
          <td>${escHtml(c.time_remaining)}</td>
          <td>${lastSeen}</td>
          <td>
            <button class="btn btn-sm" onclick="expireWHConnection(${c.id})">Expire</button>
          </td>
        </tr>`;
    }).join('');
  } catch (e) {
    console.error('Failed to load WH connections:', e);
  }
}

async function loadWHHistory() {
  try {
    const res = await fetch('/api/wormholes/history?limit=20');
    if (!res.ok) return;
    const data = await res.json();
    
    const tbody = document.getElementById('wh-history-tbody');
    if (!data.history || !data.history.length) {
      tbody.innerHTML = '<tr><td colspan="3" class="muted center">No jump history</td></tr>';
      return;
    }
    
    tbody.innerHTML = data.history.map(h => {
      const time = new Date(h.timestamp * 1000).toLocaleString();
      return `
        <tr>
          <td>${escHtml(h.system_name)}</td>
          <td>${time}</td>
          <td>${escHtml(h.notes || '—')}</td>
        </tr>`;
    }).join('');
  } catch (e) {
    console.error('Failed to load WH history:', e);
  }
}

async function expireWHConnection(connId) {
  if (!confirm('Mark this connection as expired?')) return;
  await fetch(`/api/wormholes/connection/${connId}`, { method: 'DELETE' });
  loadWHConnections();
}

function openAddWHModal() {
  document.getElementById('add-wh-modal').classList.remove('hidden');
  document.getElementById('wh-source').focus();
}

function closeAddWHModal() {
  document.getElementById('add-wh-modal').classList.add('hidden');
  ['wh-source', 'wh-dest', 'wh-type'].forEach(id => document.getElementById(id).value = '');
  document.getElementById('wh-mass').value = 'Stable';
  document.getElementById('wh-time').value = 'Fresh';
  const err = document.getElementById('add-wh-error');
  if (err) {
    err.textContent = '';
    err.classList.add('hidden');
  }
}

async function submitAddWH() {
  const source = parseInt(document.getElementById('wh-source').value, 10);
  const dest = parseInt(document.getElementById('wh-dest').value, 10);
  const type = document.getElementById('wh-type').value.trim();
  const mass = document.getElementById('wh-mass').value;
  const time = document.getElementById('wh-time').value;
  const err = document.getElementById('add-wh-error');

  if (!source || !dest || !type) {
    err.textContent = 'Source, destination, and WH type are required.';
    err.classList.remove('hidden');
    return;
  }

  try {
    const res = await fetch('/api/wormholes/connection', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        source_system_id: source,
        dest_system_id: dest,
        wh_type: type,
        mass_remaining: mass,
        time_remaining: time,
      }),
    });
    if (!res.ok) {
      const d = await res.json();
      err.textContent = d.error || `Error ${res.status}`;
      err.classList.remove('hidden');
      return;
    }
    closeAddWHModal();
    loadWHConnections();
  } catch (e) {
    err.textContent = 'Network error — is the server running?';
    err.classList.remove('hidden');
  }
}

// ── Twitch Integration ────────────────────────────────────────────────────

async function updateTwitchStatus() {
  try {
    const res = await fetch('/api/twitch/status');
    if (!res.ok) return;
    const data = await res.json();
    
    const badge = document.getElementById('twitch-status');
    if (badge) {
      if (data.live) {
        badge.textContent = '🔴 LIVE';
        badge.style.color = 'red';
      } else {
        badge.textContent = '⚫ Offline';
        badge.style.color = 'gray';
      }
    }
  } catch (e) {
    console.error('Failed to load Twitch status:', e);
  }
}
