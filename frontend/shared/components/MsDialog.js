/**
 * Maruti Suzuki Knowledge Assistant — Dialog Web Component
 *
 * Custom modal/dialog element matching WCAG standards.
 * Usage:
 * <ms-dialog id="my-dialog">
 *   <span slot="title">Confirm Delete</span>
 *   <div>Are you sure you want to proceed?</div>
 *   <div slot="footer">
 *     <ms-button variant="secondary" id="btn-cancel">Cancel</ms-button>
 *     <ms-button variant="danger" id="btn-confirm">Delete</ms-button>
 *   </div>
 * </ms-dialog>
 */

class MsDialog extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
  }

  static get observedAttributes() {
    return ['open'];
  }

  connectedCallback() {
    this.render();
    this.setupListeners();
  }

  attributeChangedCallback(name, oldValue, newValue) {
    if (name === 'open') {
      const dialog = this.shadowRoot.querySelector('dialog');
      if (dialog) {
        if (newValue !== null) {
          dialog.showModal();
          this.setAttribute('aria-hidden', 'false');
        } else {
          dialog.close();
          this.setAttribute('aria-hidden', 'true');
        }
      }
    }
  }

  setupListeners() {
    const dialog = this.shadowRoot.querySelector('dialog');
    const closeBtn = this.shadowRoot.querySelector('.close-btn');

    closeBtn.addEventListener('click', () => this.close());
    
    // Close on clicking backdrop
    dialog.addEventListener('click', (event) => {
      const rect = dialog.getBoundingClientRect();
      const isInDialog = (rect.top <= event.clientY && event.clientY <= rect.top + rect.height &&
        rect.left <= event.clientX && event.clientX <= rect.left + rect.width);
      if (!isInDialog) {
        this.close();
      }
    });

    dialog.addEventListener('cancel', (e) => {
      e.preventDefault();
      this.close();
    });
  }

  open() {
    this.setAttribute('open', '');
  }

  close() {
    this.removeAttribute('open');
    this.dispatchEvent(new CustomEvent('close', { bubbles: true, composed: true }));
  }

  render() {
    this.shadowRoot.innerHTML = `
      <style>
        dialog {
          border: none;
          border-radius: var(--ms-radius-lg);
          padding: 0;
          box-shadow: var(--ms-shadow-xl);
          background-color: var(--ms-surface-primary);
          color: var(--ms-text-primary);
          max-width: 500px;
          width: 90%;
          font-family: var(--ms-font-family-sans);
          overflow: hidden;
        }

        dialog::backdrop {
          background-color: var(--ms-surface-overlay);
          backdrop-filter: blur(4px);
        }

        .header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: var(--ms-space-4) var(--ms-space-6);
          border-bottom: 1px solid var(--ms-color-neutral-200);
        }

        .title {
          font-size: var(--ms-font-size-lg);
          font-weight: var(--ms-font-weight-semibold);
          margin: 0;
        }

        .close-btn {
          border: none;
          background: none;
          font-size: 1.5rem;
          cursor: pointer;
          color: var(--ms-text-secondary);
          display: inline-flex;
          align-items: center;
          justify-content: center;
          width: 32px;
          height: 32px;
          border-radius: var(--ms-radius-full);
          transition: background var(--ms-transition-fast);
        }

        .close-btn:hover {
          background-color: var(--ms-color-neutral-100);
          color: var(--ms-text-primary);
        }

        .body {
          padding: var(--ms-space-6);
          font-size: var(--ms-font-size-sm);
          line-height: var(--ms-line-height-normal);
        }

        .footer {
          display: flex;
          align-items: center;
          justify-content: flex-end;
          gap: var(--ms-space-3);
          padding: var(--ms-space-4) var(--ms-space-6);
          background-color: var(--ms-surface-secondary);
          border-top: 1px solid var(--ms-color-neutral-200);
        }
      </style>
      <dialog aria-labelledby="dialog-title">
        <div class="header">
          <h2 id="dialog-title" class="title">
            <slot name="title">Notification</slot>
          </h2>
          <button class="close-btn" aria-label="Close dialog">&times;</button>
        </div>
        <div class="body">
          <slot></slot>
        </div>
        <div class="footer">
          <slot name="footer"></slot>
        </div>
      </dialog>
    `;
  }
}

customElements.define('ms-dialog', MsDialog);
export default MsDialog;
