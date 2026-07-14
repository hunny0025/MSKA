/**
 * Maruti Suzuki Knowledge Assistant — Departments View Component
 */

import apiClient from '../../shared/api/apiClient.js';
import AppStore from '../../shared/store/AppStore.js';
import MsToast from '../../shared/components/MsToast.js';

class DepartmentsView extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this.departments = [];
    this.userRole = null;
  }

  connectedCallback() {
    const authState = AppStore.getState('auth');
    if (authState && authState.user) {
      this.userRole = authState.user.role_name;
    }
    this.fetchDepartments();
  }

  async fetchDepartments() {
    try {
      this.departments = await apiClient.get('/departments');
      this.render();
      this.setupListeners();
    } catch (err) {
      console.error(err);
      MsToast.show('Failed to fetch departments', 'danger');
      this.renderError();
    }
  }

  setupListeners() {
    const form = this.shadowRoot.querySelector('#dept-form');
    if (form) {
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const submitBtn = this.shadowRoot.querySelector('#submit-btn');
        submitBtn.setAttribute('loading', '');

        const name = this.shadowRoot.querySelector('#name').value;
        const code = this.shadowRoot.querySelector('#code').value;
        const description = this.shadowRoot.querySelector('#description').value;

        try {
          await apiClient.post('/departments', { name, code, description });
          MsToast.show('Department created successfully', 'success');
          // Reset form and reload
          form.reset();
          this.fetchDepartments();
        } catch (err) {
          MsToast.show(err.message || 'Failed to create department', 'danger');
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
      <div class="error">Failed to load department records. Connection issue.</div>
    `;
  }

  render() {
    const isPlatformAdmin = this.userRole === 'platform_admin';

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
            grid-template-columns: ${isPlatformAdmin ? '2fr 1fr' : '1fr'};
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

        input, textarea {
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

        input:focus, textarea:focus {
          outline: none;
          border-color: var(--ms-color-primary-500);
          box-shadow: var(--ms-focus-ring);
        }

        .dept-list {
          display: flex;
          flex-direction: column;
          gap: var(--ms-space-3);
        }

        .dept-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: var(--ms-space-3) var(--ms-space-4);
          border: 1px solid var(--ms-color-neutral-200);
          border-radius: var(--ms-radius-md);
          transition: background-color var(--ms-transition-fast);
        }

        .dept-item:hover {
          background-color: var(--ms-color-neutral-50);
        }

        .dept-meta {
          display: flex;
          flex-direction: column;
        }

        .dept-title {
          font-weight: var(--ms-font-weight-semibold);
          font-size: var(--ms-font-size-sm);
        }

        .dept-desc {
          font-size: var(--ms-font-size-xs);
          color: var(--ms-text-secondary);
          margin-top: var(--ms-space-1);
        }
      </style>
      <div class="layout">
        <div class="card">
          <h3>Departments Directory</h3>
          <div class="dept-list">
            ${this.departments.length === 0 ? `
              <div style="color:var(--ms-text-tertiary); text-align:center; padding:var(--ms-space-8);">
                No departments registered yet.
              </div>
            ` : this.departments.map(dept => `
              <div class="dept-item">
                <div class="dept-meta">
                  <div class="dept-title">${dept.name}</div>
                  <div class="dept-desc">${dept.description || 'No description provided.'}</div>
                </div>
                <ms-badge variant="info">${dept.code}</ms-badge>
              </div>
            `).join('')}
          </div>
        </div>

        ${isPlatformAdmin ? `
          <div class="card">
            <h3>Add Department</h3>
            <form id="dept-form">
              <div class="form-group">
                <label for="name">Department Name</label>
                <input type="text" id="name" required placeholder="e.g. Quality Assurance">
              </div>
              <div class="form-group">
                <label for="code">Code</label>
                <input type="text" id="code" required placeholder="e.g. QA">
              </div>
              <div class="form-group">
                <label for="description">Description</label>
                <textarea id="description" rows="3" placeholder="SOP standard checkers..."></textarea>
              </div>
              <ms-button type="submit" variant="primary" id="submit-btn">Create</ms-button>
            </form>
          </div>
        ` : ''}
      </div>
    `;
  }
}

customElements.define('departments-view', DepartmentsView);
export default DepartmentsView;
