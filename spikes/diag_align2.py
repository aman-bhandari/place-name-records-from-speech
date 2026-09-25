import sys, json, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from p015 import audio, witness, align
root = pathlib.Path(__file__).resolve().parents[1]; hits = json.load(open(root / 'data/cache/gate_cut.json'))
def ed(a, b):
    d = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        prev, d[0] = d[0], i
        for j, cb in enumerate(b, 1): prev, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, prev + (ca != cb))
    return d[len(b)]
w = witness.CTCWitness(witness.HINDI_MODELS['vakyansh'], name='vakyansh'); rows = []
for h in hits:
    p = root / 'data/cache/sent' / f"{h['path'].split('/')[-1].split('-')[1]}_{h['rg']}_{h['row']}.wav"
    if not p.exists(): continue
    y = audio.load_file(p); clip, info = align.cut_name(y, w, h['name'])
    if clip is None: rows.append((h['name'], None, 1.0, '', info)); continue
    tr = w.transcribe(clip)['text']; cer = ed(tr.replace(' ', ''), h['name']) / len(h['name'])
    rows.append((h['name'], round(info['locate_dist'], 2), round(cer, 2), tr, info['heard'], round(info['end_s'] - info['start_s'], 2)))
ok25 = sum(1 for r in rows if r[2] <= 0.25); ok34 = sum(1 for r in rows if r[2] <= 0.34); loc = sum(1 for r in rows if r[1] is not None and r[1] <= 0.34)
from p015 import consensus, deva
import collections, os
CONTEXT = os.environ.get('CONTEXT') == '1'
byname = collections.defaultdict(list)
for r in rows:
    if r[1] is not None and r[1] <= 0.34: byname[r[0]].append({'id': str(len(byname[r[0]])), 'witnesses': [{'witness': 'vakyansh', 'text': r[4] if CONTEXT else r[3], 'conf': 0.8}]})
ex = 0
for n, cl in byname.items():
    rec = consensus.reconcile(cl); ok = deva.match_key(rec['devanagari']) == deva.match_key(n); ex += ok
    print('  E2E', n, '->', rec['devanagari'], 'OK' if ok else 'X', [c['witnesses'][0]['text'] for c in cl])
print('END-TO-END consensus exact (no gazetteer):', ex, '/', len(byname))
print(f'located (dist<=0.34): {loc}/{len(rows)} | cut re-recognised CER<=0.25: {ok25} | <=0.34: {ok34}')
for r in sorted(rows, key=lambda r: -r[2])[:30]: print(r)
