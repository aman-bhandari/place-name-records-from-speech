"""Eknaam (एकनाम) — officer review API for P-015. Serves cases, clips, decisions, audit, export and the UI."""
import sys, json, pathlib, time, io, csv, hashlib, threading
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from p015 import store, deva, phon, roman, consensus, gazetteer
ROOT = pathlib.Path(__file__).resolve().parents[1]
app = FastAPI(title='Eknaam P-015')
_models = {}; _lock = threading.Lock()
def db(): return store.connect()
def rec_of(row): return json.loads(row['record']) if row and row['record'] else None
@app.get('/api/stats')
def stats():
    c = db(); s = {r['status']: r['n'] for r in c.execute('SELECT status, COUNT(*) n FROM cases GROUP BY status')}
    s['cases'] = sum(s.values()); s['clips'] = c.execute('SELECT COUNT(*) FROM clips').fetchone()[0]
    s['speakers'] = c.execute('SELECT COUNT(DISTINCT speaker) FROM clips').fetchone()[0]
    ok, at = store.verify_audit(c); s['audit_ok'] = ok; s['audit_entries'] = c.execute('SELECT COUNT(*) FROM audit').fetchone()[0]
    return s
@app.get('/api/cases')
def cases(status: str = '', q: str = '', band: str = ''):
    c = db(); out = []
    for r in c.execute('SELECT c.*, r.record FROM cases c LEFT JOIN recommendation r ON r.case_id=c.id ORDER BY c.name_hi'):
        rec = rec_of(r) or {}
        if status and r['status'] != status: continue
        if q and q not in r['name_hi'] and q.lower() not in (r['existing_en'] or '').lower() and q.lower() not in (rec.get('roman', {}).get('recommended', '')).lower(): continue
        conf = rec.get('confidence', {})
        if band and conf.get('band') != band: continue
        out.append({'id': r['id'], 'name_hi': r['name_hi'], 'kind': r['kind'], 'existing_en': r['existing_en'], 'status': r['status'],
                    'devanagari': rec.get('devanagari'), 'roman': rec.get('roman', {}).get('recommended'), 'ipa': rec.get('ipa'),
                    'confidence': conf.get('score'), 'band': conf.get('band'), 'clips': conf.get('clips'), 'speakers': conf.get('speakers'),
                    'flags': rec.get('flags', []), 'variants': len(rec.get('variants', []))})
    return out
@app.get('/api/cases/{case_id}')
def case(case_id: int):
    c = db(); r = c.execute('SELECT c.*, r.record FROM cases c LEFT JOIN recommendation r ON r.case_id=c.id WHERE c.id=?', (case_id,)).fetchone()
    if not r: raise HTTPException(404)
    clips = []
    for k in c.execute('SELECT * FROM clips WHERE case_id=? ORDER BY cut_cer', (case_id,)):
        w = {x['witness']: {'text': x['text'], 'conf': x['conf']} for x in c.execute('SELECT * FROM witness WHERE clip_id=?', (k['id'],))}
        d = dict(k); d.pop('xvec', None); d['witnesses'] = w; clips.append(d)
    decisions = [dict(x) for x in c.execute('SELECT * FROM decision WHERE case_id=? ORDER BY id', (case_id,))]
    for d in decisions: d['record'] = json.loads(d['record']) if d['record'] else None
    audit = [dict(x) for x in c.execute('SELECT id, ts, actor, action, detail, hash FROM audit WHERE case_id=? ORDER BY id', (case_id,))]
    return {'case': {k: r[k] for k in r.keys() if k != 'record'}, 'record': rec_of(r), 'clips': clips, 'decisions': decisions, 'audit': audit}
@app.get('/api/clips/{clip_id}/audio')
def clip_audio(clip_id: str, context: int = 0):
    c = db(); k = c.execute('SELECT * FROM clips WHERE id=?', (clip_id,)).fetchone()
    if not k: raise HTTPException(404)
    p = ROOT / k['file']
    if context:
        # sentence audio, if cached (mined clips): file name is derived from the source
        src = k['source'];  # ai4bharat/Shrutilipi/hindi/train-00001-of-00196.parquet#rg3row5
        corpus = 'shrutilipi' if 'Shrutilipi' in src else 'indicvoices'
        path, tail = src.split('#'); shard = path.split('/')[-1].split('-')[1]; rg, row = tail[2:].split('row')
        sp = ROOT / 'data/cache/sent' / f'{corpus}_{shard}_{rg}_{row}.wav'
        if sp.exists(): p = sp
    if not p.exists(): raise HTTPException(404)
    return FileResponse(str(p), media_type='audio/wav')
class Decision(BaseModel):
    officer: str; action: str; reason: str = ''; devanagari: str = ''; roman: str = ''; ipa: str = ''; notes: str = ''
@app.post('/api/cases/{case_id}/decision')
def decide(case_id: int, d: Decision):
    c = db(); r = c.execute('SELECT c.*, r.record FROM cases c LEFT JOIN recommendation r ON r.case_id=c.id WHERE c.id=?', (case_id,)).fetchone()
    if not r: raise HTTPException(404)
    if d.action not in ('approve', 'reject', 'hold'): raise HTTPException(400, 'action must be approve, reject or hold')
    if not d.officer.strip(): raise HTTPException(400, 'officer name required')
    if d.action != 'approve' and not d.reason.strip(): raise HTTPException(400, 'reason required')
    rec = rec_of(r) or {}
    final = {'devanagari': deva.normalise(d.devanagari or rec.get('devanagari', '')), 'roman': (d.roman or rec.get('roman', {}).get('recommended', '')).strip(),
             'ipa': d.ipa or rec.get('ipa', ''), 'notes': d.notes}
    edited = [f for f, k in (('devanagari', 'devanagari'), ('roman', None), ('ipa', 'ipa')) if final[f] != (rec.get('roman', {}).get('recommended') if f == 'roman' else rec.get(k))]
    c.execute('INSERT INTO decision (case_id, officer, action, record, reason, ts) VALUES (?,?,?,?,?,?)', (case_id, d.officer, d.action, json.dumps(final, ensure_ascii=False), d.reason, time.time()))
    status = {'approve': 'approved', 'reject': 'rejected', 'hold': 'on hold'}[d.action]
    c.execute('UPDATE cases SET status=? WHERE id=?', (status, case_id)); c.commit()
    h = store.audit(c, d.officer, d.action, case_id, {'final': final, 'edited_fields': edited, 'reason': d.reason})
    return {'status': status, 'final': final, 'edited_fields': edited, 'audit_hash': h}
@app.get('/api/audit')
def audit(case_id: int = 0):
    c = db(); q = 'SELECT * FROM audit' + (' WHERE case_id=?' if case_id else '') + ' ORDER BY id DESC LIMIT 500'
    rows = [dict(x) for x in c.execute(q, (case_id,) if case_id else ())]; ok, at = store.verify_audit(c)
    return {'ok': ok, 'broken_at': at, 'entries': rows}
@app.get('/api/export.csv')
def export():
    c = db(); buf = io.StringIO(); w = csv.writer(buf)
    w.writerow(['name_hi', 'devanagari', 'roman', 'ipa', 'kind', 'existing_en', 'officer', 'approved_at', 'audit_hash'])
    for r in c.execute("SELECT c.*, d.record, d.officer, d.ts FROM cases c JOIN decision d ON d.case_id=c.id WHERE c.status='approved' AND d.id=(SELECT MAX(id) FROM decision WHERE case_id=c.id)"):
        f = json.loads(r['record']); h = c.execute('SELECT hash FROM audit WHERE case_id=? AND action="approve" ORDER BY id DESC LIMIT 1', (r['id'],)).fetchone()
        w.writerow([r['name_hi'], f['devanagari'], f['roman'], f['ipa'], r['kind'], r['existing_en'], r['officer'], time.strftime('%Y-%m-%d %H:%M', time.localtime(r['ts'])), h[0] if h else ''])
    return StreamingResponse(iter([buf.getvalue()]), media_type='text/csv', headers={'Content-Disposition': 'attachment; filename=eknaam-approved.csv'})
@app.get('/api/preview')
def preview(text: str):
    """Live rendering of an edited Devanagari spelling: IPA and Hunterian, so an officer sees the consequence of an edit."""
    t = deva.normalise(text); return {'devanagari': t, 'ipa': phon.ipa(t), 'roman': roman.romanise(t)}
def models():
    with _lock:
        if not _models:
            from p015 import witness
            _models['w'] = [witness.CTCWitness(witness.HINDI_MODELS['vakyansh'], name='vakyansh'), witness.CTCWitness(witness.HINDI_MODELS['indicw2v'], name='indicw2v'), witness.PhoneWitness()]
            _models['spk'] = None
    return _models
@app.post('/api/cases/upload')
async def upload(name_hi: str = Form(''), existing_en: str = Form(''), kind: str = Form('field recording'), officer: str = Form('field'), files: list[UploadFile] = File(...)):
    """Create a case from officer-uploaded recordings (any format). Every clip is transcribed by the witnesses and reconciled."""
    from p015 import audio, speaker
    if len(files) < 1: raise HTTPException(400, 'at least one recording')
    m = models(); c = db(); ev = []; saved = []
    out = ROOT / 'data/audio/uploads'; out.mkdir(parents=True, exist_ok=True)
    for f in files:
        b = await f.read(); y = audio.load_bytes(b); cid = hashlib.sha1(b).hexdigest()[:12]; p = out / f'{cid}.wav'; audio.save(p, y)
        outs = [w.transcribe(y) for w in m['w']]
        saved.append((cid, p, y, outs, f.filename))
        ev.append({'id': cid, 'witnesses': outs, 'snr_db': audio.snr_db(y), 'speaker': f'upload-{cid}', 'synthetic': False})
    best = deva.normalise(max((w for w in ev[0]['witnesses'] if w['witness'] in consensus.WITNESS_W), key=lambda w: w['conf'])['text'])
    label = deva.normalise(name_hi) or best
    gaz = gazetteer.load(); firsts = {phon.phonemes(x)[0] for e in ev for w in e['witnesses'] if w['witness'] in consensus.WITNESS_W and w['text'] for x in [deva.normalise(w['text'])] if phon.phonemes(x)}
    local = [g for g in gaz if phon.phonemes(g) and phon.phonemes(g)[0] in firsts]
    existing = {'hi': label if name_hi else '', 'en': existing_en or gaz.get(label, {}).get('en', ''), 'item': gaz.get(label, {}).get('item', ''), 'source': 'officer upload'}
    rec = consensus.reconcile(ev, gazetteer=local, existing=existing if existing['hi'] else None); rec['existing'] = existing
    cur = c.execute('INSERT OR REPLACE INTO cases (name_hi, kind, existing_en, existing_src, item, status, created) VALUES (?,?,?,?,?,?,?)', (label, kind, existing['en'], 'officer upload', '', 'pending', time.time())); case_id = cur.lastrowid
    c.execute('DELETE FROM clips WHERE case_id=?', (case_id,))
    for cid, p, y, outs, fn in saved:
        c.execute('INSERT OR REPLACE INTO clips (id, case_id, file, corpus, source, licence, speaker, sentence, start_s, end_s, dur_s, snr_db, synthetic, cut_cer, xvec) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                  (cid, case_id, str(p.relative_to(ROOT)), 'upload', fn, 'officer recording', f'upload-{cid}', '', 0, len(y) / 16000, len(y) / 16000, audio.snr_db(y), 0, 0.0, '[]'))
        for o in outs: c.execute('INSERT OR REPLACE INTO witness (clip_id, witness, text, conf) VALUES (?,?,?,?)', (cid, o['witness'], o['text'], o['conf']))
    c.execute('INSERT OR REPLACE INTO recommendation (case_id, record, built) VALUES (?,?,?)', (case_id, json.dumps(rec, ensure_ascii=False), time.time())); c.commit()
    store.audit(c, officer, 'uploaded', case_id, {'files': [s[4] for s in saved], 'devanagari': rec.get('devanagari')})
    return {'case_id': case_id, 'record': rec}
@app.get('/api/results')
def results():
    p = ROOT / 'data/eval.json'; return json.load(open(p)) if p.exists() else {}
dist = ROOT / 'ui/dist'
if dist.exists(): app.mount('/', StaticFiles(directory=str(dist), html=True), name='ui')
