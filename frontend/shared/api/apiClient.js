/**
 * Maruti Suzuki Knowledge Assistant — API Client.
 *
 * Centralized fetch wrapper handling auth headers, token refresh,
 * error normalization, and request/response logging.
 * No module calls fetch() directly — all API access goes through here.
 *
 * Full implementation in Prompt 3. This establishes the public API.
 *
 * @module apiClient
 */

/** @type {string} */
const BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
  ? 'http://127.0.0.1:8000/api/v1' 
  : '/api/v1';


/**
 * Make an authenticated API request.
 *
 * @param {string} endpoint - API endpoint path (e.g., '/chat')
 * @param {Object} [options] - Fetch options
 * @param {string} [options.method='GET'] - HTTP method
 * @param {Object} [options.body] - Request body (auto-serialized to JSON)
 * @param {Object} [options.headers] - Additional headers
 * @param {boolean} [options.raw=false] - If true, return raw Response
 * @returns {Promise<Object>} Parsed JSON response
 * @throws {ApiError} On non-2xx responses
 */
export async function request(endpoint, options = {}) {
  const { method = 'GET', body, headers = {}, raw = false } = options;

  const config = {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...headers,
    },
  };

  // Attach auth token if available
  const token = sessionStorage.getItem('access_token');
  if (token) {
    config.headers['Authorization'] = `Bearer ${token}`;
  }

  if (body) {
    config.body = JSON.stringify(body);
  }

  const response = await fetch(`${BASE_URL}${endpoint}`, config);

  if (raw) {
    return response;
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new ApiError(response.status, error.detail || 'Unknown error');
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return null;
  }

  return response.json();
}

/**
 * Convenience methods.
 */
export const get    = (endpoint, opts) => request(endpoint, { ...opts, method: 'GET' });
export const post   = (endpoint, body, opts) => request(endpoint, { ...opts, method: 'POST', body });
export const put    = (endpoint, body, opts) => request(endpoint, { ...opts, method: 'PUT', body });
export const patch  = (endpoint, body, opts) => request(endpoint, { ...opts, method: 'PATCH', body });
export const del    = (endpoint, opts) => request(endpoint, { ...opts, method: 'DELETE' });

/**
 * Structured API error.
 */
export class ApiError extends Error {
  /**
   * @param {number} status - HTTP status code
   * @param {string} detail - Error message from server
   */
  constructor(status, detail) {
    super(detail);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

export default { request, get, post, put, patch, del, ApiError };
