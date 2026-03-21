import { createContext, useContext, useState, useEffect } from 'react'

const THEMES = {
  dark: {
    name: 'Dark',
    bg: '#0a0a0a',
    surface: '#111111',
    card: '#1a1a1a',
    border: '#2a2a2a',
    text: '#ffffff',
    textMuted: '#666666',
    textSub: '#999999',
    accent: '#ff3b00',
    accentBg: '#ff3b0015',
    success: '#00c851',
    successBg: '#00c85115',
    warning: '#ffbb00',
    warningBg: '#ffbb0015',
    danger: '#ff4444',
    dangerBg: '#ff444415',
    info: '#0088ff',
    infoBg: '#0088ff15',
  },
  light: {
    name: 'Light',
    bg: '#f0f0f0',
    surface: '#e8e8e8',
    card: '#ffffff',
    border: '#d0d0d0',
    text: '#111111',
    textMuted: '#888888',
    textSub: '#555555',
    accent: '#ff3b00',
    accentBg: '#ff3b0015',
    success: '#00a844',
    successBg: '#00a84415',
    warning: '#cc9900',
    warningBg: '#cc990015',
    danger: '#cc0000',
    dangerBg: '#cc000015',
    info: '#0066cc',
    infoBg: '#0066cc15',
  },
  blueprint: {
    name: 'Blueprint',
    bg: '#0a1628',
    surface: '#0d1f3c',
    card: '#112244',
    border: '#1a3355',
    text: '#e0eeff',
    textMuted: '#4477aa',
    textSub: '#6699cc',
    accent: '#ffcc00',
    accentBg: '#ffcc0015',
    success: '#00ddaa',
    successBg: '#00ddaa15',
    warning: '#ffaa00',
    warningBg: '#ffaa0015',
    danger: '#ff4455',
    dangerBg: '#ff445515',
    info: '#44aaff',
    infoBg: '#44aaff15',
  },
  paper: {
    name: 'Paper',
    bg: '#f5f0e8',
    surface: '#ede8dc',
    card: '#faf7f2',
    border: '#d4c9b0',
    text: '#1a1410',
    textMuted: '#8a7a60',
    textSub: '#5a4a30',
    accent: '#c0622a',
    accentBg: '#c0622a15',
    success: '#2a7a40',
    successBg: '#2a7a4015',
    warning: '#8a6a00',
    warningBg: '#8a6a0015',
    danger: '#aa2222',
    dangerBg: '#aa222215',
    info: '#1a5a8a',
    infoBg: '#1a5a8a15',
  },
}

const ThemeContext = createContext()

export function ThemeProvider({ children }) {
  const [themeName, setThemeName] = useState(() =>
    localStorage.getItem('emp-theme') || 'dark'
  )

  const theme = THEMES[themeName]

  useEffect(() => {
    localStorage.setItem('emp-theme', themeName)
    const root = document.documentElement
    Object.entries(theme).forEach(([key, val]) => {
      root.style.setProperty(`--emp-${key}`, val)
    })
  }, [themeName, theme])

  return (
    <ThemeContext.Provider value={{ theme, themeName, setThemeName, THEMES }}>
      {children}
    </ThemeContext.Provider>
  )
}

export const useTheme = () => useContext(ThemeContext)
export { THEMES }
