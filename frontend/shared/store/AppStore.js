/**
 * Maruti Suzuki Knowledge Assistant — Application State Store.
 *
 * Lightweight pub/sub store (~100 lines, no dependencies) providing
 * centralized state management for all modules. Each module subscribes
 * to the slices of state it cares about.
 *
 * Full implementation in Prompt 3. This file establishes the public API
 * contract that all later modules will depend on.
 *
 * @module AppStore
 */

/**
 * @typedef {Object} AppState
 * @property {Object|null} auth       - Current auth context (user, token, role)
 * @property {Object|null} activeProject  - Currently selected project
 * @property {Object|null} chatSession    - Active chat session state
 * @property {Array}       notifications  - Pending notification queue
 * @property {string}      currentRoute   - Active route path
 */

/** @type {AppState} */
const initialState = {
  auth: null,
  activeProject: null,
  chatSession: null,
  notifications: [],
  currentRoute: '/',
};

/** @type {Map<string, Set<Function>>} */
const listeners = new Map();

/** @type {AppState} */
let state = { ...initialState };

/**
 * Get current state or a specific slice.
 * @param {string} [slice] - Optional state slice key
 * @returns {AppState|*}
 */
export function getState(slice) {
  if (slice) {
    return state[slice];
  }
  return { ...state };
}

/**
 * Update state and notify subscribers of changed slices.
 * @param {Partial<AppState>} updates - Partial state to merge
 */
export function setState(updates) {
  const changedSlices = [];
  for (const [key, value] of Object.entries(updates)) {
    if (state[key] !== value) {
      state[key] = value;
      changedSlices.push(key);
    }
  }
  for (const slice of changedSlices) {
    const sliceListeners = listeners.get(slice);
    if (sliceListeners) {
      for (const callback of sliceListeners) {
        callback(state[slice], state);
      }
    }
  }
}

/**
 * Subscribe to changes on a specific state slice.
 * @param {string} slice - State slice key to watch
 * @param {Function} callback - Called with (sliceValue, fullState)
 * @returns {Function} Unsubscribe function
 */
export function subscribe(slice, callback) {
  if (!listeners.has(slice)) {
    listeners.set(slice, new Set());
  }
  listeners.get(slice).add(callback);
  return () => listeners.get(slice).delete(callback);
}

/**
 * Reset state to initial values (for testing / logout).
 */
export function resetState() {
  state = { ...initialState };
}

export default { getState, setState, subscribe, resetState };
