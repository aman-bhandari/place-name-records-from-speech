import React, { useEffect, useState } from 'react'
import Review from './pages/Review.jsx'
import Upload from './pages/Upload.jsx'
import Method from './pages/Method.jsx'
import AuditPage from './pages/Audit.jsx'
import { api } from './api.js'

const TABS = [['', 'Review'], ['add', 'Add recordings'], ['audit', 'Audit trail'], ['method', 'Method']]
function useHash() {
  const [h, setH] = useState(location.hash.replace(/^#\/?/, ''))
  useEffect(() => { const f = () => setH(location.hash.replace(/^#\/?/, '')); addEventListener('hashchange', f); return () => removeEventListener('hashchange', f) }, [])
  return h
}
export default function App() {
  const hash = useHash(); const [stats, setStats] = useState(null)
  const page = /^\d+$/.test(hash.split('/')[0]) ? '' : hash.split('/')[0]
  const caseId = /^\d+$/.test(hash.split('/')[0]) ? hash.split('/')[0] : undefined
  useEffect(() => { api.stats().then(setStats).catch(() => {}) }, [hash])
  return (
    <div className="min-h-screen overflow-x-hidden">
      <header className="border-b hair px-4 md:px-6 py-3 flex flex-wrap items-baseline gap-x-6 gap-y-1">
        <a href="#/" className="flex items-baseline gap-2"><span className="font-name text-2xl">एकनाम</span><span className="text-ink-soft">Eknaam</span></a>
        <span className="text-ink-faint text-sm">one authoritative name for every place · Survey of India review</span>
        <nav className="ml-auto flex gap-4 text-sm">
          {TABS.map(([h, t]) => <a key={h} href={'#/' + h} className={(page === h ? 'text-ink border-b-2 border-ink' : 'text-ink-soft') + ' pb-0.5'}>{t}</a>)}
          <a href="/api/export.csv" className="text-water">Export approved</a>
        </nav>
      </header>
      {stats && <div className="px-4 md:px-6 py-1.5 text-sm text-ink-soft border-b hair flex flex-wrap gap-x-5">
        <span>{stats.cases} names</span><span>{stats.clips} recordings</span><span>{stats.speakers} speakers</span>
        <span>{stats.pending || 0} pending · {stats.approved || 0} approved · {stats['on hold'] || 0} on hold · {stats.rejected || 0} rejected</span>
        <span className={stats.audit_ok ? 'text-forest' : 'text-alert'}>audit chain {stats.audit_ok ? 'verified' : 'BROKEN'} ({stats.audit_entries})</span>
      </div>}
      <main>
        {page === '' && <Review caseId={caseId} />}
        {page === 'add' && <Upload />}
        {page === 'audit' && <AuditPage />}
        {page === 'method' && <Method />}
      </main>
    </div>
  )
}
