"""Why do cuts fail? sentence-level CER of the witness vs transcript, and word-level alignment around the name."""
import sys, json, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import numpy as np
from p015 import audio, witness, align
root = pathlib.Path(__file__).resolve().parents[1]
hits = json.load(open(root / 'data/cache/gate_cut.json'))
def ed(a, b):
    d = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        prev, d[0] = d[0], i
        for j, cb in enumerate(b, 1): prev, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, prev + (ca != cb))
    return d[len(b)]
w = witness.CTCWitness(witness.HINDI_MODELS['vakyansh'], name='vakyansh')
rows = []
for h in hits:
    p = root / 'data/cache/sent' / f"{h['path'].split('/')[-1].split('-')[1]}_{h['rg']}_{h['row']}.wav"
    if not p.exists(): continue
    y = audio.load_file(p); logp = w.emissions(y); full, conf = w.greedy(logp)
    scer = ed(full.replace(' ', ''), h['text'].replace(' ', '')) / max(1, len(h['text']))
    ids, pos = w.tokens(h['text']); spans, score = align.force_align(logp, ids, w.blank)
    # per-token mean posterior of the aligned token (alignment confidence for the name span)
    idx = [k for k, q in enumerate(pos) if h['start'] <= q < h['end'] and ids[k] != w.delim]
    post = float(np.mean([np.exp(logp[spans[k][0]:spans[k][1] + 1, ids[k]]).mean() for k in idx]))
    f0, f1 = spans[idx[0]][0], spans[idx[-1]][1]
    # re-recognise with wider margins
    for m in (0.04, 0.10):
        a = max(0, int(f0 * 320 - m * 16000)); b = min(len(y), int((f1 + 1) * 320 + m * 16000)); tr = w.transcribe(y[a:b])['text']
        cer = ed(tr.replace(' ', ''), h['name']) / len(h['name'])
        if m == 0.04: c04, t04 = cer, tr
        else: c10, t10 = cer, tr
    rows.append((h['name'], round(scer, 2), round(post, 2), round(score, 2), round((f1 - f0 + 1) * 0.02, 2), c04 <= 0.25, c10 <= 0.25, t04, t10))
rows.sort(key=lambda r: r[1])
print('name sentCER alignPost pathScore nameDur pass04 pass10')
for r in rows: print(r)
good = [r for r in rows if r[1] <= 0.25]; print('sentences with sentCER<=0.25:', len(good), 'of', len(rows), '| cut pass among them (m=0.04):', sum(r[5] for r in good), '| (m=0.10):', sum(r[6] for r in good))
good = [r for r in rows if r[2] >= 0.5]; print('alignPost>=0.5:', len(good), '| pass04', sum(r[5] for r in good), '| pass10', sum(r[6] for r in good))
