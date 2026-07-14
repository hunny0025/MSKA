/**
 * Maruti Suzuki Knowledge Assistant — Admin Console Component
 */

import apiClient from '../../shared/api/apiClient.js';
import AppStore from '../../shared/store/AppStore.js';
import MsToast from '../../shared/components/MsToast.js';

class AdminView extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this.activeTab = 'quarantine'; // quarantine, audit, feedback
    
    this.quarantinedDocs = [];
    this.auditLogs = [];
    this.feedbackRecords = [];
    
    this.userRole = '';
  }

  connectedCallback() {
    const auth = AppStore.getState('auth');
    if (!auth || !auth.isAuthenticated) {
      this.renderAccessDenied();
      return;
    }
    
    this.userRole = auth.user.role;
    if (this.userRole !== 'platform_admin' && this.userRole !== 'auditor') {
      this.renderAccessDenied();
      return;
    }

    // Default to audit log tab if auditor (since quarantine is platform_admin only)
    if (this.userRole === 'auditor') {
      this.activeTab = 'audit';
    }

    this.loadActiveTabData();
  }

  async loadActiveTabData() {
    try {
      if (this.activeTab === 'quarantine' && this.userRole === 'platform_admin') {
        this.quarantinedDocs = await apiClient.get('/admin/quarantine');
      } else if (this.activeTab === 'audit') {
        this.auditLogs = await apiClient.get('/admin/audit-logs');
      } else if (this.activeTab === 'feedback') {
        this.feedbackRecords = await apiClient.get('/admin/feedback');
      }
      this.render();
      this.setupListeners();
    } catch (err) {
      console.error(err);
      MsToast.show(err.message || 'Failed to retrieve admin records', 'danger');
      this.render();
    }
  }

  setupListeners() {
    // Tab switching
    this.shadowRoot.querySelectorAll('.tab-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        this.activeTab = e.target.getAttribute('data-tab');
        this.loadActiveTabData();
      });
    });

    // Quarantine approvals
    this.shadowRoot.querySelectorAll('.btn-approve').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const docId = e.currentTarget.getAttribute('data-id');
        e.currentTarget.setAttribute('loading', '');
        try {
          await apiClient.post(`/admin/quarantine/${docId}/approve`, {});
          MsToast.show('Document approved and indexing started!', 'success');
          this.loadActiveTabData();
        } catch (err) {
          MsToast.show(err.message || 'Approval action failed', 'danger');
          e.currentTarget.removeAttribute('loading');
        }
      });
    });

    // Quarantine rejections
    this.shadowRoot.querySelectorAll('.btn-reject').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const docId = e.currentTarget.getAttribute('data-id');
        e.currentTarget.setAttribute('loading', '');
        try {
          await apiClient.post(`/admin/quarantine/${docId}/reject`, {});
          MsToast.show('Document permanently deleted from quarantine', 'success');
          this.loadActiveTabData();
        } catch (err) {
          MsToast.show(err.message || 'Rejection action failed', 'danger');
          e.currentTarget.removeAttribute('loading');
        }
      });
    });
  }

  renderAccessDenied() {
    this.shadowRoot.innerHTML = `
      <style>
        .box { padding: var(--ms-space-16); text-align:center; color: var(--ms-color-danger-500); }
      </style>
      <div class="box">
        <h3>Access Denied</h3>
        <p>You do not have required administrative credentials to access compliance consoles.</p>
      </div>
    `;
  }

  render() {
    const isAdmin = this.userRole === 'platform_admin';

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          font-family: var(--ms-font-family-sans);
        }

        .tabs-header {
          display: flex;
          border-bottom: 2px solid var(--ms-color-neutral-200);
          margin-bottom: var(--ms-space-6);
          gap: var(--ms-space-4);
        }

        .tab-btn {
          border: none;
          background: none;
          padding: var(--ms-space-2) var(--ms-space-3);
          font-size: var(--ms-font-size-sm);
          font-weight: var(--ms-font-weight-medium);
          cursor: pointer;
          color: var(--ms-text-secondary);
          border-bottom: 2px solid transparent;
          margin-bottom: -2px;
          transition: all var(--ms-transition-fast);
        }

        .tab-btn:hover {
          color: var(--ms-text-primary);
        }

        .tab-btn.active {
          color: var(--ms-color-primary-500);
          border-bottom-color: var(--ms-color-primary-500);
        }

        .card {
          background: var(--ms-surface-primary);
          border-radius: var(--ms-radius-lg);
          border: 1px solid var(--ms-color-neutral-200);
          box-shadow: var(--ms-shadow-sm);
          padding: var(--ms-space-6);
        }

        table {
          width: 100%;
          border-collapse: collapse;
          font-size: var(--ms-font-size-sm);
          text-align: left;
        }

        th {
          background-color: var(--ms-surface-secondary);
          padding: var(--ms-space-3) var(--ms-space-4);
          font-weight: var(--ms-font-weight-semibold);
          color: var(--ms-text-secondary);
          border-bottom: 1px solid var(--ms-color-neutral-200);
        }

        td {
          padding: var(--ms-space-3) var(--ms-space-4);
          border-bottom: 1px solid var(--ms-color-neutral-100);
          color: var(--ms-text-primary);
        }

        tr:hover td {
          background-color: var(--ms-surface-secondary);
        }
      </style>
      <div>
        <h3>Compliance & Admin Controls</h3>
        <p style="font-size:var(--ms-font-size-xs); color:var(--ms-text-secondary); margin-bottom:var(--ms-space-6);">Review PII quarantine flags, audit logs, and employee satisfaction scores.</p>

        <div class="tabs-header">
          ${isAdmin ? `
            <button class="tab-btn ${this.activeTab === 'quarantine' ? 'active' : ''}" data-tab="quarantine">
              PII Quarantine Manager
            </button>
          ` : ''}
          <button class="tab-btn ${this.activeTab === 'audit' ? 'active' : ''}" data-tab="audit">
            Immutable Audit Trail
          </button>
          <button class="tab-btn ${this.activeTab === 'feedback' ? 'active' : ''}" data-tab="feedback">
            User Feedback Inspection
          </button>
        </div>

        <div class="card">
          <!-- Quarantine Tab -->
          ${this.activeTab === 'quarantine' && isAdmin ? `
            <div>
              <h4 style="margin-top:0;">PII Quarantine Files Pending Review</h4>
              <table>
                <thead>
                  <tr>
                    <th>Filename</th>
                    <th>Version</th>
                    <th>Classification</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  ${this.quarantinedDocs.length === 0 ? `
                    <tr>
                      <td colspan="5" style="text-align:center; color:var(--ms-text-tertiary);">No documents currently quarantined. All safe.</td>
                    </tr>
                  ` : this.quarantinedDocs.map(d => `
                    <tr>
                      <td><strong>${d.filename}</strong></td>
                      <td>v${d.version}</td>
                      <td><ms-badge variant="danger">${d.classification}</ms-badge></td>
                      <td><span style="color:var(--ms-color-danger-500); font-weight:bold;">Quarantined (PII Alert)</span></td>
                      <td>
                        <div style="display:flex; gap:var(--ms-space-2);">
                          <ms-button variant="success" size="sm" class="btn-approve" data-id="${d.id}">Approve (Override)</ms-button>
                          <ms-button variant="danger" size="sm" class="btn-reject" data-id="${d.id}">Reject & Purge</ms-button>
                        </div>
                      </td>
                    </tr>
                  `).join('')}
                </tbody>
              </table>
            </div>
          ` : ''}

          <!-- Audit logs Tab -->
          ${this.activeTab === 'audit' ? `
            <div>
              <h4 style="margin-top:0;">Append-only Operations Activity Log</h4>
              <table>
                <thead>
                  <tr>
                    <th>Timestamp</th>
                    <th>Operator</th>
                    <th>Action</th>
                    <th>Target Type</th>
                    <th>Details</th>
                  </tr>
                </thead>
                <tbody>
                  ${this.auditLogs.length === 0 ? `
                    <tr>
                      <td colspan="5" style="text-align:center; color:var(--ms-text-tertiary);">No logged activity.</td>
                    </tr>
                  ` : this.auditLogs.map(log => `
                    <tr>
                      <td>${new Date(log.created_at).toLocaleString()}</td>
                      <td><code>${log.user_id}</code></td>
                      <td><ms-badge variant="info">${log.action}</ms-badge></td>
                      <td>${log.target_type}</td>
                      <td><span style="font-size:0.8rem; font-family:monospace;">${JSON.stringify(log.details)}</span></td>
                    </tr>
                  `).join('')}
                </tbody>
              </table>
            </div>
          ` : ''}

          <!-- User Feedback ratings Tab -->
          ${this.activeTab === 'feedback' ? `
            <div>
              <h4 style="margin-top:0;">Assistant Answer Performance Ratings</h4>
              <table>
                <thead>
                  <tr>
                    <th>Feedback ID</th>
                    <th>Score</th>
                    <th>Message Reference ID</th>
                    <th>Operator Comment</th>
                  </tr>
                </thead>
                <tbody>
                  ${this.feedbackRecords.length === 0 ? `
                    <tr>
                      <td colspan="4" style="text-align:center; color:var(--ms-text-tertiary);">No feedback submissions recorded yet.</td>
                    </tr>
                  ` : this.feedbackRecords.map(f => `
                    <tr>
                      <td><code>${f.id}</code></td>
                      <td>
                        ${f.thumbs_up 
                          ? `<span style="color:var(--ms-color-success-500); font-weight:bold;">👍 Thumbs Up</span>` 
                          : `<span style="color:var(--ms-color-danger-500); font-weight:bold;">👎 Thumbs Down</span>`
                        }
                      </td>
                      <td><code>${f.message_id}</code></td>
                      <td>${f.comment || '<span style="color:var(--ms-text-tertiary); font-style:italic;">None</span>'}</td>
                    </tr>
                  `).join('')}
                </tbody>
              </table>
            </div>
          ` : ''}
        </div>
      </div>
    `;
  }
}

customElements.define('admin-view', AdminView);
export default AdminView;
export { AdminView };
