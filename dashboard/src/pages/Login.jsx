import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { Shield, Eye, EyeOff, AlertCircle } from 'lucide-react'
import { Canvas, useFrame } from '@react-three/fiber'
import { Sphere, MeshDistortMaterial, Float } from '@react-three/drei'

function AnimatedSphere() {
  const meshRef = useRef()
  useFrame((state) => {
    meshRef.current.rotation.x = state.clock.elapsedTime * 0.15
    meshRef.current.rotation.y = state.clock.elapsedTime * 0.2
  })
  return (
    <Float speed={2} rotationIntensity={0.5} floatIntensity={0.8}>
      <Sphere ref={meshRef} args={[1.8, 64, 64]}>
        <MeshDistortMaterial
          color="#22d3ee"
          attach="material"
          distort={0.4}
          speed={2}
          roughness={0}
          metalness={0.8}
          opacity={0.15}
          transparent
          wireframe
        />
      </Sphere>
      <Sphere args={[1.4, 32, 32]}>
        <MeshDistortMaterial
          color="#0ea5e9"
          attach="material"
          distort={0.6}
          speed={3}
          roughness={0.1}
          metalness={0.9}
          opacity={0.08}
          transparent
        />
      </Sphere>
    </Float>
  )
}

export default function Login() {
  const [email,     setEmail]     = useState('')
  const [password,  setPassword]  = useState('')
  const [showPass,  setShowPass]  = useState(false)
  const { login, isLoading, error, clearError, token } = useAuthStore()
  const navigate = useNavigate()

  useEffect(() => { if (token) navigate('/dashboard') }, [token])
  useEffect(() => { clearError() }, [email, password])

  const handleSubmit = async (e) => {
    e.preventDefault()
    const ok = await login(email, password)
    if (ok) navigate('/dashboard')
  }

  return (
    <div className="min-h-screen bg-sentinel-bg grid-bg flex">
      {/* Left — 3D visual */}
      <div className="hidden lg:flex flex-1 items-center justify-center relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-radial from-cyan-400/5 via-transparent to-transparent" />
        <Canvas camera={{ position: [0, 0, 4] }}>
          <ambientLight intensity={0.5} />
          <pointLight position={[10, 10, 10]} color="#22d3ee" intensity={2} />
          <pointLight position={[-10, -10, -10]} color="#0ea5e9" intensity={1} />
          <AnimatedSphere />
        </Canvas>

        <div className="absolute bottom-16 left-16 right-16">
          <div className="glow-line mb-6" />
          <h1 className="font-display font-bold text-4xl text-sentinel-text leading-tight">
            Work Integrity<br />
            <span className="text-cyan-400">Intelligence System</span>
          </h1>
          <p className="mt-3 text-sentinel-muted font-body text-sm leading-relaxed max-w-sm">
            Real-time workforce monitoring, behavioral analytics, and integrity enforcement for modern enterprises.
          </p>
        </div>

        {/* Corner decorations */}
        <div className="absolute top-8 left-8 w-12 h-12 border-l-2 border-t-2 border-cyan-400/20 rounded-tl-lg" />
        <div className="absolute bottom-8 right-8 w-12 h-12 border-r-2 border-b-2 border-cyan-400/20 rounded-br-lg" />
      </div>

      {/* Right — form */}
      <div className="w-full lg:w-[480px] flex items-center justify-center p-8 bg-navy-900/80 border-l border-sentinel-border backdrop-blur-sm">
        <div className="w-full max-w-sm animate-fade-in">
          {/* Header */}
          <div className="flex items-center gap-3 mb-10">
            <div className="w-10 h-10 rounded-xl bg-cyan-400/10 border border-cyan-400/30 flex items-center justify-center">
              <Shield size={18} className="text-cyan-400" />
            </div>
            <div>
              <h2 className="font-display font-bold text-xl text-sentinel-text">SENTINEL</h2>
              <p className="text-xs font-mono text-sentinel-muted tracking-widest">ADMIN ACCESS</p>
            </div>
          </div>

          <div className="mb-8">
            <h3 className="font-display font-semibold text-2xl text-sentinel-text">Sign in</h3>
            <p className="text-sentinel-muted text-sm mt-1">Restricted to authorized administrators</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="label mb-2 block">Email address</label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                className="input-field"
                placeholder="admin@sentinel.com"
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
              SENTINEL v1.0 · Restricted Access · All activity logged
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
