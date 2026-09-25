const j = async (r) => { if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || r.statusText); return r.json() }
export const api = {
  stats: () => fetch('/api/stats').then(j),
  cases: (p = {}) => fetch('/api/cases?' + new URLSearchParams(p)).then(j),
  case: (id) => fetch('/api/cases/' + id).then(j),
  decide: (id, body) => fetch(`/api/cases/${id}/decision`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }).then(j),
  preview: (text) => fetch('/api/preview?' + new URLSearchParams({ text })).then(j),
  audit: (case_id = 0) => fetch('/api/audit?case_id=' + case_id).then(j),
  upload: (form) => fetch('/api/cases/upload', { method: 'POST', body: form }).then(j),
  audioUrl: (id, context = 0) => `/api/clips/${id}/audio${context ? '?context=1' : ''}`,
}
