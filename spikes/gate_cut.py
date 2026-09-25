"""Gate 0.4 + 0.5: cut place names out of Shrutilipi sentences by forced alignment; re-recognise; x-vector speakers."""
import sys, json, pathlib, collections, time, itertools
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import numpy as np, torch
from p015 import audio, witness, align
from p015.hfparquet import RemoteParquet
root = pathlib.Path(__file__).resolve().parents[1]
TARGET = ['देहरादून', 'हरिद्वार', 'नैनीताल', 'ऋषिकेश', 'अल्मोड़ा', 'पिथौरागढ़', 'चमोली', 'उत्तरकाशी', 'रुद्रप्रयाग', 'हल्द्वानी', 'रुड़की', 'मसूरी', 'जोशीमठ', 'बद्रीनाथ', 'केदारनाथ', 'कोटद्वार', 'बागेश्वर', 'चम्पावत', 'पौड़ी', 'काशीपुर']
PER = 4
hits = collections.defaultdict(list)
for l in open(root / 'data/raw/hits_shrutilipi.jsonl'):
    d = json.loads(l)
    if d['name'] in TARGET and len(hits[d['name']]) < PER and d['duration'] < 20: hits[d['name']].append(d)
sel = [h for v in hits.values() for h in v]; print('names', len(hits), 'clips', len(sel), flush=True)
groups = collections.defaultdict(list)
for h in sel: groups[(h['path'], h['rg'])].append(h)
t0 = time.time(); sent = {}; cache = root / 'data/cache/sent'; cache.mkdir(parents=True, exist_ok=True)
def cpath(h): return cache / f"{h['path'].split('/')[-1].split('-')[1]}_{h['rg']}_{h['row']}.wav"
for (path, rg), hs in groups.items():
    need = [h for h in hs if not cpath(h).exists()]
    if need:
        r = RemoteParquet('ai4bharat/Shrutilipi', path, workers=8); t = r.read(row_groups=[rg], columns=['audio_filepath'])
        for h in need: audio.save(cpath(h), audio.load_bytes(t.column('audio_filepath')[h['row']].as_py()['bytes']))
    for h in hs: sent[id(h)] = audio.load_file(cpath(h))
print('fetched', len(groups), 'row groups', f'{time.time()-t0:.0f}s', flush=True)
w = witness.CTCWitness(witness.HINDI_MODELS['vakyansh'], name='vakyansh')
out = root / 'data/audio/gate_cut'; out.mkdir(parents=True, exist_ok=True); ok = 0; rows = []
def ed(a, b):
    d = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        prev, d[0] = d[0], i
        for j, cb in enumerate(b, 1): prev, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, prev + (ca != cb))
    return d[len(b)]
for i, h in enumerate(sel):
    y = sent[id(h)]; clip, info = align.cut_span(y, w, h['text'], h['start'], h['end'])
    if clip is None: rows.append((h['name'], 'NOCUT', '', 0)); continue
    tr = w.transcribe(clip); cer = ed(tr['text'].replace(' ', ''), h['name'].replace(' ', '')) / len(h['name'])
    good = cer <= 0.25; ok += good; rows.append((h['name'], tr['text'], round(cer, 2), round(info['end_s'] - info['start_s'], 2)))
    audio.save(out / f'{h["name"]}_{i}.wav', clip); h['cut'] = info; h['recog'] = tr['text']; h['cer'] = cer; h['sent_id'] = id(h)
print(f'CUT PASS {ok}/{len(sel)} = {ok/len(sel):.0%}', flush=True)
for r in rows: print('  ', r, flush=True)
del w; torch.cuda.empty_cache()
# speaker x-vectors on the full sentence audio (more speech than the cut)
from transformers import WavLMForXVector, Wav2Vec2FeatureExtractor
fe = Wav2Vec2FeatureExtractor.from_pretrained('microsoft/wavlm-base-plus-sv'); xm = WavLMForXVector.from_pretrained('microsoft/wavlm-base-plus-sv').cuda().eval()
emb = {}
with torch.no_grad():
    for k, y in sent.items():
        x = fe(y[:16000 * 12], sampling_rate=16000, return_tensors='pt').input_values.cuda(); e = xm(x).embeddings[0]; emb[k] = torch.nn.functional.normalize(e, dim=-1).cpu().numpy()
for name, hs in hits.items():
    es = [emb[id(h)] for h in hs]; sims = [float(es[a] @ es[b]) for a, b in itertools.combinations(range(len(es)), 2)]
    # single-link clusters at 0.86
    parent = list(range(len(es)))
    def find(x):
        while parent[x] != x: x = parent[x]
        return x
    for (a, b), s in zip(itertools.combinations(range(len(es)), 2), sims):
        if s >= 0.86: parent[find(a)] = find(b)
    print(name, 'clips', len(es), 'distinct speakers', len({find(i) for i in range(len(es))}), 'sims', [round(s, 2) for s in sims], flush=True)
json.dump([{k: v for k, v in h.items() if k != 'sent_id'} for h in sel], open(root / 'data/cache/gate_cut.json', 'w'), ensure_ascii=False, indent=0)
print('DONE', flush=True)
