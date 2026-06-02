import { useState, useEffect } from 'react'
import { Stars, Alert, SectionHeader, ReplyBlock, Avatar } from '../../components/UI'
import { useAuth } from '../../context/AuthContext'
import { feedback as feedbackApi, complaints as complaintsApi, inbox as inboxApi } from '../../api'

const CAT_LABEL = { complaint_reply: 'Complaint Reply', feedback_reply: 'Feedback Reply', system: 'System' }

/* ─── My Feedback ────────────────────────────────────────── */
export function FeedbackPage() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    feedbackApi.list()
      .then(data => setItems(Array.isArray(data) ? data : data.results ?? []))
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div style={{ color: 'var(--ink-muted)', padding: 24 }}>Loading feedback…</div>
  if (error)   return <Alert type="error">Could not load feedback: {error}</Alert>
  if (!items.length) return (
    <div className="empty-state">
      <div className="empty-state-icon">✦</div>
      <h3>No feedback yet</h3>
      <p>After completing a document, you can leave feedback on it.</p>
    </div>
  )

  return (
    <div style={{ maxWidth: 620 }}>
      <SectionHeader title="My Feedback" meta={`${items.length} submitted`} />
      <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        {items.map(fb => (
          <div key={fb.id} className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10 }}>
              <div>
                <div style={{ fontWeight: 500, fontSize: 14, color: 'var(--ink)' }}>Document #{fb.document}</div>
                <div style={{ fontSize: 12, color: 'var(--ink-muted)' }}>
                  {fb.created_at ? new Date(fb.created_at).toLocaleDateString() : ''}
                </div>
              </div>
              {fb.rating && <Stars n={fb.rating} />}
            </div>
            <p style={{ fontSize: 13.5, color: 'var(--ink-light)' }}>{fb.body}</p>
            {fb.admin_reply?.body && <ReplyBlock body={fb.admin_reply.body} />}
          </div>
        ))}
      </div>
    </div>
  )
}

/* ─── Complaints ─────────────────────────────────────────── */
export function ComplaintsPage() {
  const [items, setItems]       = useState([])
  const [loading, setLoading]   = useState(true)
  const [error, setError]       = useState('')
  const [showForm, setShowForm] = useState(false)
  const [subject, setSubject]   = useState('')
  const [body, setBody]         = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [submitted, setSubmitted]   = useState(false)
  const [submitError, setSubmitError] = useState('')

  useEffect(() => {
    complaintsApi.list()
      .then(data => setItems(Array.isArray(data) ? data : data.results ?? []))
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  const handleSubmit = async () => {
    if (!subject.trim() || !body.trim()) return
    setSubmitting(true); setSubmitError('')
    try {
      const newComplaint = await complaintsApi.submit(subject, body)
      setItems(prev => [newComplaint, ...prev])
      setSubmitted(true)
      setSubject(''); setBody('')
    } catch (err) {
      setSubmitError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) return <div style={{ color: 'var(--ink-muted)', padding: 24 }}>Loading complaints…</div>
  if (error)   return <Alert type="error">Could not load complaints: {error}</Alert>

  return (
    <div style={{ maxWidth: 620 }}>
      <SectionHeader title="Complaints">
        <button className="btn btn-amber btn-sm" onClick={() => { setShowForm(true); setSubmitted(false) }}>
          + New complaint
        </button>
      </SectionHeader>

      {showForm && (
        <div className="card" style={{ marginBottom: 20 }}>
          <div className="section-title" style={{ marginBottom: 14 }}>Submit a complaint</div>
          {submitted
            ? <Alert type="success">Complaint submitted. An admin will respond shortly.</Alert>
            : <>
                {submitError && <Alert type="error">{submitError}</Alert>}
                <div className="form-group">
                  <label className="form-label">Subject</label>
                  <input className="form-input" placeholder="Brief description of the issue" value={subject} onChange={e => setSubject(e.target.value)} />
                </div>
                <div className="form-group">
                  <label className="form-label">Details</label>
                  <textarea className="form-input" placeholder="Describe the issue in detail…" value={body} onChange={e => setBody(e.target.value)} />
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                  <button className="btn btn-primary btn-sm" disabled={!subject || !body || submitting} onClick={handleSubmit}>
                    {submitting ? 'Submitting…' : 'Submit complaint'}
                  </button>
                  <button className="btn btn-ghost btn-sm" onClick={() => setShowForm(false)}>Cancel</button>
                </div>
              </>
          }
        </div>
      )}

      {!items.length
        ? <div className="empty-state"><div className="empty-state-icon">✉</div><h3>No complaints yet</h3></div>
        : <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {items.map(c => (
              <div key={c.id} className="card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10 }}>
                  <div>
                    <div style={{ fontWeight: 500, fontSize: 14, color: 'var(--ink)' }}>{c.subject}</div>
                    <div style={{ fontSize: 12, color: 'var(--ink-muted)' }}>
                      {c.created_at ? new Date(c.created_at).toLocaleDateString() : ''}
                    </div>
                  </div>
                  <span className={`badge badge-${c.status}`}>{c.status}</span>
                </div>
                <p style={{ fontSize: 13.5, color: 'var(--ink-light)' }}>{c.body}</p>
                {c.admin_reply?.body && <ReplyBlock body={c.admin_reply.body} />}
              </div>
            ))}
          </div>
      }
    </div>
  )
}

/* ─── Inbox ──────────────────────────────────────────────── */
export function InboxPage({ onRead }) {
  const [msgs, setMsgs]       = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState('')
  const [selected, setSelected] = useState(null)

  useEffect(() => {
    inboxApi.list()
      .then(data => setMsgs(Array.isArray(data) ? data : data.results ?? []))
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  const open = async msg => {
    setSelected(msg)
    if (msg.is_read) return
    try {
      await inboxApi.markRead(msg.id)
      setMsgs(prev => {
        const updated = prev.map(m => m.id === msg.id ? { ...m, is_read: true } : m)
        // If no more unread, tell App to clear the badge
        if (updated.every(m => m.is_read) && onRead) onRead()
        return updated
      })
    } catch (_) {}
  }

  const unread = msgs.filter(m => !m.is_read).length

  if (loading) return <div style={{ color: 'var(--ink-muted)', padding: 24 }}>Loading inbox…</div>
  if (error)   return <Alert type="error">Could not load inbox: {error}</Alert>

  if (selected) return (
    <div style={{ maxWidth: 600 }}>
      <button className="btn btn-ghost btn-sm" style={{ marginBottom: 18 }} onClick={() => setSelected(null)}>
        ← Inbox
      </button>
      <div className="card">
        <div style={{ fontSize: 10.5, fontWeight: 500, color: 'var(--amber)', letterSpacing: 0.5, textTransform: 'uppercase', marginBottom: 6 }}>
          {CAT_LABEL[selected.category] || selected.category}
        </div>
        <h2 style={{ fontFamily: "'Playfair Display', serif", fontSize: 20, fontWeight: 500, marginBottom: 5 }}>
          {selected.subject}
        </h2>
        <div style={{ fontSize: 12, color: 'var(--ink-muted)', marginBottom: 20 }}>
          {selected.created_at ? new Date(selected.created_at).toLocaleDateString() : ''}
        </div>
        <p style={{ fontSize: 14, color: 'var(--ink-light)', lineHeight: 1.8 }}>{selected.body}</p>
      </div>
    </div>
  )

  return (
    <div style={{ maxWidth: 620 }}>
      <SectionHeader title="Inbox" meta={`${unread} unread`} />
      {!msgs.length
        ? <div className="empty-state"><div className="empty-state-icon">◉</div><h3>Inbox is empty</h3><p>Admin replies to your complaints and feedback appear here.</p></div>
        : <div className="card card-flush">
            {msgs.map(msg => (
              <div key={msg.id} className={`inbox-item ${!msg.is_read ? 'unread' : ''}`} onClick={() => open(msg)}>
                <div>{!msg.is_read ? <div className="unread-dot" /> : <div className="read-dot" />}</div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 2 }}>
                    <span className={`inbox-subject ${msg.is_read ? 'read' : ''}`}>{msg.subject}</span>
                    <span className="inbox-date">
                      {msg.created_at ? new Date(msg.created_at).toLocaleDateString() : ''}
                    </span>
                  </div>
                  <div className="inbox-preview">{msg.body}</div>
                  <span className="inbox-cat-tag">{CAT_LABEL[msg.category] || msg.category}</span>
                </div>
              </div>
            ))}
          </div>
      }
    </div>
  )
}

/* ─── Profile ────────────────────────────────────────────── */
export function ProfilePage() {
  const { user, updateUser } = useAuth()
  const [firstName, setFirstName] = useState(user?.name?.split(' ')[0] || '')
  const [lastName,  setLastName]  = useState(user?.name?.split(' ').slice(1).join(' ') || '')
  const [phone,     setPhone]     = useState('')
  const [saved,     setSaved]     = useState(false)
  const [saveError, setSaveError] = useState('')
  const [oldPw,     setOldPw]     = useState('')
  const [newPw,     setNewPw]     = useState('')
  const [confirmPw, setConfirmPw] = useState('')
  const [pwDone,    setPwDone]    = useState(false)
  const [pwError,   setPwError]   = useState('')

  const handleSave = async () => {
    setSaved(false); setSaveError('')
    try {
      const { auth } = await import('../../api')
      await auth.updateProfile({ first_name: firstName, last_name: lastName, phone })
      updateUser({ name: `${firstName} ${lastName}`.trim() })
      setSaved(true)
    } catch (err) { setSaveError(err.message) }
  }

  const handlePassword = async () => {
    setPwDone(false); setPwError('')
    if (newPw !== confirmPw) { setPwError('Passwords do not match.'); return }
    try {
      const { auth } = await import('../../api')
      await auth.changePassword(oldPw, newPw)
      setPwDone(true)
      setOldPw(''); setNewPw(''); setConfirmPw('')
    } catch (err) { setPwError(err.message) }
  }

  return (
    <div style={{ maxWidth: 500 }}>
      <div className="card" style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 20 }}>
          <Avatar name={user?.name} size="lg" />
          <div>
            <div style={{ fontFamily: "'Playfair Display', serif", fontSize: 20, fontWeight: 500 }}>{user?.name}</div>
            <div style={{ fontSize: 13, color: 'var(--ink-muted)' }}>{user?.email}</div>
            <span className="badge badge-approved" style={{ marginTop: 5 }}>Approved</span>
          </div>
        </div>
        <div className="divider" />
        <div className="section-title" style={{ margin: '16px 0 14px' }}>Edit profile</div>
        {saved     && <Alert type="success">Profile updated successfully.</Alert>}
        {saveError && <Alert type="error">{saveError}</Alert>}
        <div className="form-row">
          <div className="form-group">
            <label className="form-label">First name</label>
            <input className="form-input" value={firstName} onChange={e => setFirstName(e.target.value)} />
          </div>
          <div className="form-group">
            <label className="form-label">Last name</label>
            <input className="form-input" value={lastName} onChange={e => setLastName(e.target.value)} />
          </div>
        </div>
        <div className="form-group">
          <label className="form-label">Email address</label>
          <input className="form-input" type="email" value={user?.email || ''} readOnly />
        </div>
        <div className="form-group">
          <label className="form-label">Phone</label>
          <input className="form-input" type="tel" placeholder="+91 98765 43210" value={phone} onChange={e => setPhone(e.target.value)} />
        </div>
        <button className="btn btn-primary btn-sm" onClick={handleSave}>Save changes</button>
      </div>

      <div className="card">
        <div className="section-title" style={{ marginBottom: 14 }}>Change password</div>
        {pwDone  && <Alert type="success">Password updated. Please sign in again.</Alert>}
        {pwError && <Alert type="error">{pwError}</Alert>}
        <div className="form-group">
          <label className="form-label">Current password</label>
          <input className="form-input" type="password" placeholder="••••••••" value={oldPw} onChange={e => setOldPw(e.target.value)} />
        </div>
        <div className="form-group">
          <label className="form-label">New password</label>
          <input className="form-input" type="password" placeholder="Min. 8 characters" value={newPw} onChange={e => setNewPw(e.target.value)} />
        </div>
        <div className="form-group">
          <label className="form-label">Confirm new password</label>
          <input className="form-input" type="password" placeholder="Re-enter new password" value={confirmPw} onChange={e => setConfirmPw(e.target.value)} />
        </div>
        <button className="btn btn-ghost btn-sm" onClick={handlePassword} disabled={!oldPw || !newPw || !confirmPw}>
          Update password
        </button>
      </div>
    </div>
  )
}
