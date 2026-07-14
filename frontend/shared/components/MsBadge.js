/**
 * Maruti Suzuki Knowledge Assistant — Badge Web Component
 *
 * Reusable small visual label component.
 * Usage: <ms-badge variant="success|warning|danger|info|primary">Public</ms-badge>
 */

class MsBadge extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
  }

  static get observedAttributes() {
    return ['variant'];
  }

  connectedCallback() {
    this.render();
  }

  attributeChangedCallback() {
    this.render();
  }

  render() {
    const variant = this.getAttribute('variant') || 'primary';

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: inline-block;
        }

        span {
          display: inline-flex;
          align-items: center;
          padding: 0.125rem 0.5rem;
          border-radius: var(--ms-radius-full);
          font-family: var(--ms-font-family-sans);
          font-size: var(--ms-font-size-xs);
          font-weight: var(--ms-font-weight-medium);
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }

        /* --- Variants --- */
        .variant-primary {
          background-color: var(--ms-color-primary-50);
          color: var(--ms-color-primary-600);
        }

        .variant-success {
          background-color: var(--ms-color-success-50);
          color: var(--ms-color-success-700);
        }

        .variant-warning {
          background-color: var(--ms-color-warning-50);
          color: var(--ms-color-warning-700);
        }

        .variant-danger {
          background-color: var(--ms-color-danger-50);
          color: var(--ms-color-danger-700);
        }

        .variant-info {
          background-color: var(--ms-color-info-50);
          color: var(--ms-color-info-700);
        }
      </style>
      <span class="variant-${variant}">
        <slot></slot>
      </span>
    `;
  }
}

customElements.define('ms-badge', MsBadge);
export default MsBadge;
