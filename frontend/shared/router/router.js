/**
 * Maruti Suzuki Knowledge Assistant — Client-side Router.
 *
 * Hash-based SPA router mapping URL fragments to module mount points.
 * Handles route guards, lazy mounting of web components, and document titles.
 *
 * @module Router
 */

import { setState, getState } from '../store/AppStore.js';

/** @type {Map<string, {component: string, title: string, requiresAuth?: boolean}>} */
const routes = new Map();

/**
 * Register a route.
 * @param {string} path - Route path (e.g., '/dashboard')
 * @param {Object} config - Route configuration
 * @param {string} config.component - Web Component tag name to mount
 * @param {string} config.title - Page title
 * @param {boolean} [config.requiresAuth=false] - If route requires authentication
 */
export function registerRoute(path, config) {
  routes.set(path, { requiresAuth: false, ...config });
}

/**
 * Navigate to a route programmatically.
 * @param {string} path - Target route path
 */
export function navigateTo(path) {
  window.location.hash = path;
}

/**
 * Get current route from hash.
 * @returns {string}
 */
export function getCurrentRoute() {
  return window.location.hash.slice(1) || '/dashboard';
}

/**
 * Initialize the router — listen for hash changes and mount the
 * correct module into #main-content.
 */
export function initRouter() {
  const handleRoute = () => {
    let path = getCurrentRoute();
    
    // Simple normalization
    if (!path.startsWith('/')) {
      path = '/' + path;
    }

    setState({ currentRoute: path });

    const route = routes.get(path) || routes.get('/dashboard');
    if (!route) {
      console.error(`Route not found: ${path}`);
      return;
    }

    // Auth Guard Check
    const authState = getState('auth');
    if (route.requiresAuth && (!authState || !authState.isAuthenticated)) {
      console.warn(`Unauthenticated access to ${path} blocked.`);
      // If auth fails, we don't have a login page anymore, just show a message.
      if (window.MsToast) {
        window.MsToast.show('Authentication required. Backend server may not be running.', 'danger');
      }
      return;
    }

    // Set page title
    const titleEl = document.getElementById('page-title');
    if (titleEl) {
      titleEl.textContent = route.title;
    }
    document.title = `${route.title} — Maruti Suzuki Knowledge Assistant`;

    // Mount Component to main-content
    const mainContent = document.getElementById('main-content');
    if (mainContent) {
      // Clear current content
      mainContent.innerHTML = '';
      
      // Create new element matching registered component tag
      const element = document.createElement(route.component);
      element.classList.add('fade-in');
      mainContent.appendChild(element);
    }

    // Update active nav item
    document.querySelectorAll('.sidebar-nav-item').forEach(item => {
      const itemRoute = item.getAttribute('data-route');
      item.classList.toggle('active', `/${itemRoute}` === path);
    });
  };

  window.addEventListener('hashchange', handleRoute);
  handleRoute(); // Initial route trigger
}

export default { registerRoute, navigateTo, getCurrentRoute, initRouter };
