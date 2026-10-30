import '@testing-library/jest-dom'

// Mock IntersectionObserver (used by some components)
globalThis.IntersectionObserver = class {
  observe() {}
  unobserve() {}
  disconnect() {}
}

// Mock matchMedia (used by EvidenceThread for reduced-motion check)
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  }),
})

// Mock scrollIntoView (used by citation chip click handler)
Element.prototype.scrollIntoView = () => {}

// Mock clipboard API
Object.defineProperty(navigator, 'clipboard', {
  writable: true,
  value: { writeText: () => Promise.resolve() },
})
