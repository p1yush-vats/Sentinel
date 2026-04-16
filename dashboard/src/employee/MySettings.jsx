import { useState } from 'react'
import toast from 'react-hot-toast'
import { authAPI, reportsAPI } from '../services/api'
import { useAuthStore } from '../store/authStore'
import { Download, Lock, KeyRound } from 'lucide-react'

export default function MySettings() {
  const { user } = useAuthStore()
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [downloading, setDownloading] = useState(false)

  const handlePasswordChange = async (e) => {
    e.preventDefault()
    if (newPassword !== confirmPassword) {
      toast.error('New passwords do not match')
      return
    }
    if (newPassword.length < 6) {
      toast.error('Password must be at least 6 characters')
      return
    }

    setLoading(true)
    try {
      await authAPI.changePassword({
        current_password: currentPassword,
        new_password: newPassword
      })
      toast.success('Password updated successfully')
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to change password')
    } finally {
      setLoading(false)
    }
  }

  const handleDownloadDossier = async () => {
    setDownloading(true)
    try {
      const toastId = toast.loading('Generating your dossier...', { id: 'dossier_emp' })
      const res = await reportsAPI.downloadDossier(user.id)
      const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `My_Dossier_${user.full_name?.replace(/ /g, '_')}.pdf`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      toast.success('Dossier downloaded successfully', { id: 'dossier_emp' })
    } catch {
      toast.error('Failed to generate dossier', { id: 'dossier_emp' })
    } finally {
      setDownloading(false)
    }
  }

  return (
    <div className="space-y-6 animate-fade-in max-w-2xl mx-auto">
      <div className="flex items-center gap-3 border-b border-sentinel-border pb-4">
        <div className="w-10 h-10 rounded-xl bg-navy-800 border border-sentinel-border flex items-center justify-center shrink-0">
          <KeyRound size={18} className="text-sentinel-text" />
        </div>
        <div>
          <h1 className="font-display text-xl font-bold tracking-tight">Account Settings</h1>
          <p className="font-mono text-xs text-sentinel-muted mt-1">Manage your credentials and data</p>
        </div>
      </div>

      <div className="card p-6">
        <h2 className="section-title mb-5 flex items-center gap-2">
          <Lock size={14} className="text-cyan-400" /> Security
        </h2>
        <form onSubmit={handlePasswordChange} className="space-y-4">
          <div>
            <label className="label block mb-1">Current Password</label>
            <input 
              type="password" 
              className="input-field w-full" 
              required
              value={currentPassword}
              onChange={e => setCurrentPassword(e.target.value)}
              placeholder="Enter current password"
            />
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="label block mb-1">New Password</label>
              <input 
                type="password" 
                className="input-field w-full" 
                required
                value={newPassword}
                onChange={e => setNewPassword(e.target.value)}
                placeholder="Minimum 6 characters"
              />
            </div>
            <div>
              <label className="label block mb-1">Confirm New Password</label>
              <input 
                type="password" 
                className="input-field w-full" 
                required
                value={confirmPassword}
                onChange={e => setConfirmPassword(e.target.value)}
                placeholder="Repeat new password"
              />
            </div>
          </div>
          <div className="pt-2">
            <button type="submit" disabled={loading} className="btn-primary w-full sm:w-auto px-6 font-mono text-sm">
              {loading ? 'UPDATING...' : 'UPDATE PASSWORD'}
            </button>
          </div>
        </form>
      </div>

      <div className="card p-6 border border-emerald-500/20 bg-emerald-500/5">
        <h2 className="section-title mb-2 flex items-center gap-2 text-emerald-400">
          <Download size={14} /> My Dossier
        </h2>
        <p className="font-mono text-xs text-sentinel-muted mb-4 leading-relaxed">
          Download a comprehensive PDF report containing your recent work sessions, tasks, attendance, flags, and overall risk score.
        </p>
        <button 
          onClick={handleDownloadDossier} 
          disabled={downloading}
          className="flex items-center justify-center gap-2 px-5 py-2.5 rounded-lg border border-emerald-500/40 text-emerald-400 hover:bg-emerald-500/10 font-mono text-sm transition-all disabled:opacity-50"
        >
          <Download size={15} />
          {downloading ? 'GENERATING PDF...' : 'DOWNLOAD DOSSIER'}
        </button>
      </div>
    </div>
  )
}
