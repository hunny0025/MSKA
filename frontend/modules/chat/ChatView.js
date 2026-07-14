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

  getSuggestions() {
    const activeProject = this.projects.find(p => p.id === this.selectedProjectId);
    const projectName = activeProject ? activeProject.name : '';

    if (projectName.includes('Welding')) {
      return [
        "How do I calibrate the Fanuc R-2000iC welding robot?",
        "What safety precautions are required for Line 4 welding robots?",
        "What is the acceptable TCP drift limit over 8 hours?"
      ];
    } else if (projectName.includes('Engine')) {
      return [
        "What is the compression ratio of the K15C smart hybrid engine?",
        "What proprietary process is used for cylinder bore coating?"
      ];
    } else if (projectName.includes('Safety')) {
      return [
        "What PPE is mandatory in production and grinding zones?",
        "How do I report chemical spills and injuries?"
      ];
    } else if (projectName.includes('Supplier')) {
      return [
        "What is Sona BLW's defect rate?",
        "Show supplier defect rates from recent audits."
      ];
    } else if (projectName.includes('HR')) {
      return [
        "Show Rajesh Kumar's salary details."
      ];
    }
    return [
      "How do I configure calibration settings?",
      "Show assembly specifications."
    ];
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

    // Send query — auto-creates session if needed
    const form = this.shadowRoot.querySelector('#query-form');
    if (form) {
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const input = this.shadowRoot.querySelector('#query-input');
        const submitBtn = this.shadowRoot.querySelector('#send-btn');
        const queryText = input.value.trim();

        if (!queryText) return;

        // Auto-create session if none
        if (!this.activeSessionId) {
          try {
            const newSession = await apiClient.post('/chat/sessions', {
              project_id: this.selectedProjectId,
              title: queryText.substring(0, 40) + '...'
            });
            this.activeSessionId = newSession.id;
            this.sessions.unshift(newSession);
          } catch (err) {
            MsToast.show('Failed to create session', 'danger');
            return;
          }
        }

        submitBtn.setAttribute('loading', '');
        input.setAttribute('disabled', '');

        // Optimistically insert user message into view local list
        this.messages.push({
          id: 'temp-u',
          role: 'user',
          content: queryText
        });
        this.render();
        this.setupListeners();
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

    // Suggested question clicks — auto-creates session if none exists
    this.shadowRoot.querySelectorAll('.suggestion-chip').forEach(chip => {
      chip.addEventListener('click', async (e) => {
        const question = e.currentTarget.getAttribute('data-question');
        
        // Auto-create session if none exists
        if (!this.activeSessionId) {
          try {
            const newSession = await apiClient.post('/chat/sessions', {
              project_id: this.selectedProjectId,
              title: question.substring(0, 40) + '...'
            });
            this.activeSessionId = newSession.id;
            this.sessions.unshift(newSession);
          } catch (err) {
            MsToast.show('Failed to create session', 'danger');
            return;
          }
        }

        // Submit the query directly
        try {
          this.messages.push({ id: 'temp-u', role: 'user', content: question });
          this.render();
          this.setupListeners();
          this.scrollToBottom();

          await apiClient.post(`/chat/sessions/${this.activeSessionId}/query`, {
            query: question
          });
          await this.loadMessages();
        } catch (err) {
          MsToast.show(err.message || 'Failed to submit query', 'danger');
          this.messages.pop();
          this.render();
          this.setupListeners();
        }
      });
    });
  }

  _formatContent(text) {
    if (!text) return '';
    let formatted = text;
    // Replace markdown bold
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Convert table lines to HTML table if present
    if (formatted.includes('|')) {
      const lines = formatted.split('\n');
      let inTable = false;
      let tableHtml = '<table style="width:100%; border-collapse: collapse; margin: 10px 0; font-size: var(--ms-font-size-sm); border: 1px solid var(--ms-color-neutral-300);">';
      const newLines = [];
      
      for (const line of lines) {
        if (line.trim().startsWith('|')) {
          if (!inTable) {
            inTable = true;
          }
          const cells = line.split('|').map(c => c.trim()).filter((c, idx, arr) => idx > 0 && idx < arr.length - 1);
          if (line.includes('---')) continue; // skip divider line
          
          const isHeader = line.includes('Supplier') || line.includes('Part'); // crude header test
          tableHtml += `<tr style="border-bottom: 1px solid var(--ms-color-neutral-200); ${isHeader ? 'background-color: var(--ms-surface-secondary); font-weight: bold;' : ''}">`;
          for (const cell of cells) {
            tableHtml += `<td style="padding: 8px; border-right: 1px solid var(--ms-color-neutral-200);">${cell}</td>`;
          }
          tableHtml += '</tr>';
        } else {
          if (inTable) {
            inTable = false;
            tableHtml += '</table>';
            newLines.push(tableHtml);
            tableHtml = '<table style="width:100%; border-collapse: collapse; margin: 10px 0; font-size: var(--ms-font-size-sm); border: 1px solid var(--ms-color-neutral-300);">';
          }
          newLines.push(line);
        }
      }
      if (inTable) {
        tableHtml += '</table>';
        newLines.push(tableHtml);
      }
      formatted = newLines.join('\n');
    }

    // Convert bullet points to list items
    formatted = formatted.replace(/•\s*(.*?)(?=\n|$)/g, '<li>$1</li>');
    // Wrap consecutive list items in <ul>
    formatted = formatted.replace(/(<li>.*?<\/li>)+/gs, '<ul>$&</ul>');
    // Replace newlines with breaks
    formatted = formatted.replace(/\n/g, '<br/>');
    return formatted;
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

        .suggestions-container {
          display: flex;
          flex-direction: column;
          gap: var(--ms-space-3);
          margin-top: var(--ms-space-6);
          align-items: center;
        }

        .suggestion-title {
          font-size: var(--ms-font-size-xs);
          font-weight: var(--ms-font-weight-semibold);
          color: var(--ms-text-secondary);
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }

        .suggestion-chips {
          display: flex;
          flex-wrap: wrap;
          gap: var(--ms-space-2);
          justify-content: center;
          max-width: 600px;
        }

        .suggestion-chip {
          background-color: var(--ms-surface-secondary);
          border: 1px solid var(--ms-color-neutral-300);
          border-radius: var(--ms-radius-full);
          padding: var(--ms-space-2) var(--ms-space-4);
          font-size: var(--ms-font-size-xs);
          color: var(--ms-color-primary-700);
          cursor: pointer;
          transition: all var(--ms-transition-fast);
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        }

        .suggestion-chip:hover {
          background-color: var(--ms-color-primary-50);
          border-color: var(--ms-color-primary-300);
          transform: translateY(-1px);
        }

        .suggestions-bar {
          padding: var(--ms-space-2) var(--ms-space-6);
          border-top: 1px solid var(--ms-color-neutral-200);
          background-color: var(--ms-surface-secondary);
          display: flex;
          align-items: center;
          gap: var(--ms-space-3);
          overflow-x: auto;
          scrollbar-width: none;
        }

        .suggestions-bar::-webkit-scrollbar {
          display: none;
        }

        .suggestions-bar-title {
          font-size: var(--ms-font-size-xs);
          font-weight: var(--ms-font-weight-semibold);
          color: var(--ms-text-secondary);
          white-space: nowrap;
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }

        .suggestions-bar-chips {
          display: flex;
          gap: var(--ms-space-2);
        }

        .suggestions-bar-chips .suggestion-chip {
          white-space: nowrap;
          box-shadow: none;
          padding: var(--ms-space-1) var(--ms-space-3);
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
            ${((!this.activeSessionId) || (this.activeSessionId && this.messages.length === 0)) ? `
              <div style="text-align:center; color:var(--ms-text-tertiary); margin:auto; padding:var(--ms-space-6);">
                <div style="font-size:24px; margin-bottom:var(--ms-space-3);">🤖</div>
                <div style="font-size:var(--ms-font-size-lg); font-weight:var(--ms-font-weight-semibold); color:var(--ms-text-primary); margin-bottom:var(--ms-space-2);">
                  Ask Maruti Suzuki Knowledge Assistant
                </div>
                <div style="margin-bottom:var(--ms-space-5); max-width:480px; line-height:1.6;">
                  Ask natural-language questions about SOPs, engine specifications, supplier audits, safety protocols, and more.
                </div>
                <div class="suggestions-container">
                  <div class="suggestion-title">Try asking</div>
                  <div class="suggestion-chips">
                    ${this.getSuggestions().map(q => `
                      <button class="suggestion-chip" data-question="${q}">${q}</button>
                    `).join('')}
                  </div>
                </div>
              </div>
            ` : this.messages.map(msg => {
                const badgeVariant = msg.confidence_score >= 0.8 ? 'success' : msg.confidence_score >= 0.65 ? 'warning' : 'danger';
                
                return `
                  <div class="message-item ${msg.role}">
                    <div>${this._formatContent(msg.content)}</div>

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

          <div class="suggestions-bar">
            <span class="suggestions-bar-title">Try asking:</span>
            <div class="suggestions-bar-chips">
              ${this.getSuggestions().map(q => `
                <button class="suggestion-chip" data-question="${q}">${q}</button>
              `).join('')}
            </div>
          </div>

          <div class="input-bar">
            <form id="query-form">
              <input type="text" id="query-input" placeholder="Ask about welding SOPs, engine specs, safety protocols..." required />
              <ms-button type="submit" variant="primary" id="send-btn">Send</ms-button>
            </form>
          </div>
        </div>
      </div>
    `;
  }
}

customElements.define('chat-view', ChatView);
export default ChatView;
