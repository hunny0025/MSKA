/**
 * Maruti Suzuki Knowledge Assistant — Dashboard Component
 */

import apiClient from '../../shared/api/apiClient.js';
import AppStore from '../../shared/store/AppStore.js';
import MsToast from '../../shared/components/MsToast.js';

class DashboardView extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this.stats = {
      total_approved_docs: 0,
      total_quarantined_docs: 0,
      total_queries: 0,
      active_users: 0
    };
    this.activities = [];
  }

  connectedCallback() {
    this.loadDashboardData();
  }

  async loadDashboardData() {
    try {
      this.stats = await apiClient.get('/analytics/stats');
      this.activities = await apiClient.get('/analytics/activities');
      this.render();
      this.setupListeners();
    } catch (err) {
      console.error(err);
      MsToast.show('Failed to load dashboard metrics', 'danger');
      this.render();
    }
  }

  setupListeners() {
    const startBtn = this.shadowRoot.querySelector('#start-chat-btn');
    if (startBtn) {
      startBtn.addEventListener('click', () => {
        window.location.hash = '/chat';
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

        .layout {
          display: flex;
          flex-direction: column;
          gap: var(--ms-space-6);
        }

        .hero-card {
          display: flex;
          flex-direction: column-reverse;
          gap: var(--ms-space-6);
          background: rgba(255, 255, 255, 0.45);
          backdrop-filter: blur(20px);
          -webkit-backdrop-filter: blur(20px);
          border: 1px solid rgba(255, 255, 255, 0.55);
          border-radius: var(--ms-radius-2xl);
          padding: var(--ms-space-8);
          position: relative;
          overflow: hidden;
        }

        @media (min-width: 768px) {
          .hero-card {
            flex-direction: row;
            align-items: center;
            justify-content: space-between;
          }
          .hero-left {
            flex: 1.2;
            text-align: left;
          }
          .hero-right {
            flex: 0.8;
            display: flex;
            justify-content: center;
            align-items: center;
          }
        }

        .hero-title {
          font-size: var(--ms-font-size-3xl);
          font-weight: var(--ms-font-weight-bold);
          background: linear-gradient(135deg, var(--ms-color-neutral-900), var(--ms-color-primary-600));
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          margin-bottom: var(--ms-space-3);
          margin-top: 0;
        }

        .hero-subtitle {
          color: var(--ms-color-neutral-700);
          font-size: var(--ms-font-size-sm);
          line-height: var(--ms-line-height-relaxed);
          margin-bottom: var(--ms-space-5);
        }

        .car-image-container {
          width: 100%;
          max-width: 320px;
          border-radius: var(--ms-radius-xl);
          overflow: hidden;
          box-shadow: 0 10px 30px rgba(139, 92, 246, 0.15);
          border: 2px solid rgba(255, 255, 255, 0.85);
          transition: transform var(--ms-transition-normal);
        }

        .car-image-container:hover {
          transform: scale(1.04) rotate(1deg);
        }

        .car-image {
          width: 100%;
          display: block;
          object-fit: cover;
        }

        .metrics-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: var(--ms-space-4);
        }

        .metric-card {
          display: flex;
          flex-direction: column;
          gap: var(--ms-space-1);
          padding: var(--ms-space-4) var(--ms-space-5);
        }

        .metric-label {
          font-size: var(--ms-font-size-xs);
          color: var(--ms-text-tertiary);
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }
 
        .metric-value {
          font-size: var(--ms-font-size-3xl);
          font-weight: var(--ms-font-weight-bold);
          color: var(--ms-text-primary);
        }

        .dashboard-columns {
          display: grid;
          grid-template-columns: 1fr;
          gap: var(--ms-space-6);
        }

        @media (min-width: 992px) {
          .dashboard-columns {
            grid-template-columns: 1fr 1fr;
          }
        }

        .activity-list {
          list-style: none;
          padding: 0;
          margin: 0;
          display: flex;
          flex-direction: column;
          gap: var(--ms-space-3);
        }

        .activity-item {
          display: flex;
          gap: var(--ms-space-3);
          font-size: var(--ms-font-size-sm);
          border-bottom: 1px solid var(--ms-color-neutral-100);
          padding-bottom: var(--ms-space-2);
          align-items: center;
        }

        .activity-item:last-child {
          border-bottom: none;
        }
      </style>
      <div class="layout">
        <!-- Hero Introduction -->
        <div class="card hero-card">
          <div class="hero-left">
            <h2 class="hero-title">Welcome to Maruti Suzuki Knowledge Assistant</h2>
            <p class="hero-subtitle">
              Your centralized AI-guided search and chat workspace. Access certified assembly SOPs, engineering references, and department workspace catalog data instantly.
            </p>
            <div style="max-width: 240px;">
              <ms-button id="start-chat-btn" variant="primary" size="md">Start AI Chat Session</ms-button>
            </div>
          </div>
          <div class="hero-right">
            <div class="car-image-container">
              <img class="car-image" src="/assets/maruti_concept_ev.png" alt="Maruti Suzuki Concept EV">
            </div>
          </div>
        </div>

        <!-- Metrics widgets -->
        <div class="metrics-grid">
          <div class="card metric-card">
            <span class="metric-label">Approved SOPs</span>
            <span class="metric-value" style="color:var(--ms-color-success-500);">${this.stats.total_approved_docs}</span>
          </div>
          <div class="card metric-card">
            <span class="metric-label">Quarantined Files</span>
            <span class="metric-value" style="color:var(--ms-color-danger-500);">${this.stats.total_quarantined_docs}</span>
          </div>
          <div class="card metric-card">
            <span class="metric-label">Queries Executed</span>
            <span class="metric-value">${this.stats.total_queries}</span>
          </div>
          <div class="card metric-card">
            <span class="metric-label">Active Collaborators</span>
            <span class="metric-value">${this.stats.active_users}</span>
          </div>
        </div>

        <div class="dashboard-columns">
          <!-- Recent Activity Log Feed -->
          <div class="card">
            <h3 style="margin-top:0; margin-bottom:var(--ms-space-4);">Recent Activity Log</h3>
            <ul class="activity-list">
              ${this.activities.length === 0 ? `
                <li style="color:var(--ms-text-tertiary); text-align:center; padding:var(--ms-space-6);">
                  No activity logged yet.
                </li>
              ` : this.activities.map(act => {
                  let badgeVariant = 'info';
                  if (act.action.includes('CREATE')) badgeVariant = 'success';
                  if (act.action.includes('ASSIGN')) badgeVariant = 'primary';
                  if (act.action.includes('INGEST') && act.details && act.details.includes('quarantined')) badgeVariant = 'danger';
                  
                  return `
                    <li class="activity-item">
                      <ms-badge variant="${badgeVariant}">${act.action}</ms-badge>
                      <span style="flex-grow:1;">
                        Performed on target: <strong>${act.target_type}</strong>
                      </span>
                      <span style="font-size:var(--ms-font-size-xs); color:var(--ms-text-tertiary);">
                        ${new Date(act.created_at).toLocaleTimeString()}
                      </span>
                    </li>
                  `;
                }).join('')}
            </ul>
          </div>

          <!-- Shortcuts list card -->
          <div class="card">
            <h3 style="margin-top:0; margin-bottom:var(--ms-space-4);">Corporate Index Quick Links</h3>
            <div style="display:flex; flex-direction:column; gap:var(--ms-space-3);">
              <ms-button variant="secondary" onclick="window.location.hash='/search'">Go to Advanced Search</ms-button>
              <ms-button variant="secondary" onclick="window.location.hash='/documents'">Go to Document Manager</ms-button>
              <ms-button variant="secondary" onclick="window.location.hash='/projects'">View Workspace Projects</ms-button>
            </div>
          </div>
        </div>
      </div>
    `;
  }
}

customElements.define('dashboard-view', DashboardView);
export default DashboardView;
export { DashboardView };
