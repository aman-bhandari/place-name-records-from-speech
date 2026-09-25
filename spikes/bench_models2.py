"""Gate 2b: phoneme model (manual CTC decode, no phonemizer) and Whisper turbo on the same Lingua Libre clips."""
import json, pathlib, time, unicodedata, collections, re, gc, sys
import numpy as np, torch, librosa
from transformers import Wav2Vec2ForCTC, Wav2Vec2FeatureExtractor, WhisperForConditionalGeneration, WhisperProcessor
sys.path.insert(0, str(pathlib.Path(__file__).parent)); 
root = pathlib.Path(__file__).resolve().parents[1]; dev = 'cuda'
man = [m for m in json.load(open(root / 'data/raw/ll_manifest_min3.json')) if (root / m['file']).exists()]
byword = collections.defaultdict(list)
for m in man: byword[m['word']].append(m)
byword = {w: v for w, v in byword.items() if len(v) >= 3}
audio = {m['file']: librosa.load(str(root / m['file']), sr=16000, mono=True)[0] for v in byword.values() for m in v}
def ed(a, b):
    d = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        prev, d[0] = d[0], i
        for j, cb in enumerate(b, 1):
            prev, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, prev + (ca != cb))
    return d[len(b)]
t0 = time.time(); repo = 'facebook/wav2vec2-xlsr-53-espeak-cv-ft'
from huggingface_hub import hf_hub_download
vocab = json.load(open(hf_hub_download(repo, 'vocab.json'))); inv = {v: k for k, v in vocab.items()}
fe = Wav2Vec2FeatureExtractor.from_pretrained(repo); model = Wav2Vec2ForCTC.from_pretrained(repo).to(dev).eval(); ph = {}; conf = {}
with torch.no_grad():
    for f, y in audio.items():
        x = fe(y, sampling_rate=16000, return_tensors='pt').input_values.to(dev)
        lp = model(x).logits[0].log_softmax(-1); ids = lp.argmax(-1).tolist()
        out = []; prev = None
        for i in ids:
            if i != prev and i != vocab['<pad>']: out.append(inv[i])
            prev = i
        ph[f] = ' '.join(t for t in out if t not in ('<s>', '</s>', '<unk>', '|'))
        conf[f] = float(lp.max(-1).values.exp().mean())
json.dump(ph, open(root / 'data/cache/bench_phoneme.json', 'w'), ensure_ascii=False)
agree = []
for w, v in byword.items():
    s = [ph[m['file']].replace(' ', '') for m in v]
    agree += [ed(a, b) / max(len(a), len(b), 1) for i, a in enumerate(s) for b in s[i+1:]]
print('phoneme', f'{time.time()-t0:.0f}s', 'mean pairwise phone distance between speakers', round(float(np.mean(agree)), 3), 'mean conf', round(float(np.mean(list(conf.values()))), 3), flush=True)
for w in list(byword)[:14]: print('  ', w, [ph[m['file']] for m in byword[w]], flush=True)
del model; gc.collect(); torch.cuda.empty_cache()
def norm(s): return re.sub(r'[^ऀ-ॿ ]', '', unicodedata.normalize('NFC', s)).strip()
t0 = time.time(); repo = 'openai/whisper-large-v3-turbo'
proc = WhisperProcessor.from_pretrained(repo); model = WhisperForConditionalGeneration.from_pretrained(repo, dtype=torch.float16).to(dev).eval(); hyp = {}
with torch.no_grad():
    for f, y in audio.items():
        feats = proc(y, sampling_rate=16000, return_tensors='pt').input_features.to(dev, torch.float16)
        ids = model.generate(feats, language='hi', task='transcribe', max_new_tokens=32, num_beams=1)
        hyp[f] = proc.batch_decode(ids, skip_special_tokens=True)[0]
json.dump(hyp, open(root / 'data/cache/bench_whisper.json', 'w'), ensure_ascii=False)
per = [ed(norm(hyp[m['file']]), norm(w)) / max(1, len(norm(w))) for w, v in byword.items() for m in v]
ex = [norm(hyp[m['file']]) == norm(w) for w, v in byword.items() for m in v]
print('whisper', f'{time.time()-t0:.0f}s', 'clip_cer', round(float(np.mean(per)), 3), 'clip_exact', round(float(np.mean(ex)), 3), flush=True)
for w in list(byword)[:10]: print('  ', w, [hyp[m['file']] for m in byword[w]], flush=True)
print('DONE', flush=True)
