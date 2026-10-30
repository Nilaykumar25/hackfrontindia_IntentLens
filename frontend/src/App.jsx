import { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Nav from './components/Nav.jsx'
import Footer from './components/Footer.jsx'
import Skeleton from './components/Skeleton.jsx'
import './tokens.css'
import './reset.css'

const Landing    = lazy(() => import('./pages/Landing.jsx'))
const Ask        = lazy(() => import('./pages/Ask.jsx'))
const Explore    = lazy(() => import('./pages/Explore.jsx'))
const How        = lazy(() => import('./pages/How.jsx'))
const Results    = lazy(() => import('./pages/Results.jsx'))
const About      = lazy(() => import('./pages/About.jsx'))
const Styleguide = import.meta.env.DEV ? lazy(() => import('./pages/Styleguide.jsx')) : null

function PageFallback() {
  return (
    <div
      role="status"
      aria-label="Page loading"
      aria-live="polite"
      style={{ padding: '48px 24px', maxWidth: '800px', margin: '0 auto' }}
    >
      <Skeleton variant="block" height="40px" style={{ marginBottom: '16px' }} />
      <Skeleton variant="text" width="60%" />
      <Skeleton variant="text" />
      <Skeleton variant="text" width="80%" />
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <Nav />
      <Suspense fallback={<PageFallback />}>
        <Routes>
          <Route path="/"        element={<Landing />} />
          <Route path="/ask"     element={<Ask />} />
          <Route path="/explore" element={<Explore />} />
          <Route path="/how"     element={<How />} />
          <Route path="/results" element={<Results />} />
          <Route path="/about"   element={<About />} />
          {Styleguide && <Route path="/styleguide" element={<Styleguide />} />}
        </Routes>
      </Suspense>
      <Footer />
    </BrowserRouter>
  )
}
