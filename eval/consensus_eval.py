"""AC2/AC6 evaluation on the built store: consensus vs single clip vs oracle; clip-count sweep; noise sweep.
Truth = the gazetteer/curated Devanagari label the clips were mined for (compared by coarse key: nasal notation,
spacing and ऋ/रि ignored). 'blind' = acoustic evidence only; 'with record' = existing record + gazetteer as candidates."""
import sys, json, pathlib, random, collections, argparse
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import numpy as np
from p015 import store, consensus, deva, phon
ROOT = pathlib.Path(__file__).resolve().parents[1]
def key(s): return deva.match_key(s or '')
def load_cases(min_clips=3):
    c = store.connect(); cases = []
    for r in c.execute('SELECT c.id, c.name_hi, c.existing_en, c.item, r.record FROM cases c JOIN recommendation r ON r.case_id=c.id'):
        clips = []
        for k in c.execute('SELECT * FROM clips WHERE case_id=? AND synthetic=0', (r['id'],)):
            w = [{'witness': x['witness'], 'text': x['text'], 'conf': x['conf']} for x in c.execute('SELECT * FROM witness WHERE clip_id=?', (k['id'],))]
            clips.append({'id': k['id'], 'witnesses': w, 'snr_db': k['snr_db'], 'speaker': k['speaker'], 'synthetic': False})
        if len(clips) >= min_clips and k and r['record']: cases.append({'id': r['id'], 'truth': r['name_hi'], 'en': r['existing_en'], 'item': r['item'], 'clips': clips, 'record': json.loads(r['record'])})
    return cases
def single_best(clip):
    ws = [w for w in clip['witnesses'] if w['witness'] in consensus.WITNESS_W and w['text']]
    return deva.normalise(max(ws, key=lambda w: w['conf'])['text']) if ws else ''
def evaluate(cases, seed=0):
    rng = random.Random(seed); out = {}
    tk = [key(c['truth']) for c in cases]
    # single clip: mean over clips (a random clip), and the oracle best clip
    single = np.mean([np.mean([key(single_best(cl)) == t for cl in c['clips']]) for c, t in zip(cases, tk)])
    oracle = np.mean([any(key(single_best(cl)) == t for cl in c['clips']) for c, t in zip(cases, tk)])
    clearest = np.mean([key(single_best(max(c['clips'], key=consensus.clip_weight))) == t for c, t in zip(cases, tk)])
    blind = np.mean([key(c['record'].get('blind', {}).get('devanagari')) == t for c, t in zip(cases, tk)])
    withrec = np.mean([key(c['record'].get('devanagari')) == t for c, t in zip(cases, tk)])
    out['n_cases'] = len(cases); out['clips_per_case'] = float(np.mean([len(c['clips']) for c in cases])); out['speakers_per_case'] = float(np.mean([len({cl['speaker'] for cl in c['clips']}) for c in cases]))
    out['exact'] = {'random single clip': float(single), 'clearest single clip': float(clearest), 'oracle best clip': float(oracle), 'consensus (acoustic only)': float(blind), 'consensus + existing record': float(withrec)}
    # calibration: accuracy by confidence band (with record)
    bands = collections.defaultdict(list)
    for c, t in zip(cases, tk): bands[c['record']['confidence']['band']].append(key(c['record']['devanagari']) == t)
    out['by_band'] = {b: {'n': len(v), 'exact': float(np.mean(v))} for b, v in bands.items()}
    # clip-count sweep (acoustic only)
    sweep = {}
    for k in (1, 2, 3, 4, 6, 8):
        acc = []
        for c, t in zip(cases, tk):
            if len(c['clips']) < k: continue
            for rep in range(3):
                sub = rng.sample(c['clips'], k); r = consensus.reconcile(sub); acc.append(key(r.get('devanagari')) == t)
        if acc: sweep[k] = {'n': len(acc), 'exact': float(np.mean(acc))}
    out['clips_sweep_acoustic'] = sweep
    return out
def noise_sweep(cases, snrs=(20, 10, 5), max_cases=40, seed=0):
    """Re-run the Hindi witnesses on noise-added clips (white noise at given SNR) and reconcile acoustically."""
    from p015 import audio, witness
    rng = random.Random(seed); sub = rng.sample(cases, min(max_cases, len(cases)))
    ws = [witness.CTCWitness(witness.HINDI_MODELS['vakyansh'], name='vakyansh'), witness.CTCWitness(witness.HINDI_MODELS['indicw2v'], name='indicw2v')]
    c = store.connect(); files = {r['id']: r['file'] for r in c.execute('SELECT id, file FROM clips')}
    res = {}
    for snr in ['clean'] + list(snrs):
        acc = []
        for case in sub:
            ev = []
            for cl in case['clips']:
                y = audio.load_file(ROOT / files[cl['id']])
                if snr != 'clean':
                    p = np.mean(y ** 2) + 1e-9; n = np.random.RandomState(1).randn(len(y)).astype('float32'); n *= np.sqrt(p / (10 ** (snr / 10)) / (np.mean(n ** 2) + 1e-9)); y = y + n
                ev.append({'id': cl['id'], 'witnesses': [w.transcribe(y) for w in ws], 'speaker': cl['speaker']})
            r = consensus.reconcile(ev); acc.append(key(r.get('devanagari')) == key(case['truth']))
        res[str(snr)] = {'n': len(acc), 'exact': float(np.mean(acc))}; print('noise', snr, res[str(snr)], flush=True)
    return res
if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--noise', action='store_true'); ap.add_argument('--min-clips', type=int, default=3); a = ap.parse_args()
    cases = load_cases(a.min_clips); out = evaluate(cases)
    print(json.dumps(out, indent=1, ensure_ascii=False))
    if a.noise: out['noise_sweep_acoustic'] = noise_sweep(cases)
    json.dump(out, open(ROOT / 'data/eval.json', 'w'), indent=1, ensure_ascii=False); print('saved data/eval.json')
