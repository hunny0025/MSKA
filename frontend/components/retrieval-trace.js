/**
 * C2 — retrieval-trace Web Component
 *
 * Usage:
 *   <retrieval-trace project-id="proj_abc"></retrieval-trace>
 *
 * Renders a query input that fires a streaming trace and animates each
 * pipeline stage (retrieval → rerank → confidence → answer) live.
 */
class RetrievalTrace extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._eventSource = null;
    this._state = { stage: 'idle', raw: [], reranked: [], conf: null, answer: null };
  }

  connectedCallback() { this.render(); this._bind(); }
  disconnectedCallback() { this._closeSSE(); }

  get projectId() { return this.getAttribute('project-id') || ''; }

  render() {
    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          font-family: 'Inter', system-ui, sans-serif;
          color: #e2e8f0;
        }

        /* Query bar */
        .query-bar {
          display: flex;
          gap: 10px;
          margin-bottom: 24px;
        }
        .query-input {
          flex: 1;
          padding: 12px 16px;
          background: rgba(255,255,255,0.05);
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 10px;
          color: #e2e8f0;
          font-size: 0.92rem;
          outline: none;
          transition: border-color 0.2s;
        }
        .query-input:focus { border-color: #63b3ed; }

        .trace-btn {
          padding: 12px 22px;
          border-radius: 10px;
          background: linear-gradient(135deg, #3182ce, #63b3ed);
          color: #fff;
          font-weight: 700;
          font-size: 0.9rem;
          border: none;
          cursor: pointer;
          white-space: nowrap;
          transition: opacity 0.2s, transform 0.15s;
        }
        .trace-btn:disabled { opacity: 0.4; cursor: not-allowed; }
        .trace-btn:not(:disabled):hover { opacity: 0.88; transform: translateY(-1px); }

        /* Pipeline stages */
        .pipeline {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 12px;
          margin-bottom: 24px;
        }

        .stage-card {
          padding: 14px 16px;
          border-radius: 12px;
          background: rgba(255,255,255,0.03);
          border: 1px solid rgba(255,255,255,0.06);
          transition: border-color 0.3s, background 0.3s;
        }
        .stage-card.active {
          border-color: #63b3ed;
          background: rgba(99,179,237,0.06);
        }
        .stage-card.done {
          border-color: #48bb78;
          background: rgba(72,187,120,0.05);
        }

        .stage-icon { font-size: 1.4rem; margin-bottom: 6px; }
        .stage-name {
          font-size: 0.8rem;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.06em;
          color: #4a5568;
          margin-bottom: 4px;
          transition: color 0.3s;
        }
        .stage-card.active .stage-name { color: #63b3ed; }
        .stage-card.done  .stage-name { color: #68d391; }

        .stage-detail { font-size: 0.78rem; color: #718096; min-height: 18px; }

        /* Spinner */
        .spin {
          display: inline-block;
          width: 12px; height: 12px;
          border: 2px solid rgba(99,179,237,0.2);
          border-top-color: #63b3ed;
          border-radius: 50%;
          animation: spin 0.7s linear infinite;
          vertical-align: middle;
          margin-right: 4px;
        }
        @keyframes spin { to { transform: rotate(360deg); } }

        /* Chunk panels */
        .section-title {
          font-size: 0.85rem;
          font-weight: 700;
          color: #718096;
          text-transform: uppercase;
          letter-spacing: 0.06em;
          margin: 20px 0 10px;
        }

        .chunks-grid {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .chunk-card {
          padding: 12px 14px;
          border-radius: 10px;
          background: rgba(255,255,255,0.03);
          border: 1px solid rgba(255,255,255,0.06);
          cursor: pointer;
          transition: background 0.15s, border-color 0.15s;
        }
        .chunk-card:hover { background: rgba(255,255,255,0.06); border-color: rgba(255,255,255,0.12); }

        .chunk-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 6px;
        }
        .chunk-id { font-size: 0.72rem; color: #4a5568; font-family: monospace; }
        .chunk-score {
          font-size: 0.78rem;
          font-weight: 700;
          padding: 2px 8px;
          border-radius: 999px;
        }
        .chunk-text { font-size: 0.8rem; color: #a0aec0; line-height: 1.5; }

        /* Confidence bar */
        .conf-bar-wrap {
          margin: 16px 0;
          padding: 14px 16px;
          border-radius: 12px;
          background: rgba(255,255,255,0.03);
          border: 1px solid rgba(255,255,255,0.06);
        }
        .conf-label {
          display: flex;
          justify-content: space-between;
          font-size: 0.82rem;
          color: #718096;
          margin-bottom: 8px;
        }
        .conf-score { font-weight: 700; font-size: 1rem; }
        .conf-track {
          height: 6px;
          background: rgba(255,255,255,0.07);
          border-radius: 999px;
          overflow: hidden;
        }
        .conf-fill {
          height: 100%;
          border-radius: 999px;
          transition: width 0.6s cubic-bezier(0.4,0,0.2,1);
        }
        .abstain-badge {
          margin-top: 8px;
          font-size: 0.78rem;
          color: #f6ad55;
          font-weight: 600;
        }

        /* Answer */
        .answer-box {
          margin-top: 20px;
          padding: 18px 20px;
          border-radius: 14px;
          background: rgba(255,255,255,0.04);
          border: 1px solid rgba(255,255,255,0.08);
          font-size: 0.9rem;
          line-height: 1.7;
          color: #e2e8f0;
          white-space: pre-wrap;
        }
      </style>

      <div class="query-bar">
        <input class="query-input" id="query-input" placeholder="Ask a question to trace retrieval…" />
        <button class="trace-btn" id="trace-btn">⚡ Trace</button>
      </div>

      <div class="pipeline" id="pipeline">
        ${[
          { id: 'retrieve',   icon: '🔎', name: 'Retrieval'  },
          { id: 'rerank',     icon: '⚖️', name: 'Reranking'  },
          { id: 'confidence', icon: '📊', name: 'Confidence' },
          { id: 'generate',   icon: '🤖', name: 'Generation' },
        ].map(s => `
          <div class="stage-card" data-stage="${s.id}">
            <div class="stage-icon">${s.icon}</div>
            <div class="stage-name">${s.name}</div>
            <div class="stage-detail" id="stage-${s.id}">Waiting…</div>
          </div>
        `).join('')}
      </div>

      <div id="chunks-section" style="display:none">
        <div class="section-title">Retrieved Chunks</div>
        <div class="chunks-grid" id="raw-chunks"></div>
        <div class="section-title" style="margin-top:16px">Reranked Chunks</div>
        <div class="chunks-grid" id="reranked-chunks"></div>
      </div>

      <div id="conf-section" style="display:none">
        <div class="section-title">Confidence</div>
        <div class="conf-bar-wrap">
          <div class="conf-label">
            <span>Retrieval Confidence</span>
            <span class="conf-score" id="conf-score">—</span>
          </div>
          <div class="conf-track">
            <div class="conf-fill" id="conf-fill" style="width:0%"></div>
          </div>
          <div class="abstain-badge" id="abstain-badge" style="display:none">
            ⚠️ Low confidence — AI call skipped
          </div>
        </div>
      </div>

      <div id="answer-section" style="display:none">
        <div class="section-title">Answer</div>
        <div class="answer-box" id="answer-box"></div>
      </div>
    `;
  }

  _bind() {
    this.shadowRoot.getElementById('trace-btn').addEventListener('click', () => this._startTrace());
    this.shadowRoot.getElementById('query-input').addEventListener('keydown', (e) => {
      if (e.key === 'Enter') this._startTrace();
    });
  }

  _startTrace() {
    const query = this.shadowRoot.getElementById('query-input').value.trim();
    if (!query || !this.projectId) return;

    this._closeSSE();
    this._reset();

    const btn = this.shadowRoot.getElementById('trace-btn');
    btn.disabled = true;
    btn.textContent = '…';

    const token = localStorage.getItem('access_token') || '';
    const url = `/api/v1/projects/${this.projectId}/trace/stream?query=${encodeURIComponent(query)}&token=${encodeURIComponent(token)}`;

    this._eventSource = new EventSource(url);

    const handlers = {
      retrieving:        (d) => this._onRetrieving(d),
      retrieved:         (d) => this._onRetrieved(d),
      reranking:         (d) => this._onReranking(d),
      reranked:          (d) => this._onReranked(d),
      confidence:        (d) => this._onConfidenceStart(d),
      confidence_result: (d) => this._onConfidenceResult(d),
      generating:        (d) => this._onGenerating(d),
      done:              (d) => this._onDone(d),
    };

    for (const [evt, fn] of Object.entries(handlers)) {
      this._eventSource.addEventListener(evt, (e) => {
        try { fn(JSON.parse(e.data)); } catch (_) {}
      });
    }

    this._eventSource.onerror = () => {
      btn.disabled = false;
      btn.textContent = '⚡ Trace';
      this._closeSSE();
    };
  }

  _closeSSE() {
    if (this._eventSource) { this._eventSource.close(); this._eventSource = null; }
  }

  _reset() {
    ['retrieve','rerank','confidence','generate'].forEach(id => {
      const card = this.shadowRoot.querySelector(`[data-stage="${id}"]`);
      card.classList.remove('active','done');
      this.shadowRoot.getElementById(`stage-${id}`).innerHTML = 'Waiting…';
    });
    this.shadowRoot.getElementById('raw-chunks').innerHTML = '';
    this.shadowRoot.getElementById('reranked-chunks').innerHTML = '';
    this.shadowRoot.getElementById('chunks-section').style.display = 'none';
    this.shadowRoot.getElementById('conf-section').style.display = 'none';
    this.shadowRoot.getElementById('answer-section').style.display = 'none';
    this.shadowRoot.getElementById('conf-fill').style.width = '0%';
    this.shadowRoot.getElementById('abstain-badge').style.display = 'none';
  }

  _setStageActive(id, html) {
    const card = this.shadowRoot.querySelector(`[data-stage="${id}"]`);
    card.classList.add('active');
    this.shadowRoot.getElementById(`stage-${id}`).innerHTML = `<span class="spin"></span>${html}`;
  }
  _setStagesDone(...ids) {
    ids.forEach(id => {
      const card = this.shadowRoot.querySelector(`[data-stage="${id}"]`);
      card.classList.remove('active');
      card.classList.add('done');
    });
  }

  _onRetrieving(d) { this._setStageActive('retrieve', d.message); }

  _onRetrieved(d) {
    this._setStagesDone('retrieve');
    this.shadowRoot.getElementById('stage-retrieve').textContent = `${d.count} chunks found`;
    this._renderChunks('raw-chunks', d.chunks);
    this.shadowRoot.getElementById('chunks-section').style.display = 'block';
  }

  _onReranking(d) { this._setStageActive('rerank', d.message); }

  _onReranked(d) {
    this._setStagesDone('rerank');
    this.shadowRoot.getElementById('stage-rerank').textContent = `${d.count} chunks reranked`;
    this._renderChunks('reranked-chunks', d.chunks);
  }

  _onConfidenceStart(d) { this._setStageActive('confidence', d.message); }

  _onConfidenceResult(d) {
    this._setStagesDone('confidence');
    const score = d.score ?? 0;
    const pct = Math.round(score * 100);
    this.shadowRoot.getElementById('stage-confidence').textContent = `${pct}%`;
    this.shadowRoot.getElementById('conf-score').textContent = `${pct}%`;
    const fill = this.shadowRoot.getElementById('conf-fill');
    fill.style.width = pct + '%';
    fill.style.background = score >= 0.65 ? '#48bb78' : '#f6ad55';
    this.shadowRoot.getElementById('conf-section').style.display = 'block';
    if (d.should_abstain) {
      this.shadowRoot.getElementById('abstain-badge').style.display = 'block';
    }
  }

  _onGenerating(d) {
    this._setStageActive('generate', d.message);
    if (!d.ai_called) this._setStagesDone('generate');
  }

  _onDone(d) {
    this._setStagesDone('generate');
    this.shadowRoot.getElementById('stage-generate').textContent = d.should_abstain ? 'Skipped' : 'Done';
    const answerBox = this.shadowRoot.getElementById('answer-box');
    answerBox.textContent = d.answer;
    this.shadowRoot.getElementById('answer-section').style.display = 'block';

    const btn = this.shadowRoot.getElementById('trace-btn');
    btn.disabled = false;
    btn.textContent = '⚡ Trace';
    this._closeSSE();
  }

  _renderChunks(containerId, chunks) {
    const container = this.shadowRoot.getElementById(containerId);
    container.innerHTML = '';
    chunks.forEach(chunk => {
      const score = chunk.score ?? 0;
      const scoreColor = score >= 0.8 ? '#68d391' : score >= 0.6 ? '#f6e05e' : '#fc8181';
      const card = document.createElement('div');
      card.className = 'chunk-card';
      card.innerHTML = `
        <div class="chunk-header">
          <span class="chunk-id">${(chunk.id || '').slice(0, 12)}…</span>
          <span class="chunk-score" style="background:${scoreColor}20;color:${scoreColor}">
            ${(score * 100).toFixed(1)}%
          </span>
        </div>
        <div class="chunk-text">${this._esc(chunk.text || '')}</div>
      `;
      container.appendChild(card);
    });
  }

  _esc(s) {
    return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  }
}

customElements.define('retrieval-trace', RetrievalTrace);
