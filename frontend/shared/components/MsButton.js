/**
 * Maruti Suzuki Knowledge Assistant — Button Web Component
 *
 * Custom button component mapping to design tokens.
 * Usage: <ms-button variant="primary|secondary|danger" size="sm|md|lg" disabled>Click Me</ms-button>
 */

class MsButton extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
  }

  static get observedAttributes() {
    return ['variant', 'size', 'disabled', 'loading'];
  }

  connectedCallback() {
    this.render();
  }

  attributeChangedCallback() {
    this.render();
  }

  render() {
    const variant = this.getAttribute('variant') || 'primary';
    const size = this.getAttribute('size') || 'md';
    const disabled = this.hasAttribute('disabled');
    const loading = this.hasAttribute('loading');

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: inline-block;
        }
        button {
          font-family: var(--ms-font-family-sans);
          font-weight: var(--ms-font-weight-medium);
          border-radius: var(--ms-radius-md);
          border: 1px solid transparent;
          cursor: pointer;
          transition: all var(--ms-transition-fast);
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: var(--ms-space-2);
          width: 100%;
          box-sizing: border-box;
        }
        button:focus-visible {
          outline: none;
          box-shadow: var(--ms-focus-ring);
        }

        /* --- Sizes --- */
        .size-sm {
          padding: var(--ms-space-1) var(--ms-space-3);
          font-size: var(--ms-font-size-xs);
        }
        .size-md {
          padding: var(--ms-space-2) var(--ms-space-4);
          font-size: var(--ms-font-size-sm);
        }
        .size-lg {
          padding: var(--ms-space-3) var(--ms-space-6);
          font-size: var(--ms-font-size-base);
        }

        /* --- Variants --- */
        .variant-primary {
          background: linear-gradient(135deg, var(--ms-color-primary-500), var(--ms-color-accent-400));
          color: var(--ms-color-neutral-0);
          box-shadow: 0 4px 14px 0 rgba(139, 92, 246, 0.4);
          border: none;
        }
        .variant-primary:hover:not(:disabled) {
          filter: brightness(1.08);
          transform: translateY(-1px);
          box-shadow: 0 6px 20px 0 rgba(139, 92, 246, 0.5);
        }
        .variant-primary:active:not(:disabled) {
          transform: translateY(0);
        }

        .variant-secondary {
          background-color: rgba(255, 255, 255, 0.55);
          color: var(--ms-text-primary);
          border: 1px solid rgba(255, 255, 255, 0.6);
          backdrop-filter: blur(8px);
          -webkit-backdrop-filter: blur(8px);
          box-shadow: 0 4px 10px rgba(0, 0, 0, 0.02);
        }
        .variant-secondary:hover:not(:disabled) {
          background-color: rgba(255, 255, 255, 0.75);
          border-color: rgba(255, 255, 255, 0.85);
          transform: translateY(-1px);
        }

        .variant-danger {
          background-color: var(--ms-color-danger-500);
          color: var(--ms-color-neutral-0);
        }
        .variant-danger:hover:not(:disabled) {
          background-color: var(--ms-color-danger-700);
        }

        /* --- States --- */
        button:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .spinner {
          width: 16px;
          height: 16px;
          border: 2px solid currentColor;
          border-right-color: transparent;
          border-radius: var(--ms-radius-full);
          animation: spin 0.8s linear infinite;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      </style>
      <button class="variant-${variant} size-${size}" ${disabled || loading ? 'disabled' : ''}>
        ${loading ? '<span class="spinner" aria-hidden="true"></span>' : ''}
        <slot></slot>
      </button>
    `;
  }
}

customElements.define('ms-button', MsButton);
export default MsButton;
