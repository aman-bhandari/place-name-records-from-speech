import React, { useEffect, useState } from 'react'
import { api } from '../api.js'
import { Waveform, Confidence, SheetEntry, Bar, Band, fmtTs } from '../components.jsx'

export default function Review({ caseId }) {
  const [list, setList] = useState([]); const [q, setQ] = useState(''); const [status, setStatus] = useState(''); const [band, setBand] = useState('')
  useEffect(() => { api.cases({ q, status, band }).then(setList).catch(() => setList([])) }, [q, status, band, caseId])
  return (
    <div className="grid md:grid-cols-[300px_1fr] min-h-[calc(100vh-90px)]">
      <aside className={'border-r hair ' + (caseId ? 'hidden md:block' : '')}>
        <div className="p-3 flex flex-col gap-2 border-b hair">
          <input placeholder="Find a name (Hindi or Roman)" value={q} onChange={(e) => setQ(e.target.value)} aria-label="Find a name" />
          <div className="flex gap-2 text-sm">
            <select value={status} onChange={(e) => setStatus(e.target.value)} aria-label="Status"><option value="">any status</option><option value="pending">pending</option><option value="approved">approved</option><option value="on hold">on hold</option><option value="rejected">rejected</option></select>
            <select value={band} onChange={(e) => setBand(e.target.value)} aria-label="Confidence"><option value="">any confidence</option><option value="high">high</option><option value="medium">medium</option><option value="low">low</option></select>
          </div>
        </div>
        <ul className="overflow-auto max-h-[calc(100vh-170px)]">
          {list.length === 0 && <li className="p-4 text-ink-faint">No names match. Clear the filters, or add recordings.</li>}
          {list.map((c) => (
            <li key={c.id}><a href={'#/' + c.id} className={'block px-3 py-2 border-b hair hover:bg-water-soft ' + (String(c.id) === caseId ? 'bg-water-soft' : '')}>
              <div className="flex items-baseline gap-2"><span className="font-name text-xl">{c.devanagari || c.name_hi}</span><span className="text-ink-soft text-sm">{c.roman}</span><span className="ml-auto text-sm"><Band band={c.band} /> {c.confidence != null ? Math.round(c.confidence) : ''}</span></div>
              <div className="text-xs text-ink-faint flex gap-2">{c.clips} clips · {c.speakers} speakers · {c.status}{c.variants ? ` · ${c.variants} variant` : ''}{c.flags?.some((f) => f.startsWith('speakers disagree')) ? ' · disagreement' : ''}</div>
            </a></li>
          ))}
        </ul>
      </aside>
      <section className="p-4 md:p-6 min-w-0">
        {caseId ? <Case id={caseId} key={caseId} /> : <Empty n={list.length} />}
      </section>
    </div>
  )
}
function Empty({ n }) {
  return <div className="max-w-xl text-ink-soft"><h1 className="text-2xl text-ink mb-2">Pick a name to review</h1><p>Each name in the queue has been heard from several speakers. The system proposes one Devanagari spelling, one Roman spelling and a pronunciation, and shows every recording and competing spelling it weighed. Nothing is published until an officer approves it.</p>{n > 0 && <p className="mt-2 md:hidden"><a className="text-water" href="#/">Open the queue</a></p>}</div>
}

function Case({ id }) {
  const [d, setD] = useState(null); const [err, setErr] = useState('')
  const load = () => api.case(id).then(setD).catch((e) => setErr(e.message))
  useEffect(() => { load() }, [id])
  if (err) return <p className="text-alert">Could not load this case: {err}</p>
  if (!d) return <p className="text-ink-faint">Loading</p>
  const { record: r, clips, decisions } = d; const last = decisions[decisions.length - 1]
  if (!r) return <p className="text-ink-soft">This name has no recommendation yet.</p>
  const byId = Object.fromEntries(clips.map((c) => [c.id, c]))
  return (
    <div className="max-w-5xl">
      <div className="md:hidden mb-2 text-sm"><a href="#/" className="text-water">← Queue</a></div>
      <div className="flex flex-wrap items-baseline gap-x-4 mb-3">
        <h1 className="text-lg text-ink-soft">{d.case.kind || 'place'} · {d.case.existing_en ? `on record as “${d.case.existing_en}”` : 'no existing record'} · <span className="text-ink">{d.case.status}</span></h1>
      </div>
      <SheetEntry rec={r} edited={last?.action === 'approve' ? last.record : null} />
      <div className="mt-4 grid md:grid-cols-[1fr_auto] gap-4 items-start">
        <Confidence c={r.confidence} />
        {r.flags?.length > 0 && <ul className="text-sm text-contour max-w-xs">{r.flags.map((f) => <li key={f}>{f}</li>)}</ul>}
      </div>

      <h2 className="mt-8 text-lg border-b hair pb-1">Recordings, and what each witness heard</h2>
      <p className="text-sm text-ink-soft mb-2">Click a waveform to play the name; “in sentence” plays the whole source sentence with the name marked. Two Hindi recognisers and one phone recogniser listen to every clip; “fit” is how well the recommended spelling explains that clip.</p>
      <div className="overflow-x-auto"><table className="evidence w-full text-sm">
        <thead><tr><th>Recording</th><th>Speaker</th><th>Hindi witness 1</th><th>Hindi witness 2</th><th>Phones heard</th><th>Fit</th><th>Source</th></tr></thead>
        <tbody>{clips.map((c) => {
          const sim = r.candidates?.[0]?.sims?.[r.per_clip_best ? clips.indexOf(c) : 0]
          const sup = r.candidates?.[0]?.supporters?.includes(c.id)
          return <tr key={c.id}>
            <td className="min-w-[180px]"><Waveform url={api.audioUrl(c.id)} label={`Play recording ${c.id}`} />
              <div className="flex gap-3 text-xs text-ink-faint mt-1"><span>{c.dur_s?.toFixed(2)} s · SNR {c.snr_db} dB{c.synthetic ? ' · synthetic' : ''}</span>{c.sentence && <button type="button" className="text-water" onClick={(e) => { const a = new Audio(api.audioUrl(c.id, 1)); a.currentTime = Math.max(0, c.start_s - 1.0); a.play(); setTimeout(() => a.pause(), (c.end_s - c.start_s + 2.2) * 1000) }}>in sentence</button>}</div></td>
            <td className="whitespace-nowrap">{c.speaker}<div className="text-xs text-ink-faint">{[c.gender, c.district, c.state].filter(Boolean).join(', ')}</div></td>
            <td className="font-name text-base">{c.witnesses?.vakyansh?.text}<div className="text-xs text-ink-faint">{Math.round((c.witnesses?.vakyansh?.conf || 0) * 100)}%</div></td>
            <td className="font-name text-base">{c.witnesses?.indicw2v?.text}<div className="text-xs text-ink-faint">{Math.round((c.witnesses?.indicw2v?.conf || 0) * 100)}%</div></td>
            <td className="font-ipa text-xs">{c.witnesses?.phones?.text}</td>
            <td><span className={sup ? 'text-forest' : 'text-ink-faint'}>{sup ? 'supports' : 'weak'}</span></td>
            <td className="text-xs max-w-[220px]"><div className="truncate" title={c.source}>{c.corpus}</div>{c.sentence && <div className="text-ink-faint line-clamp-2" title={c.sentence}>“{c.sentence}”</div>}<div className="text-ink-faint">{c.licence}</div></td>
          </tr>
        })}</tbody>
      </table></div>

      <div className="grid md:grid-cols-2 gap-8 mt-8">
        <div>
          <h2 className="text-lg border-b hair pb-1">Competing spellings</h2>
          <table className="w-full text-sm mt-2"><tbody>{r.candidates?.map((c, i) => <tr key={c.text} className="border-b hair">
            <td className="py-1.5 font-name text-lg">{c.text}</td><td className="text-ink-faint text-xs">{c.origin}</td>
            <td><Bar v={c.support} col={i === 0 ? '#3F6D4E' : '#8F5A2E'} /></td><td className="text-right text-ink-soft">{Math.round(c.support * 100)}</td><td className="text-xs text-ink-faint">{c.supporters.length} clips</td>
          </tr>)}</tbody></table>
        </div>
        <div>
          <h2 className="text-lg border-b hair pb-1">Roman spelling and existing record</h2>
          <dl className="text-sm mt-2 grid grid-cols-[130px_1fr] gap-y-1">
            <dt className="text-ink-soft">Hunterian (scheme)</dt><dd>{r.roman?.scheme} <span className="text-ink-faint">· with diacritics {r.roman?.scheme_diacritic}</span></dd>
            <dt className="text-ink-soft">Recommended</dt><dd>{r.roman?.recommended} <span className="text-ink-faint">({r.roman?.kind})</span></dd>
            <dt className="text-ink-soft">Why</dt><dd>{r.roman?.reason}</dd>
            <dt className="text-ink-soft">Existing record</dt><dd>{r.existing?.hi ? `${r.existing.hi} / ${r.existing.en || '—'}` : 'none'} <span className="text-ink-faint">{r.existing?.item ? `· Wikidata ${r.existing.item}` : r.existing?.source ? `· ${r.existing.source}` : ''}</span></dd>
            <dt className="text-ink-soft">Matches record</dt><dd>{r.confidence?.existing_match ? 'yes' : 'no — the recommended spelling differs from the record'}</dd>
          </dl>
          {r.variants?.length > 0 && <div className="mt-4">
            <h3 className="text-base border-b hair pb-1">Regional variants kept as linked alternates</h3>
            <ul className="text-sm mt-2">{r.variants.map((v) => <li key={v.devanagari} className="py-1"><span className="font-name text-lg">{v.devanagari}</span> <span className="font-ipa text-ink-soft">{v.ipa}</span> · {v.roman} · {v.speakers} speakers, {v.clips.length} clips, {Math.round(v.share * 100)}% of evidence</li>)}</ul>
          </div>}
        </div>
      </div>

      <Decide d={d} onDone={load} />

      <h2 className="mt-8 text-lg border-b hair pb-1">Audit trail for this name</h2>
      <ul className="text-sm mt-2">{d.audit.map((a) => <li key={a.id} className="py-1 border-b hair flex flex-wrap gap-x-3"><span className="text-ink-faint w-40">{fmtTs(a.ts)}</span><span>{a.actor}</span><span className="text-ink-soft">{a.action}</span><span className="text-ink-faint truncate max-w-md" title={a.detail}>{a.detail}</span><span className="text-ink-faint font-mono text-xs ml-auto">{a.hash.slice(0, 10)}</span></li>)}</ul>
    </div>
  )
}

function Decide({ d, onDone }) {
  const r = d.record; const [officer, setOfficer] = useState(() => localStorage.getItem('eknaam.officer') || '')
  const [dev, setDev] = useState(r.devanagari); const [rom, setRom] = useState(r.roman?.recommended || ''); const [ipa, setIpa] = useState(r.ipa); const [reason, setReason] = useState(''); const [notes, setNotes] = useState('')
  const [prev, setPrev] = useState(null); const [msg, setMsg] = useState(''); const [busy, setBusy] = useState(false)
  useEffect(() => { if (dev && dev !== r.devanagari) { const t = setTimeout(() => api.preview(dev).then(setPrev).catch(() => {}), 300); return () => clearTimeout(t) } else setPrev(null) }, [dev])
  const act = async (action) => {
    setBusy(true); setMsg('')
    try { localStorage.setItem('eknaam.officer', officer); const res = await api.decide(d.case.id, { officer, action, reason, devanagari: dev, roman: rom, ipa, notes }); setMsg(`${res.status}${res.edited_fields.length ? ' with edits to ' + res.edited_fields.join(', ') : ''} · audit ${res.audit_hash.slice(0, 10)}`); onDone() }
    catch (e) { setMsg(e.message) } finally { setBusy(false) }
  }
  return (
    <div className="mt-8 border-t-2 border-ink pt-4">
      <h2 className="text-lg">Officer decision</h2>
      <p className="text-sm text-ink-soft mb-3">Edit any field before approving. An edit to the Devanagari re-derives the pronunciation and the scheme Roman form below so you can compare.</p>
      <div className="grid md:grid-cols-3 gap-3 max-w-3xl">
        <label className="text-sm">Devanagari<input className="w-full font-name text-xl" value={dev} onChange={(e) => setDev(e.target.value)} /></label>
        <label className="text-sm">Roman<input className="w-full" value={rom} onChange={(e) => setRom(e.target.value)} /></label>
        <label className="text-sm">IPA<input className="w-full font-ipa" value={ipa} onChange={(e) => setIpa(e.target.value)} /></label>
      </div>
      {prev && <p className="text-sm mt-2 text-ink-soft">With “{prev.devanagari}” the rules give <span className="font-ipa">{prev.ipa}</span> and Roman “{prev.roman.scheme}”. <button type="button" className="text-water" onClick={() => { setIpa(prev.ipa); setRom(prev.roman.recommended) }}>Use these</button></p>}
      <div className="grid md:grid-cols-[1fr_2fr] gap-3 max-w-3xl mt-3">
        <label className="text-sm">Officer<input className="w-full" value={officer} onChange={(e) => setOfficer(e.target.value)} placeholder="Name, designation" /></label>
        <label className="text-sm">Reason (required to hold or reject)<input className="w-full" value={reason} onChange={(e) => setReason(e.target.value)} /></label>
      </div>
      <label className="text-sm block max-w-3xl mt-3">Notes for the record<textarea className="w-full" rows={2} value={notes} onChange={(e) => setNotes(e.target.value)} /></label>
      <div className="flex flex-wrap gap-3 mt-4 items-center">
        <button className="btn btn-forest" disabled={busy || !officer} onClick={() => act('approve')}>Approve this record</button>
        <button className="btn" disabled={busy || !officer || !reason} onClick={() => act('hold')}>Hold for more recordings</button>
        <button className="btn btn-alert" disabled={busy || !officer || !reason} onClick={() => act('reject')}>Reject</button>
        {msg && <span className="text-sm text-ink-soft">{msg}</span>}
      </div>
    </div>
  )
}
