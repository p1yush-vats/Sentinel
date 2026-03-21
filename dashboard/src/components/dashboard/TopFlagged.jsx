import { riskColor, initials, fromNow } from '../../utils/helpers'
import { AlertTriangle } from 'lucide-react'

export default function TopFlagged({ employees = [], loading, onEmployeeClick, activeEmployeeIds = new Set() }) {
  return (
    <div className="card p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="section-title">High Risk Employees</h3>
        <AlertTriangle size={15} className="text-red-400" />
      </div>

      {loading ? (
        Array(4).fill(0).map((_, i) => (
          <div key={i} className="flex items-center gap-3 py-2.5">
            <div className="w-8 h-8 rounded-full bg-navy-700 animate-pulse" />
            <div className="flex-1">
              <div className="h-3 bg-navy-700 rounded w-1/2 animate-pulse" />
              <div className="h-2 bg-navy-700 rounded w-1/3 mt-1 animate-pulse" />
            </div>
          </div>
        ))
      ) : employees.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-8 gap-2">
          <AlertTriangle size={24} className="text-sentinel-muted opacity-40" />
          <p className="text-sentinel-muted text-sm font-mono text-center">No high-risk employees</p>
          <p className="text-sentinel-muted text-xs font-mono text-center opacity-60">Risk scores are calculated from session flags</p>
        </div>
      ) : (
        employees.slice(0, 5).map((emp, i) => {
          const isActive = activeEmployeeIds.has(emp.id)
          return (
            <div
              key={emp.id}
              onClick={() => onEmployeeClick?.(emp.id)}
              className={`flex items-center gap-3 py-2.5 border-b border-sentinel-border/30 last:border-0
                ${onEmployeeClick ? 'cursor-pointer hover:bg-navy-700/30 -mx-2 px-2 rounded-lg transition-colors' : ''}
                animate-fade-in stagger-${i+1}`}
            >
              {/* Avatar with live indicator */}
              <div className="relative shrink-0">
                <div className="w-8 h-8 rounded-full bg-red-400/10 border border-red-400/20 flex items-center justify-center text-xs font-mono text-red-400 font-bold">
                  {initials(emp.full_name)}
                </div>
                {isActive && (
                  <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full bg-emerald-400 border-2 border-navy-800 animate-pulse" />
                )}
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1.5">
                  <p className="text-sm text-sentinel-text truncate">{emp.full_name}</p>
                  {isActive && (
                    <span className="text-[9px] font-mono text-emerald-400 bg-emerald-400/10 px-1 py-0.5 rounded shrink-0">LIVE</span>
                  )}
                </div>
                <p className="text-[11px] font-mono text-sentinel-muted">{emp.department || '—'}</p>
              </div>

              <div className="flex flex-col items-end shrink-0 gap-0.5">
                <span className={`font-mono font-bold text-sm ${riskColor(emp.risk_score)}`}>
                  {Math.round(emp.risk_score || 0)}
                </span>
                <span className="text-[9px] font-mono text-sentinel-muted">risk</span>
              </div>
            </div>
          )
        })
      )}
    </div>
  )
}