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
  'Full-screen interactive overlay with hover and drag selection.',
  'Global shortcuts: Ctrl+Shift+C for capture, Ctrl+Shift+L for overlay.',
  'Local OCR with libtesseract. Nothing is uploaded.',
  'QR and barcode decoding with libzbar.',
  'Clipboard history with pin and delete.',
  'Works on Wayland and X11.',
]

const COMMANDS = [
  { cmd: 'live-text-ocr live', desc: 'Launch the interactive overlay.' },
  { cmd: 'live-text-ocr capture', desc: 'Select a region and copy text.' },
  { cmd: 'live-text-ocr qr', desc: 'Scan a QR code or barcode.' },
  { cmd: 'live-text-ocr history', desc: 'View recent clips.' },
  { cmd: 'live-text-ocr download-lang deu', desc: 'Add a language pack.' },
]

const RELEASE_TAG = 'v1.0.1'

function cx(...list) {
  return list.filter(Boolean).join(' ')
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

function Logo() {
  return (
    <svg className="logo-mark" viewBox="0 0 64 64" aria-hidden="true">
      <rect x="9" y="9" width="46" height="46" rx="10" fill="none" stroke="currentColor" strokeWidth="3" />
      <path
        d="M21 21 h7 M21 21 v7 M43 21 h-7 M43 21 v7 M21 43 h7 M21 43 v-7 M43 43 h-7 M43 43 v-7"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
      />
      <text x="32" y="43" textAnchor="middle" fontSize="24" fontWeight="700" fill="currentColor">
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
      Math.max(rect.left - cRect.left - tb.offsetWidth / 2 + rect.width / 2, 8),
      cRect.width - tb.offsetWidth - 8,
    )
    const top = Math.max(rect.top - cRect.top - tb.offsetHeight - 10, 8)
    tb.style.left = `${left}px`
    tb.style.top = `${top}px`
  }, [selected])

  const firstId = selected.size > 0 ? selected.keys().next().value : null

  return (
    <div className="terminal" ref={containerRef}>
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
          <button
            className={cx('install-tab', activeArch === 'amd64' && 'active')}
            onClick={() => setActiveArch('amd64')}
          >
            amd64
          </button>
          <button
            className={cx('install-tab', activeArch === 'arm64' && 'active')}
            onClick={() => setActiveArch('arm64')}
          >
            arm64
          </button>
        </div>
        <button className="copy-btn" onClick={copy}>
          {copied ? 'copied' : 'copy'}
        </button>
      </div>
      <pre className="install-code">
        <code>{commands[activeArch]}</code>
      </pre>
    </div>
  )
}

function App() {
  const { toast, show } = useToast()

  const handleCopy = (text) => {
    if (navigator.clipboard && text) {
      navigator.clipboard.writeText(text).then(() => show('Copied to clipboard'))
    } else {
      show('Copied to clipboard')
    }
  }

  return (
    <div className="landing">
      <header className="site-header">
        <div className="container header-inner">
          <a href="#" className="brand">
            <Logo />
            <span>live-text-ocr</span>
          </a>
          <nav className="nav">
            <a href="#features">features</a>
            <a href="#commands">commands</a>
            <a href="#install">install</a>
            <a href="https://github.com/iamadityamaurya/Live-Text-Like-Mac-in-Ubuntu" target="_blank" rel="noreferrer">
              github
            </a>
          </nav>
        </div>
      </header>

      <main>
        <section className="hero">
          <div className="container hero-inner">
            <div className="hero-text">
              <span className="eyebrow">Ubuntu utility</span>
              <h1>Live Text for Linux.</h1>
              <p className="subtitle">
                Select text on any screen — videos, PDFs, slides, terminals — and copy it
                instantly. Local OCR. No cloud. No root.
              </p>
              <div className="shortcut">
                <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>C</kbd> capture <span className="shortcut-div">·</span> <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>L</kbd> overlay
              </div>
              <div className="hero-actions">
                <a href="#install" className="btn btn-primary">
                  install
                </a>
                <a
                  href="https://github.com/iamadityamaurya/Live-Text-Like-Mac-in-Ubuntu"
                  target="_blank"
                  rel="noreferrer"
                  className="btn btn-secondary"
                >
                  source
                </a>
              </div>
            </div>

            <div className="hero-demo">
              <TerminalDemo onCopy={handleCopy} />
            </div>
          </div>
        </section>

        <section id="features" className="section">
          <div className="container">
            <h2 className="section-title">what it does</h2>
            <ul className="plain-list">
              {FEATURES.map((f) => (
                <li key={f}>{f}</li>
              ))}
            </ul>
          </div>
        </section>

        <section id="commands" className="section alt">
          <div className="container">
            <h2 className="section-title">commands</h2>
            <div className="command-list">
              {COMMANDS.map((c) => (
                <div className="command-row" key={c.cmd}>
                  <code>{c.cmd}</code>
                  <span>{c.desc}</span>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section id="install" className="section">
          <div className="container narrow">
            <h2 className="section-title">install</h2>
            <p className="section-subtitle">
              Download the .deb for your architecture. apt will install the dependencies
              automatically.
            </p>
            <DownloadButton />
            <p className="section-subtitle">Or run it from the terminal:</p>
            <InstallBlock />
            <div className="badges">
              <span>Ubuntu</span>
              <span>Wayland</span>
              <span>X11</span>
              <span>MIT</span>
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
          <p>open source under the MIT License. built by Aditya.</p>
          <div className="footer-links">
            <a href="https://github.com/iamadityamaurya/Live-Text-Like-Mac-in-Ubuntu" target="_blank" rel="noreferrer">
              github
            </a>
            <a href="#install">install</a>
          </div>
        </div>
      </footer>

      {toast && <div className="toast">{toast}</div>}
    </div>
  )
}

export default App
