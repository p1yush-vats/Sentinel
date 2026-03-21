import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { Shield, Eye, EyeOff, AlertCircle } from 'lucide-react'
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

export default function Login() {
  const [email,    setEmail]    = useState('')
  const [password, setPassword] = useState('')
  const [showPass, setShowPass] = useState(false)
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

      {/* ═══════════════════════════════════
          MOBILE BACKGROUND  (below lg)
          Full-screen pillar + dark overlay
         ═══════════════════════════════════ */}
      <div className="lg:hidden absolute inset-0 z-0">
        <div style={{
          position: 'absolute', inset: '-60%',
          transform: 'rotate(45deg) scale(2)',
          transformOrigin: 'center center',
        }}>
          <LightPillar
            topColor={topColor}
            bottomColor={bottomColor}
            intensity={1.7}
            rotationSpeed={0.14}
            interactive={false}
            glowAmount={0.008}
            pillarWidth={1.8}
            pillarHeight={0.28}
            noiseIntensity={0.3}
            mixBlendMode="screen"
            quality="medium"
          />
        </div>
        {/* Multi-stop overlay: dark at edges, semi-transparent in middle so the light bleeds through */}
        <div style={{
          position: 'absolute', inset: 0,
          background: 'linear-gradient(160deg, rgba(2,8,24,0.88) 0%, rgba(2,8,24,0.45) 45%, rgba(2,8,24,0.85) 100%)',
        }} />
      </div>

      {/* ═══════════════════════════════════
          DESKTOP left panel  (lg+)
         ═══════════════════════════════════ */}
      <div className="hidden lg:flex flex-1 items-end justify-start relative overflow-hidden">
        <div style={{
          position: 'absolute', inset: '-40%',
          transform: 'rotate(45deg) scale(1.6)',
          transformOrigin: 'center center',
        }}>
          <LightPillar
            topColor={topColor}
            bottomColor={bottomColor}
            intensity={1.4}
            rotationSpeed={0.18}
            interactive={false}
            glowAmount={0.007}
            pillarWidth={2.2}
            pillarHeight={0.3}
            noiseIntensity={0.35}
            mixBlendMode="screen"
            quality="high"
          />
        </div>
        <div style={{
          position: 'absolute', inset: 0,
          background: 'linear-gradient(135deg, rgba(2,8,24,0.55) 0%, rgba(2,8,24,0.15) 50%, rgba(2,8,24,0.65) 100%)',
          pointerEvents: 'none',
        }} />
        <div className="relative z-10 p-16 pb-20">
          <div className="glow-line mb-6 max-w-xs" />
          <h1 className="font-display font-bold text-4xl text-white leading-tight drop-shadow-lg">
            Work Integrity<br />
            <span style={{ color: topColor, transition: 'color 0.8s ease' }}>Intelligence System</span>
          </h1>
          <p className="mt-4 text-white/60 font-body text-sm leading-relaxed max-w-sm">
            Real-time workforce monitoring, behavioral analytics, and integrity enforcement for modern enterprises.
          </p>
        </div>
        <div className="absolute top-8 left-8 w-12 h-12 border-l-2 border-t-2 rounded-tl-lg z-10"
          style={{ borderColor: `${topColor}50`, transition: 'border-color 0.8s ease' }} />
        <div className="absolute bottom-8 right-8 w-12 h-12 border-r-2 border-b-2 rounded-br-lg z-10"
          style={{ borderColor: `${topColor}50`, transition: 'border-color 0.8s ease' }} />
      </div>

      {/* ═══════════════════════════════════
          FORM column
          Desktop: fixed-width side panel
          Mobile:  full-width, centered,
                   floats over the pillar bg
         ═══════════════════════════════════ */}
      <div className="
        relative z-10
        w-full lg:w-[480px]
        flex flex-col items-center justify-center
        min-h-screen
        px-5 py-10
        lg:bg-navy-900 lg:border-l lg:border-sentinel-border
      ">

        {/* ── Mobile-only: branding hero above the card ── */}
        <div className="lg:hidden w-full max-w-sm mb-6">
          {/* Tiny animated line */}
          <div style={{
            height: 2, marginBottom: 14,
            background: `linear-gradient(90deg, transparent, ${topColor}, transparent)`,
            transition: 'background 0.8s ease',
          }} />
          <h1 className="font-display font-bold text-3xl text-white leading-tight">
            Work Integrity<br />
            <span style={{ color: topColor, transition: 'color 0.8s ease' }}>Intelligence System</span>
          </h1>
          <p className="text-white/45 text-xs mt-2 leading-relaxed max-w-xs">
            Real-time workforce monitoring & behavioral analytics
          </p>
        </div>

        {/* ── The form card ──
            Desktop: transparent, no border
            Mobile: frosted glass card  ── */}
        <div className="
          w-full max-w-sm
          animate-fade-in
          lg:bg-transparent lg:border-0 lg:shadow-none lg:rounded-none lg:backdrop-blur-none lg:p-0
          rounded-2xl border shadow-2xl
          p-6
        "
          style={{
            /* Mobile glass */
            background: 'rgba(10,22,40,0.72)',
            borderColor: `${topColor}22`,
            backdropFilter: 'blur(20px)',
            WebkitBackdropFilter: 'blur(20px)',
          }}
          /* Override back to transparent on desktop via Tailwind above */
        >
          {/* Logo */}
          <div className="flex items-center gap-3 mb-8">
            <div className="w-10 h-10 rounded-xl bg-cyan-400/10 border border-cyan-400/30 flex items-center justify-center">
              <Shield size={18} className="text-cyan-400" />
            </div>
            <div>
              <h2 className="font-display font-bold text-xl text-sentinel-text">SENTINEL</h2>
              <p className="text-xs font-mono text-sentinel-muted tracking-widest">SECURE ACCESS</p>
            </div>
          </div>

          <div className="mb-6">
            <h3 className="font-display font-semibold text-2xl text-sentinel-text">Sign in</h3>
            <p className="text-sentinel-muted text-sm mt-1">Admins → Dashboard · Employees → My Portal</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="label mb-2 block">Email address</label>
              <input
                type="email" value={email} onChange={e => setEmail(e.target.value)}
                className="input-field" placeholder="your@email.com"
                required autoComplete="email"
              />
            </div>

            <div>
              <label className="label mb-2 block">Password</label>
              <div className="relative">
                <input
                  type={showPass ? 'text' : 'password'} value={password}
                  onChange={e => setPassword(e.target.value)}
                  className="input-field pr-11" placeholder="••••••••"
                  required autoComplete="current-password"
                />
                <button type="button" onClick={() => setShowPass(!showPass)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-sentinel-muted hover:text-sentinel-text transition-colors">
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
              className="btn-primary w-full py-3 mt-1 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              style={{
                background: isLoading ? undefined : topColor,
                color: '#020818',
                fontWeight: 700,
                transition: 'background 0.8s ease',
                boxShadow: `0 0 24px ${topColor}50`,
              }}
            >
              {isLoading ? (
                <><div className="w-4 h-4 border-2 border-navy-950/30 border-t-navy-950 rounded-full animate-spin" /><span>Authenticating...</span></>
              ) : 'Access Dashboard'}
            </button>
          </form>

          <div className="mt-6 pt-5 border-t border-sentinel-border/40">
            <p className="text-xs font-mono text-sentinel-muted text-center">SENTINEL v1.0 · All activity logged</p>
          </div>
        </div>

        {/* Mobile corner accents outside the card */}
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