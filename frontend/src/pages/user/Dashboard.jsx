import { useState, useEffect, useRef } from 'react'
import { Badge, SectionHeader } from '../../components/UI'
import { documents, feedback as feedbackApi, inbox as inboxApi } from '../../api'

/* ─── Animated counter hook ──────────────────────────────── */
function useCountUp(target, duration = 1200) {
  const [value, setValue] = useState(0)
  useEffect(() => {
    if (target === 0) { setValue(0); return }
    let start = null
    const step = ts => {
      if (!start) start = ts
      const progress = Math.min((ts - start) / duration, 1)
      // Ease out cubic
      const eased = 1 - Math.pow(1 - progress, 3)
      setValue(Math.round(eased * target))
      if (progress < 1) requestAnimationFrame(step)
    }
    requestAnimationFrame(step)
  }, [target, duration])
  return value
}

/* ─── Animated stat card ─────────────────────────────────── */
function StatCard({ label, value, sub, accent, icon, delay = 0, loading }) {
  const [visible, setVisible] = useState(false)
  const animated = useCountUp(visible && !loading ? value : 0, 1000)

  useEffect(() => {
    const t = setTimeout(() => setVisible(true), delay)
    return () => clearTimeout(t)
  }, [delay])

  return (
    <div
      className={`stat-card ${accent ? 'accent' : ''}`}
      style={{
        opacity:    visible ? 1 : 0,
        transform:  visible ? 'translateY(0) scale(1)' : 'translateY(20px) scale(0.96)',
        transition: `opacity 0.5s ease ${delay}ms, transform 0.5s ease ${delay}ms`,
        position:   'relative',
        overflow:   'hidden',
      }}
    >
      {/* Shimmer sweep on load */}
      <div style={{
        position:   'absolute', inset: 0,
        background: 'linear-gradient(105deg, transparent 40%, rgba(255,255,255,0.12) 50%, transparent 60%)',
        transform:  visible ? 'translateX(200%)' : 'translateX(-200%)',
        transition: `transform 0.9s ease ${delay + 100}ms`,
        pointerEvents: 'none',
      }} />

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div className="stat-label">{label}</div>
        <span style={{
          fontSize: 20, opacity: 0.5,
          transform: visible ? 'rotate(0deg) scale(1)' : 'rotate(-30deg) scale(0.5)',
          transition: `transform 0.6s cubic-bezier(0.34,1.56,0.64,1) ${delay + 200}ms`,
          display: 'inline-block',
        }}>{icon}</span>
      </div>
      <div className="stat-value" style={{
        transform:  visible ? 'scale(1)' : 'scale(0.7)',
        transition: `transform 0.5s cubic-bezier(0.34,1.56,0.64,1) ${delay + 150}ms`,
      }}>
        {loading ? '—' : animated}
      </div>
      <div className="stat-sub">{sub}</div>
    </div>
  )
}

/* ─── Pipeline steps strip ───────────────────────────────── */
function PipelineStrip() {
  const [active, setActive] = useState(0)
  const steps = [
    { icon: '📷', label: 'Upload image' },
    { icon: '⚙️', label: 'OpenCV prep'  },
    { icon: '🔍', label: 'OCR Engine 3' },
    { icon: '📐', label: 'Layout detect'},
    { icon: '📄', label: 'Generate PDF' },
  ]

  useEffect(() => {
    const iv = setInterval(() => setActive(p => (p + 1) % steps.length), 1800)
    return () => clearInterval(iv)
  }, [])

  return (
    <div style={{
      background:   'var(--ink)',
      borderRadius: 'var(--radius-lg)',
      padding:      '16px 20px',
      marginBottom: 22,
    }}>
      <div style={{ fontSize: 10.5, fontWeight: 500, letterSpacing: 1.4, textTransform: 'uppercase', color: 'rgba(255,255,255,0.35)', marginBottom: 12 }}>
        Processing pipeline
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 0 }}>
        {steps.map((s, i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'center', flex: 1 }}>
            {/* Step node */}
            <div style={{
              display:       'flex',
              flexDirection: 'column',
              alignItems:    'center',
              gap:           5,
              flex:          1,
            }}>
              <div style={{
                width:      36, height: 36,
                borderRadius: '50%',
                background:   i === active
                  ? 'var(--amber)'
                  : i < active
                    ? 'rgba(217,119,6,0.25)'
                    : 'rgba(255,255,255,0.07)',
                display:      'flex',
                alignItems:   'center',
                justifyContent: 'center',
                fontSize:     16,
                transition:   'all 0.4s cubic-bezier(0.34,1.56,0.64,1)',
                transform:    i === active ? 'scale(1.2)' : 'scale(1)',
                boxShadow:    i === active ? '0 0 0 6px rgba(217,119,6,0.15)' : 'none',
              }}>
                {i < active
                  ? <span style={{ color: 'var(--amber)', fontSize: 13 }}>✓</span>
                  : <span>{s.icon}</span>
                }
              </div>
              <span style={{
                fontSize:   9.5,
                fontWeight: i === active ? 500 : 400,
                color:      i === active ? 'var(--amber)' : 'rgba(255,255,255,0.3)',
                textAlign:  'center',
                transition: 'color 0.3s',
                whiteSpace: 'nowrap',
              }}>
                {s.label}
              </span>
            </div>

            {/* Connector line */}
            {i < steps.length - 1 && (
              <div style={{
                height:     2,
                width:      '100%',
                maxWidth:   32,
                background: i < active
                  ? 'var(--amber)'
                  : 'rgba(255,255,255,0.08)',
                transition: 'background 0.4s ease',
                flexShrink: 0,
                marginBottom: 22,
              }} />
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

/* ─── Floating particles background ─────────────────────── */
function FloatingParticles() {
  const particles = Array.from({ length: 6 }, (_, i) => ({
    id: i,
    size:   6 + (i * 3) % 10,
    left:   10 + (i * 17) % 80,
    delay:  i * 0.8,
    dur:    4 + (i * 0.7),
  }))

  return (
    <div style={{
      position:   'absolute',
      inset:      0,
      overflow:   'hidden',
      pointerEvents: 'none',
      borderRadius: 'var(--radius-lg)',
    }}>
      {particles.map(p => (
        <div key={p.id} style={{
          position:      'absolute',
          width:         p.size,
          height:        p.size,
          borderRadius:  '50%',
          background:    'rgba(217,119,6,0.15)',
          left:          `${p.left}%`,
          bottom:        -p.size,
          animation:     `float-up ${p.dur}s ease-in ${p.delay}s infinite`,
        }} />
      ))}
    </div>
  )
}

/* ─── Activity wave bar ──────────────────────────────────── */
function ActivityBar({ value, max, label, color = 'var(--amber)', delay = 0 }) {
  const [filled, setFilled] = useState(false)
  const pct = max > 0 ? (value / max) * 100 : 0

  useEffect(() => {
    const t = setTimeout(() => setFilled(true), delay + 300)
    return () => clearTimeout(t)
  }, [delay])

  return (
    <div style={{ marginBottom: 10 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: 'var(--ink-muted)', marginBottom: 5 }}>
        <span>{label}</span>
        <span style={{ fontWeight: 500, color: 'var(--ink)' }}>{value}</span>
      </div>
      <div style={{ height: 6, background: 'var(--paper-dark)', borderRadius: 3, overflow: 'hidden' }}>
        <div style={{
          height:     '100%',
          width:      filled ? `${Math.max(pct, value > 0 ? 8 : 0)}%` : '0%',
          background: color,
          borderRadius: 3,
          transition: `width 0.9s cubic-bezier(0.25,1,0.5,1) ${delay}ms`,
        }} />
      </div>
    </div>
  )
}

/* ─── Welcome banner ─────────────────────────────────────── */
function WelcomeBanner({ name, loading, totalDocs }) {
  const [show, setShow] = useState(false)
  useEffect(() => { setTimeout(() => setShow(true), 50) }, [])

  const greet = () => {
    const h = new Date().getHours()
    if (h < 12) return 'Good morning'
    if (h < 17) return 'Good afternoon'
    return 'Good evening'
  }

  return (
    <div style={{
      background:   'var(--ink)',
      borderRadius: 'var(--radius-lg)',
      padding:      '22px 26px',
      marginBottom: 22,
      position:     'relative',
      overflow:     'hidden',
      opacity:      show ? 1 : 0,
      transform:    show ? 'translateY(0)' : 'translateY(-16px)',
      transition:   'opacity 0.6s ease, transform 0.6s ease',
    }}>
      <FloatingParticles />

      {/* Ink-wash decorative circle */}
      <div style={{
        position:     'absolute',
        right:        -40, top: -40,
        width:        160, height: 160,
        borderRadius: '50%',
        background:   'rgba(217,119,6,0.06)',
        pointerEvents:'none',
      }} />
      <div style={{
        position:     'absolute',
        right:        20, top: 10,
        width:        80, height: 80,
        borderRadius: '50%',
        background:   'rgba(217,119,6,0.04)',
        pointerEvents:'none',
      }} />

      <div style={{ position: 'relative', zIndex: 1 }}>
        <div style={{ fontSize: 11, fontWeight: 500, letterSpacing: 1.5, textTransform: 'uppercase', color: 'rgba(255,255,255,0.35)', marginBottom: 6 }}>
          {greet()}
        </div>
        <div style={{ fontFamily: "'Playfair Display', serif", fontSize: 22, fontWeight: 500, color: '#FAFAF8', marginBottom: 6, lineHeight: 1.3 }}>
          {name ? `${name.split(' ')[0]}` : 'Welcome back'} ✍️
        </div>
        <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.45)', lineHeight: 1.6 }}>
          {loading
            ? 'Loading your workspace…'
            : totalDocs === 0
              ? 'Upload your first handwritten note to get started.'
              : `You have ${totalDocs} document${totalDocs !== 1 ? 's' : ''} in your workspace.`
          }
        </div>
      </div>
    </div>
  )
}

/* ─── Recent document row with slide-in animation ────────── */
function DocRow({ doc, index, setPage }) {
  const [show, setShow] = useState(false)
  useEffect(() => {
    const t = setTimeout(() => setShow(true), index * 100 + 200)
    return () => clearTimeout(t)
  }, [index])

  const statusColors = {
    completed:  { bg: 'var(--sage-light)',  dot: 'var(--sage)'  },
    processing: { bg: 'var(--amber-light)', dot: 'var(--amber)' },
    pending:    { bg: 'var(--amber-light)', dot: 'var(--amber)' },
    failed:     { bg: 'var(--coral-light)', dot: 'var(--coral)' },
  }
  const sc = statusColors[doc.status] || statusColors.pending

  return (
    <div
      onClick={() => setPage('documents')}
      style={{
        display:     'flex',
        alignItems:  'center',
        gap:         12,
        padding:     '11px 0',
        borderBottom:'1px solid var(--border)',
        cursor:      'pointer',
        opacity:     show ? 1 : 0,
        transform:   show ? 'translateX(0)' : 'translateX(-20px)',
        transition:  `opacity 0.4s ease, transform 0.4s ease`,
      }}
    >
      {/* Icon with status glow */}
      <div style={{
        width:        38, height: 38,
        borderRadius: 'var(--radius-md)',
        background:   sc.bg,
        display:      'flex', alignItems: 'center', justifyContent: 'center',
        fontSize:     18, flexShrink: 0,
        position:     'relative',
      }}>
        📄
        <div style={{
          position:     'absolute',
          bottom:       2, right: 2,
          width:        8, height: 8,
          borderRadius: '50%',
          background:   sc.dot,
          border:       '1.5px solid white',
        }} />
      </div>

      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontWeight: 500, fontSize: 13.5, color: 'var(--ink)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
          {doc.title || `Document #${doc.id}`}
        </div>
        <div style={{ fontSize: 11.5, color: 'var(--ink-muted)' }}>
          {doc.created_at ? new Date(doc.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : ''}
          {' · '}{doc.style_template || 'default'} style
        </div>
      </div>

      <Badge status={doc.status} />
    </div>
  )
}

/* ─── Main Dashboard ─────────────────────────────────────── */
export default function UserDashboard({ setPage }) {
  const [docs,      setDocs]      = useState([])
  const [totalDocs, setTotalDocs] = useState(0)
  const [completed, setCompleted] = useState(0)
  const [feedbacks, setFeedbacks] = useState(0)
  const [unread,    setUnread]    = useState(0)
  const [loading,   setLoading]   = useState(true)
  const [userName,  setUserName]  = useState('')

  useEffect(() => {
    // Get user name from localStorage
    setUserName(localStorage.getItem('userName') || '')

    Promise.all([
      documents.list(),
      feedbackApi.list(),
      inboxApi.list(),
    ]).then(([docsData, fbData, inboxData]) => {
      const docList = Array.isArray(docsData)  ? docsData  : docsData.results  ?? []
      const fbList  = Array.isArray(fbData)    ? fbData    : fbData.results    ?? []
      const msgList = Array.isArray(inboxData) ? inboxData : inboxData.results ?? []

      setDocs(docList.slice(0, 4))
      setTotalDocs(docList.length)
      setCompleted(docList.filter(d => d.status === 'completed').length)
      setFeedbacks(fbList.length)
      setUnread(msgList.filter(m => !m.is_read).length)
    }).catch(() => {}).finally(() => setLoading(false))
  }, [])

  return (
    <div>
      {/* ── Keyframes injected once ─────────────────────── */}
      <style>{`
        @keyframes float-up {
          0%   { transform: translateY(0) scale(1);   opacity: 0.6; }
          80%  { transform: translateY(-120px) scale(0.8); opacity: 0.3; }
          100% { transform: translateY(-140px) scale(0.6); opacity: 0; }
        }
        @keyframes pulse-ring {
          0%   { transform: scale(1);   opacity: 0.6; }
          100% { transform: scale(1.8); opacity: 0; }
        }
        @keyframes spin-slow {
          from { transform: rotate(0deg); }
          to   { transform: rotate(360deg); }
        }
        @keyframes blink-dot {
          0%, 100% { opacity: 1; }
          50%      { opacity: 0.3; }
        }
      `}</style>

      {/* ── Welcome banner ──────────────────────────────── */}
      <WelcomeBanner name={userName} loading={loading} totalDocs={totalDocs} />

      {/* ── Stats grid ──────────────────────────────────── */}
      <div className="stats-grid" style={{ marginBottom: 22 }}>
        <StatCard label="Total Documents" value={totalDocs} sub="Since joining"       accent icon="📁" delay={0}   loading={loading} />
        <StatCard label="Completed"       value={completed} sub="Ready to download"   icon="✅" delay={80}  loading={loading} />
        <StatCard label="Feedbacks"       value={feedbacks} sub="Submitted"           icon="✦" delay={160} loading={loading} />
        <StatCard label="Unread Messages" value={unread}    sub="In your inbox"       icon="◉" delay={240} loading={loading} />
      </div>

      {/* ── Pipeline animation strip ─────────────────────── */}
      <PipelineStrip />

      {/* ── Bottom grid ──────────────────────────────────── */}
      <div className="grid-2">

        {/* Recent documents */}
        <div className="card" style={{ position: 'relative', overflow: 'hidden' }}>
          <SectionHeader title="Recent Documents">
            <button className="btn btn-ghost btn-sm" onClick={() => setPage('documents')}>View all</button>
          </SectionHeader>

          {loading && (
            <div style={{ display: 'flex', gap: 8, alignItems: 'center', padding: '16px 0', color: 'var(--ink-muted)', fontSize: 13 }}>
              <div style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--amber)', animation: 'blink-dot 1s ease infinite' }} />
              Loading documents…
            </div>
          )}

          {!loading && docs.length === 0 && (
            <div style={{ padding: '20px 0', textAlign: 'center' }}>
              <div style={{ fontSize: 36, marginBottom: 10, opacity: 0.4 }}>📂</div>
              <div style={{ fontSize: 13, color: 'var(--ink-muted)', marginBottom: 10 }}>No documents yet</div>
              <button
                className="btn btn-amber btn-sm"
                onClick={() => setPage('upload')}
              >
                ↑ Upload your first note
              </button>
            </div>
          )}

          {docs.map((doc, i) => (
            <DocRow key={doc.id} doc={doc} index={i} setPage={setPage} />
          ))}
        </div>

        {/* Right column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

          {/* Activity breakdown */}
          <div className="card">
            <div className="section-title" style={{ marginBottom: 14 }}>Activity Overview</div>
            <ActivityBar value={totalDocs}              max={Math.max(totalDocs, 1)}  label="Total uploaded"  color="var(--ink)"    delay={100} />
            <ActivityBar value={completed}              max={Math.max(totalDocs, 1)}  label="Completed"       color="var(--sage)"   delay={200} />
            <ActivityBar value={totalDocs - completed}  max={Math.max(totalDocs, 1)}  label="In progress"     color="var(--amber)"  delay={300} />
            <ActivityBar value={feedbacks}              max={Math.max(feedbacks, 1)}  label="Feedback given"  color="#7C6BDB"       delay={400} />
          </div>

          {/* Quick actions */}
          <div className="card">
            <div className="section-title" style={{ marginBottom: 14 }}>Quick Actions</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {[
                { icon: '↑', label: 'Upload handwritten notes', page: 'upload',     style: 'btn-amber' },
                { icon: '◻', label: 'Browse my documents',      page: 'documents',  style: 'btn-ghost' },
                { icon: '◉', label: 'Check inbox',              page: 'inbox',      style: 'btn-ghost' },
                { icon: '✉', label: 'Submit a complaint',       page: 'complaints', style: 'btn-ghost' },
              ].map((a, i) => (
                <button
                  key={a.page}
                  className={`btn ${a.style}`}
                  style={{
                    justifyContent: 'flex-start',
                    opacity:        1,
                    transform:      'none',
                    animation:      `none`,
                  }}
                  onClick={() => setPage(a.page)}
                >
                  <span style={{ fontSize: 15 }}>{a.icon}</span> {a.label}
                </button>
              ))}
            </div>
          </div>

        </div>
      </div>
    </div>
  )
}
