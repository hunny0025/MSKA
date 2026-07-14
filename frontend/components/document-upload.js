/**
 * A4 — document-upload Web Component
 *
 * Usage:
 *   <document-upload project-id="proj_abc"></document-upload>
 *
 * Fires:
 *   CustomEvent 'upload-started'  { detail: { documentId, filename } }
 *   CustomEvent 'upload-error'    { detail: { message } }
 */
class DocumentUpload extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
  }

  connectedCallback() {
    this.render();
    this._bindEvents();
  }

  get projectId() {
    return this.getAttribute('project-id') || '';
  }

  render() {
    this.shadowRoot.innerHTML = `
      <style>
        :host { display: block; font-family: 'Inter', system-ui, sans-serif; }

        .drop-zone {
          border: 2px dashed rgba(99, 179, 237, 0.5);
          border-radius: 16px;
          padding: 48px 32px;
          text-align: center;
          background: rgba(255,255,255,0.03);
          cursor: pointer;
          transition: border-color 0.25s, background 0.25s;
          position: relative;
        }
        .drop-zone.dragover {
          border-color: #63b3ed;
          background: rgba(99,179,237,0.07);
        }

        .drop-icon {
          font-size: 2.5rem;
          margin-bottom: 12px;
        }

        .drop-title {
          font-size: 1.05rem;
          font-weight: 600;
          color: #e2e8f0;
          margin: 0 0 6px;
        }
        .drop-sub {
          font-size: 0.82rem;
          color: #718096;
          margin: 0 0 20px;
        }

        .browse-btn {
          display: inline-block;
          padding: 9px 24px;
          border-radius: 8px;
          background: linear-gradient(135deg, #3182ce, #63b3ed);
          color: #fff;
          font-size: 0.9rem;
          font-weight: 600;
          cursor: pointer;
          border: none;
          transition: opacity 0.2s, transform 0.15s;
          letter-spacing: 0.01em;
        }
        .browse-btn:hover { opacity: 0.88; transform: translateY(-1px); }
        .browse-btn:active { transform: translateY(0); }

        #file-input { display: none; }

        .file-list {
          margin-top: 20px;
          display: flex;
          flex-direction: column;
          gap: 10px;
        }

        .file-row {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 10px 14px;
          background: rgba(255,255,255,0.04);
          border-radius: 10px;
          border: 1px solid rgba(255,255,255,0.06);
        }

        .file-icon { font-size: 1.4rem; flex-shrink: 0; }

        .file-name {
          flex: 1;
          font-size: 0.85rem;
          color: #e2e8f0;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .file-size {
          font-size: 0.75rem;
          color: #718096;
          white-space: nowrap;
        }

        .remove-btn {
          background: none;
          border: none;
          cursor: pointer;
          color: #fc8181;
          font-size: 1rem;
          padding: 2px 6px;
          border-radius: 4px;
          transition: background 0.15s;
          flex-shrink: 0;
        }
        .remove-btn:hover { background: rgba(252,129,129,0.12); }

        .actions {
          margin-top: 18px;
          display: flex;
          gap: 12px;
          justify-content: flex-end;
        }

        .upload-btn {
          padding: 10px 28px;
          border-radius: 9px;
          background: linear-gradient(135deg, #276749, #48bb78);
          color: #fff;
          font-size: 0.92rem;
          font-weight: 700;
          border: none;
          cursor: pointer;
          transition: opacity 0.2s, transform 0.15s;
          letter-spacing: 0.02em;
        }
        .upload-btn:disabled {
          opacity: 0.4;
          cursor: not-allowed;
          transform: none;
        }
        .upload-btn:not(:disabled):hover { opacity: 0.88; transform: translateY(-1px); }

        .clear-btn {
          padding: 10px 18px;
          border-radius: 9px;
          background: rgba(255,255,255,0.06);
          color: #a0aec0;
          font-size: 0.88rem;
          font-weight: 600;
          border: 1px solid rgba(255,255,255,0.08);
          cursor: pointer;
          transition: background 0.15s;
        }
        .clear-btn:hover { background: rgba(255,255,255,0.1); }

        .error-msg {
          margin-top: 12px;
          padding: 10px 14px;
          border-radius: 8px;
          background: rgba(252,129,129,0.1);
          border: 1px solid rgba(252,129,129,0.25);
          color: #fc8181;
          font-size: 0.83rem;
          display: none;
        }
        .error-msg.visible { display: block; }

        .spinner {
          display: inline-block;
          width: 14px; height: 14px;
          border: 2px solid rgba(255,255,255,0.3);
          border-top-color: #fff;
          border-radius: 50%;
          animation: spin 0.7s linear infinite;
          vertical-align: middle;
          margin-right: 6px;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
      </style>

      <div class="drop-zone" id="drop-zone">
        <div class="drop-icon">📁</div>
        <p class="drop-title">Drag &amp; drop files here</p>
        <p class="drop-sub">PDF, DOCX, XLSX, PPTX, CSV, TXT · Max 50 MB</p>
        <button class="browse-btn" id="browse-btn">Browse Files</button>
        <input type="file" id="file-input" multiple accept=".pdf,.docx,.xlsx,.xls,.pptx,.csv,.txt">
      </div>

      <div class="file-list" id="file-list"></div>
      <div class="error-msg" id="error-msg"></div>

      <div class="actions" id="actions" style="display:none;">
        <button class="clear-btn" id="clear-btn">Clear</button>
        <button class="upload-btn" id="upload-btn">Upload</button>
      </div>
    `;
  }

  _bindEvents() {
    const dropZone   = this.shadowRoot.getElementById('drop-zone');
    const browseBtn  = this.shadowRoot.getElementById('browse-btn');
    const fileInput  = this.shadowRoot.getElementById('file-input');
    const clearBtn   = this.shadowRoot.getElementById('clear-btn');
    const uploadBtn  = this.shadowRoot.getElementById('upload-btn');

    this._files = [];

    browseBtn.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', () => this._addFiles([...fileInput.files]));

    dropZone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropZone.classList.add('dragover');
    });
    dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
    dropZone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropZone.classList.remove('dragover');
      this._addFiles([...e.dataTransfer.files]);
    });

    clearBtn.addEventListener('click', () => this._clearFiles());
    uploadBtn.addEventListener('click', () => this._upload());
  }

  _addFiles(newFiles) {
    const ACCEPTED = ['.pdf','.docx','.xlsx','.xls','.pptx','.csv','.txt'];
    const MAX_BYTES = 50 * 1024 * 1024;

    const filtered = newFiles.filter(f => {
      const ext = '.' + f.name.split('.').pop().toLowerCase();
      return ACCEPTED.includes(ext) && f.size <= MAX_BYTES;
    });

    this._files = [...this._files, ...filtered];
    this._renderFileList();
  }

  _renderFileList() {
    const list    = this.shadowRoot.getElementById('file-list');
    const actions = this.shadowRoot.getElementById('actions');
    list.innerHTML = '';

    this._files.forEach((file, idx) => {
      const ext  = file.name.split('.').pop().toLowerCase();
      const icon = { pdf: '📄', docx: '📝', xlsx: '📊', xls: '📊', pptx: '📊', csv: '📋', txt: '🗒️' }[ext] || '📁';
      const size = file.size > 1024*1024
        ? (file.size/1024/1024).toFixed(1) + ' MB'
        : Math.round(file.size/1024) + ' KB';

      const row = document.createElement('div');
      row.className = 'file-row';
      row.innerHTML = `
        <span class="file-icon">${icon}</span>
        <span class="file-name" title="${file.name}">${file.name}</span>
        <span class="file-size">${size}</span>
        <button class="remove-btn" data-idx="${idx}" title="Remove">✕</button>
      `;
      row.querySelector('.remove-btn').addEventListener('click', () => {
        this._files.splice(idx, 1);
        this._renderFileList();
      });
      list.appendChild(row);
    });

    actions.style.display = this._files.length ? 'flex' : 'none';
  }

  _clearFiles() {
    this._files = [];
    this.shadowRoot.getElementById('file-input').value = '';
    this._renderFileList();
    this._hideError();
  }

  async _upload() {
    if (!this._files.length) return;
    if (!this.projectId) {
      this._showError('No project-id attribute set on <document-upload>.');
      return;
    }

    const uploadBtn = this.shadowRoot.getElementById('upload-btn');
    uploadBtn.disabled = true;
    uploadBtn.innerHTML = '<span class="spinner"></span>Uploading…';

    this._hideError();

    const token = localStorage.getItem('access_token') || '';

    for (const file of this._files) {
      const fd = new FormData();
      fd.append('file', file);

      try {
        const res = await fetch(`/api/v1/projects/${this.projectId}/documents`, {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}` },
          body: fd,
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({ detail: res.statusText }));
          throw new Error(err.detail || 'Upload failed');
        }

        const doc = await res.json();
        this.dispatchEvent(new CustomEvent('upload-started', {
          bubbles: true,
          composed: true,
          detail: { documentId: doc.id, filename: file.name },
        }));
      } catch (err) {
        this._showError(`Failed to upload ${file.name}: ${err.message}`);
        this.dispatchEvent(new CustomEvent('upload-error', {
          bubbles: true,
          composed: true,
          detail: { message: err.message },
        }));
      }
    }

    uploadBtn.disabled = false;
    uploadBtn.innerHTML = 'Upload';
    this._clearFiles();
  }

  _showError(msg) {
    const el = this.shadowRoot.getElementById('error-msg');
    el.textContent = msg;
    el.classList.add('visible');
  }
  _hideError() {
    this.shadowRoot.getElementById('error-msg').classList.remove('visible');
  }
}

customElements.define('document-upload', DocumentUpload);
