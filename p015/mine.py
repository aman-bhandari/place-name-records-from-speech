"""Mine real-speaker clips of target place names out of open speech corpora (resumable).
Hits (from spikes/scan_corpora.py) → choose occurrences per name with greedy row-group coverage → fetch sentence
audio (cached) → CTC forced alignment cut → QA by re-recognition → x-vector speaker → data/audio/clips + clips.jsonl"""
import json, sys, time, pathlib, collections, argparse, hashlib
import numpy as np, torch, yaml
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from p015 import audio, witness, align, speaker, gazetteer
from p015.hfparquet import RemoteParquet
ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO = {'shrutilipi': 'ai4bharat/Shrutilipi', 'indicvoices': 'ai4bharat/IndicVoices'}
LIC = {'shrutilipi': 'CC-BY-4.0 (AI4Bharat Shrutilipi, All India Radio news)', 'indicvoices': 'CC-BY-4.0 (AI4Bharat IndicVoices)'}
def ed(a, b):
    d = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        prev, d[0] = d[0], i
        for j, cb in enumerate(b, 1): prev, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, prev + (ca != cb))
    return d[len(b)]
def load_hits(names, max_dur=16.0):
    hits = collections.defaultdict(list)
    for corpus in REPO:
        p = ROOT / f'data/raw/hits_{corpus}.jsonl'
        if not p.exists(): continue
        for l in open(p):
            d = json.loads(l)
            if d['name'] in names and (d.get('duration') or 0) <= max_dur: hits[d['name']].append(d)
    return hits
def choose(hits, per_name, max_groups):
    """Greedy: prefer occurrences in row groups already selected; spread across corpora; cap per name."""
    chosen = collections.defaultdict(list); groups = set()
    order = sorted(hits, key=lambda n: len(hits[n]))
    for rnd in range(per_name):
        for n in order:
            if len(chosen[n]) > rnd: continue
            cands = [h for h in hits[n] if h not in chosen[n]]
            if not cands: continue
            cands.sort(key=lambda h: (0 if (h['corpus'], h['path'], h['rg']) in groups else 1, 0 if h['corpus'] == 'indicvoices' and rnd % 2 else 1, h.get('duration') or 0))
            h = cands[0]
            if (h['corpus'], h['path'], h['rg']) not in groups and len(groups) >= max_groups: continue
            groups.add((h['corpus'], h['path'], h['rg'])); chosen[n].append(h)
    return chosen, groups
def sent_path(h): return ROOT / 'data/cache/sent' / f"{h['corpus']}_{h['path'].split('/')[-1].split('-')[1]}_{h['rg']}_{h['row']}.wav"
def clip_id(h): return hashlib.sha1(f"{h['corpus']}|{h['path']}|{h['rg']}|{h['row']}|{h['start']}".encode()).hexdigest()[:12]
def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--targets', nargs='+', default=['data/targets_uk.yaml']); ap.add_argument('--per-name', type=int, default=8)
    ap.add_argument('--max-groups', type=int, default=700); ap.add_argument('--all-india', type=int, default=0, help='add N most frequent unambiguous towns/districts')
    a = ap.parse_args()
    targets = {}
    for t in a.targets:
        for r in yaml.safe_load(open(ROOT / t)): targets[r['hi']] = r
    gaz = gazetteer.load()
    if a.all_india:
        y = json.load(open(ROOT / 'data/raw/yield.json'))['occ']
        pool = sorted(((sum(c.values()), n) for n, c in y.items() if n in gaz and gaz[n]['src'] in ('town', 'district') and not gaz[n]['ambiguous'] and len(n) >= 4 and n not in targets), reverse=True)
        for _, n in pool[:a.all_india]: targets[n] = {'hi': n, 'en': gaz[n]['en'], 'kind': gaz[n]['src']}
    hits = load_hits(set(targets)); chosen, groups = choose(hits, a.per_name, a.max_groups)
    print('targets', len(targets), 'with hits', len(chosen), 'clips planned', sum(map(len, chosen.values())), 'row groups', len(groups), flush=True)
    out_dir = ROOT / 'data/audio/clips'; out_dir.mkdir(parents=True, exist_ok=True); (ROOT / 'data/cache/sent').mkdir(parents=True, exist_ok=True)
    man_path = ROOT / 'data/clips.jsonl'; done = set()
    if man_path.exists():
        for l in open(man_path): done.add(json.loads(l)['id'])
    man = open(man_path, 'a')
    w = witness.CTCWitness(witness.HINDI_MODELS['vakyansh'], name='vakyansh'); spk = speaker.SpeakerModel()
    by_group = collections.defaultdict(list)
    for n, hs in chosen.items():
        for h in hs:
            if clip_id(h) not in done: by_group[(h['corpus'], h['path'], h['rg'])].append(h)
    t0 = time.time(); nclips = 0; nfail = 0
    for gi, ((corpus, path, rg), hs) in enumerate(sorted(by_group.items())):
        need = [h for h in hs if not sent_path(h).exists()]
        if need:
            try:
                r = RemoteParquet(REPO[corpus], path, workers=8); col = 'audio_filepath'; t = r.read(row_groups=[rg], columns=[col] + (['speaker_id', 'district', 'state', 'gender'] if corpus == 'indicvoices' else []))
                for h in need: audio.save(sent_path(h), audio.load_bytes(t.column(col)[h['row']].as_py()['bytes']))
            except Exception as e:
                print('FETCH FAIL', path, rg, type(e).__name__, str(e)[:120], flush=True); continue
        for h in hs:
            try:
                y = audio.load_file(sent_path(h)); clip, info = align.cut_name(y, w, h['name'])
                if clip is None or len(clip) < 1600 or info['locate_dist'] > 0.34: nfail += 1; continue
                tr = w.transcribe(clip); cer = ed(tr['text'].replace(' ', ''), h['name'].replace(' ', '')) / max(1, len(h['name'].replace(' ', '')))
                cid = clip_id(h); audio.save(out_dir / f'{cid}.wav', clip); emb = spk.embed(y)
                rec = {'id': cid, 'name_hi': h['name'], 'corpus': corpus, 'source': f"{REPO[corpus]}/{path}#rg{rg}row{h['row']}", 'licence': LIC[corpus],
                       'speaker': h.get('speaker_id') or None, 'district': h.get('district'), 'state': h.get('state'), 'gender': h.get('gender'),
                       'sentence': h['text'], 'start_s': round(info['start_s'], 3), 'end_s': round(info['end_s'], 3), 'dur_s': round(len(clip) / 16000, 3),
                       'snr_db': round(audio.snr_db(clip), 1), 'cut_cer': round(cer, 3), 'cut_text': tr['text'], 'heard': info['heard'], 'locate_dist': round(info['locate_dist'], 3), 'sentence_file': str(sent_path(h).relative_to(ROOT)), 'synthetic': False, 'file': f'data/audio/clips/{cid}.wav',
                       'xvec': [round(float(x), 5) for x in emb]}
                man.write(json.dumps(rec, ensure_ascii=False) + '\n'); man.flush(); nclips += 1
            except Exception as e:
                nfail += 1; print('CUT FAIL', h['name'], type(e).__name__, str(e)[:120], flush=True)
        if gi % 10 == 0: print(f'group {gi+1}/{len(by_group)} clips={nclips} fail={nfail} {time.time()-t0:.0f}s', flush=True)
    print('DONE clips', nclips, 'fail', nfail, f'{time.time()-t0:.0f}s', flush=True)
if __name__ == '__main__': main()
