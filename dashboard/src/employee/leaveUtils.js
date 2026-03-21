export const LEAVE_TYPES = {
  EL: {
    code: 'EL',
    name: 'Earned Leave',
    fullName: 'Earned Leave / Privilege Leave',
    totalPerYear: 18,
    accrualRate: '1 day per 20 days worked',
    carryForward: 30,
    encashable: true,
    color: '#0088ff',
    description: 'Accrued based on days worked. Can be carried forward up to 30 days or encashed on separation.',
    requiresCertificate: false,
    minNoticeDays: 3,
    genderRestricted: false,
  },
  CL: {
    code: 'CL',
    name: 'Casual Leave',
    fullName: 'Casual Leave',
    totalPerYear: 8,
    accrualRate: 'Granted annually',
    carryForward: 0,
    encashable: false,
    color: '#ff3b00',
    description: 'For short-term personal emergencies. Lapses at year end, cannot be carried forward.',
    requiresCertificate: false,
    minNoticeDays: 0,
    genderRestricted: false,
  },
  SL: {
    code: 'SL',
    name: 'Sick Leave',
    fullName: 'Sick Leave',
    totalPerYear: 12,
    accrualRate: 'Granted annually',
    carryForward: 0,
    encashable: false,
    color: '#ffbb00',
    description: 'For illness or recovery. Medical certificate required for 3+ consecutive days.',
    requiresCertificate: true,
    certificateAfterDays: 2,
    minNoticeDays: 0,
    genderRestricted: false,
  },
  ML: {
    code: 'ML',
    name: 'Maternity Leave',
    fullName: 'Maternity Leave',
    totalPerYear: 182,
    accrualRate: 'As per Maternity Benefit Act 2017',
    carryForward: 0,
    encashable: false,
    color: '#cc00aa',
    description: '26 weeks paid leave for first 2 children, 12 weeks for subsequent. As per Maternity Benefit Act 2017.',
    requiresCertificate: true,
    minNoticeDays: 30,
    genderRestricted: true,
    allowedGenders: ['female', 'Female', 'F', 'f'],
  },
}

// Returns only the leave types applicable to this employee
export function getApplicableLeaveTypes(gender) {
  return Object.fromEntries(
    Object.entries(LEAVE_TYPES).filter(([, info]) => {
      if (!info.genderRestricted) return true
      return info.allowedGenders?.includes(gender)
    })
  )
}

export function calculateLeaveBalance(joinDate, leavesTaken = [], workingDaysDone = 0, gender = null) {
  const now  = new Date()
  const join = new Date(joinDate)
  const monthsWorked = Math.max(0,
    (now.getFullYear() - join.getFullYear()) * 12 +
    (now.getMonth() - join.getMonth())
  )

  const applicable = getApplicableLeaveTypes(gender)
  const result = {}

  if (applicable.EL) {
    const elAccrued = Math.floor(workingDaysDone / 20)
    const elTaken   = leavesTaken.filter(l => l.type === 'EL').reduce((a, l) => a + l.days, 0)
    result.EL = {
      total:   elAccrued,
      taken:   elTaken,
      balance: Math.max(0, Math.min(elAccrued - elTaken, LEAVE_TYPES.EL.carryForward + LEAVE_TYPES.EL.totalPerYear)),
      accrued: elAccrued,
    }
  }

  if (applicable.CL) {
    const clTotal = Math.floor((LEAVE_TYPES.CL.totalPerYear / 12) * Math.min(monthsWorked, 12))
    const clTaken = leavesTaken.filter(l => l.type === 'CL').reduce((a, l) => a + l.days, 0)
    result.CL = { total: clTotal, taken: clTaken, balance: Math.max(0, clTotal - clTaken) }
  }

  if (applicable.SL) {
    const slTotal = Math.floor((LEAVE_TYPES.SL.totalPerYear / 12) * Math.min(monthsWorked, 12))
    const slTaken = leavesTaken.filter(l => l.type === 'SL').reduce((a, l) => a + l.days, 0)
    result.SL = { total: slTotal, taken: slTaken, balance: Math.max(0, slTotal - slTaken) }
  }

  if (applicable.ML) {
    const mlTaken = leavesTaken.filter(l => l.type === 'ML').reduce((a, l) => a + l.days, 0)
    result.ML = { total: LEAVE_TYPES.ML.totalPerYear, taken: mlTaken, balance: Math.max(0, LEAVE_TYPES.ML.totalPerYear - mlTaken) }
  }

  return result
}

export function getLeaveStatusColor(status, theme) {
  switch (status) {
    case 'approved': return theme.success
    case 'rejected': return theme.danger
    case 'pending':  return theme.warning
    default:         return theme.textMuted
  }
}

export function workingDaysBetween(start, end) {
  let count = 0
  const cur = new Date(start)
  while (cur <= end) {
    const day = cur.getDay()
    if (day !== 0 && day !== 6) count++
    cur.setDate(cur.getDate() + 1)
  }
  return count
}