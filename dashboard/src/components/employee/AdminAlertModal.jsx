import { useState } from 'react'
import { createPortal } from 'react-dom'
import { AlertTriangle, Send, X } from 'lucide-react'

export default function AdminAlertModal({ isOpen, onClose, onSend, employeeName }) {
  const [message, setMessage] = useState('')
  const [isSending, setIsSending] = useState(false)

  if (!isOpen) return null

  const handleSend = async () => {
    if (!message.trim()) return
    setIsSending(true)
    await onSend(message)
    setIsSending(false)
    setMessage('')
    onClose()
  }

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fade-in p-4">
      <div className="bg-navy-800 border border-sentinel-border rounded-xl shadow-2xl w-full max-w-md overflow-hidden animate-slide-up relative">
        <div className="p-4 border-b border-sentinel-border bg-navy-900/50 flex justify-between items-center">
          <div className="flex items-center gap-2 text-sentinel-text">
            <AlertTriangle className="w-5 h-5 text-amber-500" />
            <h3 className="font-display font-semibold">Alert Employee</h3>
          </div>
          <button onClick={onClose} className="text-sentinel-muted hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-5">
          <p className="text-sm text-sentinel-muted mb-4 font-mono">
            Send an instant desktop popup and sound alert directly to <span className="font-bold text-white">{employeeName}</span>.
          </p>

          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Type your alert message here (e.g. 'Please return to your workstation')"
            className="w-full bg-navy-900 border border-sentinel-border rounded-lg p-3 text-sm text-white focus:outline-none focus:border-blue-500 transition-colors h-24 resize-none"
            autoFocus
          />
        </div>

        <div className="p-4 bg-navy-900/50 border-t border-sentinel-border flex justify-end gap-3">
          <button 
            onClick={onClose}
            className="px-4 py-2 rounded-lg text-sm font-medium text-sentinel-muted hover:bg-white/5 transition-colors"
          >
            Cancel
          </button>
          <button 
            onClick={handleSend}
            disabled={!message.trim() || isSending}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg text-sm font-medium transition-colors shadow-lg shadow-blue-900/20"
          >
            <Send className="w-4 h-4" />
            {isSending ? 'Sending...' : 'Send Alert'}
          </button>
        </div>
      </div>
    </div>, document.body
  )
}
