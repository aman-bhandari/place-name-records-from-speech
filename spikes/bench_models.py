"""Gate 2: how well each open model hears real Hindi speakers (Lingua Libre words with >=3 speakers).
Reports CER per model, and consensus-over-speakers vs best/mean single clip."""
import json, pathlib, sys, time, unicodedata, collections, re, gc
import numpy as np, torch, librosa
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor, WhisperForConditionalGeneration, WhisperProcessor
root = pathlib.Path(__file__).resolve().parents[1]
dev = 'cuda'
man = [m for m in json.load(open(root / 'data/raw/ll_manifest_min3.json')) if (root / m['file']).exists()]
byword = collections.defaultdict(list)
for m in man: byword[m['word']].append(m)
byword = {w: v for w, v in byword.items() if len(v) >= 3}
print('words', len(byword), 'clips', sum(map(len, byword.values())), flush=True)
def load(p):
    y, _ = librosa.load(str(root / p), sr=16000, mono=True); return y
audio = {m['file']: load(m['file']) for v in byword.values() for m in v}
def norm(s): return re.sub(r'[^ऀ-ॿ ]', '', unicodedata.normalize('NFC', s)).strip()
def ed(a, b):
    d = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        prev, d[0] = d[0], i
        for j, cb in enumerate(b, 1):
            prev, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, prev + (ca != cb))
    return d[len(b)]
def cer(h, t): return ed(h, t) / max(1, len(t))
def center_star(seqs):
    """Consensus by aligning all seqs to the medoid and majority-voting per column (ROVER-lite)."""
    if len(seqs) == 1: return seqs[0]
    med = min(seqs, key=lambda s: sum(ed(s, o) for o in seqs))
    cols = [collections.Counter() for _ in range(len(med) + 1)]  # insertions before position i tracked in cols[i]
    sub = [collections.Counter() for _ in range(len(med))]
    for s in seqs:
        # DP alignment s vs med
        n, m = len(s), len(med); D = np.zeros((n + 1, m + 1), int); D[:, 0] = range(n + 1); D[0, :] = range(m + 1)
        for i in range(1, n + 1):
            for j in range(1, m + 1): D[i, j] = min(D[i-1, j] + 1, D[i, j-1] + 1, D[i-1, j-1] + (s[i-1] != med[j-1]))
        i, j = n, m; ins = ''
        while i > 0 or j > 0:
            if i > 0 and j > 0 and D[i, j] == D[i-1, j-1] + (s[i-1] != med[j-1]):
                sub[j-1][s[i-1]] += 1; cols[j][ins[::-1]] += 1; ins = ''; i -= 1; j -= 1
            elif i > 0 and D[i, j] == D[i-1, j] + 1: ins += s[i-1]; i -= 1
            else: sub[j-1][''] += 1; cols[j][ins[::-1]] += 1; ins = ''; j -= 1
        cols[0][ins[::-1]] += 1
    out = ''
    for j in range(len(med) + 1):
        out += cols[j].most_common(1)[0][0] if cols[j] else ''
        if j < len(med): out += sub[j].most_common(1)[0][0]
    return out
results = {}
def report(name, hyp):
    per = {f: cer(norm(h), norm(w)) for w, v in byword.items() for m in v for f, h in [(m['file'], hyp[m['file']])]}
    cons = {w: center_star([norm(hyp[m['file']]) for m in v]) for w, v in byword.items()}
    best = {w: min(cer(norm(hyp[m['file']]), norm(w)) for m in v) for w, v in byword.items()}
    ccer = {w: cer(cons[w], norm(w)) for w in byword}
    exact_single = np.mean([norm(hyp[m['file']]) == norm(w) for w, v in byword.items() for m in v])
    exact_cons = np.mean([cons[w] == norm(w) for w in byword])
    r = {'clip_cer': float(np.mean(list(per.values()))), 'clip_exact': float(exact_single), 'oracle_best_clip_cer': float(np.mean(list(best.values()))),
         'consensus_cer': float(np.mean(list(ccer.values()))), 'consensus_exact': float(exact_cons)}
    results[name] = r; print(name, json.dumps(r), flush=True)
    for w in list(byword)[:8]: print('  ', w, '->', cons[w], '|', [norm(hyp[m['file']]) for m in byword[w]], flush=True)
def run_ctc(repo, name):
    t0 = time.time(); proc = Wav2Vec2Processor.from_pretrained(repo); model = Wav2Vec2ForCTC.from_pretrained(repo).to(dev).eval()
    hyp = {}
    with torch.no_grad():
        for f, y in audio.items():
            x = proc(y, sampling_rate=16000, return_tensors='pt').input_values.to(dev)
            ids = model(x).logits.argmax(-1)[0]
            hyp[f] = proc.decode(ids)
    print(name, f'{time.time()-t0:.0f}s', flush=True); report(name, hyp)
    json.dump(hyp, open(root / f'data/cache/bench_{name}.json', 'w'), ensure_ascii=False)
    del model; gc.collect(); torch.cuda.empty_cache(); return hyp
run_ctc('Harveenchadha/vakyansh-wav2vec2-hindi-him-4200', 'vakyansh')
try:
    from huggingface_hub import snapshot_download
    snapshot_download('ai4bharat/indicwav2vec-hindi', allow_patterns=['*.json', '*.txt', '*.safetensors', 'pytorch_model.bin', '*.py'])
    run_ctc('ai4bharat/indicwav2vec-hindi', 'indicwav2vec')
except Exception as e: print('indicwav2vec FAIL', type(e).__name__, str(e)[:300], flush=True)
# phoneme model: report inter-speaker agreement (no truth IPA yet)
t0 = time.time(); repo = 'facebook/wav2vec2-xlsr-53-espeak-cv-ft'
proc = Wav2Vec2Processor.from_pretrained(repo); model = Wav2Vec2ForCTC.from_pretrained(repo).to(dev).eval(); ph = {}
with torch.no_grad():
    for f, y in audio.items():
        x = proc(y, sampling_rate=16000, return_tensors='pt').input_values.to(dev)
        ph[f] = proc.decode(model(x).logits.argmax(-1)[0])
json.dump(ph, open(root / 'data/cache/bench_phoneme.json', 'w'), ensure_ascii=False)
agree = []
for w, v in byword.items():
    s = [ph[m['file']].replace(' ', '') for m in v]
    agree += [ed(a, b) / max(len(a), len(b), 1) for i, a in enumerate(s) for b in s[i+1:]]
print('phoneme', f'{time.time()-t0:.0f}s', 'mean pairwise phone distance between speakers', float(np.mean(agree)), flush=True)
for w in list(byword)[:10]: print('  ', w, [ph[m['file']] for m in byword[w]], flush=True)
del model; gc.collect(); torch.cuda.empty_cache()
# whisper turbo, language hi
t0 = time.time(); repo = 'openai/whisper-large-v3-turbo'
proc = WhisperProcessor.from_pretrained(repo); model = WhisperForConditionalGeneration.from_pretrained(repo, torch_dtype=torch.float16).to(dev).eval(); hyp = {}
with torch.no_grad():
    for f, y in audio.items():
        feats = proc(y, sampling_rate=16000, return_tensors='pt').input_features.to(dev, torch.float16)
        ids = model.generate(feats, language='hi', task='transcribe', max_new_tokens=32, num_beams=1)
        hyp[f] = proc.batch_decode(ids, skip_special_tokens=True)[0]
print('whisper', f'{time.time()-t0:.0f}s', flush=True); report('whisper_turbo', hyp)
json.dump(hyp, open(root / 'data/cache/bench_whisper.json', 'w'), ensure_ascii=False)
json.dump(results, open(root / 'data/cache/bench_results.json', 'w'), indent=1)
print('DONE', flush=True)
