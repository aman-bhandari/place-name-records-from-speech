import React, { useEffect, useRef, useState } from 'react'
import { api } from './api.js'

// One shared AudioContext; decoded buffers cached by URL.
let ctx; const cache = new Map()
async function buffer(url) {
  ctx = ctx || new (window.AudioContext || window.webkitAudioContext)()
  if (!cache.has(url)) cache.set(url, fetch(url).then((r) => r.arrayBuffer()).then((b) => ctx.decodeAudioData(b)))
  return cache.get(url)
}

/** Waveform drawn in contour brown; click plays; the playhead is a drainage-blue line. Optional highlight = [start_s, end_s]. */
export function Waveform({ url, highlight, height = 36, label }) {
  const canvas = useRef(); const [buf, setBuf] = useState(null); const [pos, setPos] = useState(-1); const src = useRef(); const raf = useRef()
  useEffect(() => { let on = true; buffer(url).then((b) => on && setBuf(b)).catch(() => setBuf('error')); return () => { on = false } }, [url])
  useEffect(() => {
    const c = canvas.current; if (!c) return; const w = c.clientWidth || 240; c.width = w * devicePixelRatio; c.height = height * devicePixelRatio
    const g = c.getContext('2d'); g.scale(devicePixelRatio, devicePixelRatio); g.clearRect(0, 0, w, height)
    if (!buf || buf === 'error') { g.fillStyle = '#7C8684'; g.font = '12px Mukta'; g.fillText(buf === 'error' ? 'audio unavailable' : 'loading', 4, height / 2 + 4); return }
    const d = buf.getChannelData(0); const n = d.length; const step = Math.max(1, Math.floor(n / w))
    if (highlight) { g.fillStyle = '#EFE4D8'; const a = (highlight[0] / buf.duration) * w, b = (highlight[1] / buf.duration) * w; g.fillRect(a, 0, Math.max(2, b - a), height) }
    g.strokeStyle = '#8F5A2E'; g.lineWidth = 1; g.beginPath()
    for (let x = 0; x < w; x++) { let m = 0; for (let i = x * step; i < (x + 1) * step && i < n; i++) m = Math.max(m, Math.abs(d[i])); const h = Math.max(1, m * (height - 4)); g.moveTo(x + 0.5, height / 2 - h / 2); g.lineTo(x + 0.5, height / 2 + h / 2) }
    g.stroke()
    if (pos >= 0) { g.strokeStyle = '#2B6C8C'; g.lineWidth = 2; g.beginPath(); g.moveTo(pos * w, 0); g.lineTo(pos * w, height); g.stroke() }
  }, [buf, pos, highlight, height])
  const play = () => {
    if (!buf || buf === 'error') return
    if (src.current) { try { src.current.stop() } catch {} }
    const s = ctx.createBufferSource(); s.buffer = buf; s.connect(ctx.destination); s.start(); src.current = s; const t0 = ctx.currentTime
    const tick = () => { const p = (ctx.currentTime - t0) / buf.duration; if (p >= 1) { setPos(-1); return } setPos(p); raf.current = requestAnimationFrame(tick) }
    tick(); s.onended = () => { cancelAnimationFrame(raf.current); setPos(-1) }
  }
  return (
    <button type="button" onClick={play} aria-label={label || 'Play recording'} title="Play" className="block w-full text-left">
      <canvas ref={canvas} style={{ width: '100%', height }} />
    </button>
  )
}

/** Confidence as a ruled meter with its parts, not a lone number. */
export function Confidence({ c, compact }) {
  if (!c) return null
  const col = c.band === 'high' ? '#3F6D4E' : c.band === 'medium' ? '#8F5A2E' : '#9A3B2E'
  const parts = [['clips agree', c.agreement], ['spelling explains clips', c.support], ['lead over next', Math.min(1, c.margin * 3)], ['speakers', Math.min(1, c.speakers / 5)]]
  return (
    <div>
      <div className="flex items-baseline gap-3"><span className="text-3xl" style={{ color: col }}>{Math.round(c.score)}</span><span className="text-ink-soft">{c.band} confidence · {c.clips} clips · {c.speakers} speakers</span></div>
      {!compact && <div className="mt-2 grid grid-cols-2 gap-x-6 gap-y-1 text-sm max-w-md">
        {parts.map(([k, v]) => <div key={k} className="flex items-center gap-2"><span className="w-40 text-ink-soft">{k}</span><span className="flex-1 h-1.5 bg-grid/60"><span className="block h-1.5" style={{ width: `${Math.round(v * 100)}%`, background: col }} /></span><span className="w-8 text-right text-ink-faint">{Math.round(v * 100)}</span></div>)}
      </div>}
    </div>
  )
}

const contours = "M0 62c40-30 80-30 120 0s80 30 120 0 80-30 120 0 80 30 120 0 80-30 120 0M0 88c40-26 80-26 120 0s80 26 120 0 80-26 120 0 80 26 120 0 80-26 120 0M0 110c40-20 80-20 120 0s80 20 120 0 80-20 120 0 80 20 120 0 80-20 120 0M0 36c40-22 80-22 120 0s80 22 120 0 80-22 120 0 80 22 120 0 80-22 120 0"

/** The sheet entry: the record as it would be lettered on a map sheet. */
export function SheetEntry({ rec, edited }) {
  const dev = edited?.devanagari || rec.devanagari, rom = edited?.roman || rec.roman?.recommended, ipa = edited?.ipa || rec.ipa
  return (
    <div className="relative border hair border-b-2 overflow-hidden" style={{ borderBottomColor: '#17201F' }}>
      <svg aria-hidden="true" className="absolute inset-0 w-full h-full" viewBox="0 0 600 140" preserveAspectRatio="none"><path d={contours} fill="none" stroke="#8F5A2E" strokeOpacity="0.16" strokeWidth="1" /></svg>
      <div className="relative px-5 py-5 grid gap-1 md:grid-cols-[1fr_auto] md:items-end">
        <div>
          <div className="font-name text-5xl md:text-6xl leading-tight">{dev}</div>
          <div className="sheet-roman text-xl md:text-2xl mt-2">{rom}</div>
          <div className="font-ipa text-lg text-ink-soft mt-1">{ipa}</div>
        </div>
        <div className="text-sm text-ink-soft md:text-right">{rec.roman?.kind === 'established' ? 'established form kept' : 'Hunterian scheme'}{edited && Object.values(edited).some(Boolean) ? ' · edited by officer' : ''}</div>
      </div>
    </div>
  )
}

export function Bar({ v, col = '#2B6C8C', w = 120 }) {
  return <span className="inline-block align-middle h-2 bg-grid/60" style={{ width: w }}><span className="block h-2" style={{ width: `${Math.round(v * 100)}%`, background: col }} /></span>
}
export function Band({ band }) {
  const c = { high: 'text-forest', medium: 'text-contour', low: 'text-alert' }[band] || 'text-ink-faint'
  return <span className={c}>{band}</span>
}
export const fmtTs = (t) => new Date(t * 1000).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' })
