/**
 * Maruti Suzuki Knowledge Assistant — Documents View Component
 */

import apiClient from '../../shared/api/apiClient.js';
import AppStore from '../../shared/store/AppStore.js';
import MsToast from '../../shared/components/MsToast.js';

class DocumentsView extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this.projects = [];
    this.selectedProjectId = null;
    this.documents = [];
    this.userRole = null;
  }

  connectedCallback() {
    const authState = AppStore.getState('auth');
    if (authState && authState.user) {
      this.userRole = authState.user.role_name;
    }
    this.loadProjects();
  }

  async loadProjects() {
    try {
      this.projects = await apiClient.get('/projects');
      if (this.projects.length > 0) {
        this.selectedProjectId = this.projects[0].id;
        await this.loadDocuments();
      } else {
        this.render();
      }
    } catch (err) {
      console.error(err);
      MsToast.show('Failed to load project context list', 'danger');
      this.render();
    }
  }

  async loadDocuments() {
    if (!this.selectedProjectId) return;
    try {
      this.documents = await apiClient.get(`/documents/project/${this.selectedProjectId}`);
      this.render();
      this.setupListeners();
    } catch (err) {
      console.error(err);
      MsToast.show('Failed to fetch documents for project', 'danger');
      this.render();
    }
  }

  setupListeners() {
    const projectSelect = this.shadowRoot.querySelector('#project-filter-select');
    if (projectSelect) {
      projectSelect.addEventListener('change', (e) => {
        this.selectedProjectId = e.target.value;
        this.loadDocuments();
      });
    }

    const uploadBtn = this.shadowRoot.querySelector('#upload-doc-btn');
    const dialog = this.shadowRoot.querySelector('#upload-dialog');
    if (uploadBtn && dialog) {
      uploadBtn.addEventListener('click', () => dialog.open());
    }

    const cancelBtn = this.shadowRoot.querySelector('#cancel-upload');
    if (cancelBtn && dialog) {
      cancelBtn.addEventListener('click', () => dialog.close());
    }

    const confirmBtn = this.shadowRoot.querySelector('#confirm-upload');
    if (confirmBtn && dialog) {
      confirmBtn.addEventListener('click', async () => {
        const fileInput = this.shadowRoot.querySelector('#file-input');
        const classificationSelect = this.shadowRoot.querySelector('#classification-select');
        const uploadForm = this.shadowRoot.querySelector('#upload-form');

        if (!fileInput.files[0]) {
          MsToast.show('Please select a file to upload', 'warning');
          return;
        }

        const project = this.projects.find(p => p.id === this.selectedProjectId);
        if (!project) {
          MsToast.show('Invalid project context', 'danger');
          return;
        }

        confirmBtn.setAttribute('loading', '');
        
        // Prepare multipart upload
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        formData.append('project_id', this.selectedProjectId);
        formData.append('department_id', project.department_id);
        formData.append('classification', classificationSelect.value);
        try {
          const uploadUrl = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
            ? 'http://127.0.0.1:8000/api/v1/documents/'
            : '/api/v1/documents/';

          const response = await fetch(uploadUrl, {
            method: 'POST',
            body: formData
          });

          if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Upload failed');
          }

          const doc = await response.json();
          if (doc.status === 'quarantined') {
            MsToast.show('PII pattern detected! File has been quarantined.', 'warning', 5000);
          } else {
            MsToast.show('Document uploaded and parsed successfully', 'success');
          }
          
          dialog.close();
          uploadForm.reset();
          this.loadDocuments();
        } catch (err) {
          MsToast.show(err.message || 'Ingestion failed', 'danger');
        } finally {
          confirmBtn.removeAttribute('loading');
        }
      });
    }
  }

  render() {
    const isCreator = ['platform_admin', 'project_admin', 'department_lead'].includes(this.userRole);

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          font-family: var(--ms-font-family-sans);
        }

        .card {
          background: var(--ms-surface-primary);
          border-radius: var(--ms-radius-lg);
          border: 1px solid var(--ms-color-neutral-200);
          box-shadow: var(--ms-shadow-sm);
          padding: var(--ms-space-6);
        }

        .header-bar {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: var(--ms-space-6);
        }

        .actions {
          display: flex;
          gap: var(--ms-space-3);
          align-items: center;
        }

        select {
          padding: var(--ms-space-2) var(--ms-space-4);
          border: 1px solid var(--ms-color-neutral-300);
          border-radius: var(--ms-radius-md);
          font-family: var(--ms-font-family-sans);
          font-size: var(--ms-font-size-sm);
          background-color: var(--ms-surface-primary);
          color: var(--ms-text-primary);
        }

        select:focus {
          outline: none;
          border-color: var(--ms-color-primary-500);
        }

        .form-group {
          margin-bottom: var(--ms-space-4);
          display: flex;
          flex-direction: column;
          gap: var(--ms-space-1);
        }

        label {
          font-size: var(--ms-font-size-xs);
          font-weight: var(--ms-font-weight-medium);
        }

        input[type="file"] {
          border: 1px solid var(--ms-color-neutral-300);
          padding: var(--ms-space-2);
          border-radius: var(--ms-radius-md);
        }
      </style>
      <div>
        <div class="header-bar">
          <div>
            <h3 style="margin:0; font-size:var(--ms-font-size-lg);">Document Manager</h3>
            <p style="margin:var(--ms-space-1) 0 0 0; font-size:var(--ms-font-size-xs); color:var(--ms-text-secondary);">Upload reference documentation into project spaces.</p>
          </div>
          <div class="actions">
            <select id="project-filter-select">
              ${this.projects.map(p => `
                <option value="${p.id}" ${p.id === this.selectedProjectId ? 'selected' : ''}>
                  ${p.name}
                </option>
              `).join('')}
            </select>
            ${isCreator && this.selectedProjectId ? `
              <ms-button variant="primary" id="upload-doc-btn">Upload Document</ms-button>
            ` : ''}
          </div>
        </div>

        <div class="card">
          <ms-table id="documents-table"></ms-table>
        </div>

        <ms-dialog id="upload-dialog">
          <span slot="title">Upload Document</span>
          <div>
            <form id="upload-form">
              <div class="form-group">
                <label for="file-input">File (PDF, DOCX, XLSX, PPTX, TXT, CSV)</label>
                <input type="file" id="file-input" required accept=".pdf,.docx,.xlsx,.pptx,.txt,.csv" />
              </div>
              <div class="form-group">
                <label for="classification-select">Data Classification</label>
                <select id="classification-select">
                  <option value="public">Public (Internal Public)</option>
                  <option value="internal" selected>Internal (Confidential to MSIL)</option>
                  <option value="confidential">Confidential (Restricted Division)</option>
                  <option value="restricted">Restricted (Management Only)</option>
                </select>
              </div>
            </form>
          </div>
          <div slot="footer">
            <ms-button variant="secondary" id="cancel-upload">Cancel</ms-button>
            <ms-button variant="primary" id="confirm-upload">Upload</ms-button>
          </div>
        </ms-dialog>
      </div>
    `;

    // Populate data table
    const table = this.shadowRoot.querySelector('#documents-table');
    if (table) {
      table.data = {
        columns: [
          { key: 'filename', label: 'File Name', sortable: true },
          { key: 'classification', label: 'Classification', sortable: true },
          { key: 'version', label: 'Version' },
          { key: 'status_badge', label: 'Status' }
        ],
        rows: this.documents.map(d => ({
          filename: d.filename,
          classification: d.classification.toUpperCase(),
          version: `v${d.version}`,
          status_badge: d.status === 'quarantined' 
            ? '<ms-badge variant="danger">Quarantined (PII)</ms-badge>' 
            : '<ms-badge variant="success">Approved</ms-badge>'
        }))
      };
    }
  }
}

customElements.define('documents-view', DocumentsView);
export default DocumentsView;
