import React, { useState } from 'react'
import { api } from '../api.js'
export default function Upload() {
  const [name, setName] = useState(''); const [en, setEn] = useState(''); const [officer, setOfficer] = useState(() => localStorage.getItem('eknaam.officer') || ''); const [files, setFiles] = useState([]); const [busy, setBusy] = useState(false); const [res, setRes] = useState(null); const [err, setErr] = useState('')
  const go = async (e) => {
    e.preventDefault(); setBusy(true); setErr(''); setRes(null)
    const f = new FormData(); f.append('name_hi', name); f.append('existing_en', en); f.append('officer', officer || 'field'); for (const x of files) f.append('files', x)
    try { setRes(await api.upload(f)) } catch (x) { setErr(x.message) } finally { setBusy(false) }
  }
  return (
    <div className="p-4 md:p-6 max-w-2xl">
      <h1 className="text-2xl mb-1">Add recordings of one place name</h1>
      <p className="text-ink-soft mb-4">Upload several recordings of different people saying the same name: phone recordings, field survey audio, any format. The witnesses listen to each, the spellings are reconciled, and the name joins the review queue. The first model load takes about half a minute.</p>
      <form onSubmit={go} className="grid gap-3">
        <label className="text-sm">Name as the surveyor wrote it, in Devanagari (optional; the system proposes one if left blank)<input className="w-full font-name text-xl" value={name} onChange={(e) => setName(e.target.value)} /></label>
        <label className="text-sm">Existing Roman spelling on record (optional)<input className="w-full" value={en} onChange={(e) => setEn(e.target.value)} /></label>
        <label className="text-sm">Your name<input className="w-full" value={officer} onChange={(e) => setOfficer(e.target.value)} /></label>
        <label className="text-sm">Recordings<input type="file" multiple accept="audio/*,.wav,.mp3,.ogg,.m4a,.flac" onChange={(e) => setFiles([...e.target.files])} className="block mt-1" /></label>
        <div><button className="btn btn-forest" disabled={busy || files.length === 0}>{busy ? 'Listening…' : `Reconcile ${files.length || ''} recording${files.length === 1 ? '' : 's'}`}</button></div>
      </form>
      {err && <p className="text-alert mt-3">{err}</p>}
      {res && <p className="mt-4">Added as <a className="text-water" href={'#/' + res.case_id}><span className="font-name text-xl">{res.record.devanagari}</span> · {res.record.roman?.recommended} · <span className="font-ipa">{res.record.ipa}</span></a> with {res.record.confidence?.band} confidence. Open it to review.</p>}
    </div>
  )
}
