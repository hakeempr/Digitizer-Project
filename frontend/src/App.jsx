import { useState, useEffect, useCallback } from 'react'
import { AuthProvider, useAuth } from './context/AuthContext'

import Sidebar  from './components/Sidebar'
import Topbar   from './components/Topbar'
import LoginPage from './pages/LoginPage'

import UserDashboard  from './pages/user/Dashboard'
import UploadPage     from './pages/user/UploadPage'
import DocumentsPage  from './pages/user/DocumentsPage'
import { FeedbackPage, ComplaintsPage, InboxPage, ProfilePage } from './pages/user/UserPages'
import { AdminDashboard, AdminRequests, AdminComplaints, AdminFeedbacks, AdminProfile } from './pages/admin/AdminPages'

/* ─── Inner authenticated app ───────────────────────────── */
function AuthenticatedApp() {
  const { user } = useAuth()
  const isAdmin  = user?.role === 'admin'

  const defaultPage = isAdmin ? 'a-dashboard' : 'dashboard'
  const [page, setPage] = useState(defaultPage)

  // ── Live badge counts from API ─────────────────────────
  const [inboxUnread,      setInboxUnread]      = useState(0)
  const [pendingRequests,  setPendingRequests]  = useState(0)
  const [openComplaints,   setOpenComplaints]   = useState(0)

  const refreshBadges = useCallback(() => {
    if (isAdmin) {
      // Admin: fetch dashboard stats for badge counts
      import('./api').then(({ adminDashboard }) => {
        adminDashboard.stats()
          .then(data => {
            setPendingRequests(data.pending_requests  ?? 0)
            setOpenComplaints(data.open_complaints    ?? 0)
          })
          .catch(() => {})
      })
    } else {
      // User: fetch unread inbox count
      import('./api').then(({ inbox }) => {
        inbox.unreadCount()
          .then(data => setInboxUnread(data.unread_count ?? 0))
          .catch(() => {})
      })
    }
  }, [isAdmin])

  // Fetch on mount and whenever page changes
  useEffect(() => {
    refreshBadges()
  }, [page, refreshBadges])

  // Also refresh every 30 seconds in background
  useEffect(() => {
    const iv = setInterval(refreshBadges, 30000)
    return () => clearInterval(iv)
  }, [refreshBadges])

  const badges = isAdmin
    ? {
        'a-requests':   pendingRequests || undefined,
        'a-complaints': openComplaints  || undefined,
      }
    : {
        inbox: inboxUnread || undefined,
      }

  // When user visits inbox, mark all read and clear badge
  const handleSetPage = (newPage) => {
    setPage(newPage)
    if (newPage === 'inbox' && !isAdmin) {
      // Optimistically clear badge, API will confirm
      setInboxUnread(0)
    }
  }

  const renderPage = () => {
    switch (page) {
      case 'dashboard':    return <UserDashboard setPage={handleSetPage} />
      case 'upload':       return <UploadPage setPage={handleSetPage} />
      case 'documents':    return <DocumentsPage />
      case 'feedback':     return <FeedbackPage />
      case 'complaints':   return <ComplaintsPage />
      case 'inbox':        return <InboxPage onRead={() => setInboxUnread(0)} />
      case 'profile':      return <ProfilePage />
      case 'a-dashboard':  return <AdminDashboard />
      case 'a-requests':   return <AdminRequests onDecide={refreshBadges} />
      case 'a-complaints': return <AdminComplaints onReply={refreshBadges} />
      case 'a-feedbacks':  return <AdminFeedbacks />
      case 'a-profile':    return <AdminProfile />
      default:             return null
    }
  }

  return (
    <div className="app-shell">
      <Sidebar page={page} setPage={handleSetPage} badges={badges} />
      <div className="main-area">
        <Topbar page={page} setPage={handleSetPage} />
        <main className="page-content">
          {renderPage()}
        </main>
      </div>
    </div>
  )
}

function Root() {
  const { user } = useAuth()
  return user ? <AuthenticatedApp /> : <LoginPage />
}

export default function App() {
  return (
    <AuthProvider>
      <Root />
    </AuthProvider>
  )
}
