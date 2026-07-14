/**
 * Maruti Suzuki Knowledge Assistant — Chat View Component
 */

import apiClient from '../../shared/api/apiClient.js';
import AppStore from '../../shared/store/AppStore.js';
import MsToast from '../../shared/components/MsToast.js';

class ChatView extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this.projects = [];
    this.selectedProjectId = null;
    
    this.sessions = [];
    this.activeSessionId = null;
    
    this.messages = [];
    this._explainingMessageId = null;
  }

  connectedCallback() {
    this.loadProjects();
  }

  async loadProjects() {
    try {
      this.projects = await apiClient.get('/projects');
      if (this.projects.length > 0) {
        this.selectedProjectId = this.projects[0].id;
        await this.loadSessions();
      } else {
        this.render();
      }
    } catch (err) {
      console.error(err);
      MsToast.show('Failed to load project references', 'danger');
      this.render();
    }
  }

  async loadSessions() {
    if (!this.selectedProjectId) return;
    try {
      this.sessions = await apiClient.get(`/chat/sessions/project/${this.selectedProjectId}`);
      if (this.sessions.length > 0) {
        this.activeSessionId = this.sessions[0].id;
        await this.loadMessages();
      } else {
        this.messages = [];
        this.activeSessionId = null;
        this.render();
        this.setupListeners();
      }
    } catch (err) {
      console.error(err);
      MsToast.show('Failed to fetch chat sessions', 'danger');
      this.render();
    }
  }

  async loadMessages() {
    if (!this.activeSessionId) return;
    try {
      this.messages = await apiClient.get(`/chat/sessions/${this.activeSessionId}/messages`);
      this.render();
      this.setupListeners();
      this.scrollToBottom();
    } catch (err) {
      console.error(err);
      MsToast.show('Failed to fetch session messages', 'danger');
      this.render();
    }
  }

  scrollToBottom() {
    const box = this.shadowRoot.querySelector('.message-box');
    if (box) {
      box.scrollTop = box.scrollHeight;
    }
  }

  setupListeners() {
    // Project filter change
    const projSelect = this.shadowRoot.querySelector('#project-select');
    if (projSelect) {
      projSelect.addEventListener('change', (e) => {
        this.selectedProjectId = e.target.value;
        this.loadSessions();
      });
    }

    // Session selection clicks
    this.shadowRoot.querySelectorAll('.session-item').forEach(item => {
      item.addEventListener('click', (e) => {
        this.activeSessionId = e.currentTarget.getAttribute('data-id');
        this.loadMessages();
      });
    });

    // New Session click
    const newSessionBtn = this.shadowRoot.querySelector('#new-session-btn');
    if (newSessionBtn) {
      newSessionBtn.addEventListener('click', async () => {
        try {
          const newSession = await apiClient.post('/chat/sessions', {
            project_id: this.selectedProjectId,
            title: 'New Chat Session'
          });
          MsToast.show('New session created', 'success');
          this.activeSessionId = newSession.id;
          await this.loadSessions();
        } catch (err) {
          MsToast.show('Failed to create new session', 'danger');
        }
      });
    }

    // Send query
    const form = this.shadowRoot.querySelector('#query-form');
    if (form) {
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const input = this.shadowRoot.querySelector('#query-input');
        const submitBtn = this.shadowRoot.querySelector('#send-btn');
        const queryText = input.value.trim();

        if (!queryText || !this.activeSessionId) return;

        submitBtn.setAttribute('loading', '');
        input.setAttribute('disabled', '');

        // Optimistically insert user message into view local list
        this.messages.push({
          id: 'temp-u',
          role: 'user',
          content: queryText
        });
        this.render();
        this.scrollToBottom();

        try {
          const aiReply = await apiClient.post(`/chat/sessions/${this.activeSessionId}/query`, {
            query: queryText
          });
          // Replace local optimistic message list with real list reload
          await this.loadMessages();
        } catch (err) {
          MsToast.show(err.message || 'Failed to submit query', 'danger');
          // rollback optimistic insert
          this.messages.pop();
          this.render();
          this.setupListeners();
        } finally {
          submitBtn.removeAttribute('loading');
          input.removeAttribute('disabled');
          input.value = '';
          input.focus();
        }
      });
    }

    // Explain Simply triggers
    this.shadowRoot.querySelectorAll('.btn-explain').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const msgId = e.currentTarget.getAttribute('data-id');
        e.currentTarget.setAttribute('disabled', 'true');
        e.currentTarget.textContent = 'Simplifying...';
        
        try {
          const simplifiedText = await apiClient.post(`/chat/messages/${msgId}/explain`, {});
          // Add simplified text locally to memory and re-render
          const msg = this.messages.find(m => m.id === msgId);
          if (msg) {
            msg._simplifiedContent = simplifiedText;
            this.render();
            this.setupListeners();
            this.scrollToBottom();
          }
        } catch (err) {
          MsToast.show('Failed to generate simplified instructions', 'danger');
          e.currentTarget.removeAttribute('disabled');
          e.currentTarget.textContent = 'Explain Simply';
        }
      });
    });

    // Bookmark triggers
    this.shadowRoot.querySelectorAll('.btn-bookmark').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const msgId = e.currentTarget.getAttribute('data-id');
        try {
          await apiClient.post(`/chat/messages/${msgId}/bookmark`, {});
          MsToast.show('Answer bookmarked to dashboard!', 'success');
          e.currentTarget.style.color = 'var(--ms-color-accent-500)';
        } catch (err) {
          MsToast.show(err.message || 'Failed to bookmark message', 'danger');
        }
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

        .chat-layout {
          display: grid;
          grid-template-columns: 1fr;
          gap: var(--ms-space-6);
          height: calc(100vh - var(--ms-header-height) - 100px);
        }

        @media (min-width: 768px) {
          .chat-layout {
            grid-template-columns: 240px 1fr;
          }
        }

        .sidebar {
          background-color: var(--ms-surface-primary);
          border: 1px solid var(--ms-color-neutral-200);
          border-radius: var(--ms-radius-lg);
          padding: var(--ms-space-4);
          display: flex;
          flex-direction: column;
          gap: var(--ms-space-4);
          overflow-y: auto;
        }

        .session-list {
          display: flex;
          flex-direction: column;
          gap: var(--ms-space-2);
          flex-grow: 1;
        }

        .session-item {
          padding: var(--ms-space-2) var(--ms-space-3);
          font-size: var(--ms-font-size-sm);
          border-radius: var(--ms-radius-md);
          cursor: pointer;
          transition: background-color var(--ms-transition-fast);
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
          border: 1px solid transparent;
        }

        .session-item:hover {
          background-color: var(--ms-color-neutral-100);
        }

        .session-item.active {
          background-color: var(--ms-color-primary-50);
          border-color: var(--ms-color-primary-200);
          color: var(--ms-color-primary-700);
          font-weight: var(--ms-font-weight-medium);
        }

        .chat-main {
          background-color: var(--ms-surface-primary);
          border: 1px solid var(--ms-color-neutral-200);
          border-radius: var(--ms-radius-lg);
          display: flex;
          flex-direction: column;
          justify-content: space-between;
          overflow: hidden;
        }

        .message-box {
          flex-grow: 1;
          padding: var(--ms-space-6);
          overflow-y: auto;
          display: flex;
          flex-direction: column;
          gap: var(--ms-space-4);
        }

        .message-item {
          max-width: 80%;
          padding: var(--ms-space-3) var(--ms-space-4);
          border-radius: var(--ms-radius-lg);
          font-size: var(--ms-font-size-sm);
          line-height: var(--ms-line-height-normal);
        }

        .message-item.user {
          align-self: flex-end;
          background-color: var(--ms-color-primary-500);
          color: white;
          border-bottom-right-radius: 0;
        }

        .message-item.assistant {
          align-self: flex-start;
          background-color: var(--ms-surface-secondary);
          color: var(--ms-text-primary);
          border-bottom-left-radius: 0;
          border: 1px solid var(--ms-color-neutral-200);
        }

        .meta-row {
          margin-top: var(--ms-space-3);
          border-top: 1px solid var(--ms-color-neutral-200);
          padding-top: var(--ms-space-2);
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: var(--ms-space-4);
          font-size: var(--ms-font-size-xs);
          flex-wrap: wrap;
        }

        .citations {
          color: var(--ms-text-secondary);
          display: flex;
          flex-direction: column;
          gap: 2px;
        }

        .input-bar {
          padding: var(--ms-space-4) var(--ms-space-6);
          border-top: 1px solid var(--ms-color-neutral-200);
          background-color: var(--ms-surface-secondary);
        }

        #query-form {
          display: flex;
          gap: var(--ms-space-2);
        }

        #query-input {
          flex-grow: 1;
          padding: var(--ms-space-2) var(--ms-space-3);
          border: 1px solid var(--ms-color-neutral-300);
          border-radius: var(--ms-radius-md);
          font-family: var(--ms-font-family-sans);
          font-size: var(--ms-font-size-sm);
          background-color: var(--ms-surface-primary);
          color: var(--ms-text-primary);
        }

        #query-input:focus {
          outline: none;
          border-color: var(--ms-color-primary-500);
          box-shadow: var(--ms-focus-ring);
        }
      </style>
      <div class="chat-layout">
        <div class="sidebar">
          <div>
            <label style="font-size:var(--ms-font-size-xs); font-weight:var(--ms-font-weight-medium); margin-bottom:var(--ms-space-1); display:block;">Project Context</label>
            <select id="project-select" style="width:100%;">
              ${this.projects.map(p => `
                <option value="${p.id}" ${p.id === this.selectedProjectId ? 'selected' : ''}>
                  ${p.name}
                </option>
              `).join('')}
            </select>
          </div>

          <ms-button variant="secondary" size="sm" id="new-session-btn">+ New Chat</ms-button>
          
          <div class="session-list">
            ${this.sessions.map(s => `
              <div class="session-item ${s.id === this.activeSessionId ? 'active' : ''}" data-id="${s.id}">
                ${s.title}
              </div>
            `).join('')}
          </div>
        </div>

        <div class="chat-main">
          <div class="message-box">
            ${!this.activeSessionId ? `
              <div style="text-align:center; color:var(--ms-text-tertiary); margin:auto;">
                Please select or create a chat session on the left to begin query interaction.
              </div>
            ` : this.messages.length === 0 ? `
              <div style="text-align:center; color:var(--ms-text-tertiary); margin:auto;">
                Ask a natural-language query about production guidelines or assembly specifications.
              </div>
            ` : this.messages.map(msg => {
                const badgeVariant = msg.confidence_score >= 0.8 ? 'success' : msg.confidence_score >= 0.65 ? 'warning' : 'danger';
                
                return `
                  <div class="message-item ${msg.role}">
                    <div>${msg.content}</div>

                    ${msg._simplifiedContent ? `
                      <div style="margin-top:var(--ms-space-3); padding:var(--ms-space-3); border-radius:var(--ms-radius-md); background-color:var(--ms-color-success-50); border:1px dashed var(--ms-color-success-500); color:var(--ms-color-success-700);">
                        <strong>Simplified Assembly Instructions:</strong>
                        <div style="margin-top:var(--ms-space-1);">${msg._simplifiedContent.replace(/\n/g, '<br/>')}</div>
                      </div>
                    ` : ''}

                    ${msg.role === 'assistant' ? `
                      <div class="meta-row">
                        <div class="citations">
                          <strong>Source Reference Citations:</strong>
                          ${msg.citations && msg.citations.length > 0 
                            ? msg.citations.map(c => `<span>• ${c.filename}</span>`).join('') 
                            : '<span>• None (Abstained Response)</span>'
                          }
                        </div>
                        <div style="display:flex; align-items:center; gap:var(--ms-space-2);">
                          <span style="font-weight:var(--ms-font-weight-medium);">Conf:</span>
                          <ms-badge variant="${badgeVariant}">${(msg.confidence_score * 100).toFixed(0)}%</ms-badge>
                          <button class="btn-bookmark" data-id="${msg.id}" style="background:none; border:none; cursor:pointer; color:var(--ms-text-secondary); padding:2px;" aria-label="Bookmark answer">&#9733;</button>
                          ${!msg._simplifiedContent && msg.citations && msg.citations.length > 0 ? `
                            <ms-button size="sm" variant="secondary" class="btn-explain" data-id="${msg.id}">Explain Simply</ms-button>
                          ` : ''}
                        </div>
                      </div>
                    ` : ''}
                  </div>
                `;
              }).join('')
            }
          </div>

          <div class="input-bar">
            <form id="query-form">
              <input type="text" id="query-input" placeholder="e.g. DZIRE brake pad specifications?" required ${!this.activeSessionId ? 'disabled' : ''} />
              <ms-button type="submit" variant="primary" id="send-btn" ${!this.activeSessionId ? 'disabled' : ''}>Send</ms-button>
            </form>
          </div>
        </div>
      </div>
    `;
  }
}

customElements.define('chat-view', ChatView);
export default ChatView;
