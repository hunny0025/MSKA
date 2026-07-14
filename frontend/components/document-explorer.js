/**
 * D1 — document-explorer Web Component
 *
 * Usage:
 *   <document-explorer project-id="proj_abc"></document-explorer>
 *
 * Features:
 *   - Paginated document list with status badges
 *   - Status + PII filters
 *   - Expandable document detail panel with status history timeline
 *   - Chunk viewer (paginated)
 *   - Admin delete button (fires 'document-deleted' event on success)
 */
class DocumentExplorer extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._page = 1;
    this._pageSize = 20;
    this._statusFilter = '';
    this._piiOnly = false;
    this._selectedDocId = null;
    this._chunkPage = 1;
  }

  connectedCallback() {
    this.render();
    this._bind();
    this._loadDocuments();
  }

  get projectId() { return this.getAttribute('project-id') || ''; }

  static get observedAttributes() { return ['project-id']; }
  attributeChangedCallback() { this._page = 1; this._loadDocuments(); }

  // ─── CSS ──────────────────────────────────────────────────────────────────

  _css() {
    return `
      :host {
        display: block;
        font-family: 'Inter', system-ui, sans-serif;
        color: #e2e8f0;
      }

      /* Toolbar */
      .toolbar {
        display: flex;
        align-items: center;
        gap: 10px;
        flex-wrap: wrap;
        margin-bottom: 18px;
      }
      .filter-select, .filter-check-label {
        padding: 8px 12px;
        border-radius: 8px;
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        color: #e2e8f0;
        font-size: 0.82rem;
        cursor: pointer;
      }
      .filter-select { appearance: none; padding-right: 28px; }
      .filter-check-label {
        display: flex; align-items: center; gap: 6px; cursor: pointer; user-select: none;
      }

      .refresh-btn {
        margin-left: auto;
        padding: 8px 14px;
        border-radius: 8px;
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.08);
        color: #a0aec0;
        font-size: 0.82rem;
        cursor: pointer;
        transition: background 0.15s;
      }
      .refresh-btn:hover { background: rgba(255,255,255,0.1); }

      /* Table */
      .doc-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.83rem;
      }
      .doc-table th {
        text-align: left;
        padding: 8px 12px;
        color: #4a5568;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        border-bottom: 1px solid rgba(255,255,255,0.05);
        font-weight: 700;
      }
      .doc-table td {
        padding: 10px 12px;
        border-bottom: 1px solid rgba(255,255,255,0.04);
        vertical-align: middle;
      }
      .doc-table tr:hover td { background: rgba(255,255,255,0.025); }
      .doc-table tr.selected td { background: rgba(99,179,237,0.06); }

      .filename {
        color: #63b3ed;
        cursor: pointer;
        font-weight: 500;
        max-width: 200px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        display: block;
      }
      .filename:hover { text-decoration: underline; }

      /* Status badge */
      .badge {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 3px 9px;
        border-radius: 999px;
        font-size: 0.72rem;
        font-weight: 700;
      }

      /* Pagination */
      .pagination {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-top: 14px;
        justify-content: flex-end;
        font-size: 0.82rem;
        color: #718096;
      }
      .page-btn {
        padding: 5px 12px;
        border-radius: 7px;
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.07);
        color: #a0aec0;
        cursor: pointer;
        font-size: 0.8rem;
        transition: background 0.15s;
      }
      .page-btn:disabled { opacity: 0.35; cursor: not-allowed; }
      .page-btn:not(:disabled):hover { background: rgba(255,255,255,0.1); }

      /* Detail panel */
      .detail-panel {
        margin-top: 24px;
        padding: 20px;
        border-radius: 14px;
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.07);
        display: none;
      }
      .detail-panel.open { display: block; }
      .detail-title {
        font-size: 1rem;
        font-weight: 700;
        margin: 0 0 14px;
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
      .close-btn {
        background: none;
        border: none;
        color: #718096;
        cursor: pointer;
        font-size: 1.1rem;
        padding: 2px 6px;
        border-radius: 4px;
        transition: color 0.15s;
      }
      .close-btn:hover { color: #e2e8f0; }

      .meta-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
        gap: 10px;
        margin-bottom: 16px;
      }
      .meta-cell { font-size: 0.78rem; }
      .meta-label { color: #4a5568; margin-bottom: 2px; font-weight: 600; text-transform: uppercase; font-size: 0.68rem; letter-spacing: 0.05em; }
      .meta-val { color: #e2e8f0; }

      /* History timeline */
      .section-title {
        font-size: 0.78rem;
        font-weight: 700;
        color: #4a5568;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin: 16px 0 8px;
      }
      .timeline { display: flex; flex-direction: column; gap: 6px; }
      .timeline-row {
        display: flex;
        align-items: center;
        gap: 10px;
        font-size: 0.78rem;
        color: #718096;
      }
      .timeline-row .t-status {
        padding: 2px 8px;
        border-radius: 999px;
        font-size: 0.7rem;
        font-weight: 700;
      }
      .timeline-row .t-time { color: #4a5568; font-family: monospace; font-size: 0.7rem; }
      .timeline-row .t-msg  { color: #fc8181; font-size: 0.72rem; }

      /* Chunks */
      .chunk-row {
        padding: 8px 10px;
        border-radius: 7px;
        background: rgba(255,255,255,0.02);
        border: 1px solid rgba(255,255,255,0.04);
        margin-bottom: 5px;
        font-size: 0.78rem;
        color: #a0aec0;
        line-height: 1.5;
      }
      .chunk-idx { font-size: 0.68rem; color: #4a5568; margin-bottom: 3px; font-weight: 600; }

      /* Admin actions */
      .admin-bar {
        margin-top: 16px;
        display: flex;
        justify-content: flex-end;
      }
      .delete-btn {
        padding: 8px 18px;
        border-radius: 8px;
        background: rgba(252,129,129,0.1);
        border: 1px solid rgba(252,129,129,0.25);
        color: #fc8181;
        font-size: 0.82rem;
        font-weight: 600;
        cursor: pointer;
        transition: background 0.15s;
      }
      .delete-btn:hover { background: rgba(252,129,129,0.2); }

      .empty-state {
        padding: 40px;
        text-align: center;
        color: #4a5568;
        font-size: 0.88rem;
      }

      .spinner {
        display: inline-block; width: 16px; height: 16px;
        border: 2px solid rgba(255,255,255,0.15);
        border-top-color: #63b3ed;
        border-radius: 50%;
        animation: spin 0.7s linear infinite;
        vertical-align: middle; margin-right: 6px;
      }
      @keyframes spin { to { transform: rotate(360deg); } }
    `;
  }

  // ─── Render ───────────────────────────────────────────────────────────────

  render() {
    this.shadowRoot.innerHTML = `
      <style>${this._css()}</style>

      <div class="toolbar">
        <select class="filter-select" id="status-select">
          <option value="">All Statuses</option>
          ${['uploaded','extracting','scanning_pii','chunking','embedding','indexing','ready','quarantined','failed']
            .map(s => `<option value="${s}">${s}</option>`).join('')}
        </select>
        <label class="filter-check-label">
          <input type="checkbox" id="pii-check"> PII Only
        </label>
        <button class="refresh-btn" id="refresh-btn">⟳ Refresh</button>
      </div>

      <div id="table-wrap">
        <div class="empty-state"><span class="spinner"></span> Loading…</div>
      </div>

      <div class="pagination" id="pagination" style="display:none">
        <button class="page-btn" id="prev-btn">← Prev</button>
        <span id="page-info">Page 1</span>
        <button class="page-btn" id="next-btn">Next →</button>
      </div>

      <div class="detail-panel" id="detail-panel">
        <div class="detail-title">
          <span id="detail-filename">Document Detail</span>
          <button class="close-btn" id="close-detail">✕</button>
        </div>
        <div id="detail-content"></div>
      </div>
    `;
  }

  _bind() {
    this.shadowRoot.getElementById('status-select').addEventListener('change', (e) => {
      this._statusFilter = e.target.value;
      this._page = 1;
      this._loadDocuments();
    });
    this.shadowRoot.getElementById('pii-check').addEventListener('change', (e) => {
      this._piiOnly = e.target.checked;
      this._page = 1;
      this._loadDocuments();
    });
    this.shadowRoot.getElementById('refresh-btn').addEventListener('click', () => this._loadDocuments());
    this.shadowRoot.getElementById('prev-btn')?.addEventListener('click', () => { this._page--; this._loadDocuments(); });
    this.shadowRoot.getElementById('next-btn')?.addEventListener('click', () => { this._page++; this._loadDocuments(); });
    this.shadowRoot.getElementById('close-detail').addEventListener('click', () => {
      this.shadowRoot.getElementById('detail-panel').classList.remove('open');
      this._selectedDocId = null;
    });
  }

  // ─── Data ─────────────────────────────────────────────────────────────────

  async _fetch(path, opts = {}) {
    const token = localStorage.getItem('access_token') || '';
    const res = await fetch(path, {
      ...opts,
      headers: { 'Authorization': `Bearer ${token}`, ...(opts.headers || {}) },
    });
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    return res.json();
  }

  async _loadDocuments() {
    const wrap = this.shadowRoot.getElementById('table-wrap');
    wrap.innerHTML = `<div class="empty-state"><span class="spinner"></span> Loading…</div>`;

    try {
      const params = new URLSearchParams({ page: this._page, page_size: this._pageSize });
      if (this._statusFilter) params.set('status', this._statusFilter);
      if (this._piiOnly) params.set('pii_only', 'true');

      const data = await this._fetch(
        `/api/v1/projects/${this.projectId}/explorer/documents?${params}`
      );

      this._renderTable(data);
    } catch (err) {
      wrap.innerHTML = `<div class="empty-state">⚠️ Failed to load documents: ${err.message}</div>`;
    }
  }

  _renderTable(data) {
    const wrap = this.shadowRoot.getElementById('table-wrap');
    const { items, total, page, page_size } = data;

    if (!items.length) {
      wrap.innerHTML = `<div class="empty-state">No documents found.</div>`;
      this.shadowRoot.getElementById('pagination').style.display = 'none';
      return;
    }

    wrap.innerHTML = `
      <table class="doc-table">
        <thead>
          <tr>
            <th>Filename</th>
            <th>Status</th>
            <th>Classification</th>
            <th>PII</th>
            <th>Chunks</th>
            <th>Version</th>
            <th>Created</th>
          </tr>
        </thead>
        <tbody>
          ${items.map(doc => `
            <tr data-id="${doc.id}" class="${this._selectedDocId === doc.id ? 'selected' : ''}">
              <td><span class="filename" data-id="${doc.id}">${this._esc(doc.filename)}</span></td>
              <td>${this._statusBadge(doc.status)}</td>
              <td><span style="color:#a0aec0;font-size:0.8rem">${doc.classification}</span></td>
              <td>${doc.pii_flagged ? '<span style="color:#f6ad55">⚠️</span>' : '<span style="color:#68d391">✓</span>'}</td>
              <td style="color:#718096">${doc.chunk_count}</td>
              <td style="color:#718096">v${doc.version}</td>
              <td style="color:#4a5568;font-size:0.75rem;font-family:monospace">${doc.created_at ? doc.created_at.slice(0,10) : '—'}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;

    // Click filename → load detail
    wrap.querySelectorAll('.filename').forEach(el => {
      el.addEventListener('click', () => this._loadDetail(el.dataset.id));
    });

    // Pagination
    const totalPages = Math.ceil(total / page_size);
    const pagination = this.shadowRoot.getElementById('pagination');
    pagination.style.display = totalPages > 1 ? 'flex' : 'none';
    this.shadowRoot.getElementById('page-info').textContent = `Page ${page} of ${totalPages}`;
    const prev = this.shadowRoot.getElementById('prev-btn');
    const next = this.shadowRoot.getElementById('next-btn');
    if (prev) { prev.disabled = page <= 1; prev.onclick = () => { this._page--; this._loadDocuments(); }; }
    if (next) { next.disabled = page >= totalPages; next.onclick = () => { this._page++; this._loadDocuments(); }; }
  }

  async _loadDetail(docId) {
    this._selectedDocId = docId;
    const panel = this.shadowRoot.getElementById('detail-panel');
    const content = this.shadowRoot.getElementById('detail-content');
    panel.classList.add('open');
    content.innerHTML = `<div class="empty-state"><span class="spinner"></span> Loading detail…</div>`;

    try {
      const doc = await this._fetch(`/api/v1/projects/${this.projectId}/explorer/documents/${docId}`);
      this.shadowRoot.getElementById('detail-filename').textContent = doc.filename;
      this._renderDetail(doc);
    } catch (err) {
      content.innerHTML = `<div class="empty-state">⚠️ ${err.message}</div>`;
    }
  }

  _renderDetail(doc) {
    const content = this.shadowRoot.getElementById('detail-content');

    const historyHtml = (doc.history || []).map(h => `
      <div class="timeline-row">
        ${this._statusBadge(h.to_status, true)}
        <span class="t-time">${h.created_at ? h.created_at.replace('T', ' ').slice(0, 19) : '—'}</span>
        ${h.message ? `<span class="t-msg">${this._esc(h.message)}</span>` : ''}
      </div>
    `).join('') || '<span style="color:#4a5568">No history</span>';

    content.innerHTML = `
      <div class="meta-grid">
        ${[
          ['ID', doc.id],
          ['Status', this._statusBadge(doc.status)],
          ['Classification', doc.classification],
          ['PII Flagged', doc.pii_flagged ? '⚠️ Yes' : '✓ No'],
          ['Chunks', doc.chunk_count],
          ['Version', 'v' + doc.version],
          ['Uploaded By', doc.uploaded_by || '—'],
          ['Department', doc.department_id],
        ].map(([l, v]) => `
          <div class="meta-cell">
            <div class="meta-label">${l}</div>
            <div class="meta-val">${v}</div>
          </div>
        `).join('')}
      </div>

      ${doc.status_message ? `<div style="color:#fc8181;font-size:0.8rem;margin-bottom:12px">Message: ${this._esc(doc.status_message)}</div>` : ''}

      <div class="section-title">Status History</div>
      <div class="timeline" id="timeline">${historyHtml}</div>

      <div class="section-title">Chunks
        <button style="margin-left:10px;padding:3px 10px;border-radius:6px;background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.08);color:#a0aec0;font-size:0.72rem;cursor:pointer" id="load-chunks-btn">Load</button>
      </div>
      <div id="chunks-container"></div>

      <div class="admin-bar">
        <button class="delete-btn" id="delete-btn">🗑 Delete Document</button>
      </div>
    `;

    // Load chunks
    content.querySelector('#load-chunks-btn').addEventListener('click', () => this._loadChunks(doc.id));

    // Delete
    content.querySelector('#delete-btn').addEventListener('click', () => this._deleteDocument(doc.id));
  }

  async _loadChunks(docId) {
    const container = this.shadowRoot.getElementById('chunks-container');
    container.innerHTML = `<div class="empty-state"><span class="spinner"></span></div>`;

    try {
      const data = await this._fetch(
        `/api/v1/projects/${this.projectId}/explorer/documents/${docId}/chunks?page=1&page_size=10`
      );
      if (!data.items.length) {
        container.innerHTML = `<div style="color:#4a5568;font-size:0.8rem">No chunks yet.</div>`;
        return;
      }
      container.innerHTML = data.items.map(c => `
        <div class="chunk-row">
          <div class="chunk-idx">Chunk #${c.chunk_index}</div>
          ${this._esc(c.text)}
        </div>
      `).join('');

      if (data.total > 10) {
        container.innerHTML += `<div style="color:#4a5568;font-size:0.75rem;margin-top:6px">Showing 10 of ${data.total} chunks</div>`;
      }
    } catch (err) {
      container.innerHTML = `<div style="color:#fc8181;font-size:0.8rem">Failed: ${err.message}</div>`;
    }
  }

  async _deleteDocument(docId) {
    if (!confirm('Delete this document? This cannot be undone.')) return;

    try {
      await this._fetch(
        `/api/v1/projects/${this.projectId}/explorer/documents/${docId}`,
        { method: 'DELETE' }
      );
      this.shadowRoot.getElementById('detail-panel').classList.remove('open');
      this._selectedDocId = null;
      this._loadDocuments();
      this.dispatchEvent(new CustomEvent('document-deleted', {
        bubbles: true, composed: true, detail: { documentId: docId },
      }));
    } catch (err) {
      alert(`Delete failed: ${err.message}`);
    }
  }

  // ─── Helpers ──────────────────────────────────────────────────────────────

  _statusBadge(s, small = false) {
    const map = {
      uploaded:     ['#63b3ed', '📤'],
      extracting:   ['#f6e05e', '🔍'],
      scanning_pii: ['#f6e05e', '🛡️'],
      chunking:     ['#f6e05e', '✂️'],
      embedding:    ['#f6e05e', '🧠'],
      indexing:     ['#f6e05e', '📑'],
      ready:        ['#68d391', '✅'],
      quarantined:  ['#f6ad55', '⚠️'],
      failed:       ['#fc8181', '❌'],
    };
    const [color, icon] = map[s] || ['#718096', '❓'];
    return `<span class="badge" style="background:${color}18;color:${color};${small ? 'font-size:0.68rem' : ''}">${icon} ${s}</span>`;
  }

  _esc(s) {
    return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  }
}

customElements.define('document-explorer', DocumentExplorer);
