/**
 * Maruti Suzuki Knowledge Assistant — KnowledgeGraphView Component
 */

import apiClient from '../../shared/api/apiClient.js';
import AppStore from '../../shared/store/AppStore.js';
import MsToast from '../../shared/components/MsToast.js';

class KnowledgeGraphView extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this.document = null;
    this.relationships = null;
    this.docId = null;
  }

  connectedCallback() {
    this.parseParams();
    if (this.docId) {
      this.loadGraphData();
    } else {
      this.renderSelector();
    }
  }

  parseParams() {
    const hash = window.location.hash;
    const urlParams = new URLSearchParams(hash.split('?')[1] || '');
    this.docId = urlParams.get('doc_id');
  }

  async loadGraphData() {
    try {
      // Re-use hybrid search with filter to isolate specific document and fetch relationships
      const docDetailList = await apiClient.get(`/search?q=&classification=`);
      this.document = docDetailList.find(r => r.document.id === this.docId);
      
      if (this.document) {
        this.relationships = this.document.relationships;
      }
      this.render();
      this.setupListeners();
    } catch (err) {
      console.error(err);
      MsToast.show('Failed to fetch document relationships', 'danger');
      this.renderSelector();
    }
  }

  setupListeners() {
    const backBtn = this.shadowRoot.querySelector('#back-btn');
    if (backBtn) {
      backBtn.addEventListener('click', () => {
        window.location.hash = '/search';
      });
    }

    this.shadowRoot.querySelectorAll('.graph-node.child').forEach(node => {
      node.addEventListener('click', (e) => {
        const targetId = e.currentTarget.getAttribute('data-id');
        window.location.hash = `/knowledge-graph?doc_id=${targetId}`;
        this.docId = targetId;
        this.loadGraphData();
      });
    });
  }

  renderSelector() {
    this.shadowRoot.innerHTML = `
      <style>
        .box { padding: var(--ms-space-6); text-align:center; }
      </style>
      <div class="box">
        <h3>Document Knowledge Graph</h3>
        <p style="color:var(--ms-text-secondary); font-size:var(--ms-font-size-sm);">Please search and select a document from the <a href="#/search" style="color:var(--ms-color-primary-500);">Enterprise Search Page</a> to inspect version relationships.</p>
      </div>
    `;
  }

  render() {
    if (!this.document) {
      this.renderSelector();
      return;
    }

    const { document: doc, relationships } = this.document;

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

        .graph-area {
          height: 380px;
          border: 1px solid var(--ms-color-neutral-200);
          border-radius: var(--ms-radius-lg);
          background-color: var(--ms-surface-secondary);
          margin-top: var(--ms-space-4);
          position: relative;
          overflow: hidden;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        /* Graph nodes styling */
        .graph-node {
          position: absolute;
          width: 130px;
          height: 130px;
          border-radius: var(--ms-radius-full);
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          text-align: center;
          padding: var(--ms-space-2);
          box-shadow: var(--ms-shadow-md);
          font-size: var(--ms-font-size-xs);
          font-weight: var(--ms-font-weight-medium);
          box-sizing: border-box;
          transition: transform var(--ms-transition-fast);
        }

        .graph-node.root {
          background: linear-gradient(135deg, var(--ms-color-primary-500), var(--ms-color-primary-600));
          color: white;
          width: 150px;
          height: 150px;
          z-index: 10;
        }

        .graph-node.child {
          cursor: pointer;
          z-index: 5;
        }

        .graph-node.child:hover {
          transform: scale(1.05);
        }

        .graph-node.superseded_by {
          background-color: var(--ms-color-danger-50);
          border: 2px solid var(--ms-color-danger-500);
          color: var(--ms-color-danger-700);
        }

        .graph-node.supersedes {
          background-color: var(--ms-color-success-50);
          border: 2px solid var(--ms-color-success-500);
          color: var(--ms-color-success-700);
        }

        .graph-node.related {
          background-color: var(--ms-color-info-50);
          border: 2px solid var(--ms-color-info-500);
          color: var(--ms-color-info-700);
        }

        .node-name {
          font-weight: var(--ms-font-weight-bold);
          overflow: hidden;
          text-overflow: ellipsis;
          width: 100%;
          white-space: nowrap;
        }

        /* Simple placement layout */
        .pos-center { /* handled by flex center */ }
        .pos-top { top: 20px; }
        .pos-bottom { bottom: 20px; }
        .pos-left { left: 40px; }
        .pos-right { right: 40px; }

        .header-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: var(--ms-space-4);
        }
      </style>
      <div>
        <div class="header-row">
          <div>
            <h3 style="margin:0;">Document Relationship Graph</h3>
            <p style="margin:var(--ms-space-1) 0 0 0; font-size:var(--ms-font-size-xs); color:var(--ms-text-secondary);">Interactive visualization of version updates and scope links.</p>
          </div>
          <ms-button id="back-btn" variant="secondary" size="sm">Back to Search</ms-button>
        </div>

        <div class="card">
          <div style="font-size:var(--ms-font-size-sm); margin-bottom:var(--ms-space-2);">
            Inspecting: <strong>${doc.filename}</strong> (Version ${doc.version} | Classification: <ms-badge variant="info">${doc.classification}</ms-badge>)
          </div>

          <div class="graph-area">
            <!-- Central Active Node -->
            <div class="graph-node root">
              <span class="node-name">${doc.filename}</span>
              <span style="font-size:0.75rem; opacity:0.8;">Active (v${doc.version})</span>
            </div>

            <!-- Superseded By (Newer) -->
            ${relationships.superseded_by && relationships.superseded_by.length > 0 ? `
              <div class="graph-node child superseded_by pos-top" data-id="${relationships.superseded_by[0].id}">
                <span class="node-name">${relationships.superseded_by[0].filename}</span>
                <span>Newer Version</span>
                <span style="font-weight:var(--ms-font-weight-bold);">${relationships.superseded_by[0].version}</span>
              </div>
            ` : ''}

            <!-- Supersedes (Older) -->
            ${relationships.supersedes && relationships.supersedes.length > 0 ? `
              <div class="graph-node child supersedes pos-bottom" data-id="${relationships.supersedes[0].id}">
                <span class="node-name">${relationships.supersedes[0].filename}</span>
                <span>Older Version</span>
                <span style="font-weight:var(--ms-font-weight-bold);">${relationships.supersedes[0].version}</span>
              </div>
            ` : ''}

            <!-- Related Project links -->
            ${relationships.related && relationships.related.length > 0 ? `
              <div class="graph-node child related pos-left" data-id="${relationships.related[0].id}">
                <span class="node-name">${relationships.related[0].filename}</span>
                <span>Related (Project)</span>
              </div>
            ` : ''}

            ${relationships.related && relationships.related.length > 1 ? `
              <div class="graph-node child related pos-right" data-id="${relationships.related[1].id}">
                <span class="node-name">${relationships.related[1].filename}</span>
                <span>Related (Project)</span>
              </div>
            ` : ''}
          </div>
        </div>
      </div>
    `;
  }
}

customElements.define('knowledge-graph-view', KnowledgeGraphView);
export default KnowledgeGraphView;
export { KnowledgeGraphView };
