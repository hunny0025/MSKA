/**
 * Maruti Suzuki Knowledge Assistant — Toast Web Component
 *
 * Emits global transient notification messages.
 * Usage:
 * <ms-toast></ms-toast>
 *
 * In JS:
 * MsToast.show('Document scanned successfully', 'success');
 */

class MsToast extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this.toasts = [];
  }

  connectedCallback() {
    this.render();
  }

  /**
   * Helper to append toast. If no ms-toast element exists on page, one is appended to body automatically.
   * @param {string} message - Notification text
   * @param {'success'|'danger'|'warning'|'info'} [type='info'] - Severity level
   * @param {number} [duration=3000] - Lifespan in milliseconds
   */
  static show(message, type = 'info', duration = 3000) {
    let instance = document.querySelector('ms-toast');
    if (!instance) {
      instance = document.createElement('ms-toast');
      document.body.appendChild(instance);
    }
    instance.add(message, type, duration);
  }

  add(message, type, duration) {
    const id = Date.now() + Math.random().toString(36).substr(2, 9);
    const toast = { id, message, type };
    this.toasts.push(toast);
    this.render();

    setTimeout(() => {
      this.remove(id);
    }, duration);
  }

  remove(id) {
    this.toasts = this.toasts.filter(t => t.id !== id);
    this.render();
  }

  render() {
    this.shadowRoot.innerHTML = `
      <style>
        .toast-container {
          position: fixed;
          bottom: var(--ms-space-6);
          right: var(--ms-space-6);
          display: flex;
          flex-direction: column;
          gap: var(--ms-space-2);
          z-index: var(--ms-z-toast);
          max-width: 320px;
          width: 100%;
          font-family: var(--ms-font-family-sans);
          pointer-events: none;
        }

        .toast-item {
          pointer-events: auto;
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: var(--ms-space-3) var(--ms-space-4);
          border-radius: var(--ms-radius-md);
          box-shadow: var(--ms-shadow-md);
          animation: slideIn var(--ms-transition-normal) cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
          color: var(--ms-color-neutral-900);
          font-size: var(--ms-font-size-sm);
        }

        @keyframes slideIn {
          from { transform: translateY(100%) scale(0.9); opacity: 0; }
          to { transform: translateY(0) scale(1); opacity: 1; }
        }

        .type-success {
          background-color: var(--ms-color-success-50);
          border-left: 4px solid var(--ms-color-success-500);
        }

        .type-danger {
          background-color: var(--ms-color-danger-50: #fef2f2);
          border-left: 4px solid var(--ms-color-danger-500);
        }

        .type-warning {
          background-color: var(--ms-color-warning-50);
          border-left: 4px solid var(--ms-color-warning-500);
        }

        .type-info {
          background-color: var(--ms-color-info-50);
          border-left: 4px solid var(--ms-color-info-500);
        }

        .close-btn {
          border: none;
          background: none;
          cursor: pointer;
          color: var(--ms-text-secondary);
          font-size: 1.1rem;
          margin-left: var(--ms-space-3);
        }
      </style>
      <div class="toast-container" role="status" aria-live="polite">
        ${this.toasts.map(toast => `
          <div class="toast-item type-${toast.type}">
            <span>${toast.message}</span>
            <button class="close-btn" data-id="${toast.id}" aria-label="Dismiss">&times;</button>
          </div>
        `).join('')}
      </div>
    `;

    // Attach click events to close buttons
    this.shadowRoot.querySelectorAll('.close-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const id = e.currentTarget.getAttribute('data-id');
        this.remove(id);
      });
    });
  }
}

customElements.define('ms-toast', MsToast);
export default MsToast;
