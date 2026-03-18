/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        display: ['Syne', 'sans-serif'],
        mono: ['IBM Plex Mono', 'monospace'],
        body: ['DM Sans', 'sans-serif'],
      },
      colors: {
        navy: {
          950: '#020818',
          900: '#060d20',
          800: '#0a1628',
          700: '#0f1f38',
          600: '#162848',
        },
        cyan: {
          400: '#22d3ee',
          500: '#06b6d4',
          glow: '#22d3ee',
        },
        sentinel: {
          bg:      '#020818',
          surface: '#0a1628',
          card:    '#0f1f38',
          border:  '#162848',
          accent:  '#22d3ee',
          green:   '#10b981',
          red:     '#ef4444',
          amber:   '#f59e0b',
          muted:   '#64748b',
          text:    '#e2e8f0',
        }
      },
      boxShadow: {
        'glow-cyan':  '0 0 20px rgba(34, 211, 238, 0.15)',
        'glow-green': '0 0 20px rgba(16, 185, 129, 0.15)',
        'glow-red':   '0 0 20px rgba(239, 68, 68, 0.15)',
        'card':       '0 4px 24px rgba(0,0,0,0.4)',
      },
      backgroundImage: {
        'grid-pattern': "linear-gradient(rgba(34,211,238,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(34,211,238,0.03) 1px, transparent 1px)",
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
      },
      backgroundSize: {
        'grid': '40px 40px',
      },
      animation: {
        'pulse-slow':   'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow':         'glow 2s ease-in-out infinite alternate',
        'slide-in':     'slideIn 0.3s ease-out',
        'fade-in':      'fadeIn 0.4s ease-out',
        'count-up':     'countUp 1s ease-out',
      },
      keyframes: {
        glow: {
          '0%':   { boxShadow: '0 0 5px rgba(34,211,238,0.2)' },
          '100%': { boxShadow: '0 0 20px rgba(34,211,238,0.5), 0 0 40px rgba(34,211,238,0.1)' },
        },
        slideIn: {
          '0%':   { transform: 'translateX(-10px)', opacity: '0' },
          '100%': { transform: 'translateX(0)',     opacity: '1' },
        },
        fadeIn: {
          '0%':   { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      }
    },
  },
  plugins: [],
}
