/**
 * Maruti Suzuki Knowledge Assistant — Notifications View Component
 */

import apiClient from '../../shared/api/apiClient.js';
import AppStore from '../../shared/store/AppStore.js';
import MsToast from '../../shared/components/MsToast.js';

class NotificationsView extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this.notifications = [];
  }

  connectedCallback() {
    this.fetchNotifications();
  }

  async fetchNotifications() {
    try {
      this.notifications = await apiClient.get('/notifications/unread');
      // Sync to global store
      AppStore.setState({ notifications: this.notifications });
      this.render();
      this.setupListeners();
    } catch (err) {
      console.error(err);
      this.render();
    }
  }

  setupListeners() {
    this.shadowRoot.querySelectorAll('.btn-read').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const nId = e.currentTarget.getAttribute('data-id');
        try {
          await apiClient.post(`/notifications/${nId}/read`, {});
          MsToast.show('Notification dismissed', 'success');
          this.fetchNotifications();
        } catch (err) {
          MsToast.show('Failed to dismiss notification', 'danger');
        }
      });
    });

    const readAllBtn = this.shadowRoot.querySelector('#read-all-btn');
    if (readAllBtn) {
      readAllBtn.addEventListener('click', async () => {
        try {
          await apiClient.post('/notifications/read-all', {});
          MsToast.show('All notifications dismissed', 'success');
          this.fetchNotifications();
        } catch (err) {
          MsToast.show('Failed to dismiss notifications', 'danger');
        }
      });
    }
  }

  render() {
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

        .header-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: var(--ms-space-4);
        }

        .notification-list {
          display: flex;
          flex-direction: column;
          gap: var(--ms-space-3);
        }

        .notification-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: var(--ms-space-3) var(--ms-space-4);
          border: 1px solid var(--ms-color-neutral-200);
          border-radius: var(--ms-radius-md);
          background-color: var(--ms-surface-primary);
        }

        .type-success { border-left: 4px solid var(--ms-color-success-500); }
        .type-danger { border-left: 4px solid var(--ms-color-danger-500); }
        .type-warning { border-left: 4px solid var(--ms-color-warning-500); }
        .type-info { border-left: 4px solid var(--ms-color-info-500); }

        .message {
          font-size: var(--ms-font-size-sm);
          color: var(--ms-text-primary);
        }
      </style>
      <div>
        <div class="header-row">
          <div>
            <h3 style="margin:0;">System Notifications</h3>
            <p style="margin:var(--ms-space-1) 0 0 0; font-size:var(--ms-font-size-xs); color:var(--ms-text-secondary);">Real-time alerts tracking RAG parsing completions and security warnings.</p>
          </div>
          ${this.notifications.length > 0 ? `
            <ms-button variant="secondary" size="sm" id="read-all-btn">Clear All</ms-button>
          ` : ''}
        </div>

        <div class="card">
          <div class="notification-list">
            ${this.notifications.length === 0 ? `
              <div style="text-align:center; color:var(--ms-text-tertiary); padding:var(--ms-space-10);">
                No unread notifications.
              </div>
            ` : this.notifications.map(n => `
              <div class="notification-item type-${n.type}">
                <div class="message">${n.message}</div>
                <ms-button size="sm" variant="secondary" class="btn-read" data-id="${n.id}">Dismiss</ms-button>
              </div>
            `).join('')}
          </div>
        </div>
      </div>
    `;
  }
}

customElements.define('notifications-view', NotificationsView);
export default NotificationsView;
