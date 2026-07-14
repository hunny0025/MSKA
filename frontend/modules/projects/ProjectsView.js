/**
 * Maruti Suzuki Knowledge Assistant — Projects View Component
 */

import apiClient from '../../shared/api/apiClient.js';
import AppStore from '../../shared/store/AppStore.js';
import MsToast from '../../shared/components/MsToast.js';

class ProjectsView extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this.projects = [];
    this.departments = [];
    this.userRole = null;
  }

  connectedCallback() {
    const authState = AppStore.getState('auth');
    if (authState && authState.user) {
      this.userRole = authState.user.role_name;
    }
    this.loadData();
  }

  async loadData() {
    try {
      this.projects = await apiClient.get('/projects');
      
      const isCreator = ['platform_admin', 'project_admin', 'department_lead'].includes(this.userRole);
      if (isCreator) {
        this.departments = await apiClient.get('/departments');
      }
      
      this.render();
      this.setupListeners();
    } catch (err) {
      console.error(err);
      MsToast.show('Failed to fetch project catalog', 'danger');
      this.renderError();
    }
  }

  setupListeners() {
    const form = this.shadowRoot.querySelector('#project-form');
    if (form) {
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const submitBtn = this.shadowRoot.querySelector('#submit-btn');
        submitBtn.setAttribute('loading', '');

        const name = this.shadowRoot.querySelector('#name').value;
        const description = this.shadowRoot.querySelector('#description').value;
        const department_id = this.shadowRoot.querySelector('#dept-select').value;

        try {
          await apiClient.post('/projects', { name, description, department_id });
          MsToast.show('Project isolation space created', 'success');
          form.reset();
          this.loadData();
        } catch (err) {
          MsToast.show(err.message || 'Failed to create project', 'danger');
        } finally {
          submitBtn.removeAttribute('loading');
        }
      });
    }
  }

  renderError() {
    this.shadowRoot.innerHTML = `
      <style>
        .error { color: var(--ms-color-danger-500); padding: var(--ms-space-4); }
      </style>
      <div class="error">Failed to load project database. Connection issue.</div>
    `;
  }

  render() {
    const isCreator = ['platform_admin', 'project_admin', 'department_lead'].includes(this.userRole);

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          font-family: var(--ms-font-family-sans);
        }

        .layout {
          display: grid;
          grid-template-columns: 1fr;
          gap: var(--ms-space-6);
        }

        @media (min-width: 768px) {
          .layout {
            grid-template-columns: ${isCreator ? '2fr 1fr' : '1fr'};
          }
        }

        .card {
          background: var(--ms-surface-primary);
          border-radius: var(--ms-radius-lg);
          border: 1px solid var(--ms-color-neutral-200);
          box-shadow: var(--ms-shadow-sm);
          padding: var(--ms-space-6);
        }

        h3 {
          margin-bottom: var(--ms-space-4);
          font-size: var(--ms-font-size-lg);
        }

        .form-group {
          margin-bottom: var(--ms-space-4);
        }

        label {
          display: block;
          font-size: var(--ms-font-size-xs);
          font-weight: var(--ms-font-weight-medium);
          margin-bottom: var(--ms-space-1);
        }

        input, textarea, select {
          width: 100%;
          padding: var(--ms-space-2) var(--ms-space-3);
          border: 1px solid var(--ms-color-neutral-300);
          border-radius: var(--ms-radius-md);
          font-family: var(--ms-font-family-sans);
          font-size: var(--ms-font-size-sm);
          box-sizing: border-box;
          background-color: var(--ms-surface-primary);
          color: var(--ms-text-primary);
        }

        input:focus, textarea:focus, select:focus {
          outline: none;
          border-color: var(--ms-color-primary-500);
          box-shadow: var(--ms-focus-ring);
        }

        .project-grid {
          display: grid;
          grid-template-columns: 1fr;
          gap: var(--ms-space-4);
        }

        @media (min-width: 576px) {
          .project-grid {
            grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
          }
        }

        .project-item {
          background-color: var(--ms-surface-secondary);
          border: 1px solid var(--ms-color-neutral-200);
          border-radius: var(--ms-radius-md);
          padding: var(--ms-space-4);
          display: flex;
          flex-direction: column;
          justify-content: space-between;
          height: 140px;
          transition: transform var(--ms-transition-fast), box-shadow var(--ms-transition-fast);
        }

        .project-item:hover {
          transform: translateY(-2px);
          box-shadow: var(--ms-shadow-md);
          border-color: var(--ms-color-primary-200);
        }

        .project-name {
          font-weight: var(--ms-font-weight-bold);
          font-size: var(--ms-font-size-sm);
          color: var(--ms-text-primary);
        }

        .project-desc {
          font-size: var(--ms-font-size-xs);
          color: var(--ms-text-secondary);
          margin-top: var(--ms-space-1);
          overflow: hidden;
          text-overflow: ellipsis;
          display: -webkit-box;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
        }

        .project-footer {
          margin-top: var(--ms-space-3);
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
      </style>
      <div class="layout">
        <div class="card">
          <h3>Projects Catalog</h3>
          <div class="project-grid">
            ${this.projects.length === 0 ? `
              <div style="color:var(--ms-text-tertiary); text-align:center; padding:var(--ms-space-10); grid-column:1/-1;">
                No isolated projects mapped to your workspace.
              </div>
            ` : this.projects.map(proj => `
              <div class="project-item">
                <div>
                  <div class="project-name">${proj.name}</div>
                  <div class="project-desc">${proj.description || 'No project scope description.'}</div>
                </div>
                <div class="project-footer">
                  <span style="font-size:var(--ms-font-size-xs); color:var(--ms-text-tertiary);">RAG Isolated</span>
                  <ms-badge variant="primary">Context Enabled</ms-badge>
                </div>
              </div>
            `).join('')}
          </div>
        </div>

        ${isCreator ? `
          <div class="card">
            <h3>Add Project Space</h3>
            <form id="project-form">
              <div class="form-group">
                <label for="name">Project Name</label>
                <input type="text" id="name" required placeholder="e.g. Dzire Facelift 2026">
              </div>
              <div class="form-group">
                <label for="description">Scope Description</label>
                <textarea id="description" rows="3" placeholder="SOPs, manuals and parts listings..."></textarea>
              </div>
              <div class="form-group">
                <label for="dept-select">Department Mapping</label>
                <select id="dept-select" required>
                  <option value="" disabled selected>Select Department</option>
                  ${this.departments.map(dept => `
                    <option value="${dept.id}">${dept.name} (${dept.code})</option>
                  `).join('')}
                </select>
              </div>
              <ms-button type="submit" variant="primary" id="submit-btn">Create Project</ms-button>
            </form>
          </div>
        ` : ''}
      </div>
    `;
  }
}

customElements.define('projects-view', ProjectsView);
export default ProjectsView;
