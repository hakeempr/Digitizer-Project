import { useState, useEffect, useRef } from 'react'
import { useAuth } from '../context/AuthContext'
import { Alert } from '../components/UI'
import { auth as authApi } from '../api'

/* ════════════════════════════════════════════════════════════
   ANIMATED BACKGROUND — floating ink strokes + mesh gradient
════════════════════════════════════════════════════════════ */
function AnimatedBackground() {
  const canvasRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    let raf

    const resize = () => {
      canvas.width  = window.innerWidth
      canvas.height = window.innerHeight
    }
    resize()
    window.addEventListener('resize', resize)

    // Ink stroke particles
    const strokes = Array.from({ length: 28 }, (_, i) => ({
      x:     Math.random() * window.innerWidth,
      y:     Math.random() * window.innerHeight,
      vx:    (Math.random() - 0.5) * 0.4,
      vy:    (Math.random() - 0.5) * 0.4,
      len:   30 + Math.random() * 80,
      angle: Math.random() * Math.PI * 2,
      va:    (Math.random() - 0.5) * 0.008,
      alpha: 0.04 + Math.random() * 0.1,
      width: 1 + Math.random() * 2.5,
      hue:   Math.random() > 0.7 ? 38 : 25,   // amber or warm brown
    }))

    // Glowing orbs
    const orbs = [
      { x: 0.15, y: 0.25, r: 320, color: 'rgba(217,119,6,0.06)' },
      { x: 0.85, y: 0.75, r: 280, color: 'rgba(217,119,6,0.04)' },
      { x: 0.5,  y: 0.1,  r: 200, color: 'rgba(146,64,14,0.05)' },
    ]

    let t = 0
    const draw = () => {
      t += 0.005
      const W = canvas.width, H = canvas.height
      ctx.clearRect(0, 0, W, H)

      // Background gradient
      const bg = ctx.createLinearGradient(0, 0, W, H)
      bg.addColorStop(0, '#FAF7F2')
      bg.addColorStop(0.5, '#F5F0E8')
      bg.addColorStop(1, '#EDE8DE')
      ctx.fillStyle = bg
      ctx.fillRect(0, 0, W, H)

      // Animated orbs
      orbs.forEach(o => {
        const grd = ctx.createRadialGradient(
          o.x * W + Math.sin(t * 0.5) * 40,
          o.y * H + Math.cos(t * 0.3) * 30,
          0,
          o.x * W, o.y * H, o.r
        )
        grd.addColorStop(0, o.color)
        grd.addColorStop(1, 'transparent')
        ctx.fillStyle = grd
        ctx.fillRect(0, 0, W, H)
      })

      // Ink strokes
      strokes.forEach(s => {
        s.x += s.vx; s.y += s.vy; s.angle += s.va
        if (s.x < -100) s.x = W + 100
        if (s.x > W + 100) s.x = -100
        if (s.y < -100) s.y = H + 100
        if (s.y > H + 100) s.y = -100

        ctx.save()
        ctx.translate(s.x, s.y)
        ctx.rotate(s.angle)
        ctx.globalAlpha = s.alpha
        ctx.strokeStyle = `hsl(${s.hue}, 60%, 35%)`
        ctx.lineWidth   = s.width
        ctx.lineCap     = 'round'
        ctx.beginPath()
        // Slightly curved stroke
        ctx.moveTo(-s.len / 2, 0)
        ctx.quadraticCurveTo(0, s.len * 0.08, s.len / 2, 0)
        ctx.stroke()
        ctx.restore()
      })

      // Subtle dot grid
      ctx.globalAlpha = 0.035
      ctx.fillStyle   = '#8B6914'
      const spacing = 40
      for (let gx = 0; gx < W; gx += spacing) {
        for (let gy = 0; gy < H; gy += spacing) {
          ctx.beginPath()
          ctx.arc(gx, gy, 1.2, 0, Math.PI * 2)
          ctx.fill()
        }
      }
      ctx.globalAlpha = 1

      raf = requestAnimationFrame(draw)
    }
    draw()
    return () => { cancelAnimationFrame(raf); window.removeEventListener('resize', resize) }
  }, [])

  return (
    <canvas ref={canvasRef} style={{
      position: 'fixed', inset: 0, zIndex: 0, pointerEvents: 'none'
    }} />
  )
}

/* ════════════════════════════════════════════════════════════
   FLOATING FEATURE TAGS (left side)
════════════════════════════════════════════════════════════ */
function FeatureTags() {
  const tags = [
    { icon: '✍️', text: 'Handwriting OCR',  delay: 0.2,  x: '8%',  y: '18%' },
    { icon: '📄', text: 'PDF Generation',   delay: 0.6,  x: '5%',  y: '38%' },
    { icon: '❗', text: 'Complaints',delay: 1.0,  x: '10%', y: '56%' },
    { icon: '🎨', text: 'Style Templates',delay: 1.4,  x: '6%',  y: '74%' },
   
  ]
  return (
    <>
      {tags.map((tag, i) => (
        <div key={i} style={{
          position:    'fixed',
          left:        tag.x,
          top:         tag.y,
          background:  'rgba(255,255,255,0.72)',
          backdropFilter: 'blur(8px)',
          border:      '1px solid rgba(217,119,6,0.18)',
          borderRadius: 30,
          padding:     '6px 14px',
          fontSize:    12,
          fontWeight:  500,
          color:       '#44403C',
          display:     'flex',
          alignItems:  'center',
          gap:         6,
          zIndex:      2,
          animation:   `tag-float 4s ease-in-out ${tag.delay}s infinite alternate`,
          boxShadow:   '0 2px 12px rgba(217,119,6,0.08)',
        }}>
          <span style={{ fontSize: 14 }}>{tag.icon}</span>
          {tag.text}
        </div>
      ))}
    </>
  )
}

/* ════════════════════════════════════════════════════════════
   REGISTER PAGE
════════════════════════════════════════════════════════════ */
function RegisterPage({ onBack }) {
  const [form, setForm]       = useState({ first_name:'', last_name:'', email:'', phone:'', password:'', password2:'' })
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState('')
  const [done,    setDone]    = useState(false)
  const [visible, setVisible] = useState(false)

  useEffect(() => { setTimeout(() => setVisible(true), 60) }, [])

  const set = k => e => setForm(f => ({ ...f, [k]: e.target.value }))

  const handleSubmit = async e => {
    e.preventDefault(); setError('')
    if (!form.first_name.trim() || !form.last_name.trim()) { setError('First name and last name are required.'); return }
    if (form.password !== form.password2) { setError('Passwords do not match.'); return }
    if (form.password.length < 8) { setError('Password must be at least 8 characters.'); return }
    setLoading(true)
    try {
      await authApi.register({ first_name:form.first_name.trim(), last_name:form.last_name.trim(), email:form.email.trim(), phone:form.phone.trim(), password:form.password, password2:form.password2 })
      setDone(true)
    } catch (err) {
      setError(err.message || 'Registration failed.')
    } finally { setLoading(false) }
  }

  const cardStyle = {
    background:    'rgba(255,255,255,0.88)',
    backdropFilter:'blur(20px)',
    border:        '1px solid rgba(217,119,6,0.15)',
    borderRadius:  20,
    padding:       '36px 34px',
    width:         '100%',
    maxWidth:      420,
    boxShadow:     '0 24px 64px rgba(28,25,23,0.12), 0 0 0 1px rgba(255,255,255,0.6) inset',
    opacity:       visible ? 1 : 0,
    transform:     visible ? 'translateY(0) scale(1)' : 'translateY(28px) scale(0.97)',
    transition:    'opacity 0.6s ease, transform 0.6s cubic-bezier(0.34,1.2,0.64,1)',
    position:      'relative',
    zIndex:        10,
  }

  if (done) return (
    <div style={pageWrap}>
      <AnimatedBackground />
      <div style={{ ...cardStyle, textAlign:'center', maxWidth:380 }}>
        <div style={{ fontSize:52, marginBottom:16, animation:'bounce-in 0.6s cubic-bezier(0.34,1.56,0.64,1)' }}>📬</div>
        <div style={{ fontFamily:"'Playfair Display',serif", fontSize:22, fontWeight:500, color:'#1C1917', marginBottom:10 }}>Registration submitted!</div>
        <p style={{ color:'#78716C', fontSize:13.5, lineHeight:1.7, marginBottom:24 }}>
          Your account is pending admin approval.<br/>You will be notified once reviewed.
        </p>
        <button className="btn btn-primary btn-full" onClick={onBack}>Back to login</button>
      </div>
    </div>
  )

  return (
    <div style={pageWrap}>
      <AnimatedBackground />
      <div style={cardStyle}>
        <div style={{ fontFamily:"'Playfair Display',serif", fontSize:20, fontWeight:500, color:'#1C1917', marginBottom:4 }}>Create account</div>
        <p style={{ fontSize:12.5, color:'#78716C', marginBottom:22 }}>Join Digitizer · Notes → polished PDFs</p>
        {error && <Alert type="error">{error}</Alert>}
        <form onSubmit={handleSubmit}>
          <div className="form-row">
            <div className="form-group"><label className="form-label">First name</label><input className="form-input" placeholder="Priya" value={form.first_name} onChange={set('first_name')} required /></div>
            <div className="form-group"><label className="form-label">Last name</label><input className="form-input" placeholder="Nair" value={form.last_name} onChange={set('last_name')} required /></div>
          </div>
          <div className="form-group"><label className="form-label">Email address</label><input className="form-input" type="email" placeholder="priya@example.com" value={form.email} onChange={set('email')} required /></div>
          <div className="form-group"><label className="form-label">Phone (optional)</label><input className="form-input" type="tel" placeholder="+91 98765 43210" value={form.phone} onChange={set('phone')} /></div>
          <div className="form-group"><label className="form-label">Password</label><input className="form-input" type="password" placeholder="Min. 8 characters" value={form.password} onChange={set('password')} required minLength={8} /></div>
          <div className="form-group"><label className="form-label">Confirm password</label><input className="form-input" type="password" placeholder="Re-enter password" value={form.password2} onChange={set('password2')} required /></div>
          <button type="submit" className="btn btn-amber btn-full" disabled={loading} style={{ marginBottom:10 }}>
            {loading ? <span style={{ display:'flex', alignItems:'center', justifyContent:'center', gap:8 }}><Spinner />Creating account…</span> : 'Submit registration request'}
          </button>
        </form>
        <button className="btn btn-ghost btn-full" onClick={onBack}>Already have an account? Sign in</button>
      </div>
    </div>
  )
}

/* ════════════════════════════════════════════════════════════
   SPINNER
════════════════════════════════════════════════════════════ */
function Spinner() {
  return (
    <span style={{
      width:16, height:16, border:'2px solid rgba(255,255,255,0.3)',
      borderTopColor:'white', borderRadius:'50%',
      display:'inline-block', animation:'spin 0.7s linear infinite', flexShrink:0
    }} />
  )
}

/* ════════════════════════════════════════════════════════════
   TYPING TAGLINE
════════════════════════════════════════════════════════════ */
function TypingTagline() {
  const lines = [
    'Transform handwritten notes into polished PDFs.',
    'OCR Engine 3 — built for handwriting.',
    'Four beautiful style templates.',
    'Auto layout detection & structure.',
  ]
  const [lineIdx, setLineIdx] = useState(0)
  const [charIdx, setCharIdx] = useState(0)
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    const current = lines[lineIdx]
    if (!deleting && charIdx < current.length) {
      const t = setTimeout(() => setCharIdx(c => c + 1), 42)
      return () => clearTimeout(t)
    }
    if (!deleting && charIdx === current.length) {
      const t = setTimeout(() => setDeleting(true), 1800)
      return () => clearTimeout(t)
    }
    if (deleting && charIdx > 0) {
      const t = setTimeout(() => setCharIdx(c => c - 1), 22)
      return () => clearTimeout(t)
    }
    if (deleting && charIdx === 0) {
      setDeleting(false)
      setLineIdx(i => (i + 1) % lines.length)
    }
  }, [charIdx, deleting, lineIdx])

  return (
    <div style={{ fontSize:13, color:'#78716C', minHeight:20, marginBottom:26 }}>
      {lines[lineIdx].slice(0, charIdx)}
      <span style={{ borderRight:'2px solid #D97706', marginLeft:1, animation:'blink-cursor 0.8s step-end infinite' }} />
    </div>
  )
}

/* ════════════════════════════════════════════════════════════
   MAIN LOGIN PAGE
════════════════════════════════════════════════════════════ */
const pageWrap = {
  minHeight:      '100vh',
  display:        'flex',
  alignItems:     'center',
  justifyContent: 'center',
  position:       'relative',
  overflow:       'hidden',
  padding:        '24px',
}

export default function LoginPage() {
  const { login }            = useAuth()
  const [view, setView]      = useState('login')
  const [email, setEmail]    = useState('')
  const [password, setPass]  = useState('')
  const [error, setError]    = useState('')
  const [loading, setLoading]= useState(false)
  const [visible, setVisible]= useState(false)
  const [focused, setFocused]= useState(null)

  useEffect(() => { setTimeout(() => setVisible(true), 80) }, [])

  if (view === 'register') return <RegisterPage onBack={() => setView('login')} />

  const handleSubmit = async e => {
    e.preventDefault(); setLoading(true); setError('')
    try { await login(email, password) }
    catch (err) { setError(err.message || 'Invalid email or password.') }
    finally { setLoading(false) }
  }

  return (
    <div style={pageWrap}>
      {/* Global keyframes */}
      <style>{`
        @keyframes tag-float {
          0%   { transform: translateY(0px) rotate(-1deg); }
          100% { transform: translateY(-12px) rotate(1deg); }
        }
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
        @keyframes blink-cursor {
          0%,100% { opacity: 1; }
          50%     { opacity: 0; }
        }
        @keyframes bounce-in {
          0%   { transform: scale(0.3); opacity: 0; }
          60%  { transform: scale(1.15); }
          100% { transform: scale(1); opacity: 1; }
        }
        @keyframes slide-up {
          from { transform: translateY(12px); opacity: 0; }
          to   { transform: translateY(0);    opacity: 1; }
        }
        @keyframes logo-write {
          from { stroke-dashoffset: 300; }
          to   { stroke-dashoffset: 0; }
        }
        @keyframes pulse-amber {
          0%,100% { box-shadow: 0 0 0 0 rgba(217,119,6,0.25); }
          50%     { box-shadow: 0 0 0 8px rgba(217,119,6,0); }
        }
        @keyframes shimmer-slide {
          from { transform: translateX(-100%); }
          to   { transform: translateX(100%); }
        }
        .form-input:focus {
          border-color: #D97706 !important;
          box-shadow: 0 0 0 3px rgba(217,119,6,0.12) !important;
        }
      `}</style>

      <AnimatedBackground />
      <FeatureTags />

      {/* Decorative right-side illustration panel */}
      <div style={{
        position:   'fixed',
        right:      '8%',
        top:        '50%',
        transform:  'translateY(-50%)',
        display:    'flex',
        flexDirection:'column',
        gap:         20,
        zIndex:      2,
        opacity:     visible ? 1 : 0,
        transition: 'opacity 1s ease 0.8s',
      }}>
        {[
          { bg:'#FEF3C7', border:'rgba(217,119,6,0.2)',  icon:'✍️', title:'Upload', sub:'Any handwritten image' },
          { bg:'#F0FDF4', border:'rgba(77,124,94,0.2)',  icon:'📐', title:'Layout',    sub:'Structure detection'   },
          { bg:'#EFF6FF', border:'rgba(59,130,246,0.2)', icon:'📄', title:'PDF', sub:'Styled output ready'   },
          { bg:'#FDF2F8', border:'rgba(168,85,247,0.2)', icon:'🚀', title:'Fast',    sub:'Super fast processing'   },
        ].map((s, i) => (
          <div key={i} style={{
            background:  s.bg,
            border:      `1px solid ${s.border}`,
            borderRadius: 14,
            padding:     '10px 16px',
            display:     'flex',
            alignItems:  'center',
            gap:          10,
            minWidth:    180,
            boxShadow:   '0 4px 16px rgba(0,0,0,0.06)',
            animation:   `slide-up 0.5s ease ${0.9 + i * 0.15}s both`,
          }}>
            <span style={{ fontSize:22 }}>{s.icon}</span>
            <div>
              <div style={{ fontWeight:600, fontSize:13, color:'#1C1917' }}>{s.title}</div>
              <div style={{ fontSize:11.5, color:'#78716C' }}>{s.sub}</div>
            </div>
            {/* Animated connector dot */}
            {i < 3 && (
              <div style={{
                position:'absolute',
                right:'-6px',
                width:12, height:12,
                borderRadius:'50%',
                background:'white',
                border:'2px solid rgba(217,119,6,0.4)',
                animation:'pulse-amber 2s ease infinite',
              }} />
            )}
          </div>
        ))}
      </div>

      {/* Login card */}
      <div style={{
        background:    'rgba(255,255,255,0.9)',
        backdropFilter:'blur(24px)',
        border:        '1px solid rgba(217,119,6,0.12)',
        borderRadius:  22,
        padding:       '44px 40px',
        width:         '100%',
        maxWidth:      400,
        boxShadow:     '0 32px 80px rgba(28,25,23,0.14), 0 0 0 1px rgba(255,255,255,0.7) inset',
        opacity:       visible ? 1 : 0,
        transform:     visible ? 'translateY(0) scale(1)' : 'translateY(32px) scale(0.96)',
        transition:    'opacity 0.7s ease, transform 0.7s cubic-bezier(0.34,1.2,0.64,1)',
        position:      'relative',
        zIndex:        10,
        overflow:      'hidden',
      }}>

        {/* Shimmer strip at top */}
        <div style={{
          position:'absolute', top:0, left:0, right:0, height:3,
          background:'linear-gradient(90deg, transparent, #D97706, transparent)',
          animation:'shimmer-slide 3s ease infinite',
        }} />

        {/* Logo */}
        <div style={{
          fontFamily:"'Playfair Display',serif",
          fontSize:26, fontWeight:500, color:'#1C1917',
          marginBottom:6,
          animation:'slide-up 0.5s ease 0.2s both',
        }}>
          ✍️ Digitizer
        </div>

        <TypingTagline />

        {error && (
          <div style={{ animation:'slide-up 0.3s ease' }}>
            <Alert type="error">{error}</Alert>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {/* Email field */}
          <div className="form-group" style={{ animation:'slide-up 0.5s ease 0.3s both' }}>
            <label className="form-label">Email address</label>
            <div style={{ position:'relative' }}>
              <span style={{
                position:'absolute', left:12, top:'50%', transform:'translateY(-50%)',
                fontSize:16, opacity: focused === 'email' ? 1 : 0.4,
                transition:'opacity 0.2s', pointerEvents:'none',
              }}>✉</span>
              <input
                className="form-input"
                style={{ paddingLeft:36 }}
                type="email" placeholder="you@example.com"
                value={email} onChange={e => setEmail(e.target.value)}
                onFocus={() => setFocused('email')}
                onBlur={() => setFocused(null)}
                required
              />
            </div>
          </div>

          {/* Password field */}
          <div className="form-group" style={{ animation:'slide-up 0.5s ease 0.4s both' }}>
            <label className="form-label">Password</label>
            <div style={{ position:'relative' }}>
              <span style={{
                position:'absolute', left:12, top:'50%', transform:'translateY(-50%)',
                fontSize:16, opacity: focused === 'pass' ? 1 : 0.4,
                transition:'opacity 0.2s', pointerEvents:'none',
              }}>🔒</span>
              <input
                className="form-input"
                style={{ paddingLeft:36 }}
                type="password" placeholder="••••••••"
                value={password} onChange={e => setPass(e.target.value)}
                onFocus={() => setFocused('pass')}
                onBlur={() => setFocused(null)}
                required
              />
            </div>
          </div>

          <div style={{ animation:'slide-up 0.5s ease 0.5s both' }}>
            <button
              type="submit"
              className="btn btn-primary btn-full"
              disabled={loading}
              style={{
                marginBottom:10,
                background: loading ? '#44403C' : '#1C1917',
                transition:'all 0.2s',
                position:'relative', overflow:'hidden',
              }}
            >
              {loading
                ? <span style={{ display:'flex', alignItems:'center', justifyContent:'center', gap:8 }}><Spinner />Signing in…</span>
                : 'Sign in →'
              }
              {/* Ripple shimmer on hover */}
              {!loading && (
                <span style={{
                  position:'absolute', inset:0,
                  background:'linear-gradient(105deg,transparent 40%,rgba(255,255,255,0.07) 50%,transparent 60%)',
                  animation:'shimmer-slide 2.5s ease infinite',
                }} />
              )}
            </button>
          </div>
        </form>

        <div className="divider" style={{ animation:'slide-up 0.5s ease 0.6s both' }} />

        <div style={{ animation:'slide-up 0.5s ease 0.65s both' }}>
          <button className="btn btn-ghost btn-full" onClick={() => setView('register')}>
            Create new account
          </button>
        </div>
      </div>
    </div>
  )
}
