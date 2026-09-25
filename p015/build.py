"""Build the case store from mined clips: witnesses → consensus → SQLite. Resumable per case."""
import sys, json, pathlib, collections, argparse, time
import numpy as np, torch, yaml
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from p015 import audio, witness, consensus, gazetteer, speaker, store, deva, phon, align
ROOT = pathlib.Path(__file__).resolve().parents[1]
def load_targets(paths):
    t = {}
    for p in paths:
        for r in yaml.safe_load(open(ROOT / p)): t[r['hi']] = r
    return t
def pick_diverse(clips, k):
    """Prefer distinct speakers: known speaker ids first, then x-vector clusters; ≤2 clips per speaker; best cut_cer first."""
    for c in clips:
        if not c.get('speaker'): c['speaker'] = None
    embs = [np.array(c['xvec'], dtype='float32') for c in clips]
    cl = speaker.cluster(embs) if embs else []
    for c, g in zip(clips, cl): c['spk_key'] = c['speaker'] or f"{c['corpus']}-x{g}"
    clips = sorted(clips, key=lambda c: (c['cut_cer'], -c['snr_db']))
    out, per = [], collections.Counter()
    for rnd in (1, 2):
        for c in clips:
            if c in out or per[c['spk_key']] >= rnd: continue
            out.append(c); per[c['spk_key']] += 1
            if len(out) >= k: return out
    return out
def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--targets', nargs='+', default=['data/targets_uk.yaml']); ap.add_argument('--per-case', type=int, default=8)
    ap.add_argument('--rebuild', action='store_true'); ap.add_argument('--gaz-all-india', type=int, default=0, help='also create cases for N all-India names found in clips')
    a = ap.parse_args()
    targets = load_targets(a.targets); gaz = gazetteer.load()
    clips = collections.defaultdict(list)
    for l in open(ROOT / 'data/clips.jsonl'):
        c = json.loads(l); clips[c['name_hi']].append(c)
    names = [n for n in targets if n in clips]
    if a.gaz_all_india:
        extra = sorted((n for n in clips if n not in targets and n in gaz), key=lambda n: -len(clips[n]))[:a.gaz_all_india]
        for n in extra: targets[n] = {'hi': n, 'en': gaz[n]['en'], 'kind': gaz[n]['src']}
        names += extra
    db = store.connect()
    if a.rebuild:
        for t in ('cases', 'clips', 'witness', 'recommendation', 'decision', 'audit'): db.execute(f'DELETE FROM {t}')
        db.commit()
    done = {r[0] for r in db.execute('SELECT name_hi FROM cases WHERE id IN (SELECT case_id FROM recommendation)')}
    todo = [n for n in names if n not in done]
    print('cases', len(names), 'todo', len(todo), flush=True)
    if not todo: return
    ws = [witness.CTCWitness(witness.HINDI_MODELS['vakyansh'], name='vakyansh'), witness.CTCWitness(witness.HINDI_MODELS['indicw2v'], name='indicw2v'), witness.PhoneWitness()]
    gaz_names = list(gaz); gaz_by_first = collections.defaultdict(list)
    for g in gaz_names:
        ph = phon.phonemes(g); gaz_by_first[ph[0] if ph else ''].append(g)
    t0 = time.time()
    for k, n in enumerate(todo):
        tg = targets[n]; chosen = pick_diverse(clips[n], a.per_case)
        wd = gaz.get(n, {}); existing = {'hi': n, 'en': tg.get('en') or wd.get('en', ''), 'item': wd.get('item', ''), 'source': 'Wikidata' if wd else 'curated'}
        cur = db.execute('INSERT OR REPLACE INTO cases (name_hi, kind, existing_en, existing_src, item, status, created) VALUES (?,?,?,?,?,?,?)',
                         (n, tg.get('kind', ''), existing['en'], existing['source'], existing['item'], 'pending', time.time())); case_id = cur.lastrowid
        db.execute('DELETE FROM clips WHERE case_id=?', (case_id,))
        ev = []
        for c in chosen:
            y = audio.load_file(ROOT / c['file']); outs = []
            sent = audio.load_file(ROOT / c['sentence_file']) if c.get('sentence_file') and (ROOT / c['sentence_file']).exists() else None
            for w in ws:
                if sent is not None and w.name in consensus.WITNESS_W:
                    # corpus clip: the witness hears the word inside its sentence (co-articulation context), located by its own emissions
                    lp = w.emissions(sent); em = align.greedy_frames(lp, w); loc = align.locate(em, n)
                    if loc is not None and loc[2] <= 0.5:
                        i, j, _ = loc; confs = [float(np.exp(lp[f, lp[f].argmax()])) for _, f in em[i:j + 1]]
                        outs.append({'witness': w.name, 'text': ''.join(ch for ch, _ in em[i:j + 1]).strip(), 'conf': float(np.mean(confs)), 'context': 'sentence'}); continue
                o = w.transcribe(y); o['context'] = 'clip'; outs.append(o)
            db.execute('INSERT OR REPLACE INTO clips (id, case_id, file, corpus, source, licence, speaker, district, state, gender, sentence, start_s, end_s, dur_s, snr_db, synthetic, cut_cer, xvec) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                       (c['id'], case_id, c['file'], c['corpus'], c['source'], c['licence'], c['spk_key'], c.get('district'), c.get('state'), c.get('gender'), c['sentence'], c['start_s'], c['end_s'], c['dur_s'], c['snr_db'], int(c.get('synthetic', False)), c['cut_cer'], json.dumps(c['xvec'])))
            for o in outs: db.execute('INSERT OR REPLACE INTO witness (clip_id, witness, text, conf) VALUES (?,?,?,?)', (c['id'], o['witness'], o['text'], o['conf']))
            ev.append({'id': c['id'], 'witnesses': outs, 'snr_db': c['snr_db'], 'speaker': c['spk_key'], 'synthetic': c.get('synthetic', False)})
        cands0 = [deva.normalise(max((w for w in e['witnesses'] if w['witness'] in consensus.WITNESS_W), key=lambda w: w['conf'])['text']) for e in ev]
        firsts = {phon.phonemes(c)[0] for c in cands0 if c and phon.phonemes(c)}
        local_gaz = [g for f in firsts for g in gaz_by_first.get(f, [])]
        rec = consensus.reconcile(ev, gazetteer=local_gaz, existing=existing)
        blind = consensus.reconcile(ev)   # acoustic only, for the evaluation
        rec['blind'] = {'devanagari': blind.get('devanagari'), 'confidence': blind.get('confidence')}; rec['existing'] = existing
        db.execute('INSERT OR REPLACE INTO recommendation (case_id, record, built) VALUES (?,?,?)', (case_id, json.dumps(rec, ensure_ascii=False), time.time()))
        store.audit(db, 'system', 'built', case_id, {'clips': len(ev), 'devanagari': rec.get('devanagari'), 'confidence': rec.get('confidence', {}).get('score')})
        db.commit()
        if k % 10 == 0: print(f'{k+1}/{len(todo)} {n} -> {rec.get("devanagari")} blind={blind.get("devanagari")} conf={rec.get("confidence",{}).get("score")} {time.time()-t0:.0f}s', flush=True)
    print('DONE', f'{time.time()-t0:.0f}s', flush=True)
if __name__ == '__main__': main()
