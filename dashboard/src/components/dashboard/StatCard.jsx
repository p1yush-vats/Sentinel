import { useEffect, useRef, useState } from 'react'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

function useCountUp(target, duration = 1200) {
  const [value, setValue] = useState(0)
  useEffect(() => {
    if (!target && target !== 0) return
    const start = Date.now()
    const tick = () => {
      const elapsed = Date.now() - start
      const progress = Math.min(elapsed / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 3)
      setValue(Math.round(eased * target))
      if (progress < 1) requestAnimationFrame(tick)
    }
    requestAnimationFrame(tick)
  }, [target])
  return value
}

export default function StatCard({ label, value, unit = '', icon: Icon, trend, trendLabel, accent = 'cyan', loading }) {
  const displayed = useCountUp(typeof value === 'number' ? value : 0)

  const colors = {
    cyan:   { icon: 'text-cyan-400',    bg: 'bg-cyan-400/8',   border: 'border-cyan-400/15',   glow: 'shadow-glow-cyan' },
    green:  { icon: 'text-emerald-400', bg: 'bg-emerald-400/8',border: 'border-emerald-400/15', glow: 'shadow-glow-green' },
    red:    { icon: 'text-red-400',     bg: 'bg-red-400/8',    border: 'border-red-400/15',     glow: 'shadow-glow-red' },
    amber:  { icon: 'text-amber-400',   bg: 'bg-amber-400/8',  border: 'border-amber-400/15',   glow: '' },
    purple: { icon: 'text-purple-400',  bg: 'bg-purple-400/8', border: 'border-purple-400/15',  glow: '' },
  }
  const c = colors[accent] || colors.cyan

  return (
    <div className={`card p-5 transition-all duration-300 hover:${c.border} hover:${c.glow} animate-fade-in`}>
      <div className="flex items-start justify-between mb-4">
        <p className="label">{label}</p>
        {Icon && (
          <div className={`w-8 h-8 rounded-lg ${c.bg} border ${c.border} flex items-center justify-center`}>
            <Icon size={15} className={c.icon} />
          </div>
        )}
      </div>

      {loading ? (
        <div className="h-8 w-24 bg-navy-700 rounded animate-pulse" />
      ) : (
        <div className="flex items-end gap-1.5">
          <span className={`font-display font-bold text-3xl text-sentinel-text`}>
            {typeof value === 'number' ? displayed.toLocaleString() : value}
          </span>
          {unit && <span className="text-sentinel-muted font-mono text-sm mb-1">{unit}</span>}
        </div>
      )}

      {trendLabel && (
        <div className="flex items-center gap-1.5 mt-3">
          {trend > 0  ? <TrendingUp  size={12} className="text-emerald-400" /> :
           trend < 0  ? <TrendingDown size={12} className="text-red-400" /> :
                        <Minus size={12} className="text-sentinel-muted" />}
          <span className={`text-xs font-mono ${trend > 0 ? 'text-emerald-400' : trend < 0 ? 'text-red-400' : 'text-sentinel-muted'}`}>
            {trendLabel}
          </span>
        </div>
      )}
    </div>
  )
}
