import { useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react'
import './App.css'

const DEMO_LINES = [
  ['#', 'Select', 'any', 'text', 'on', 'your', 'screen'],
  ['$', 'live-text-ocr', 'capture'],
  ['Extracted', '(42', 'chars):'],
  ['ROS', '2', 'Navigation', 'Stack'],
  ['$', 'live-text-ocr', 'qr'],
  ['Decoded', 'QR', '(128', 'chars):', 'https://github.com/...'],
]

const SCAN_STEP_MS = 180

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

const SURFACES = [
  'Paused videos',
  'PDFs & papers',
  'Terminal',
  'Slides',
  'VS Code',
  'Browser windows',
  'Image viewers',
  'LibreOffice',
  'Obsidian',
  'Slack',
]

const RELEASE_TAG = 'v1.0.1'

function cx(...list) {
  return list.filter(Boolean).join(' ')
}

function usePrefersReducedMotion() {
  const [reduced, setReduced] = useState(
    () => typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches,
  )
  useEffect(() => {
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)')
    const onChange = () => setReduced(mq.matches)
    mq.addEventListener('change', onChange)
    return () => mq.removeEventListener('change', onChange)
  }, [])
  return reduced
}

function useFinePointer() {
  const [fine, setFine] = useState(
    () => typeof window !== 'undefined' && window.matchMedia('(hover: hover) and (pointer: fine)').matches,
  )
  useEffect(() => {
    const mq = window.matchMedia('(hover: hover) and (pointer: fine)')
    const onChange = () => setFine(mq.matches)
    mq.addEventListener('change', onChange)
    return () => mq.removeEventListener('change', onChange)
  }, [])
  return fine
}

function useOnScreen() {
  const ref = useRef(null)
  const [visible, setVisible] = useState(false)
  useEffect(() => {
    const el = ref.current
    if (!el) return
    const obs = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true)
          obs.unobserve(el)
        }
      },
      { threshold: 0.12 },
    )
    obs.observe(el)
    return () => obs.disconnect()
  }, [])
  return [ref, visible]
}

function useToast() {
  const [state, setState] = useState({ message: null, visible: false })
  const timers = useRef([])
  const show = (message, duration = 2000) => {
    timers.current.forEach(clearTimeout)
    timers.current = []
    setState({ message, visible: true })
    timers.current.push(
      setTimeout(() => setState((s) => ({ ...s, visible: false })), duration),
    )
  }
  useEffect(() => () => timers.current.forEach(clearTimeout), [])
  return { toast: state.message, toastVisible: state.visible, show }
}

function Reveal({ className = '', delay = 0, children, ...rest }) {
  const [ref, visible] = useOnScreen()
  return (
    <div
      ref={ref}
      className={cx(className, visible && 'reveal')}
      style={{ animationDelay: `${delay}ms` }}
      {...rest}
    >
      {children}
    </div>
  )
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
      <defs>
        <linearGradient id="logo-g" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#ff7a45" />
          <stop offset="1" stopColor="#e95420" />
        </linearGradient>
      </defs>
      <rect x="6" y="6" width="52" height="52" rx="15" fill="url(#logo-g)" />
      <path
        d="M15 15 h6 M15 15 v6 M49 15 h-6 M49 15 v6 M15 49 h6 M15 49 v-6 M49 49 h-6 M49 49 v-6"
        stroke="rgba(255,255,255,0.85)"
        strokeWidth="3.2"
        strokeLinecap="round"
      />
      <text x="32" y="43" textAnchor="middle" fontSize="24" fontWeight="700" fill="#ffffff">
        T
      </text>
    </svg>
  )
}

function TerminalDemo({ onCopy }) {
  const [hoveredId, setHoveredId] = useState(null)
  const [selected, setSelected] = useState(new Set())
  const [isDragging, setIsDragging] = useState(false)
  const [detected, setDetected] = useState(() => new Set())
  const [scan, setScan] = useState(false)
  const containerRef = useRef(null)
  const bodyRef = useRef(null)
  const scanRef = useRef(null)
  const toolbarRef = useRef(null)
  const firstRef = useRef(null)
  const reduced = usePrefersReducedMotion()

  /* One-shot OCR scan sweep on mount — shows how detection works.
     Everything is scheduled via timeouts so no synchronous setState in the effect. */
  useEffect(() => {
    if (reduced) return
    const timers = []
    const start = 380
    timers.push(setTimeout(() => setScan(true), start))
    DEMO_LINES.forEach((line, i) => {
      const ids = line.map((_, w) => `${i}-${w}`)
      timers.push(
        setTimeout(() => {
          setDetected((prev) => {
            const next = new Set(prev)
            ids.forEach((id) => next.add(id))
            return next
          })
          timers.push(
            setTimeout(() => {
              setDetected((prev) => {
                const next = new Set(prev)
                ids.forEach((id) => next.delete(id))
                return next
              })
            }, 620),
          )
        }, start + 60 + i * SCAN_STEP_MS),
      )
    })
    timers.push(setTimeout(() => setScan(false), start + DEMO_LINES.length * SCAN_STEP_MS + 700))
    return () => timers.forEach(clearTimeout)
  }, [reduced])

  /* Size the sweep to the terminal body. */
  useLayoutEffect(() => {
    if (!scan || !scanRef.current || !bodyRef.current) return
    scanRef.current.style.setProperty('--scan-d', `${bodyRef.current.offsetHeight - 6}px`)
    scanRef.current.style.setProperty('--scan-t', `${DEMO_LINES.length * SCAN_STEP_MS}ms`)
  }, [scan])

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

  /* Position the floating toolbar with transform so it glides between selections. */
  useLayoutEffect(() => {
    const tb = toolbarRef.current
    if (selected.size === 0 || !tb || !firstRef.current || !containerRef.current) return
    const rect = firstRef.current.getBoundingClientRect()
    const cRect = containerRef.current.getBoundingClientRect()
    const x = Math.min(
      Math.max(rect.left - cRect.left - tb.offsetWidth / 2 + rect.width / 2, 12),
      cRect.width - tb.offsetWidth - 12,
    )
    const y = Math.max(rect.top - cRect.top - tb.offsetHeight - 12, 12)
    tb.style.transform = `translate(${x}px, ${y}px)`
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
      <div className="terminal-body" ref={bodyRef}>
        {DEMO_LINES.map((line, lineIdx) => (
          <div key={lineIdx} className="terminal-line">
            {line.map((text, wordIdx) => {
              const id = `${lineIdx}-${wordIdx}`
              const isPrompt = text === '$' || text === '#'
              const isSelected = selected.has(id)
              const isHovered = hoveredId === id
              const isDetected = detected.has(id)
              return (
                <span
                  key={id}
                  ref={isSelected && firstId === id ? firstRef : null}
                  className={cx(
                    'terminal-word',
                    isPrompt && 'prompt',
                    isSelected && 'selected',
                    isHovered && 'hovered',
                    isDetected && 'detected',
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
        {scan && <div className="scan-line" ref={scanRef} />}
      </div>

      {selected.size > 0 && (
        <div className="terminal-toolbar" ref={toolbarRef}>
          <div className="terminal-toolbar-inner">
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
        </div>
      )}

      <div className="terminal-hint">hover · click · drag · esc · ctrl+a</div>
    </div>
  )
}

/* Decorative mouse tilt for the hero demo — spring-lerped, fine pointers only. */
function HeroDemo({ children }) {
  const wrapRef = useRef(null)
  const tiltRef = useRef(null)
  const fine = useFinePointer()
  const reduced = usePrefersReducedMotion()

  useEffect(() => {
    if (!fine || reduced) return
    const wrap = wrapRef.current
    const tilt = tiltRef.current
    if (!wrap || !tilt) return
    let raf = null
    const cur = { x: 0, y: 0 }
    const target = { x: 0, y: 0 }
    const MAX = 4.5

    const loop = () => {
      cur.x += (target.x - cur.x) * 0.075
      cur.y += (target.y - cur.y) * 0.075
      tilt.style.transform = `rotateX(${cur.x.toFixed(3)}deg) rotateY(${cur.y.toFixed(3)}deg)`
      raf =
        Math.abs(target.x - cur.x) > 0.005 || Math.abs(target.y - cur.y) > 0.005
          ? requestAnimationFrame(loop)
          : null
    }
    const kick = () => {
      if (raf === null) raf = requestAnimationFrame(loop)
    }
    const onMove = (e) => {
      const r = wrap.getBoundingClientRect()
      const px = (e.clientX - r.left) / r.width - 0.5
      const py = (e.clientY - r.top) / r.height - 0.5
      target.x = -py * MAX
      target.y = px * MAX
      kick()
    }
    const onLeave = () => {
      target.x = 0
      target.y = 0
      kick()
    }
    wrap.addEventListener('mousemove', onMove)
    wrap.addEventListener('mouseleave', onLeave)
    return () => {
      wrap.removeEventListener('mousemove', onMove)
      wrap.removeEventListener('mouseleave', onLeave)
      if (raf !== null) cancelAnimationFrame(raf)
    }
  }, [fine, reduced])

  return (
    <div className="hero-demo" ref={wrapRef}>
      <div className="demo-float">
        <div className="demo-idle">
          <div className="demo-tilt" ref={tiltRef}>
            {children}
          </div>
        </div>
      </div>
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
      <a href={url} className="btn btn-primary btn-lg" download>
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
        <button className={cx('copy-btn', copied && 'copied')} onClick={copy}>
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
  return (
    <Reveal className="command-card" delay={i * 60}>
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
    </Reveal>
  )
}

function FeatureCard({ feature, i }) {
  return (
    <Reveal className="feature-card" delay={i * 60}>
      <Icon name={feature.icon} />
      <h3>{feature.title}</h3>
      <p>{feature.desc}</p>
    </Reveal>
  )
}

function Step({ step, i }) {
  return (
    <Reveal className="step" delay={i * 90}>
      <div className="step-number">{step.n}</div>
      <h3>{step.title}</h3>
      <p>{step.desc}</p>
    </Reveal>
  )
}

function Marquee() {
  return (
    <div className="marquee-strip">
      <div className="container marquee-inner">
        <span className="marquee-label">works over</span>
        <div className="marquee">
          <div className="marquee-track" aria-hidden="true">
            {[...SURFACES, ...SURFACES].map((s, i) => (
              <span key={i} className="marquee-item">
                {s}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

function App() {
  const { toast, toastVisible, show } = useToast()
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8)
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

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

      <header className={cx('site-header', scrolled && 'scrolled')}>
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
        <section className="hero">
          <div className="container hero-inner">
            <div className="hero-text">
              <span className="eyebrow rise" style={{ animationDelay: '0ms' }}>
                Ubuntu · Wayland · X11
              </span>
              <h1>
                <span className="hl-line">
                  <span className="hl-inner" style={{ animationDelay: '60ms' }}>
                    Copy any text
                  </span>
                </span>
                <span className="hl-line">
                  <span className="hl-inner" style={{ animationDelay: '140ms' }}>
                    on your <span className="gradient-text">screen.</span>
                  </span>
                </span>
              </h1>
              <p className="subtitle rise" style={{ animationDelay: '260ms' }}>
                A native OCR utility that turns paused videos, PDFs, slides, and terminals into
                selectable, copyable text — instantly and locally.
              </p>
              <div className="shortcut-pills rise" style={{ animationDelay: '340ms' }}>
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
              <div className="hero-actions rise" style={{ animationDelay: '420ms' }}>
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

            <HeroDemo>
              <TerminalDemo onCopy={handleCopy} />
            </HeroDemo>
          </div>
        </section>

        <Marquee />

        <section id="features" className="section">
          <div className="container">
            <Reveal className="section-head">
              <span className="eyebrow">Features</span>
              <h2 className="section-title">Built for the desktop.</h2>
              <p className="section-lead">
                Everything you need to grab text from anywhere on Ubuntu, without sending a single pixel to the cloud.
              </p>
            </Reveal>
            <div className="feature-grid">
              {FEATURES.map((f, i) => (
                <FeatureCard key={f.title} feature={f} i={i} />
              ))}
            </div>
          </div>
        </section>

        <section id="how" className="section alt">
          <div className="container">
            <Reveal className="section-head">
              <span className="eyebrow">How it works</span>
              <h2 className="section-title">Three keys to copy.</h2>
            </Reveal>
            <div className="steps">
              {STEPS.map((s, i) => (
                <Step key={s.n} step={s} i={i} />
              ))}
            </div>
          </div>
        </section>

        <section id="commands" className="section">
          <div className="container">
            <Reveal className="section-head">
              <span className="eyebrow">CLI</span>
              <h2 className="section-title">Commands you will actually use.</h2>
            </Reveal>
            <div className="command-grid">
              {COMMANDS.map((c, i) => (
                <CommandCard key={c.cmd} c={c} i={i} onCopy={handleCopy} />
              ))}
            </div>
          </div>
        </section>

        <section id="install" className="section alt">
          <div className="container narrow">
            <Reveal className="section-head">
              <span className="eyebrow">Install</span>
              <h2 className="section-title">Ready in seconds.</h2>
              <p className="section-lead">
                Download the .deb for your architecture, or paste the terminal command. apt handles the rest.
              </p>
            </Reveal>
            <Reveal delay={120}>
              <DownloadButton />
              <InstallBlock />
            </Reveal>
            <Reveal className="badges" delay={240}>
              <span>Ubuntu</span>
              <span>Wayland</span>
              <span>X11</span>
              <span>MIT License</span>
            </Reveal>
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

      <div className="toast" data-visible={toastVisible} aria-live="polite">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="20 6 9 17 4 12" />
        </svg>
        <span>{toast}</span>
      </div>
    </div>
  )
}

export default App
