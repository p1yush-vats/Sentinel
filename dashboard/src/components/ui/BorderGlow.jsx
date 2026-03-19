import { useRef } from 'react'

export default function BorderGlow({ children, className = '', glowColor = '#22d3ee', borderRadius = '0.75rem' }) {
  const containerRef = useRef(null)

  const handleMouseMove = (e) => {
    const el = containerRef.current
    if (!el) return
    const rect = el.getBoundingClientRect()
    const x = ((e.clientX - rect.left) / rect.width) * 100
    const y = ((e.clientY - rect.top) / rect.height) * 100
    el.style.setProperty('--glow-x', `${x}%`)
    el.style.setProperty('--glow-y', `${y}%`)
  }

  const handleMouseLeave = () => {
    const el = containerRef.current
    if (!el) return
    el.style.setProperty('--glow-x', '50%')
    el.style.setProperty('--glow-y', '50%')
  }

  return (
    <div
      ref={containerRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      className={`border-glow-card ${className}`}
      style={{
        '--glow-color': glowColor,
        '--border-radius': borderRadius,
        '--glow-x': '50%',
        '--glow-y': '50%',
      }}
    >
      {children}
    </div>
  )
}
