import { useEffect, useMemo, useRef, useState } from 'react'
import './App.css'

const DEMO_LINES = [
  ['#', 'Select', 'any', 'text', 'on', 'your', 'screen'],
  ['$', 'live-text-ocr', 'capture'],
  ['Extracted', '(42', 'chars):'],
  ['ROS', '2', 'Navigation', 'Stack'],
  ['$', 'live-text-ocr', 'qr'],
  ['Decoded', 'QR', '(128', 'chars):', 'https://github.com/...'],
]

const FEATURES = [
  {
    title: 'Interactive overlay',
    desc: 'Full-screen word highlighting. Hover, click, or drag to select text exactly like macOS Live Text.',
    icon: 'overlay',
  },
  {
    title: 'Region capture',
    desc: 'Press the shortcut, drag a box, and the text is instantly copied to your clipboard.',
    icon: 'capture',
  },
  {
    title: 'Local OCR',
    desc: 'Powered by libtesseract5. Everything runs on your machine — nothing is uploaded.',
    icon: 'local',
  },
  {
    title: 'QR & barcode',
    desc: 'Point at a QR code or barcode and decode it in one shortcut.',
    icon: 'qr',
  },
  {
    title: 'Clipboard history',
    desc: 'Pin important clips, delete old ones, and copy anything again from the tray menu.',
    icon: 'history',
  },
  {
    title: 'Wayland + X11',
    desc: 'Works on modern Ubuntu under both Wayland and X11 with native system integration.',
    icon: 'display',
  },
]

const STEPS = [
  { n: '01', title: 'Freeze the screen', desc: 'Hit the shortcut. The overlay pauses your desktop so you can pick text from videos, slides, or PDFs.' },
  { n: '02', title: 'Select the text', desc: 'Hover over words, click to select, or drag across lines. Bounding boxes appear around every detected word.' },
  { n: '03', title: 'Copy instantly', desc: 'Press Enter or click Copy. The text is saved to history and ready to paste with Ctrl+V anywhere.' },
]

const COMMANDS = [
  { cmd: 'live-text-ocr live', desc: 'Launch the interactive overlay' },
  { cmd: 'live-text-ocr capture', desc: 'Select a region and copy text' },
  { cmd: 'live-text-ocr qr', desc: 'Scan a QR code or barcode' },
  { cmd: 'live-text-ocr history', desc: 'View recent clips' },
  { cmd: 'live-text-ocr download-lang deu', desc: 'Add a language pack' },
]

const RELEASE_TAG = 'v1.0.1'

function cx(...list) {
  return list.filter(Boolean).join(' ')
}

function useOnScreen(options = {}) {
  const ref = useRef(null)
  const [visible, setVisible] = useState(false)
  useEffect(() => {
    const el = ref.current
    if (!el) return
    const obs = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) {
        setVisible(true)
        obs.unobserve(el)
      }
    }, { threshold: 0.12, ...options })
    obs.observe(el)
    return () => obs.disconnect()
  }, [options])
  return [ref, visible]
}

function useToast() {
  const [toast, setToast] = useState(null)
  const timer = useRef(null)
  const show = (message, duration = 1800) => {
    if (timer.current) clearTimeout(timer.current)
    setToast(message)
    timer.current = setTimeout(() => setToast(null), duration)
  }
  return { toast, show }
}

function Icon({ name }) {
  const icons = {
    overlay: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="3" width="18" height="18" rx="3" />
        <path d="M3 9h18M9 21V9" />
      </svg>
    ),
    capture: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 19V5M5 12h14" />
        <circle cx="12" cy="12" r="9" />
      </svg>
    ),
    local: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
      </svg>
    ),
    qr: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="3" width="7" height="7" rx="1" />
        <rect x="14" y="3" width="7" height="7" rx="1" />
        <rect x="3" y="14" width="7" height="7" rx="1" />
        <path d="M14 14h7M14 17h4M14 21h7" />
      </svg>
    ),
    history: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10" />
        <polyline points="12 6 12 12 16 14" />
      </svg>
    ),
    display: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <rect x="2" y="4" width="20" height="14" rx="2" />
        <path d="M8 21h8M12 18v3" />
      </svg>
    ),
  }
  return <span className="feature-icon">{icons[name]}</span>
}

function Logo() {
  return (
    <svg className="logo-mark" viewBox="0 0 64 64" aria-hidden="true">
      <rect x="9" y="9" width="46" height="46" rx="14" fill="#ffffff" />
      <path
        d="M21 21 h7 M21 21 v7 M43 21 h-7 M43 21 v7 M21 43 h7 M21 43 v-7 M43 43 h-7 M43 43 v-7"
        stroke="rgba(10,10,12,0.85)"
        strokeWidth="3"
        strokeLinecap="round"
      />
      <text x="32" y="44" textAnchor="middle" fontSize="24" fontWeight="700" fill="#0a0a0c">
        T
      </text>
    </svg>
  )
}

function TerminalDemo({ onCopy }) {
  const [hoveredId, setHoveredId] = useState(null)
  const [selected, setSelected] = useState(new Set())
  const [isDragging, setIsDragging] = useState(false)
  const containerRef = useRef(null)
  const toolbarRef = useRef(null)
  const firstRef = useRef(null)

  const words = useMemo(() => {
    const all = []
    DEMO_LINES.forEach((line, lineIdx) => {
      line.forEach((text, wordIdx) => {
        all.push({ id: `${lineIdx}-${wordIdx}`, text, lineIdx })
      })
    })
    return all
  }, [])

  const selectedText = useMemo(() => {
    if (selected.size === 0) return ''
    const lines = {}
    words.forEach((w) => {
      if (selected.has(w.id)) {
        if (!lines[w.lineIdx]) lines[w.lineIdx] = []
        lines[w.lineIdx].push(w.text)
      }
    })
    return Object.keys(lines)
      .sort((a, b) => Number(a) - Number(b))
      .map((idx) => lines[idx].join(' '))
      .join('\n')
  }, [selected, words])

  const toggle = (id, keep) => {
    setSelected((prev) => {
      const next = keep ? new Set(prev) : new Set()
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const handleMouseDown = (e, id) => {
    e.preventDefault()
    setIsDragging(true)
    toggle(id, e.shiftKey)
  }

  const handleEnter = (id) => {
    setHoveredId(id)
    if (isDragging) {
      setSelected((prev) => {
        const next = new Set(prev)
        next.add(id)
        return next
      })
    }
  }

  useEffect(() => {
    const up = () => setIsDragging(false)
    window.addEventListener('mouseup', up)
    return () => window.removeEventListener('mouseup', up)
  }, [])

  useEffect(() => {
    const onKey = (e) => {
      if (e.key === 'Escape') {
        setSelected(new Set())
        setHoveredId(null)
      } else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'a') {
        e.preventDefault()
        setSelected(new Set(words.map((w) => w.id)))
      } else if (
        (e.key === 'Enter' || ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'c')) &&
        selected.size > 0
      ) {
        onCopy(selectedText)
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [selected, selectedText, words, onCopy])

  useEffect(() => {
    if (selected.size === 0 || !toolbarRef.current || !firstRef.current) return
    const rect = firstRef.current.getBoundingClientRect()
    const cRect = containerRef.current.getBoundingClientRect()
    const tb = toolbarRef.current
    const left = Math.min(
      Math.max(rect.left - cRect.left - tb.offsetWidth / 2 + rect.width / 2, 12),
      cRect.width - tb.offsetWidth - 12,
    )
    const top = Math.max(rect.top - cRect.top - tb.offsetHeight - 12, 12)
    tb.style.left = `${left}px`
    tb.style.top = `${top}px`
  }, [selected])

  const firstId = selected.size > 0 ? selected.keys().next().value : null

  return (
    <div className="terminal" ref={containerRef}>
      <div className="terminal-shine" />
      <div className="terminal-bar">
        <div className="terminal-dots">
          <span />
          <span />
          <span />
        </div>
        <span className="terminal-title">live-text-ocr --demo</span>
      </div>
      <div className="terminal-body">
        {DEMO_LINES.map((line, lineIdx) => (
          <div key={lineIdx} className="terminal-line">
            {line.map((text, wordIdx) => {
              const id = `${lineIdx}-${wordIdx}`
              const isPrompt = text === '$' || text === '#'
              const isSelected = selected.has(id)
              const isHovered = hoveredId === id
              return (
                <span
                  key={id}
                  ref={isSelected && firstId === id ? firstRef : null}
                  className={cx(
                    'terminal-word',
                    isPrompt && 'prompt',
                    isSelected && 'selected',
                    isHovered && 'hovered',
                  )}
                  onMouseEnter={() => handleEnter(id)}
                  onMouseLeave={() => setHoveredId((prev) => (prev === id ? null : prev))}
                  onMouseDown={(e) => handleMouseDown(e, id)}
                >
                  {text}
                </span>
              )
            })}
          </div>
        ))}
        <span className="terminal-cursor" />
      </div>

      {selected.size > 0 && (
        <div className="terminal-toolbar" ref={toolbarRef}>
          <span className="tb-count">{selected.size}</span>
          <button className="tb-btn primary" onClick={() => onCopy(selectedText)}>
            copy
          </button>
          <button
            className="tb-btn"
            onClick={() => window.open(`https://www.google.com/search?q=${encodeURIComponent(selectedText)}`, '_blank')}
          >
            search
          </button>
          <button className="tb-btn" onClick={() => setSelected(new Set())}>
            clear
          </button>
        </div>
      )}

      <div className="terminal-hint">hover · click · drag · esc · ctrl+a</div>
    </div>
  )
}

function getDefaultArch() {
  if (typeof navigator === 'undefined') return 'amd64'
  const ua = navigator.userAgent.toLowerCase()
  if (ua.includes('aarch64') || ua.includes('arm64') || ua.includes('arm')) return 'arm64'
  return 'amd64'
}

function DownloadButton() {
  const [arch, setArch] = useState(getDefaultArch)
  const filename = `live-text-ocr_1.0.1-1_${arch}.deb`
  const url = `https://github.com/iamadityamaurya/Live-Text-Like-Mac-in-Ubuntu/releases/download/${RELEASE_TAG}/${filename}`

  return (
    <div className="download-group">
      <a href={url} className="btn btn-primary" download>
        <span className="btn-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3" />
          </svg>
        </span>
        Download .deb
      </a>
      <div className="arch-toggle">
        <button className={cx('arch-btn', arch === 'amd64' && 'active')} onClick={() => setArch('amd64')}>
          amd64
        </button>
        <button className={cx('arch-btn', arch === 'arm64' && 'active')} onClick={() => setArch('arm64')}>
          arm64
        </button>
      </div>
      <span className="download-name">{filename}</span>
    </div>
  )
}

function InstallBlock() {
  const commands = {
    amd64: `wget https://github.com/iamadityamaurya/Live-Text-Like-Mac-in-Ubuntu/releases/download/v1.0.1/live-text-ocr_1.0.1-1_amd64.deb
sudo apt install ./live-text-ocr_1.0.1-1_amd64.deb`,
    arm64: `wget https://github.com/iamadityamaurya/Live-Text-Like-Mac-in-Ubuntu/releases/download/v1.0.1/live-text-ocr_1.0.1-1_arm64.deb
sudo apt install ./live-text-ocr_1.0.1-1_arm64.deb`,
  }

  const [activeArch, setActiveArch] = useState('amd64')
  const [copied, setCopied] = useState(false)

  const copy = () => {
    navigator.clipboard.writeText(commands[activeArch]).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    })
  }

  return (
    <div className="install-block">
      <div className="install-header">
        <div className="install-tabs">
          <button className={cx('install-tab', activeArch === 'amd64' && 'active')} onClick={() => setActiveArch('amd64')}>
            amd64
          </button>
          <button className={cx('install-tab', activeArch === 'arm64' && 'active')} onClick={() => setActiveArch('arm64')}>
            arm64
          </button>
        </div>
        <button className="copy-btn" onClick={copy}>
          {copied ? (
            <>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="20 6 9 17 4 12" />
              </svg>
              copied
            </>
          ) : (
            <>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
              </svg>
              copy
            </>
          )}
        </button>
      </div>
      <pre className="install-code">
        <code>{commands[activeArch]}</code>
      </pre>
    </div>
  )
}

function CommandCard({ c, i, onCopy }) {
  const [ref, visible] = useOnScreen()
  return (
    <div
      ref={ref}
      className={cx('command-card', visible && 'reveal')}
      style={{ transitionDelay: `${i * 70}ms` }}
    >
      <code>{c.cmd}</code>
      <span>{c.desc}</span>
      <button
        className="command-copy"
        onClick={() => onCopy(c.cmd)}
        aria-label="Copy command"
        title="Copy command"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
          <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
        </svg>
      </button>
    </div>
  )
}

function CommandGrid({ onCopy }) {
  return (
    <div className="command-grid">
      {COMMANDS.map((c, i) => (
        <CommandCard key={c.cmd} c={c} i={i} onCopy={onCopy} />
      ))}
    </div>
  )
}

function FeatureCard({ feature }) {
  const [ref, visible] = useOnScreen()
  return (
    <div ref={ref} className={cx('feature-card', visible && 'reveal')}>
      <Icon name={feature.icon} />
      <h3>{feature.title}</h3>
      <p>{feature.desc}</p>
    </div>
  )
}

function Step({ step, i }) {
  const [ref, visible] = useOnScreen()
  return (
    <div ref={ref} className={cx('step', visible && 'reveal')} style={{ transitionDelay: `${i * 90}ms` }}>
      <div className="step-number">{step.n}</div>
      <h3>{step.title}</h3>
      <p>{step.desc}</p>
    </div>
  )
}

function App() {
  const { toast, show } = useToast()
  const [heroRef, heroVisible] = useOnScreen()

  const handleCopy = (text) => {
    if (navigator.clipboard && text) {
      navigator.clipboard.writeText(text).then(() => show('Copied to clipboard'))
    } else {
      show('Copied to clipboard')
    }
  }

  return (
    <div className="landing">
      <div className="ambient-glow" />

      <header className="site-header">
        <div className="container header-inner">
          <a href="#" className="brand">
            <Logo />
            <span>live-text-ocr</span>
          </a>
          <nav className="nav">
            <a href="#features">Features</a>
            <a href="#how">How it works</a>
            <a href="#install">Install</a>
            <a href="https://github.com/iamadityamaurya/Live-Text-Like-Mac-in-Ubuntu" target="_blank" rel="noreferrer">
              GitHub
            </a>
          </nav>
        </div>
      </header>

      <main>
        <section className="hero" ref={heroRef}>
          <div className={cx('container hero-inner', heroVisible && 'reveal')}>
            <div className="hero-text">
              <span className="eyebrow">Ubuntu · Wayland · X11</span>
              <h1>
                Copy any text on
                <br />
                <span className="gradient-text">your screen.</span>
              </h1>
              <p className="subtitle">
                A native OCR utility that turns paused videos, PDFs, slides, and terminals into
                selectable, copyable text — instantly and locally.
              </p>
              <div className="shortcut-pills">
                <div className="shortcut-pill">
                  <kbd>Super</kbd>
                  <span>+</span>
                  <kbd>Shift</kbd>
                  <span>+</span>
                  <kbd>C</kbd>
                  <span className="pill-sep">capture</span>
                </div>
                <div className="shortcut-pill">
                  <kbd>Super</kbd>
                  <span>+</span>
                  <kbd>Shift</kbd>
                  <span>+</span>
                  <kbd>O</kbd>
                  <span className="pill-sep">overlay</span>
                </div>
              </div>
              <div className="hero-actions">
                <a href="#install" className="btn btn-primary btn-lg">
                  Get live-text-ocr
                </a>
                <a
                  href="https://github.com/iamadityamaurya/Live-Text-Like-Mac-in-Ubuntu"
                  target="_blank"
                  rel="noreferrer"
                  className="btn btn-secondary"
                >
                  View on GitHub
                </a>
              </div>
            </div>

            <div className="hero-demo">
              <div className="demo-float">
                <TerminalDemo onCopy={handleCopy} />
              </div>
            </div>
          </div>
        </section>

        <section id="features" className="section">
          <div className="container">
            <div className="section-head">
              <span className="eyebrow">Features</span>
              <h2 className="section-title">Built for the desktop.</h2>
              <p className="section-lead">
                Everything you need to grab text from anywhere on Ubuntu, without sending a single pixel to the cloud.
              </p>
            </div>
            <div className="feature-grid">
              {FEATURES.map((f) => (
                <FeatureCard key={f.title} feature={f} />
              ))}
            </div>
          </div>
        </section>

        <section id="how" className="section alt">
          <div className="container">
            <div className="section-head">
              <span className="eyebrow">How it works</span>
              <h2 className="section-title">Three keys to copy.</h2>
            </div>
            <div className="steps">
              {STEPS.map((s, i) => (
                <Step key={s.n} step={s} i={i} />
              ))}
            </div>
          </div>
        </section>

        <section id="commands" className="section">
          <div className="container">
            <div className="section-head">
              <span className="eyebrow">CLI</span>
              <h2 className="section-title">Commands you will actually use.</h2>
            </div>
            <CommandGrid onCopy={handleCopy} />
          </div>
        </section>

        <section id="install" className="section alt">
          <div className="container narrow">
            <div className="section-head">
              <span className="eyebrow">Install</span>
              <h2 className="section-title">Ready in seconds.</h2>
              <p className="section-lead">
                Download the .deb for your architecture, or paste the terminal command. apt handles the rest.
              </p>
            </div>
            <DownloadButton />
            <InstallBlock />
            <div className="badges">
              <span>Ubuntu</span>
              <span>Wayland</span>
              <span>X11</span>
              <span>MIT License</span>
            </div>
          </div>
        </section>
      </main>

      <footer className="footer">
        <div className="container footer-inner">
          <div className="footer-brand">
            <Logo />
            <span>live-text-ocr</span>
          </div>
          <p>open source under the MIT License · built by Aditya</p>
          <div className="footer-links">
            <a href="https://github.com/iamadityamaurya/Live-Text-Like-Mac-in-Ubuntu" target="_blank" rel="noreferrer">
              GitHub
            </a>
            <a href="#install">Install</a>
            <a href="#features">Features</a>
          </div>
        </div>
      </footer>

      {toast && <div className="toast">{toast}</div>}
    </div>
  )
}

export default App
