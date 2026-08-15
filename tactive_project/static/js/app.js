/**
 * app.js — DataCentre Allocator frontend
 *
 * Security notes:
 *   - All API data is inserted via textContent / safe DOM APIs (never innerHTML).
 *   - Frontend validation is for UX only; backend validation is authoritative.
 *
 * Architecture:
 *   api      — thin fetch wrapper with consistent error handling
 *   ui       — DOM manipulation helpers (safe)
 *   handlers — event handlers for each form / action
 *   init     — bootstrap on DOMContentLoaded
 */

'use strict';

/* ================================================================
   API layer
   ================================================================ */
const api = {
  async request(method, path, body = null) {
    const opts = {
      method,
      headers: { 'Content-Type': 'application/json' },
    };
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(path, opts);
    const data = await res.json();
    return { ok: res.ok, status: res.status, data };
  },

  get:  (path)       => api.request('GET',  path),
  post: (path, body) => api.request('POST', path, body),
  patch: (path, body) => api.request('PATCH', path, body),
  delete: (path)     => api.request('DELETE', path),
};

/* ================================================================
   UI helpers (all DOM-safe)
   ================================================================ */
const ui = {
  el: (id) => document.getElementById(id),

  setText(id, text) {
    const el = this.el(id);
    if (el) el.textContent = text;
  },

  show(id) { const e = this.el(id); if (e) e.classList.remove('hidden'); },
  hide(id) { const e = this.el(id); if (e) e.classList.add('hidden'); },
  toggle(id, show) { show ? this.show(id) : this.hide(id); },

  showFeedback(id, message, type) {
    const el = this.el(id);
    if (!el) return;
    el.textContent = message;
    el.className = `form-feedback ${type}`;
    el.classList.remove('hidden');
  },

  clearFeedback(id) {
    const el = this.el(id);
    if (!el) return;
    el.textContent = '';
    el.className = 'form-feedback hidden';
  },

  toast(message, type = 'info') {
    const t = this.el('toast');
    t.textContent = message;
    t.className = `toast ${type}`;
    clearTimeout(t._timer);
    t._timer = setTimeout(() => t.classList.add('hidden'), 3500);
  },

  badge(status) {
    const span = document.createElement('span');
    span.textContent = status;
    span.className = `badge badge-${status.toLowerCase()}`;
    return span;
  },

  resourceBar(pct) {
    const wrap = document.createElement('div');
    wrap.className = 'resource-bar-wrap';
    const bar = document.createElement('div');
    bar.className = 'resource-bar';
    if (pct >= 90) bar.classList.add('crit');
    else if (pct >= 70) bar.classList.add('warn');
    bar.style.width = `${Math.min(pct, 100)}%`;
    wrap.appendChild(bar);
    return wrap;
  },

  kv(k, v) {
    const row = document.createElement('div');
    row.className = 'result-kv';
    const key = document.createElement('span');
    key.className = 'result-k';
    key.textContent = k;
    const val = document.createElement('span');
    val.className = 'result-v';
    val.textContent = v;
    row.appendChild(key);
    row.appendChild(val);
    return row;
  },
};

/* ================================================================
   State
   ================================================================ */
let workloads = [];
let servers   = [];

/* ================================================================
   Data loaders
   ================================================================ */
async function loadDashboard() {
  const [sr, wr] = await Promise.all([
    api.get('/api/servers'),
    api.get('/api/workloads'),
  ]);

  if (sr.ok) {
    servers = sr.data.servers || [];
    ui.setText('stat-total-servers',  servers.length);
    ui.setText('stat-online-servers', servers.filter(s => s.status === 'ONLINE').length);
  }

  if (wr.ok) {
    workloads = wr.data.workloads || [];
    ui.setText('stat-total-workloads',     workloads.length);
    ui.setText('stat-allocated-workloads', workloads.filter(w => w.status === 'ALLOCATED').length);
  }
}

async function loadServers() {
  const r = await api.get('/api/servers');
  if (!r.ok) return;
  servers = r.data.servers || [];
  renderServers(servers);
}

async function loadWorkloads() {
  const r = await api.get('/api/workloads');
  if (!r.ok) return;
  workloads = r.data.workloads || [];
  renderWorkloads(workloads);
  populateWorkloadSelect(workloads);
}

async function refreshAll() {
  await loadDashboard();
  renderServers(servers);
  renderWorkloads(workloads);
  populateWorkloadSelect(workloads);
}

async function updateServerStatus(serverId, status) {
  const r = await api.patch(`/api/servers/${serverId}/status`, { status });
  if (r.ok) {
    ui.toast(`Server status updated to ${status}.`, 'success');
    await refreshAll();
  } else {
    ui.toast(r.data.message || 'Failed to update server status.', 'error');
    await refreshAll();
  }
}

async function deleteServer(serverId) {
  const r = await api.delete(`/api/servers/${serverId}`);
  if (r.ok) {
    ui.toast('Server deleted successfully.', 'success');
    await refreshAll();
  } else {
    ui.toast(r.data.message || 'Failed to delete server.', 'error');
  }
}

async function updateWorkloadResources(workloadId, cpu, ram) {
  const r = await api.patch(`/api/workloads/${workloadId}`, { cpu_required: cpu, ram_required: ram });
  if (r.ok) {
    ui.toast('Workload resources updated.', 'success');
    await refreshAll();
  } else {
    ui.toast(r.data.message || 'Failed to update workload resources.', 'error');
  }
}

async function deleteWorkload(workloadId) {
  const r = await api.delete(`/api/workloads/${workloadId}`);
  if (r.ok) {
    ui.toast('Workload deleted successfully.', 'success');
    await refreshAll();
  } else {
    ui.toast(r.data.message || 'Failed to delete workload.', 'error');
  }
}

/* ================================================================
   Renderers
   ================================================================ */
function renderServers(list) {
  const container = ui.el('servers-list');
  container.innerHTML = '';

  if (!list.length) {
    const em = document.createElement('div');
    em.className = 'empty-state';
    em.textContent = 'No servers yet. Add one above.';
    container.appendChild(em);
    return;
  }

  list.forEach(s => {
    const card = document.createElement('div');
    card.className = 'item-card';

    // Main info
    const main = document.createElement('div');
    main.className = 'item-main';
    const name = document.createElement('div');
    name.className = 'item-name';
    name.textContent = s.name;
    const meta = document.createElement('div');
    meta.className = 'item-meta';
    meta.textContent = s.server_type + ' · ';
    meta.appendChild(ui.badge(s.status));
    const idEl = document.createElement('div');
    idEl.className = 'item-id';
    idEl.textContent = 'id: ' + s.id;
    main.appendChild(name);
    main.appendChild(meta);
    main.appendChild(idEl);

    // Resources
    const res = document.createElement('div');
    res.className = 'item-resources';

    const makeBlock = (label, used, cap) => {
      const block = document.createElement('div');
      block.className = 'resource-block';
      const lbl = document.createElement('div');
      lbl.className = 'resource-label';
      lbl.textContent = label;
      const val = document.createElement('div');
      val.className = 'resource-value';
      val.textContent = `${used} / ${cap}`;
      const pct = cap > 0 ? (used / cap) * 100 : 0;
      block.appendChild(lbl);
      block.appendChild(val);
      block.appendChild(ui.resourceBar(pct));
      return block;
    };

    res.appendChild(makeBlock('CPU (cores)', s.allocated_cpu, s.cpu_capacity));
    res.appendChild(makeBlock('RAM (MB)', s.allocated_ram, s.ram_capacity));

    // Controls
    const controls = document.createElement('div');
    controls.className = 'item-controls';

    // Status select
    const statusSelect = document.createElement('select');
    statusSelect.className = 'server-status-select';
    statusSelect.dataset.id = s.id;
    statusSelect.addEventListener('change', async (e) => {
      const newStatus = e.target.value;
      if (newStatus !== s.status) {
        let warning = '';
        if (newStatus === 'OFFLINE' || newStatus === 'MAINTENANCE') {
          warning = `Warning: Setting this server to ${newStatus} will evict and re-queue all workloads assigned to it. Do you want to proceed?`;
        }
        if (warning && !confirm(warning)) {
          // Revert selection
          statusSelect.value = s.status;
          return;
        }
        await updateServerStatus(s.id, newStatus);
      }
    });

    ['ONLINE', 'OFFLINE', 'MAINTENANCE'].forEach(status => {
      const opt = document.createElement('option');
      opt.value = status;
      opt.textContent = status;
      if (s.status === status) opt.selected = true;
      statusSelect.appendChild(opt);
    });

    // Delete button
    const deleteBtn = document.createElement('button');
    deleteBtn.className = 'btn btn-ghost btn-danger btn-delete-server';
    deleteBtn.textContent = 'Delete';
    deleteBtn.addEventListener('click', async () => {
      const warning = `Warning: Permanently delete server "${s.name}"? All assigned workloads will be unassigned and re-queued. This action cannot be undone.`;
      if (confirm(warning)) {
        await deleteServer(s.id);
      }
    });

    controls.appendChild(statusSelect);
    controls.appendChild(deleteBtn);

    card.appendChild(main);
    card.appendChild(res);
    card.appendChild(controls);
    container.appendChild(card);
  });
}

function renderWorkloads(list) {
  const container = ui.el('workloads-list');
  container.innerHTML = '';

  if (!list.length) {
    const em = document.createElement('div');
    em.className = 'empty-state';
    em.textContent = 'No workloads yet. Add one above.';
    container.appendChild(em);
    return;
  }

  list.forEach(w => {
    const card = document.createElement('div');
    card.className = 'item-card';

    const main = document.createElement('div');
    main.className = 'item-main';
    const name = document.createElement('div');
    name.className = 'item-name';
    name.textContent = w.name;
    const meta = document.createElement('div');
    meta.className = 'item-meta';
    meta.textContent = 'Status: ';
    meta.appendChild(ui.badge(w.status));
    const idEl = document.createElement('div');
    idEl.className = 'item-id';
    idEl.textContent = 'id: ' + w.id;
    main.appendChild(name);
    main.appendChild(meta);
    main.appendChild(idEl);

    const res = document.createElement('div');
    res.className = 'item-resources';

    const makeBlock = (label, val) => {
      const block = document.createElement('div');
      block.className = 'resource-block';
      const lbl = document.createElement('div');
      lbl.className = 'resource-label';
      lbl.textContent = label;
      const v = document.createElement('div');
      v.className = 'resource-value';
      v.textContent = val;
      block.appendChild(lbl);
      block.appendChild(v);
      return block;
    };

    res.appendChild(makeBlock('CPU req.', w.cpu_required + ' cores'));
    res.appendChild(makeBlock('RAM req.', w.ram_required + ' MB'));

    // Controls
    const controls = document.createElement('div');
    controls.className = 'item-controls';

    // Edit button
    const editBtn = document.createElement('button');
    editBtn.className = 'btn btn-ghost btn-edit-workload';
    editBtn.textContent = 'Edit';
    editBtn.addEventListener('click', async () => {
      const cpuInput = prompt(`Edit CPU cores (1-10000) for "${w.name}":`, w.cpu_required);
      if (cpuInput === null) return;
      const cpu = parseInt(cpuInput, 10);
      
      const ramInput = prompt(`Edit RAM (MB, 1-1048576) for "${w.name}":`, w.ram_required);
      if (ramInput === null) return;
      const ram = parseInt(ramInput, 10);

      if (isNaN(cpu) || cpu < 1 || cpu > 10000 || isNaN(ram) || ram < 1 || ram > 1048576) {
        ui.toast('Invalid inputs. CPU and RAM must be valid integers within limit.', 'error');
        return;
      }
      await updateWorkloadResources(w.id, cpu, ram);
    });

    // Delete button
    const deleteBtn = document.createElement('button');
    deleteBtn.className = 'btn btn-ghost btn-danger btn-delete-workload';
    deleteBtn.textContent = 'Delete';
    deleteBtn.addEventListener('click', async () => {
      const warning = `Warning: Permanently delete workload "${w.name}"? This action cannot be undone.`;
      if (confirm(warning)) {
        await deleteWorkload(w.id);
      }
    });

    controls.appendChild(editBtn);
    controls.appendChild(deleteBtn);

    card.appendChild(main);
    card.appendChild(res);
    card.appendChild(controls);
    container.appendChild(card);
  });
}

function populateWorkloadSelect(list) {
  const sel = ui.el('alloc-workload-id');
  // Clear existing options except placeholder
  while (sel.options.length > 1) sel.remove(1);
  const pending = list.filter(w => w.status === 'PENDING');
  pending.forEach(w => {
    const opt = document.createElement('option');
    opt.value = w.id;
    // Safe: textContent equivalent for option
    opt.textContent = `${w.name}  (CPU: ${w.cpu_required}, RAM: ${w.ram_required} MB)`;
    sel.appendChild(opt);
  });
}

/* ================================================================
   Allocation result
   ================================================================ */
function showAllocationResult(type, title, details) {
  const panel  = ui.el('allocation-result');
  const header = ui.el('result-header');
  const body   = ui.el('result-body');

  header.textContent = title;
  header.className = `result-header ${type}`;

  body.innerHTML = '';
  details.forEach(([k, v]) => body.appendChild(ui.kv(k, v)));

  panel.classList.remove('hidden');
}

/* ================================================================
   Event handlers
   ================================================================ */

// --- Server form ---
function initServerForm() {
  const showBtn   = ui.el('btn-show-server-form');
  const cancelBtn = ui.el('btn-cancel-server');
  const form      = ui.el('server-form');

  showBtn.addEventListener('click', () => {
    ui.show('server-form-card');
    ui.clearFeedback('server-feedback');
    showBtn.classList.add('hidden');
  });

  cancelBtn.addEventListener('click', () => {
    ui.hide('server-form-card');
    showBtn.classList.remove('hidden');
    form.reset();
    ui.clearFeedback('server-feedback');
  });

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const name   = ui.el('server-name').value.trim();
    const type   = ui.el('server-type').value.trim() || 'general';
    const cpu    = parseInt(ui.el('server-cpu').value, 10);
    const ram    = parseInt(ui.el('server-ram').value, 10);
    const status = ui.el('server-status').value;

    if (!name) {
      ui.showFeedback('server-feedback', 'Server name is required.', 'error');
      return;
    }

    const r = await api.post('/api/servers', { name, server_type: type, cpu_capacity: cpu, ram_capacity: ram, status });

    if (r.ok) {
      ui.showFeedback('server-feedback', `Server "${name}" created successfully.`, 'success');
      form.reset();
      await refreshAll();
      ui.toast(`Server "${name}" added.`, 'success');
    } else {
      const msg = r.data.message || 'Failed to create server.';
      const det = (r.data.details || []).join(' ');
      ui.showFeedback('server-feedback', msg + (det ? ' ' + det : ''), 'error');
    }
  });
}

// --- Workload form ---
function initWorkloadForm() {
  const showBtn   = ui.el('btn-show-workload-form');
  const cancelBtn = ui.el('btn-cancel-workload');
  const form      = ui.el('workload-form');

  showBtn.addEventListener('click', () => {
    ui.show('workload-form-card');
    ui.clearFeedback('workload-feedback');
    showBtn.classList.add('hidden');
  });

  cancelBtn.addEventListener('click', () => {
    ui.hide('workload-form-card');
    showBtn.classList.remove('hidden');
    form.reset();
    ui.clearFeedback('workload-feedback');
  });

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const name = ui.el('workload-name').value.trim();
    const cpu  = parseInt(ui.el('workload-cpu').value, 10);
    const ram  = parseInt(ui.el('workload-ram').value, 10);

    if (!name) {
      ui.showFeedback('workload-feedback', 'Workload name is required.', 'error');
      return;
    }

    const r = await api.post('/api/workloads', { name, cpu_required: cpu, ram_required: ram });

    if (r.ok) {
      ui.showFeedback('workload-feedback', `Workload "${name}" created.`, 'success');
      form.reset();
      await refreshAll();
      ui.toast(`Workload "${name}" added.`, 'success');
    } else {
      const msg = r.data.message || 'Failed to create workload.';
      const det = (r.data.details || []).join(' ');
      ui.showFeedback('workload-feedback', msg + (det ? ' ' + det : ''), 'error');
    }
  });
}

// --- Allocation form ---
function initAllocationForm() {
  const form = ui.el('allocation-form');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const workloadId = ui.el('alloc-workload-id').value;

    if (!workloadId) {
      ui.toast('Please select a workload.', 'error');
      return;
    }

    ui.hide('allocation-result');
    const btn = ui.el('btn-allocate');
    btn.textContent = 'Allocating…';
    btn.disabled = true;

    const r = await api.post('/api/allocations', { workload_id: workloadId });

    btn.textContent = 'Allocate';
    btn.disabled = false;

    if (r.ok) {
      const { allocation, workload, server } = r.data;
      showAllocationResult('success', '✓ Allocation Successful', [
        ['Allocation ID',   allocation.id],
        ['Workload',        workload.name],
        ['Server',          server.name],
        ['Status',          allocation.status],
        ['CPU allocated',   `${workload.cpu_required} cores`],
        ['RAM allocated',   `${workload.ram_required} MB`],
        ['Server CPU used', `${server.allocated_cpu} / ${server.cpu_capacity} cores`],
        ['Server RAM used', `${server.allocated_ram} / ${server.ram_capacity} MB`],
      ]);
      await refreshAll();
      ui.toast('Workload allocated successfully.', 'success');
    } else {
      const msg = r.data.message || 'Allocation failed.';
      showAllocationResult('error', '✗ Allocation Failed', [
        ['Reason', msg],
        ['HTTP status', r.status],
      ]);
      ui.toast('Allocation failed: ' + msg, 'error');
    }
  });
}

/* ================================================================
   Health check
   ================================================================ */
async function checkHealth() {
  try {
    const r = await api.get('/api/health');
    const dot = ui.el('status-dot');
    const lbl = ui.el('status-label');
    if (r.ok) {
      dot.className = 'status-dot online';
      lbl.textContent = 'API online';
    } else {
      dot.className = 'status-dot offline';
      lbl.textContent = 'API error';
    }
  } catch {
    ui.el('status-dot').className = 'status-dot offline';
    ui.el('status-label').textContent = 'Cannot reach API';
  }
}

/* ================================================================
   Bootstrap
   ================================================================ */
document.addEventListener('DOMContentLoaded', async () => {
  await checkHealth();
  await refreshAll();
  initServerForm();
  initWorkloadForm();
  initAllocationForm();

  // Refresh dashboard every 30 seconds
  setInterval(async () => {
    await loadDashboard();
  }, 30_000);
});
