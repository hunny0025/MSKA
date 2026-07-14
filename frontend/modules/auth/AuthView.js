/**
 * Maruti Suzuki Knowledge Assistant — Auth / Login Component
 */

import apiClient from '../../shared/api/apiClient.js';
import { setState } from '../../shared/store/AppStore.js';
import { navigateTo } from '../../shared/router/router.js';

class AuthView extends HTMLElement {
  connectedCallback() {
    this.render();
    this.setupListeners();
  }

  setupListeners() {
    const form = this.shadowRoot.querySelector('form');
    const errorEl = this.shadowRoot.querySelector('.error-message');
    const submitBtn = this.shadowRoot.querySelector('ms-button');

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      errorEl.textContent = '';
      submitBtn.setAttribute('loading', '');

      const username = this.shadowRoot.querySelector('#username').value;
      const password = this.shadowRoot.querySelector('#password').value;

      try {
        // Prepare Form Data URL encoded for OAuth2 /login
        const params = new URLSearchParams();
        params.append('username', username);
        params.append('password', password);

        const response = await fetch('/api/v1/auth/login', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
          body: params.toString()
        });

        if (!response.ok) {
          const err = await response.json();
          throw new Error(err.detail || 'Authentication failed');
        }

        const data = await response.json();

        // Save tokens
        sessionStorage.setItem('access_token', data.access_token);
        sessionStorage.setItem('refresh_token', data.refresh_token);

        // Fetch profile
        const userProfile = await apiClient.get('/auth/me');

        // Update Global state
        setState({
          auth: {
            isAuthenticated: true,
            user: userProfile,
            token: data.access_token
          }
        });

        import('../../shared/components/MsToast.js').then((m) => {
          m.default.show('Welcome to Maruti Suzuki Knowledge Assistant!', 'success');
        });

        navigateTo('/dashboard');
      } catch (err) {
        errorEl.textContent = err.message || 'Login failed. Please check credentials.';
      } finally {
        submitBtn.removeAttribute('loading');
      }
    });
  }

  render() {
    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          max-width: 400px;
          margin: 100px auto;
          font-family: var(--ms-font-family-sans);
        }

        .login-card {
          background-color: var(--ms-surface-primary);
          border-radius: var(--ms-radius-lg);
          border: 1px solid var(--ms-color-neutral-200);
          box-shadow: var(--ms-shadow-lg);
          padding: var(--ms-space-8);
        }

        .logo-header {
          text-align: center;
          margin-bottom: var(--ms-space-6);
        }

        .logo {
          width: 50px;
          height: 50px;
          background: linear-gradient(135deg, var(--ms-color-primary-400), var(--ms-color-accent-400));
          border-radius: var(--ms-radius-xl);
          display: inline-flex;
          align-items: center;
          justify-content: center;
          font-weight: var(--ms-font-weight-bold);
          font-size: var(--ms-font-size-2xl);
          color: white;
          margin-bottom: var(--ms-space-2);
          box-shadow: 0 4px 12px rgba(26,86,219,0.3);
        }

        h2 {
          font-size: var(--ms-font-size-xl);
          margin-bottom: var(--ms-space-1);
        }

        p {
          font-size: var(--ms-font-size-xs);
          color: var(--ms-text-secondary);
        }

        .form-group {
          margin-bottom: var(--ms-space-4);
        }

        label {
          display: block;
          font-size: var(--ms-font-size-xs);
          font-weight: var(--ms-font-weight-medium);
          margin-bottom: var(--ms-space-1);
          color: var(--ms-text-primary);
        }

        input {
          width: 100%;
          padding: var(--ms-space-2) var(--ms-space-3);
          border: 1px solid var(--ms-color-neutral-300);
          border-radius: var(--ms-radius-md);
          font-family: var(--ms-font-family-sans);
          font-size: var(--ms-font-size-sm);
          box-sizing: border-box;
          background-color: var(--ms-surface-primary);
          color: var(--ms-text-primary);
          transition: border var(--ms-transition-fast);
        }

        input:focus {
          outline: none;
          border-color: var(--ms-color-primary-500);
          box-shadow: var(--ms-focus-ring);
        }

        .error-message {
          color: var(--ms-color-danger-500);
          font-size: var(--ms-font-size-xs);
          margin-bottom: var(--ms-space-3);
          min-height: 18px;
        }

        .footer-note {
          text-align: center;
          font-size: var(--ms-font-size-xs);
          color: var(--ms-text-tertiary);
          margin-top: var(--ms-space-6);
        }
      </style>
      <div class="login-card">
        <div class="logo-header">
          <div class="logo">M</div>
          <h2>Maruti Suzuki</h2>
          <p>Knowledge Assistant Sign In</p>
        </div>
        <form>
          <div class="form-group">
            <label for="username">Username</label>
            <input type="text" id="username" required autocomplete="username" placeholder="e.g. admin">
          </div>
          <div class="form-group">
            <label for="password">Password</label>
            <input type="password" id="password" required autocomplete="current-password" placeholder="••••••••">
          </div>
          <div class="error-message" role="alert"></div>
          <ms-button type="submit" variant="primary">Sign In</ms-button>
        </form>
        <div class="footer-note">
          For demo, seed roles via /api/v1/auth/setup then create/login users.
        </div>
      </div>
    `;
  }
}

customElements.define('auth-view', AuthView);
export default AuthView;
export { AuthView };
