/**
 * Maruti Suzuki Knowledge Assistant — SearchView Component
 */

import apiClient from '../../shared/api/apiClient.js';
import AppStore from '../../shared/store/AppStore.js';
import MsToast from '../../shared/components/MsToast.js';

class SearchView extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this.projects = [];
    this.results = [];
    this.selectedProjectId = '';
    this.selectedClassification = '';
  }

  connectedCallback() {
    this.loadFilterMetadata();
  }

  async loadFilterMetadata() {
    try {
      this.projects = await apiClient.get('/projects');
      this.render();
      this.setupListeners();
    } catch (err) {
      console.error(err);
      MsToast.show('Failed to load search filter options', 'danger');
      this.render();
    }
  }

  setupListeners() {
    const form = this.shadowRoot.querySelector('#search-form');
    if (form) {
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const q = this.shadowRoot.querySelector('#search-input').value.trim();
        const projectSelect = this.shadowRoot.querySelector('#project-select');
        const classSelect = this.shadowRoot.querySelector('#classification-select');
        
        this.selectedProjectId = projectSelect.value;
        this.selectedClassification = classSelect.value;

        const searchBtn = this.shadowRoot.querySelector('#search-btn');
        searchBtn.setAttribute('loading', '');

        try {
          // Construct query params
          const params = new URLSearchParams();
          if (q) params.append('q', q);
          if (this.selectedProjectId) params.append('project_id', this.selectedProjectId);
          if (this.selectedClassification) params.append('classification', this.selectedClassification);

          this.results = await apiClient.get(`/search?${params.toString()}`);
          this.render();
          this.setupListeners();
          
          // Re-hydrate search term input value
          this.shadowRoot.querySelector('#search-input').value = q;
        } catch (err) {
          MsToast.show(err.message || 'Search execution failed', 'danger');
        } finally {
          searchBtn.removeAttribute('loading');
        }
      });
    }

    // Graph visual link navigation triggers
    this.shadowRoot.querySelectorAll('.relation-link').forEach(link => {
      link.addEventListener('click', (e) => {
        const docId = e.currentTarget.getAttribute('data-id');
        MsToast.show(`Navigating to Knowledge Graph document details for ID: ${docId}`, 'info');
        window.location.hash = `/knowledge-graph?doc_id=${docId}`;
      });
    });
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

        .filter-panel {
          display: grid;
          grid-template-columns: 1fr;
          gap: var(--ms-space-4);
          margin-bottom: var(--ms-space-6);
        }

        @media (min-width: 768px) {
          .filter-panel {
            grid-template-columns: 2fr 1fr 1fr 100px;
          }
        }

        input, select {
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

        input:focus, select:focus {
          outline: none;
          border-color: var(--ms-color-primary-500);
          box-shadow: var(--ms-focus-ring);
        }

        .result-list {
          display: flex;
          flex-direction: column;
          gap: var(--ms-space-4);
          margin-top: var(--ms-space-6);
        }

        .result-item {
          border: 1px solid var(--ms-color-neutral-200);
          border-radius: var(--ms-radius-lg);
          padding: var(--ms-space-4);
          background-color: var(--ms-surface-primary);
        }

        .result-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: var(--ms-space-2);
        }

        .doc-title {
          font-weight: var(--ms-font-weight-bold);
          font-size: var(--ms-font-size-base);
          color: var(--ms-color-primary-600);
        }

        .snippet {
          background-color: var(--ms-surface-secondary);
          border-left: 3px solid var(--ms-color-primary-500);
          padding: var(--ms-space-3);
          font-size: var(--ms-font-size-xs);
          border-radius: var(--ms-radius-sm);
          margin-top: var(--ms-space-2);
          color: var(--ms-text-secondary);
        }

        .relationship-box {
          margin-top: var(--ms-space-3);
          font-size: var(--ms-font-size-xs);
          border-top: 1px solid var(--ms-color-neutral-100);
          padding-top: var(--ms-space-2);
          display: flex;
          gap: var(--ms-space-4);
          flex-wrap: wrap;
        }

        .relation-link {
          color: var(--ms-color-primary-500);
          text-decoration: underline;
          cursor: pointer;
        }
      </style>
      <div>
        <h3>Hybrid Enterprise Search</h3>
        <p style="font-size:var(--ms-font-size-xs); color:var(--ms-text-secondary); margin-bottom:var(--ms-space-4);">Execute structured filters combined with semantic vector queries.</p>

        <form id="search-form" class="card">
          <div class="filter-panel">
            <div>
              <input type="text" id="search-input" placeholder="Enter keywords or search phrases..." />
            </div>
            <div>
              <select id="project-select">
                <option value="">Global Project Scopes</option>
                ${this.projects.map(p => `
                  <option value="${p.id}" ${p.id === this.selectedProjectId ? 'selected' : ''}>
                    ${p.name}
                  </option>
                `).join('')}
              </select>
            </div>
            <div>
              <select id="classification-select">
                <option value="">Global Classifications</option>
                <option value="public" ${this.selectedClassification === 'public' ? 'selected' : ''}>Public</option>
                <option value="internal" ${this.selectedClassification === 'internal' ? 'selected' : ''}>Internal</option>
                <option value="confidential" ${this.selectedClassification === 'confidential' ? 'selected' : ''}>Confidential</option>
                <option value="restricted" ${this.selectedClassification === 'restricted' ? 'selected' : ''}>Restricted</option>
              </select>
            </div>
            <ms-button type="submit" variant="primary" id="search-btn">Search</ms-button>
          </div>
        </form>

        <div class="result-list">
          ${this.results.length === 0 ? `
            <div style="text-align:center; color:var(--ms-text-tertiary); padding:var(--ms-space-16);">
              No search matching results found. Execute a query to find SOP indices.
            </div>
          ` : this.results.map(res => `
            <div class="result-item">
              <div class="result-header">
                <span class="doc-title">${res.document.filename} (v${res.document.version})</span>
                <div style="display:flex; gap:var(--ms-space-2);">
                  <ms-badge variant="info">${res.document.classification}</ms-badge>
                  <ms-badge variant="success">Match Score: ${(res.search_score * 100).toFixed(0)}%</ms-badge>
                </div>
              </div>
              
              ${res.matches && res.matches.length > 0 ? `
                <div>
                  <strong>Semantic Chunk Matches:</strong>
                  ${res.matches.map(c => `
                    <div class="snippet">
                      ${c.text}
                    </div>
                  `).join('')}
                </div>
              ` : ''}

              <div class="relationship-box">
                ${res.relationships.superseded_by && res.relationships.superseded_by.length > 0 ? `
                  <div>
                    <span style="color:var(--ms-color-danger-500); font-weight:var(--ms-font-weight-medium);">Superseded By:</span>
                    ${res.relationships.superseded_by.map(r => `
                      <span class="relation-link" data-id="${r.id}">${r.filename} (${r.version})</span>
                    `).join(', ')}
                  </div>
                ` : ''}

                ${res.relationships.supersedes && res.relationships.supersedes.length > 0 ? `
                  <div>
                    <span style="color:var(--ms-color-success-700); font-weight:var(--ms-font-weight-medium);">Supersedes:</span>
                    ${res.relationships.supersedes.map(r => `
                      <span class="relation-link" data-id="${r.id}">${r.filename} (${r.version})</span>
                    `).join(', ')}
                  </div>
                ` : ''}

                ${res.relationships.related && res.relationships.related.length > 0 ? `
                  <div>
                    <span style="color:var(--ms-text-secondary); font-weight:var(--ms-font-weight-medium);">Related (Project):</span>
                    ${res.relationships.related.map(r => `
                      <span class="relation-link" data-id="${r.id}">${r.filename}</span>
                    `).join(', ')}
                  </div>
                ` : ''}
              </div>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  }
}

customElements.define('search-view', SearchView);
export default SearchView;
export { SearchView };
