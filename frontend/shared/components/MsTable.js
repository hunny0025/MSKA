/**
 * Maruti Suzuki Knowledge Assistant — DataTable Web Component
 *
 * A reusable data table component with support for headers, sorting, and row render.
 * Usage:
 * <ms-table id="my-table"></ms-table>
 *
 * In JS:
 * document.getElementById('my-table').data = {
 *   columns: [{ key: 'id', label: 'ID' }, { key: 'name', label: 'Name', sortable: true }],
 *   rows: [{ id: 1, name: 'SOP Assembly' }]
 * };
 */

class MsTable extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._data = { columns: [], rows: [] };
    this._sortKey = null;
    this._sortDesc = false;
  }

  connectedCallback() {
    this.render();
  }

  set data(value) {
    this._data = value;
    this.render();
  }

  get data() {
    return this._data;
  }

  handleSort(columnKey) {
    if (this._sortKey === columnKey) {
      this._sortDesc = !this._sortDesc;
    } else {
      this._sortKey = columnKey;
      this._sortDesc = false;
    }

    this._data.rows.sort((a, b) => {
      let valA = a[columnKey];
      let valB = b[columnKey];

      if (typeof valA === 'string') {
        return this._sortDesc 
          ? valB.localeCompare(valA)
          : valA.localeCompare(valB);
      }
      return this._sortDesc ? valB - valA : valA - valB;
    });

    this.render();
  }

  render() {
    const { columns, rows } = this._data;

    this.shadowRoot.innerHTML = `
      <style>
        .table-container {
          width: 100%;
          overflow-x: auto;
          border-radius: var(--ms-radius-md);
          border: 1px solid var(--ms-color-neutral-200);
          box-shadow: var(--ms-shadow-sm);
          background-color: var(--ms-surface-primary);
        }

        table {
          width: 100%;
          border-collapse: collapse;
          text-align: left;
          font-family: var(--ms-font-family-sans);
          font-size: var(--ms-font-size-sm);
        }

        th {
          background-color: var(--ms-surface-secondary);
          color: var(--ms-text-secondary);
          font-weight: var(--ms-font-weight-semibold);
          padding: var(--ms-space-3) var(--ms-space-4);
          border-bottom: 1px solid var(--ms-color-neutral-200);
          user-select: none;
        }

        th.sortable {
          cursor: pointer;
        }

        th.sortable:hover {
          color: var(--ms-text-primary);
          background-color: var(--ms-color-neutral-100);
        }

        td {
          padding: var(--ms-space-3) var(--ms-space-4);
          border-bottom: 1px solid var(--ms-color-neutral-150, #f3f4f6);
          color: var(--ms-text-primary);
        }

        tr:last-child td {
          border-bottom: none;
        }

        tr:hover td {
          background-color: var(--ms-color-neutral-50);
        }

        .sort-indicator {
          margin-left: var(--ms-space-1);
          font-size: var(--ms-font-size-xs);
        }

        .empty-state {
          padding: var(--ms-space-8);
          text-align: center;
          color: var(--ms-text-secondary);
          background-color: var(--ms-surface-primary);
        }
      </style>
      <div class="table-container">
        <table>
          <thead>
            <tr>
              ${columns.map(col => `
                <th class="${col.sortable ? 'sortable' : ''}" data-key="${col.key}">
                  ${col.label}
                  ${this._sortKey === col.key 
                    ? `<span class="sort-indicator">${this._sortDesc ? '▼' : '▲'}</span>` 
                    : ''
                  }
                </th>
              `).join('')}
            </tr>
          </thead>
          <tbody>
            ${rows.length === 0 ? `
              <tr>
                <td colspan="${columns.length}">
                  <div class="empty-state">No records found.</div>
                </td>
              </tr>
            ` : rows.map(row => `
              <tr>
                ${columns.map(col => `<td>${row[col.key] !== undefined ? row[col.key] : ''}</td>`).join('')}
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    `;

    // Attach sorting click events
    this.shadowRoot.querySelectorAll('th.sortable').forEach(th => {
      th.addEventListener('click', () => {
        this.handleSort(th.getAttribute('data-key'));
      });
    });
  }
}

customElements.define('ms-table', MsTable);
export default MsTable;
