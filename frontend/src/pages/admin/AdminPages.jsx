import { useState, useEffect } from 'react'
import { Badge, Stars, Avatar, Alert, TabBar, Modal, ReplyBlock, SectionHeader } from '../../components/UI'
import { useAuth } from '../../context/AuthContext'
import { adminDashboard, adminRequests, adminComplaints, adminFeedback } from '../../api'

/* ─── Admin Dashboard ────────────────────────────────────── */
export function AdminDashboard() {
  const [stats,   setStats]   = useState(null)
  const [reqs,    setReqs]    = useState([])
  const [comps,   setComps]   = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      adminDashboard.stats(),
      adminRequests.list(),
      adminComplaints.list(),
    ]).then(([s, r, c]) => {
      setStats(s)
      setReqs(Array.isArray(r) ? r : r.results ?? [])
      setComps(Array.isArray(c) ? c : c.results ?? [])
    }).catch(() => {}).finally(() => setLoading(false))
  }, [])

  if (loading) return <div style={{ color: 'var(--ink-muted)', padding: 24 }}>Loading dashboard…</div>

  return (
    <div>
      <div className="stats-grid">
        <div className="stat-card accent">
          <div className="stat-label">Total Users</div>
          <div className="stat-value">{stats?.total_customers ?? 0}</div>
          <div className="stat-sub">Registered accounts</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Pending Requests</div>
          <div className="stat-value">{stats?.pending_requests ?? 0}</div>
          <div className="stat-sub">Awaiting review</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Open Complaints</div>
          <div className="stat-value">{stats?.open_complaints ?? 0}</div>
          <div className="stat-sub">Need response</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Total Documents</div>
          <div className="stat-value">{stats?.total_documents ?? 0}</div>
          <div className="stat-sub">Processed via OCR</div>
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <SectionHeader title="Recent Account Requests" />
          {reqs.length === 0
            ? <div style={{ color: 'var(--ink-muted)', fontSize: 13 }}>No requests yet.</div>
            : reqs.slice(0, 4).map(r => (
              <div key={r.id} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 0', borderBottom: '1px solid var(--border)' }}>
                <Avatar name={r.customer_detail?.full_name || r.customer} size="md" />
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 500, fontSize: 13.5, color: 'var(--ink)' }}>{r.customer_detail?.full_name || `User #${r.customer}`}</div>
                  <div style={{ fontSize: 12, color: 'var(--ink-muted)' }}>{r.customer_detail?.email}</div>
                </div>
                <Badge status={r.decision} />
              </div>
          ))}
        </div>

        <div className="card">
          <SectionHeader title="Recent Complaints" />
          {comps.length === 0
            ? <div style={{ color: 'var(--ink-muted)', fontSize: 13 }}>No complaints yet.</div>
            : comps.slice(0, 4).map(c => (
              <div key={c.id} style={{ padding: '10px 0', borderBottom: '1px solid var(--border)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 2 }}>
                  <span style={{ fontWeight: 500, fontSize: 13.5, color: 'var(--ink)' }}>{c.subject}</span>
                  <Badge status={c.status} />
                </div>
                <div style={{ fontSize: 12, color: 'var(--ink-muted)' }}>
                  {c.customer_email} · {c.created_at ? new Date(c.created_at).toLocaleDateString() : ''}
                </div>
              </div>
          ))}
        </div>
      </div>
    </div>
  )
}

/* ─── Account Requests ───────────────────────────────────── */
export function AdminRequests({ onDecide }) {
  const [reqs,    setReqs]    = useState([])
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState('')
  const [tab,     setTab]     = useState('pending')
  const [modal,   setModal]   = useState(null)
  const [dec,     setDec]     = useState('')
  const [notes,   setNotes]   = useState('')
  const [saving,  setSaving]  = useState(false)

  useEffect(() => {
    adminRequests.list()
      .then(data => setReqs(Array.isArray(data) ? data : data.results ?? []))
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  const confirm = async () => {
    setSaving(true)
    try {
      await adminRequests.decide(modal.id, dec, notes)
      setReqs(prev => prev.map(r => r.id === modal.id ? { ...r, decision: dec } : r))
      setModal(null); setDec(''); setNotes('')
      if (onDecide) onDecide()
    } catch (err) {
      alert(`Error: ${err.message}`)
    } finally { setSaving(false) }
  }

  const tabList = [
    { id: 'pending',  label: 'Pending',  badge: reqs.filter(r => r.decision === 'pending').length },
    { id: 'approved', label: 'Approved' },
    { id: 'rejected', label: 'Rejected' },
    { id: 'all',      label: 'All' },
  ]
  const filtered = tab === 'all' ? reqs : reqs.filter(r => r.decision === tab)

  if (loading) return <div style={{ color: 'var(--ink-muted)', padding: 24 }}>Loading requests…</div>
  if (error)   return <Alert type="error">Could not load requests: {error}</Alert>

  return (
    <div>
      <TabBar tabs={tabList} active={tab} onChange={setTab} />
      <div className="card card-flush">
        <table className="data-table">
          <thead><tr><th>User</th><th>Email</th><th>Date</th><th>Status</th><th></th></tr></thead>
          <tbody>
            {filtered.length === 0
              ? <tr><td colSpan={5} style={{ textAlign: 'center', padding: 32, color: 'var(--ink-muted)' }}>No records</td></tr>
              : filtered.map(r => (
                <tr key={r.id}>
                  <td className="td-primary">
                    <div style={{ display: 'flex', alignItems: 'center', gap: 9 }}>
                      <Avatar name={r.customer_detail?.full_name || 'U'} size="sm" />
                      {r.customer_detail?.full_name || `User #${r.customer}`}
                    </div>
                  </td>
                  <td className="td-mono">{r.customer_detail?.email}</td>
                  <td>{r.created_at ? new Date(r.created_at).toLocaleDateString() : ''}</td>
                  <td><Badge status={r.decision} /></td>
                  <td>
                    {r.decision === 'pending' && (
                      <button className="btn btn-ghost btn-xs" onClick={() => { setModal(r); setDec(''); setNotes('') }}>
                        Review
                      </button>
                    )}
                  </td>
                </tr>
              ))
            }
          </tbody>
        </table>
      </div>

      {modal && (
        <Modal
          title="Review account request"
          subtitle={`Approve or reject ${modal.customer_detail?.full_name || `User #${modal.customer}`}`}
          onClose={() => setModal(null)}
        >
          <div className="info-block" style={{ marginBottom: 18, lineHeight: 1.9 }}>
            <div><strong>Name:</strong> {modal.customer_detail?.full_name}</div>
            <div><strong>Email:</strong> {modal.customer_detail?.email}</div>
            <div><strong>Registered:</strong> {modal.created_at ? new Date(modal.created_at).toLocaleDateString() : ''}</div>
          </div>
          <div className="form-group">
            <label className="form-label">Decision</label>
            <select className="form-input" value={dec} onChange={e => setDec(e.target.value)}>
              <option value="">Select decision…</option>
              <option value="approved">Approve account</option>
              <option value="rejected">Reject account</option>
            </select>
          </div>
          <div className="form-group">
            <label className="form-label">Admin notes (optional)</label>
            <textarea className="form-input" placeholder="Reason for decision…" value={notes} onChange={e => setNotes(e.target.value)} />
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn btn-success btn-sm" disabled={!dec || saving} onClick={confirm}>
              {saving ? 'Saving…' : 'Confirm decision'}
            </button>
            <button className="btn btn-ghost btn-sm" onClick={() => setModal(null)}>Cancel</button>
          </div>
        </Modal>
      )}
    </div>
  )
}

/* ─── Complaint Management ───────────────────────────────── */
export function AdminComplaints({ onReply }) {
  const [comps,    setComps]    = useState([])
  const [loading,  setLoading]  = useState(true)
  const [error,    setError]    = useState('')
  const [selected, setSelected] = useState(null)
  const [reply,    setReply]    = useState('')
  const [sending,  setSending]  = useState(false)
  const [sent,     setSent]     = useState(false)

  useEffect(() => {
    adminComplaints.list()
      .then(data => setComps(Array.isArray(data) ? data : data.results ?? []))
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  const sendReply = async () => {
    setSending(true)
    try {
      await adminComplaints.reply(selected.id, reply)
      setComps(prev => prev.map(c => c.id === selected.id ? { ...c, status: 'resolved', admin_reply: { body: reply } } : c))
      setSent(true)
      if (onReply) onReply()
    } catch (err) { alert(`Error: ${err.message}`) }
    finally { setSending(false) }
  }

  const back = () => { setSelected(null); setSent(false); setReply('') }

  if (loading) return <div style={{ color: 'var(--ink-muted)', padding: 24 }}>Loading complaints…</div>
  if (error)   return <Alert type="error">Could not load complaints: {error}</Alert>

  if (selected) return (
    <div style={{ maxWidth: 620 }}>
      <button className="btn btn-ghost btn-sm" style={{ marginBottom: 20 }} onClick={back}>← Back</button>
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 18 }}>
          <div>
            <h2 style={{ fontFamily: "'Playfair Display', serif", fontSize: 20, fontWeight: 500, marginBottom: 4 }}>{selected.subject}</h2>
            <div style={{ fontSize: 12.5, color: 'var(--ink-muted)' }}>
              From: <strong style={{ color: 'var(--ink-light)' }}>{selected.customer_email}</strong> · {selected.created_at ? new Date(selected.created_at).toLocaleDateString() : ''}
            </div>
          </div>
          <Badge status={selected.status} />
        </div>
        <div className="info-block" style={{ marginBottom: 18 }}>
          <p style={{ fontSize: 14, lineHeight: 1.8 }}>{selected.body}</p>
        </div>
        {sent || selected.admin_reply?.body
          ? <ReplyBlock body={sent ? reply : selected.admin_reply.body} sent />
          : <>
              <div className="section-title" style={{ marginBottom: 12 }}>Write reply</div>
              <textarea className="form-input" placeholder="Type your reply…" style={{ marginBottom: 12 }} value={reply} onChange={e => setReply(e.target.value)} />
              <button className="btn btn-primary btn-sm" disabled={!reply || sending} onClick={sendReply}>
                {sending ? 'Sending…' : 'Send reply & resolve complaint'}
              </button>
            </>
        }
      </div>
    </div>
  )

  return (
    <div>
      {comps.length === 0
        ? <div className="empty-state"><div className="empty-state-icon">✉</div><h3>No complaints yet</h3></div>
        : <div className="card card-flush">
            <table className="data-table">
              <thead><tr><th>From</th><th>Subject</th><th>Date</th><th>Status</th><th></th></tr></thead>
              <tbody>
                {comps.map(c => (
                  <tr key={c.id}>
                    <td className="td-primary">{c.customer_email}</td>
                    <td style={{ maxWidth: 220, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{c.subject}</td>
                    <td>{c.created_at ? new Date(c.created_at).toLocaleDateString() : ''}</td>
                    <td><Badge status={c.status} /></td>
                    <td>
                      <button className="btn btn-ghost btn-xs" onClick={() => { setSelected(c); setSent(false); setReply('') }}>
                        {c.status === 'open' ? 'Reply' : 'View'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
      }
    </div>
  )
}

/* ─── Feedback Management ────────────────────────────────── */
export function AdminFeedbacks() {
  const [fbs,      setFbs]      = useState([])
  const [loading,  setLoading]  = useState(true)
  const [error,    setError]    = useState('')
  const [selected, setSelected] = useState(null)
  const [reply,    setReply]    = useState('')
  const [sending,  setSending]  = useState(false)
  const [sent,     setSent]     = useState(false)

  useEffect(() => {
    adminFeedback.list()
      .then(data => setFbs(Array.isArray(data) ? data : data.results ?? []))
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  const sendReply = async () => {
    setSending(true)
    try {
      await adminFeedback.reply(selected.id, reply)
      setFbs(prev => prev.map(f => f.id === selected.id ? { ...f, admin_reply: { body: reply } } : f))
      setSent(true)
    } catch (err) { alert(`Error: ${err.message}`) }
    finally { setSending(false) }
  }

  const back = () => { setSelected(null); setSent(false); setReply('') }

  if (loading) return <div style={{ color: 'var(--ink-muted)', padding: 24 }}>Loading feedback…</div>
  if (error)   return <Alert type="error">Could not load feedback: {error}</Alert>

  if (selected) return (
    <div style={{ maxWidth: 580 }}>
      <button className="btn btn-ghost btn-sm" style={{ marginBottom: 20 }} onClick={back}>← Back</button>
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 18 }}>
          <div>
            <div style={{ fontFamily: "'Playfair Display', serif", fontSize: 18, fontWeight: 500, marginBottom: 4 }}>
              Feedback from {selected.customer_email}
            </div>
            <div style={{ fontSize: 12.5, color: 'var(--ink-muted)' }}>
              Document #{selected.document} · {selected.created_at ? new Date(selected.created_at).toLocaleDateString() : ''}
            </div>
          </div>
          {selected.rating && <Stars n={selected.rating} />}
        </div>
        <div className="info-block" style={{ marginBottom: 18 }}>
          <p style={{ fontSize: 14, lineHeight: 1.8 }}>{selected.body}</p>
        </div>
        {sent || selected.admin_reply?.body
          ? <ReplyBlock body={sent ? reply : selected.admin_reply.body} sent />
          : <>
              <div className="section-title" style={{ marginBottom: 12 }}>Write reply</div>
              <textarea className="form-input" placeholder="Respond to the feedback…" style={{ marginBottom: 12 }} value={reply} onChange={e => setReply(e.target.value)} />
              <button className="btn btn-primary btn-sm" disabled={!reply || sending} onClick={sendReply}>
                {sending ? 'Sending…' : 'Send reply'}
              </button>
            </>
        }
      </div>
    </div>
  )

  return (
    <div>
      {fbs.length === 0
        ? <div className="empty-state"><div className="empty-state-icon">✦</div><h3>No feedback yet</h3></div>
        : <div className="card card-flush">
            <table className="data-table">
              <thead><tr><th>From</th><th>Doc</th><th>Rating</th><th>Feedback</th><th>Status</th><th></th></tr></thead>
              <tbody>
                {fbs.map(f => (
                  <tr key={f.id}>
                    <td className="td-primary">{f.customer_email}</td>
                    <td style={{ color: 'var(--ink-muted)' }}>#{f.document}</td>
                    <td>{f.rating ? <Stars n={f.rating} /> : '—'}</td>
                    <td style={{ maxWidth: 200, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{f.body}</td>
                    <td><Badge status={f.admin_reply ? 'resolved' : 'open'} /></td>
                    <td>
                      <button className="btn btn-ghost btn-xs" onClick={() => { setSelected(f); setSent(false); setReply('') }}>
                        {f.admin_reply ? 'View' : 'Reply'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
      }
    </div>
  )
}

/* ─── Admin Profile ──────────────────────────────────────── */
export function AdminProfile() {
  const { user } = useAuth()
  const [saved,     setSaved]     = useState(false)
  const [saveError, setSaveError] = useState('')
  const [firstName, setFirstName] = useState(user?.name?.split(' ')[0] || '')
  const [lastName,  setLastName]  = useState(user?.name?.split(' ').slice(1).join(' ') || '')

  const handleSave = async () => {
    setSaved(false); setSaveError('')
    try {
      const { auth } = await import('../../api')
      await auth.updateProfile({ first_name: firstName, last_name: lastName })
      setSaved(true)
    } catch (err) { setSaveError(err.message) }
  }

  return (
    <div style={{ maxWidth: 480 }}>
      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 20 }}>
          <Avatar name={user?.name} size="lg" admin />
          <div>
            <div style={{ fontFamily: "'Playfair Display', serif", fontSize: 20, fontWeight: 500 }}>{user?.name}</div>
            <div style={{ fontSize: 13, color: 'var(--ink-muted)' }}>{user?.email}</div>
            <span className="badge badge-dark" style={{ marginTop: 5 }}>Administrator</span>
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
          <label className="form-label">Email address (read-only)</label>
          <input className="form-input" type="email" value={user?.email || ''} readOnly />
        </div>
        <button className="btn btn-primary btn-sm" onClick={handleSave}>Save changes</button>
      </div>
    </div>
  )
}
