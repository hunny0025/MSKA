/**
 * A4 — ingestion-progress Web Component
 *
 * Usage:
 *   <ingestion-progress document-id="doc_xyz"></ingestion-progress>
 *
 * Connects to the SSE endpoint and renders a live stepper.
 * Closes the SSE stream when status is terminal (ready|quarantined|failed).
 */

const STEPS = [
  { key: 'uploaded',     label: 'Uploaded',      icon: '📤' },
  { key: 'extracting',   label: 'Extracting',     icon: '🔍' },
  { key: 'scanning_pii', label: 'Scanning PII',   icon: '🛡️' },
  { key: 'chunking',     label: 'Chunking',       icon: '✂️' },
  { key: 'embedding',    label: 'Embedding',      icon: '🧠' },
  { key: 'indexing',     label: 'Indexing',       icon: '📑' },
  { key: 'ready',        label: 'Ready',          icon: '✅' },
];

const STATUS_MAP = {
  quarantined: { label: 'Quarantined', icon: '⚠️', color: '#f6ad55' },
  failed:      { label: 'Failed',      icon: '❌', color: '#fc8181' },
};

class IngestionProgress extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._currentStatus = null;
    this._eventSource   = null;
  }

  connectedCallback() {
    this.render();
    if (this.documentId) this._connect();
  }

  disconnectedCallback() {
    this._disconnect();
  }

  static get observedAttributes() { return ['document-id']; }

  attributeChangedCallback(name, _old, value) {
    if (name === 'document-id' && value) {
      this._disconnect();
      this._currentStatus = null;
      this.render();
      this._connect();
    }
  }

  get documentId() {
    return this.getAttribute('document-id') || '';
  }

  _connect() {
    const token = localStorage.getItem('access_token') || '';
    // EventSource doesn't support custom headers; pass token as query param
    const url = `/api/v1/documents/${this.documentId}/progress?token=${encodeURIComponent(token)}`;
    this._eventSource = new EventSource(url);

    this._eventSource.addEventListener('progress', (evt) => {
      try {
        const data = JSON.parse(evt.data);
        this._currentStatus = data.status;
        this._updateStepper(data.status, data.message);
        if (data.done) this._disconnect();
      } catch (_) {}
    });

    this._eventSource.addEventListener('heartbeat', () => {/* keep alive */});

    this._eventSource.onerror = () => {
      this._showStatusBadge('Connection lost — retrying…', '#718096');
    };
  }

  _disconnect() {
    if (this._eventSource) {
      this._eventSource.close();
      this._eventSource = null;
    }
  }

  render() {
    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          font-family: 'Inter', system-ui, sans-serif;
          padding: 24px;
          background: rgba(255,255,255,0.03);
          border: 1px solid rgba(255,255,255,0.06);
          border-radius: 16px;
        }

        .header {
          display: flex;
          align-items: center;
          gap: 10px;
          margin-bottom: 28px;
        }
        .header-title {
          font-size: 1rem;
          font-weight: 700;
          color: #e2e8f0;
          margin: 0;
        }
        .doc-id {
          font-size: 0.72rem;
          color: #4a5568;
          font-family: monospace;
        }

        /* Stepper */
        .stepper {
          display: flex;
          flex-direction: column;
          gap: 0;
        }

        .step {
          display: flex;
          align-items: flex-start;
          gap: 16px;
          position: relative;
        }

        /* Connector line */
        .step:not(:last-child) .step-line {
          position: absolute;
          left: 19px;
          top: 38px;
          width: 2px;
          height: calc(100% - 14px);
          background: rgba(255,255,255,0.07);
          transition: background 0.4s;
        }
        .step.done .step-line,
        .step.active .step-line { background: rgba(99,179,237,0.35); }

        .step-icon-wrap {
          width: 40px; height: 40px;
          border-radius: 50%;
          display: flex; align-items: center; justify-content: center;
          font-size: 1.1rem;
          flex-shrink: 0;
          border: 2px solid rgba(255,255,255,0.08);
          background: rgba(255,255,255,0.04);
          transition: border-color 0.3s, background 0.3s, box-shadow 0.3s;
          position: relative;
          z-index: 1;
        }
        .step.done .step-icon-wrap {
          border-color: #48bb78;
          background: rgba(72,187,120,0.12);
        }
        .step.active .step-icon-wrap {
          border-color: #63b3ed;
          background: rgba(99,179,237,0.12);
          box-shadow: 0 0 0 4px rgba(99,179,237,0.15);
          animation: pulse 1.4s infinite;
        }

        @keyframes pulse {
          0%, 100% { box-shadow: 0 0 0 4px rgba(99,179,237,0.15); }
          50%       { box-shadow: 0 0 0 8px rgba(99,179,237,0.05); }
        }

        .step-body {
          flex: 1;
          padding: 8px 0 20px;
        }

        .step-label {
          font-size: 0.9rem;
          font-weight: 600;
          color: #718096;
          transition: color 0.3s;
        }
        .step.done  .step-label { color: #68d391; }
        .step.active .step-label { color: #63b3ed; }

        .step-msg {
          font-size: 0.75rem;
          color: #4a5568;
          margin-top: 3px;
          font-family: monospace;
        }

        /* Terminal badge */
        .status-badge {
          display: none;
          margin-top: 16px;
          padding: 10px 16px;
          border-radius: 10px;
          font-size: 0.88rem;
          font-weight: 600;
          text-align: center;
        }
        .status-badge.visible { display: block; }
      </style>

      <div class="header">
        <span style="font-size:1.3rem">⚙️</span>
        <div>
          <p class="header-title">Ingestion Progress</p>
          <span class="doc-id">${this.documentId || '…'}</span>
        </div>
      </div>

      <div class="stepper" id="stepper">
        ${STEPS.map(s => `
          <div class="step" data-step="${s.key}">
            <div class="step-line"></div>
            <div class="step-icon-wrap">${s.icon}</div>
            <div class="step-body">
              <div class="step-label">${s.label}</div>
              <div class="step-msg"></div>
            </div>
          </div>
        `).join('')}
      </div>

      <div class="status-badge" id="status-badge"></div>
    `;
  }

  _updateStepper(currentStatus, message) {
    const stepEls = this.shadowRoot.querySelectorAll('.step');
    const currentIdx = STEPS.findIndex(s => s.key === currentStatus);

    stepEls.forEach((el, idx) => {
      el.classList.remove('done', 'active');
      if (currentIdx >= 0) {
        if (idx < currentIdx) el.classList.add('done');
        if (idx === currentIdx) el.classList.add('active');
      }
      const msgEl = el.querySelector('.step-msg');
      if (msgEl) msgEl.textContent = '';
    });

    // Show message on active step
    if (currentIdx >= 0 && message) {
      const activeEl = this.shadowRoot.querySelector(`.step[data-step="${currentStatus}"] .step-msg`);
      if (activeEl) activeEl.textContent = message;
    }

    // Handle terminal statuses that aren't in the main STEPS list
    const terminal = STATUS_MAP[currentStatus];
    if (terminal) {
      this._showStatusBadge(
        `${terminal.icon} ${terminal.label}${message ? ': ' + message : ''}`,
        terminal.color,
      );
    } else if (currentStatus === 'ready') {
      this._showStatusBadge('✅ Document is ready for queries', '#68d391');
    }
  }

  _showStatusBadge(text, color) {
    const badge = this.shadowRoot.getElementById('status-badge');
    badge.textContent = text;
    badge.style.background = color + '18';
    badge.style.color = color;
    badge.style.border = `1px solid ${color}40`;
    badge.classList.add('visible');
  }
}

customElements.define('ingestion-progress', IngestionProgress);
