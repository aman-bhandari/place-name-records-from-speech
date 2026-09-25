import React, { useEffect, useState } from 'react'
import { api } from '../api.js'
import { fmtTs } from '../components.jsx'
export default function AuditPage() {
  const [a, setA] = useState(null)
  useEffect(() => { api.audit().then(setA) }, [])
  if (!a) return <p className="p-6 text-ink-faint">Loading</p>
  return (
    <div className="p-4 md:p-6">
      <h1 className="text-2xl mb-1">Audit trail</h1>
      <p className="text-ink-soft mb-3">Every build, upload and officer decision is appended with a hash that includes the previous entry. Chain {a.ok ? 'verifies' : `is broken at entry ${a.broken_at}`}.</p>
      <div className="overflow-x-auto"><table className="w-full text-sm"><thead><tr className="text-left text-ink-soft border-b hair"><th className="py-1">When</th><th>Who</th><th>Action</th><th>Name</th><th>Detail</th><th>Hash</th></tr></thead>
        <tbody>{a.entries.map((e) => <tr key={e.id} className="border-b hair align-top"><td className="py-1 whitespace-nowrap">{fmtTs(e.ts)}</td><td>{e.actor}</td><td>{e.action}</td><td><a className="text-water" href={'#/' + e.case_id}>{e.case_id}</a></td><td className="text-ink-soft max-w-xl truncate" title={e.detail}>{e.detail}</td><td className="font-mono text-xs text-ink-faint">{e.hash.slice(0, 12)}</td></tr>)}</tbody></table></div>
    </div>
  )
}
