import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { Eye, EyeOff, AlertCircle, Mail, Lock, Download, Monitor } from 'lucide-react'
import LightPillar from '../components/ui/LightPillar'

/* ── Smooth animated gradient palette ── */
const COLOR_PALETTE = [
  { top: '#22d3ee', bottom: '#0a1628' },
  { top: '#a855f7', bottom: '#0f0a1e' },
  { top: '#ec4899', bottom: '#1a0514' },
  { top: '#10b981', bottom: '#041a10' },
  { top: '#f59e0b', bottom: '#1a0e00' },
  { top: '#6366f1', bottom: '#080b1e' },
  { top: '#22d3ee', bottom: '#0a1628' },
]

function useCyclingColors(intervalMs = 3500) {
  const [idx,  setIdx]  = useState(0)
  const [next, setNext] = useState(1)
  const [prog, setProg] = useState(0)
  const rafRef   = useRef(null)
  const startRef = useRef(null)

  useEffect(() => {
    const tick = (now) => {
      if (!startRef.current) startRef.current = now
      const p = Math.min((now - startRef.current) / intervalMs, 1)
      setProg(p)
      if (p >= 1) {
        setIdx(i => { const ni = (i + 1) % (COLOR_PALETTE.length - 1); setNext((ni + 1) % (COLOR_PALETTE.length - 1)); return ni })
        startRef.current = now
        setProg(0)
      }
      rafRef.current = requestAnimationFrame(tick)
    }
    rafRef.current = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(rafRef.current)
  }, [intervalMs])

  const lerpHex = (a, b, t) => {
    const parse = h => [parseInt(h.slice(1,3),16), parseInt(h.slice(3,5),16), parseInt(h.slice(5,7),16)]
    const [ra, rb] = [parse(a), parse(b)]
    return '#' + ra.map((v,i) => Math.round(v + (rb[i]-v)*t).toString(16).padStart(2,'0')).join('')
  }
  const ease = prog < 0.5 ? 2*prog*prog : -1+(4-2*prog)*prog

  return {
    topColor:    lerpHex(COLOR_PALETTE[idx].top,    COLOR_PALETTE[next].top,    ease),
    bottomColor: lerpHex(COLOR_PALETTE[idx].bottom, COLOR_PALETTE[next].bottom, ease),
  }
}

/* ── Logo path — update this to your actual logo file ── */
const LOGO_SRC = '/logo.png'   // e.g. put logo.png in /public and it'll resolve

export default function Login() {
  const [email,      setEmail]      = useState('')
  const [password,   setPassword]   = useState('')
  const [showPass,   setShowPass]   = useState(false)
  const [logoError,  setLogoError]  = useState(false)
  const { login, isLoading, error, clearError, token, user } = useAuthStore()
  const navigate = useNavigate()
  const { topColor, bottomColor } = useCyclingColors(3500)

  useEffect(() => {
    if (token && user)
      navigate(user.role === 'admin' || user.role === 'super_admin' ? '/dashboard' : '/my/dashboard')
  }, [token, user])

  useEffect(() => { clearError() }, [email, password])

  const handleSubmit = async (e) => {
    e.preventDefault()
    const result = await login(email, password)
    if (result?.success)
      navigate(result.role === 'admin' || result.role === 'super_admin' ? '/dashboard' : '/my/dashboard')
  }

  return (
    <div className="min-h-screen bg-sentinel-bg flex overflow-hidden relative">

      {/* ── Full-screen animated background ── */}
      <div className="absolute inset-0 z-0">
        <div style={{
          position: 'absolute', inset: '-60%',
          transform: 'rotate(45deg) scale(2)',
          transformOrigin: 'center center',
        }}>
          <LightPillar
            topColor={topColor} bottomColor={bottomColor}
            intensity={1.7} rotationSpeed={0.14} interactive={false}
            glowAmount={0.008} pillarWidth={1.8} pillarHeight={0.28}
            noiseIntensity={0.3} mixBlendMode="screen" quality="medium"
          />
        </div>
        <div style={{
          position: 'absolute', inset: 0,
          background: 'linear-gradient(160deg, rgba(2,8,24,0.88) 0%, rgba(2,8,24,0.45) 45%, rgba(2,8,24,0.85) 100%)',
        }} />
      </div>

      {/* ── Desktop left panel (Branding container) ── */}
      <div className="hidden lg:flex flex-1 items-end justify-start relative">

        <div className="relative z-10 p-16 pb-20">
          <div className="glow-line mb-6 max-w-xs" />
          <h1 className="font-display font-bold text-4xl text-white leading-tight drop-shadow-lg">
            Work Integrity<br />
            <span style={{ color: topColor, transition: 'color 0.8s ease' }}>Intelligence System</span>
          </h1>
          <p className="mt-4 text-white/60 font-body text-sm leading-relaxed max-w-sm">
            Real-time workforce monitoring, behavioral analytics, and integrity enforcement for modern enterprises.
          </p>

          {/* Desktop Download Client Button */}
          <div className="mt-12 animate-fade-in stagger-2">
            <a 
              href="https://drive.google.com/uc?export=download&id=1UlCMSVUt1VGfu-B9AH-DVlO4C35XC9QC" 
              target="_blank" 
              rel="noopener noreferrer"
              download
              className="group inline-flex items-center gap-3 px-6 py-3 rounded-xl border border-white/10 bg-white/5 hover:bg-white/10 hover:border-white/20 transition-all duration-300 backdrop-blur-sm"
              style={{ borderLeftColor: `${topColor}44`, borderTopColor: `${topColor}44` }}
            >
              <div 
                className="w-10 h-10 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform duration-300"
                style={{ background: `${topColor}11`, border: `1px solid ${topColor}33` }}
              >
                <Monitor size={20} style={{ color: topColor }} />
              </div>
              <div className="text-left">
                <div className="text-[10px] font-mono text-white/40 uppercase tracking-widest leading-none mb-1">Desktop Client</div>
                <div className="text-sm font-display font-medium text-white/90 tracking-wide">Download for Windows</div>
              </div>
              <div className="ml-2 opacity-30 group-hover:opacity-100 transition-opacity">
                <Download size={14} className="text-white" />
              </div>
            </a>
          </div>
        </div>
        <div className="absolute top-8 left-8 w-12 h-12 border-l-2 border-t-2 rounded-tl-lg z-10"
          style={{ borderColor: `${topColor}50`, transition: 'border-color 0.8s ease' }} />
        <div className="absolute bottom-8 right-8 w-12 h-12 border-r-2 border-b-2 rounded-br-lg z-10"
          style={{ borderColor: `${topColor}50`, transition: 'border-color 0.8s ease' }} />
      </div>

      {/* ── Form column ── */}
      <div className="
        relative z-10
        w-full lg:w-[480px]
        flex flex-col items-center justify-center
        min-h-screen
        px-5 py-10
        lg:bg-[#0a1628]/30 lg:backdrop-blur-xl lg:border-l lg:border-white/10
      ">

        {/* Mobile branding strip */}
        <div className="lg:hidden w-full max-w-sm mb-6">
          <div style={{
            height: 2, marginBottom: 14,
            background: `linear-gradient(90deg, transparent, ${topColor}, transparent)`,
            transition: 'background 0.8s ease',
          }} />
          <h1 className="font-display font-bold text-3xl text-white leading-tight">
            Work Integrity<br />
            <span style={{ color: topColor, transition: 'color 0.8s ease' }}>Intelligence System</span>
          </h1>
          <p className="text-white/45 text-xs mt-2 leading-relaxed">Real-time workforce monitoring & behavioral analytics</p>
        </div>

        <div
          className="w-full max-w-sm animate-fade-in rounded-2xl p-6 lg:p-0 lg:!bg-transparent lg:!border-transparent lg:!backdrop-blur-none"
          style={{
            background: 'rgba(10,22,40,0.72)',
            borderColor: `${topColor}22`,
            backdropFilter: 'blur(20px)',
            WebkitBackdropFilter: 'blur(20px)',
            border: '1px solid',
          }}
        >

          {/* ═══════════════════════════════════════════
              LOGO — large, no box, just the image
              with SENTINEL name below it
             ═══════════════════════════════════════════ */}
          <div className="flex flex-col items-center mb-8 pt-2">
            {/* Logo image — no border, no background box */}
            <div style={{ width: 72, height: 72, marginBottom: 10 }}>
              {!logoError ? (
                <img
                  src={LOGO_SRC}
                  alt="Sentinel"
                  onError={() => setLogoError(true)}
                  style={{ width: '100%', height: '100%', objectFit: 'contain', display: 'block' }}
                />
              ) : (
                /* Fallback: just the glowing S letter if no logo file */
                <div style={{
                  width: '100%', height: '100%',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 40, fontWeight: 900, fontFamily: 'var(--font-display, serif)',
                  color: topColor,
                  filter: `drop-shadow(0 0 12px ${topColor}90)`,
                  transition: 'color 0.8s ease, filter 0.8s ease',
                }}>
                  S
                </div>
              )}
            </div>

            {/* SENTINEL wordmark */}
            <h2
              className="font-display font-bold tracking-widest"
              style={{ fontSize: 22, letterSpacing: '0.2em', color: '#fff', lineHeight: 1 }}
            >
              SENTINEL
            </h2>
            {/* Underline accent in animated color */}
            <div style={{
              marginTop: 5, height: 2, width: 40,
              background: topColor,
              boxShadow: `0 0 8px ${topColor}`,
              transition: 'background 0.8s ease, box-shadow 0.8s ease',
              borderRadius: 1,
            }} />
            <p className="text-xs font-mono text-sentinel-muted tracking-widest mt-2">SECURE ACCESS</p>
          </div>

          {/* Sign in heading */}
          <div className="mb-6">
            <h3 className="font-display font-semibold text-2xl text-sentinel-text">Sign in</h3>
            <p className="text-sentinel-muted text-sm mt-1">Admins → Dashboard · Employees → My Portal</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="label mb-2 block text-sentinel-muted">Email address</label>
              <div className="relative">
                <Mail size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-sentinel-muted" />
                <input
                  type="email" value={email} onChange={e => setEmail(e.target.value)}
                  className="input-field pl-11" placeholder="your@email.com"
                  required autoComplete="email"
                />
              </div>
            </div>
            <div>
              <label className="label mb-2 block text-sentinel-muted">Password</label>
              <div className="relative">
                <Lock size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-sentinel-muted" />
                <input
                  type={showPass ? 'text' : 'password'} value={password}
                  onChange={e => setPassword(e.target.value)}
                  className="input-field pl-11 pr-11" placeholder="••••••••"
                  required autoComplete="current-password"
                />
                <button type="button" onClick={() => setShowPass(!showPass)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-sentinel-muted hover:text-sentinel-text transition-colors">
                  {showPass ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            {error && (
              <div className="flex items-start gap-2 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2.5">
                <AlertCircle size={14} className="text-red-400 mt-0.5 shrink-0" />
                <p className="text-red-400 text-xs font-mono">{error}</p>
              </div>
            )}

            <button
              type="submit" disabled={isLoading}
              className="w-full py-3 mt-1 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 rounded-lg font-mono font-bold text-sm tracking-wide transition-all"
              style={{
                background: isLoading ? '#1e3a5f' : topColor,
                color: '#020818',
                boxShadow: isLoading ? 'none' : `0 0 28px ${topColor}55`,
                transition: 'background 0.8s ease, box-shadow 0.8s ease',
              }}
            >
              {isLoading ? (
                <><div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" /><span style={{ color: '#94a3b8' }}>Authenticating...</span></>
              ) : 'Access Dashboard'}
            </button>
          </form>

          <div className="mt-6 pt-5 border-t border-sentinel-border/40 flex flex-col items-center gap-4">
            <p className="text-xs font-mono text-sentinel-muted text-center">SENTINEL v1.0 · All activity logged</p>
            
            {/* Secondary Download Link (Mobile focus) */}
            <a 
              href="https://drive.google.com/uc?export=download&id=1UlCMSVUt1VGfu-B9AH-DVlO4C35XC9QC"
              target="_blank"
              rel="noopener noreferrer"
              download
              className="lg:hidden flex items-center gap-2 text-[10px] font-mono font-bold tracking-widest text-sentinel-muted hover:text-cyan-400 transition-colors uppercase"
            >
              <Monitor size={12} /> Get Desktop App <Download size={10} />
            </a>
          </div>
        </div>

        {/* Mobile corner accents */}
        <div className="lg:hidden absolute top-5 left-5 w-7 h-7 pointer-events-none"
          style={{ borderLeft: `1.5px solid ${topColor}55`, borderTop: `1.5px solid ${topColor}55`, transition: 'border-color 0.8s ease' }} />
        <div className="lg:hidden absolute top-5 right-5 w-7 h-7 pointer-events-none"
          style={{ borderRight: `1.5px solid ${topColor}55`, borderTop: `1.5px solid ${topColor}55`, transition: 'border-color 0.8s ease' }} />
        <div className="lg:hidden absolute bottom-5 left-5 w-7 h-7 pointer-events-none"
          style={{ borderLeft: `1.5px solid ${topColor}55`, borderBottom: `1.5px solid ${topColor}55`, transition: 'border-color 0.8s ease' }} />
        <div className="lg:hidden absolute bottom-5 right-5 w-7 h-7 pointer-events-none"
          style={{ borderRight: `1.5px solid ${topColor}55`, borderBottom: `1.5px solid ${topColor}55`, transition: 'border-color 0.8s ease' }} />
      </div>
    </div>
  )
}