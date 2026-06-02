/** Shared reusable UI components */

// ── Avatar ────────────────────────────────────────────────
export function Avatar({ name, size = 'md', admin = false }) {
  const initials = name
    ? name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase()
    : '?'
  return (
    <div className={`avatar avatar-${size} ${admin ? 'avatar-admin' : ''}`}>
      {initials}
    </div>
  )
}

// ── Badge ─────────────────────────────────────────────────
export function Badge({ status, label }) {
  return (
    <span className={`badge badge-${status}`}>
      {label || status}
    </span>
  )
}

// ── Star rating (display only) ────────────────────────────
export function Stars({ n }) {
  return (
    <span className="stars">
      {'★'.repeat(n)}{'☆'.repeat(5 - n)}
    </span>
  )
}

// ── Interactive star picker ────────────────────────────────
export function StarPicker({ value, onChange }) {
  return (
    <div style={{ display: 'flex', gap: 2 }}>
      {[1, 2, 3, 4, 5].map(n => (
        <button
          key={n}
          type="button"
          className={`star-btn ${value >= n ? 'on' : 'off'}`}
          onClick={() => onChange(n)}
        >
          ★
        </button>
      ))}
    </div>
  )
}

// ── Modal ─────────────────────────────────────────────────
export function Modal({ title, subtitle, onClose, children }) {
  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <button className="modal-close" onClick={onClose}>✕</button>
        {title && <div className="modal-title">{title}</div>}
        {subtitle && <div className="modal-sub">{subtitle}</div>}
        {children}
      </div>
    </div>
  )
}

// ── Alert ─────────────────────────────────────────────────
export function Alert({ type = 'info', children }) {
  return <div className={`alert alert-${type}`}>{children}</div>
}

// ── Progress bar ──────────────────────────────────────────
export function ProgressBar({ value }) {
  return (
    <div className="progress-bar">
      <div className="progress-fill" style={{ width: `${value}%` }} />
    </div>
  )
}

// ── Section header ────────────────────────────────────────
export function SectionHeader({ title, meta, children }) {
  return (
    <div className="section-header">
      <span className="section-title">{title}</span>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        {meta && <span className="section-meta">{meta}</span>}
        {children}
      </div>
    </div>
  )
}

// ── Tab bar ───────────────────────────────────────────────
export function TabBar({ tabs, active, onChange }) {
  return (
    <div className="tab-bar">
      {tabs.map(tab => (
        <button
          key={tab.id}
          className={`tab-item ${active === tab.id ? 'active' : ''}`}
          onClick={() => onChange(tab.id)}
        >
          {tab.label}
          {tab.badge != null && (
            <span className="nav-badge" style={{ marginLeft: 6 }}>{tab.badge}</span>
          )}
        </button>
      ))}
    </div>
  )
}

// ── Reply block ───────────────────────────────────────────
export function ReplyBlock({ body, sent = false }) {
  const cls = sent ? 'reply-success-block' : 'reply-block'
  const labelCls = sent ? 'reply-success-label' : 'reply-label'
  const label = sent ? 'Reply sent' : 'Admin reply'
  return (
    <div className={cls}>
      <div className={labelCls}>{label}</div>
      <p style={{ fontSize: 13, color: 'var(--ink-light)' }}>{body}</p>
    </div>
  )
}

// ── Data table wrapper ────────────────────────────────────
export function DataTable({ columns, rows, onRowClick }) {
  if (!rows.length) {
    return (
      <div className="empty-state" style={{ padding: '40px 24px' }}>
        <div className="empty-state-icon">📭</div>
        <h3>No records found</h3>
      </div>
    )
  }
  return (
    <table className="data-table">
      <thead>
        <tr>{columns.map(col => <th key={col.key}>{col.label}</th>)}</tr>
      </thead>
      <tbody>
        {rows.map((row, i) => (
          <tr key={row.id ?? i} onClick={() => onRowClick?.(row)}
            style={{ cursor: onRowClick ? 'pointer' : 'default' }}>
            {columns.map(col => (
              <td key={col.key} className={col.className}>
                {col.render ? col.render(row) : row[col.key]}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  )
}

// ── Empty state ───────────────────────────────────────────
export function EmptyState({ icon = '📭', title, description, action }) {
  return (
    <div className="empty-state">
      <div className="empty-state-icon">{icon}</div>
      <h3>{title}</h3>
      {description && <p>{description}</p>}
      {action && <div style={{ marginTop: 18 }}>{action}</div>}
    </div>
  )
}
