import { useAuth } from '../context/AuthContext'
import { Avatar } from './UI'

const PAGE_TITLES = {
  dashboard:    'Dashboard',
  upload:       'Upload Notes',
  documents:    'My Documents',
  feedback:     'My Feedback',
  complaints:   'Complaints',
  inbox:        'Inbox',
  profile:      'Profile',
  'a-dashboard':  'Admin Dashboard',
  'a-requests':   'Account Requests',
  'a-complaints': 'Complaint Management',
  'a-feedbacks':  'Feedback & Reviews',
  'a-profile':    'Profile',
}

export default function Topbar({ page, setPage }) {
  const { user } = useAuth()
  const isAdmin = user?.role === 'admin'

  return (
    <header className="topbar">
      <span className="topbar-title">{PAGE_TITLES[page] || 'Digitizer'}</span>

      <div className="topbar-actions">
        {!isAdmin && (
          <button className="btn btn-amber btn-sm" onClick={() => setPage('upload')}>
            ↑ Upload Notes
          </button>
        )}
        <Avatar name={user?.name} size="sm" admin={isAdmin} />
        <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--ink)' }}>
          {user?.name}
        </span>
      </div>
    </header>
  )
}
