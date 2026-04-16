import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: '#0f1f38',
            color: '#e2e8f0',
            border: '1px solid #162848',
            fontFamily: 'IBM Plex Mono, monospace',
            fontSize: '13px',
          },
          success: { iconTheme: { primary: '#10b981', secondary: '#020818' } },
          error:   { iconTheme: { primary: '#ef4444', secondary: '#020818' } },
        }}
      />
    </BrowserRouter>
  </React.StrictMode>
)
