/**
 * Maruti Suzuki Knowledge Assistant — Application Entry Point.
 *
 * Imports components, registers routes, and boots the application.
 *
 * @module app
 */

// Import Shared Components Registry to register all global components
import './shared/components/index.js';

// Import Views to register custom elements for routing
import './modules/dashboard/DashboardView.js';
import './modules/chat/ChatView.js';
import './modules/documents/DocumentsView.js';
import './modules/projects/ProjectsView.js';
import './modules/departments/DepartmentsView.js';
import './modules/admin/AdminView.js';
import './modules/search/SearchView.js';
// AuthView removed
import './modules/knowledge-graph/KnowledgeGraphView.js';
import './modules/notifications/NotificationsView.js';

import { registerRoute, initRouter, navigateTo } from './shared/router/router.js';
import { setState, getState, subscribe } from './shared/store/AppStore.js';
import apiClient from './shared/api/apiClient.js';
import MsToast from './shared/components/MsToast.js';

/**
 * Boot the application.
 */
async function init() {
  // Register routes mapping URLs to custom elements
  // Register routes mapping URLs to custom elements
  // Auth route removed per user request
  registerRoute('/dashboard', { component: 'dashboard-view', title: 'Dashboard' });
  registerRoute('/chat', { component: 'chat-view', title: 'AI Chat Assistant' });
  registerRoute('/documents', { component: 'documents-view', title: 'Document Manager' });
  registerRoute('/projects', { component: 'projects-view', title: 'Projects Catalog' });
  registerRoute('/departments', { component: 'departments-view', title: 'Departments Directory' });
  registerRoute('/admin', { component: 'admin-view', title: 'Platform Administration' });
  registerRoute('/search', { component: 'search-view', title: 'Enterprise Search' });
  registerRoute('/knowledge-graph', { component: 'knowledge-graph-view', title: 'Knowledge Graph' });
  registerRoute('/notifications', { component: 'notifications-view', title: 'System Notifications' });

  // Set dummy authenticated state since auth is completely removed
  setState({
    auth: {
      isAuthenticated: true,
      user: { username: 'plat_admin_user', role: { name: 'platform_admin' }, full_name: 'Platform Admin' },
      token: 'dummy_token'
    }
  });

  // Initialize router
  initRouter();

  // Reactive unread notification indicator update
  subscribe('notifications', (unreadList) => {
    const countEl = document.getElementById('notification-count');
    if (countEl) {
      const count = unreadList.length;
      countEl.textContent = count;
      countEl.style.display = count > 0 ? 'inline-flex' : 'none';
    }
  });


  // Notification Poller logic
  const startNotificationPoller = () => {
    setInterval(async () => {
      const auth = getState('auth');
      if (!auth || !auth.isAuthenticated) return;

      try {
        const unread = await apiClient.get('/notifications/unread');
        const current = getState('notifications') || [];

        // Check for new notifications
        const currentIds = new Set(current.map(n => n.id));
        const newItems = unread.filter(n => !currentIds.has(n.id));

        if (newItems.length > 0) {
          // Trigger toast message for each new alert
          newItems.forEach(n => {
            MsToast.show(n.message, n.type);
          });
          setState({ notifications: unread });
        }
      } catch (err) {
        // Quiet failure during background polling
      }
    }, 15000);
  };
  startNotificationPoller();


  // API connectivity test
  const healthUrl = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://127.0.0.1:8000/health'
    : '/health';
  fetch(healthUrl)
    .then(res => res.json())
    .then(data => {
      if (data.status === 'ok') {
        const logo = document.querySelector('.sidebar-brand-logo');
        if (logo) {
          logo.style.background = 'linear-gradient(135deg, var(--ms-color-success-500), var(--ms-color-primary-500))';
        }
      }
    })
    .catch(() => {
      // Degraded state handler
    });
}


// Boot when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
