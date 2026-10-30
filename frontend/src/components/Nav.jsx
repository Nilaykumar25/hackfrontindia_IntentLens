import { useEffect, useState } from 'react'
import { Link, NavLink, useLocation } from 'react-router-dom'
import './Nav.css'

/* Theme stored in localStorage; falls back to prefers-color-scheme */
function useTheme() {
  const [theme, setTheme] = useState(() => {
    const stored = localStorage.getItem('il-theme')
    if (stored) return stored
    return window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark'
  })

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('il-theme', theme)
  }, [theme])

  return [theme, setTheme]
}

export default function Nav() {
  const [theme, setTheme] = useTheme()
  const [open, setOpen] = useState(false)
  const loc = useLocation()

  /* Close mobile menu on navigation */
  useEffect(() => { setOpen(false) }, [loc.pathname])

  const toggle = () => setTheme(t => t === 'dark' ? 'light' : 'dark')

  return (
    <header className="nav-shell" role="banner">
      <a href="#main" className="skip-link">Skip to main content</a>

      <nav className="nav container" aria-label="Main navigation">
        <Link to="/" className="nav-logo" aria-label="IntentLens home">
          <LogoMark />
          <span>IntentLens</span>
        </Link>

        <button
          className="nav-burger"
          aria-label={open ? 'Close menu' : 'Open menu'}
          aria-expanded={open}
          aria-controls="nav-links"
          onClick={() => setOpen(o => !o)}
        >
          <BurgerIcon open={open} />
        </button>

        <ul id="nav-links" className={`nav-links ${open ? 'is-open' : ''}`} role="list">
          <li><NavLink to="/ask" end>Ask</NavLink></li>
          <li><NavLink to="/explore">Explore</NavLink></li>
          <li><NavLink to="/how">How it works</NavLink></li>
          <li><NavLink to="/results">Results</NavLink></li>
          <li><NavLink to="/about">About</NavLink></li>
        </ul>

        <div className="nav-actions">
          <button
            className="theme-toggle"
            onClick={toggle}
            aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}
            title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}
          >
            {theme === 'dark' ? <SunIcon /> : <MoonIcon />}
          </button>
          <Link to="/ask" className="nav-cta">Ask the codebase</Link>
        </div>
      </nav>
    </header>
  )
}

function LogoMark() {
  return (
    <svg width="28" height="28" viewBox="0 0 28 28" fill="none" aria-hidden="true" focusable="false">
      <circle cx="8" cy="20" r="4" fill="var(--entity)" opacity="0.9" />
      <circle cx="14" cy="8" r="4" fill="var(--accent)" />
      <circle cx="22" cy="20" r="3" fill="var(--muted)" opacity="0.7" />
      <line x1="8" y1="20" x2="14" y2="8" stroke="var(--line)" strokeWidth="1.5" />
      <line x1="14" y1="8" x2="22" y2="20" stroke="var(--line)" strokeWidth="1.5" />
    </svg>
  )
}

function BurgerIcon({ open }) {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
      {open ? (
        <>
          <line x1="4" y1="4" x2="16" y2="16" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          <line x1="16" y1="4" x2="4" y2="16" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        </>
      ) : (
        <>
          <line x1="3" y1="6" x2="17" y2="6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          <line x1="3" y1="10" x2="17" y2="10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          <line x1="3" y1="14" x2="17" y2="14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        </>
      )}
    </svg>
  )
}

function SunIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
      <circle cx="9" cy="9" r="4" stroke="currentColor" strokeWidth="1.5" />
      {[0,45,90,135,180,225,270,315].map(deg => (
        <line
          key={deg}
          x1={9 + 6.5 * Math.cos(deg * Math.PI / 180)}
          y1={9 + 6.5 * Math.sin(deg * Math.PI / 180)}
          x2={9 + 8.5 * Math.cos(deg * Math.PI / 180)}
          y2={9 + 8.5 * Math.sin(deg * Math.PI / 180)}
          stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"
        />
      ))}
    </svg>
  )
}

function MoonIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
      <path d="M15 10.5A7 7 0 0 1 7.5 3a7 7 0 1 0 7.5 7.5z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}
