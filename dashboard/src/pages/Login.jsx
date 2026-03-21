import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { Shield, Eye, EyeOff, AlertCircle } from 'lucide-react'
import LightPillar from '../components/ui/LightPillar'

/* Cycles through a palette of vibrant gradient pairs */
const COLOR_PALETTE = [
  { top: '#22d3ee', bottom: '#0a1628' },  // cyan / deep navy
  { top: '#a855f7', bottom: '#0f0a1e' },  // violet / dark purple
  { top: '#ec4899', bottom: '#1a0514' },  // pink / deep rose
  { top: '#10b981', bottom: '#041a10' },  // emerald / forest
  { top: '#f59e0b', bottom: '#1a0e00' },  // amber / deep brown
  { top: '#6366f1', bottom: '#080b1e' },  // indigo / void
  { top: '#22d3ee', bottom: '#0a1628' },  // back to start (smooth loop)
]

function useCyclingColors(intervalMs = 3500) {
  const [idx, setIdx]  = useState(0)
  const [next, setNext] = useState(1)
  const [t, setT]      = useState(0)         // 0→1 interpolation
  const rafRef         = useRef(null)
  const startRef       = useRef(null)

  useEffect(() => {
    const duration = intervalMs

    const tick = (now) => {
      if (!startRef.current) startRef.current = now
      const elapsed = now - startRef.current
      const progress = Math.min(elapsed / duration, 1)

      setT(progress)

      if (progress >= 1) {
        // Advance to next pair
        setIdx(i => {
          const ni = (i + 1) % (COLOR_PALETTE.length - 1)
          setNext((ni + 1) % (COLOR_PALETTE.length - 1))
          return ni
        })
        startRef.current = now
        setT(0)
      }

      rafRef.current = requestAnimationFrame(tick)
    }

    rafRef.current = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(rafRef.current)
  }, [intervalMs])

  /* Lerp hex colors */
  const lerp = (a, b, t) => {
    const hexToRgb = h => [
      parseInt(h.slice(1,3),16),
      parseInt(h.slice(3,5),16),
      parseInt(h.slice(5,7),16),
    ]
    const rgbToHex = ([r,g,b]) =>
      '#' + [r,g,b].map(v => Math.round(v).toString(16).padStart(2,'0')).join('')
    const ra = hexToRgb(a), rb = hexToRgb(b)
    return rgbToHex(ra.map((v,i) => v + (rb[i]-v) * t))
  }

  const ease = t < 0.5 ? 2*t*t : -1+(4-2*t)*t  // ease-in-out

  return {
    topColor:    lerp(COLOR_PALETTE[idx].top,    COLOR_PALETTE[next].top,    ease),
    bottomColor: lerp(COLOR_PALETTE[idx].bottom, COLOR_PALETTE[next].bottom, ease),
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
    if (token && user) {
      const isAdmin = user.role === 'admin' || user.role === 'super_admin'
      navigate(isAdmin ? '/dashboard' : '/my/dashboard')
    }
  }, [token, user])

  useEffect(() => { clearError() }, [email, password])

  const handleSubmit = async (e) => {
    e.preventDefault()
    const result = await login(email, password)
    if (result?.success) {
      const isAdmin = result.role === 'admin' || result.role === 'super_admin'
      navigate(isAdmin ? '/dashboard' : '/my/dashboard')
    }
  }

  return (
    <div className="min-h-screen bg-sentinel-bg flex">

      {/* ── Left panel — animated diagonal LightPillar ── */}
      <div className="hidden lg:flex flex-1 items-end justify-start relative overflow-hidden">
        {/*
          pillarRotation={45} tilts the internal UV space by 45°
          We also physically rotate the container 45° and scale it up so
          the pillar fills the panel edge-to-edge without leaving gaps.
        */}
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
            pillarRotation={0}
            quality="high"
          />
        </div>

        {/* Dark vignette so the text is readable */}
        <div style={{
          position: 'absolute', inset: 0,
          background: 'linear-gradient(135deg, rgba(2,8,24,0.55) 0%, rgba(2,8,24,0.15) 50%, rgba(2,8,24,0.65) 100%)',
          pointerEvents: 'none',
        }} />

        {/* Overlay text */}
        <div className="relative z-10 p-16 pb-20">
          <div className="glow-line mb-6 max-w-xs" />
          <h1 className="font-display font-bold text-4xl text-white leading-tight drop-shadow-lg">
            Work Integrity<br />
            <span style={{ color: topColor, transition: 'color 0.8s ease' }}>
              Intelligence System
            </span>
          </h1>
          <p className="mt-4 text-white/60 font-body text-sm leading-relaxed max-w-sm">
            Real-time workforce monitoring, behavioral analytics, and
            integrity enforcement for modern enterprises.
          </p>
        </div>

        {/* Corner decorations */}
        <div className="absolute top-8 left-8 w-12 h-12 border-l-2 border-t-2 rounded-tl-lg z-10"
          style={{ borderColor: `${topColor}50`, transition: 'border-color 0.8s ease' }} />
        <div className="absolute bottom-8 right-8 w-12 h-12 border-r-2 border-b-2 rounded-br-lg z-10"
          style={{ borderColor: `${topColor}50`, transition: 'border-color 0.8s ease' }} />
      </div>

      {/* ── Right panel — form ── */}
      <div className="w-full lg:w-[480px] flex items-center justify-center p-8 bg-navy-900 border-l border-sentinel-border">
        <div className="w-full max-w-sm animate-fade-in">

          {/* Logo */}
          <div className="flex items-center gap-3 mb-10">
            <div className="w-10 h-10 rounded-xl bg-cyan-400/10 border border-cyan-400/30 flex items-center justify-center">
              <Shield size={18} className="text-cyan-400" />
            </div>
            <div>
              <h2 className="font-display font-bold text-xl text-sentinel-text">SENTINEL</h2>
              <p className="text-xs font-mono text-sentinel-muted tracking-widest">SECURE ACCESS</p>
            </div>
          </div>

          <div className="mb-8">
            <h3 className="font-display font-semibold text-2xl text-sentinel-text">Sign in</h3>
            <p className="text-sentinel-muted text-sm mt-1">
              Admins → Dashboard · Employees → My Portal
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="label mb-2 block">Email address</label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                className="input-field"
                placeholder="your@email.com"
                required
                autoComplete="email"
              />
            </div>

            <div>
              <label className="label mb-2 block">Password</label>
              <div className="relative">
                <input
                  type={showPass ? 'text' : 'password'}
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  className="input-field pr-11"
                  placeholder="••••••••"
                  required
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPass(!showPass)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-sentinel-muted hover:text-sentinel-text transition-colors"
                >
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
              type="submit"
              disabled={isLoading}
              className="btn-primary w-full py-3 mt-2 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <>
                  <div className="w-4 h-4 border-2 border-navy-950/30 border-t-navy-950 rounded-full animate-spin" />
                  <span>Authenticating...</span>
                </>
              ) : (
                'Access Dashboard'
              )}
            </button>
          </form>

          <div className="mt-8 pt-6 border-t border-sentinel-border">
            <p className="text-xs font-mono text-sentinel-muted text-center">
              SENTINEL v1.0 · All activity logged
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}