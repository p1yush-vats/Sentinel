import { riskColor, initials, fromNow } from '../../utils/helpers'
import { AlertTriangle } from 'lucide-react'

export default function TopFlagged({ employees = [], loading, onEmployeeClick }) {
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
        <p className="text-sentinel-muted text-sm font-mono text-center py-6">No high-risk employees</p>
      ) : (
        employees.slice(0, 5).map((emp, i) => (
          <div
            key={emp.id}
            onClick={() => onEmployeeClick?.(emp.id)}
            className={`flex items-center gap-3 py-2.5 border-b border-sentinel-border/30 last:border-0
              ${onEmployeeClick ? 'cursor-pointer hover:bg-navy-700/30 -mx-2 px-2 rounded-lg transition-colors' : ''}
              animate-fade-in stagger-${i+1}`}
          >
            <div className="w-8 h-8 rounded-full bg-red-400/10 border border-red-400/20 flex items-center justify-center text-xs font-mono text-red-400 font-bold shrink-0">
              {initials(emp.full_name)}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm text-sentinel-text truncate">{emp.full_name}</p>
              <p className="text-[11px] font-mono text-sentinel-muted">{emp.department || '—'}</p>
            </div>
            <span className={`font-mono font-bold text-sm shrink-0 ${riskColor(emp.risk_score)}`}>
              {Math.round(emp.risk_score || 0)}
            </span>
          </div>
        ))
      )}
    </div>
  )
}