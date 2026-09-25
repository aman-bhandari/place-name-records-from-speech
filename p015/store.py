"""SQLite case store: names (cases), clips, witness outputs, recommendations, officer decisions, hash-chained audit."""
import sqlite3, json, hashlib, time, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]; DB = ROOT / 'data/p015.sqlite'
SCHEMA = """
CREATE TABLE IF NOT EXISTS cases (id INTEGER PRIMARY KEY, name_hi TEXT UNIQUE, kind TEXT, existing_en TEXT, existing_src TEXT, item TEXT, status TEXT DEFAULT 'pending', created REAL);
CREATE TABLE IF NOT EXISTS clips (id TEXT PRIMARY KEY, case_id INTEGER, file TEXT, corpus TEXT, source TEXT, licence TEXT, speaker TEXT, district TEXT, state TEXT, gender TEXT,
  sentence TEXT, start_s REAL, end_s REAL, dur_s REAL, snr_db REAL, synthetic INTEGER DEFAULT 0, cut_cer REAL, xvec BLOB);
CREATE TABLE IF NOT EXISTS witness (clip_id TEXT, witness TEXT, text TEXT, conf REAL, PRIMARY KEY (clip_id, witness));
CREATE TABLE IF NOT EXISTS recommendation (case_id INTEGER PRIMARY KEY, record TEXT, built REAL);
CREATE TABLE IF NOT EXISTS decision (id INTEGER PRIMARY KEY, case_id INTEGER, officer TEXT, action TEXT, record TEXT, reason TEXT, ts REAL);
CREATE TABLE IF NOT EXISTS audit (id INTEGER PRIMARY KEY, ts REAL, actor TEXT, action TEXT, case_id INTEGER, detail TEXT, prev_hash TEXT, hash TEXT);
CREATE INDEX IF NOT EXISTS clips_case ON clips(case_id);
"""
def connect(path=DB):
    c = sqlite3.connect(str(path)); c.row_factory = sqlite3.Row; c.executescript(SCHEMA); return c
def audit(c, actor, action, case_id=None, detail=None):
    prev = c.execute('SELECT hash FROM audit ORDER BY id DESC LIMIT 1').fetchone(); prev = prev[0] if prev else 'genesis'
    ts = time.time(); d = json.dumps(detail, ensure_ascii=False) if detail is not None else ''
    h = hashlib.sha256(f'{prev}|{ts}|{actor}|{action}|{case_id}|{d}'.encode()).hexdigest()
    c.execute('INSERT INTO audit (ts, actor, action, case_id, detail, prev_hash, hash) VALUES (?,?,?,?,?,?,?)', (ts, actor, action, case_id, d, prev, h)); c.commit(); return h
def verify_audit(c):
    prev = 'genesis'
    for r in c.execute('SELECT * FROM audit ORDER BY id'):
        h = hashlib.sha256(f"{prev}|{r['ts']}|{r['actor']}|{r['action']}|{r['case_id']}|{r['detail']}".encode()).hexdigest()
        if h != r['hash'] or r['prev_hash'] != prev: return False, r['id']
        prev = h
    return True, None
