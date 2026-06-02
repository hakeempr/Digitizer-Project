import { useAuth } from '../context/AuthContext'
import { Avatar } from './UI'

const USER_NAV = [
  { id: 'dashboard',  icon: '⊞', label: 'Dashboard' },
  { id: 'upload',     icon: '↑', label: 'Upload Notes' },
  { id: 'documents',  icon: '◻', label: 'My Documents' },
  { id: 'feedback',   icon: '✦', label: 'My Feedback' },
  { id: 'complaints', icon: '✉', label: 'Complaints' },
  { id: 'inbox',      icon: '◉', label: 'Inbox' },
  { id: 'profile',    icon: '◎', label: 'Profile' },
]

const ADMIN_NAV = [
  { id: 'a-dashboard',  icon: '⊞', label: 'Dashboard' },
  { id: 'a-requests',   icon: '◈', label: 'Account Requests' },
  { id: 'a-complaints', icon: '✉', label: 'Complaints' },
  { id: 'a-feedbacks',  icon: '✦', label: 'Feedback & Reviews' },
  { id: 'a-profile',    icon: '◎', label: 'Profile' },
]

export default function Sidebar({ page, setPage, badges = {} }) {
  const { user, logout } = useAuth()
  const isAdmin = user?.role === 'admin'
  const nav = isAdmin ? ADMIN_NAV : USER_NAV

  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="sidebar-logo">
        <div className="sidebar-logo-mark">✍️ Digitizer</div>
        <div className="sidebar-logo-sub">{isAdmin ? 'Admin Console' : 'User Portal'}</div>
      </div>

      {/* Navigation */}
      <nav className="sidebar-nav">
        {nav.map(item => {
          const badge = badges[item.id]
          return (
            <button
              key={item.id}
              className={`nav-item ${page === item.id ? 'active' : ''}`}
              onClick={() => setPage(item.id)}
            >
              <span className="nav-icon">{item.icon}</span>
              {item.label}
              {badge ? <span className="nav-badge">{badge}</span> : null}
            </button>
          )
        })}
      </nav>

      {/* User footer */}
      <div className="sidebar-footer">
        <div className="user-chip" onClick={logout} title="Click to log out">
          <Avatar name={user?.name} size="sm" admin={isAdmin} />
          <div className="user-chip-info">
            <div className="name">{user?.name}</div>
            <div className="role">{isAdmin ? 'Administrator' : 'User'} · Log out</div>
          </div>
        </div>
      </div>
    </aside>
  )
}
