"""Consensus engine: reconcile many speakers' evidence for one place name into one recommended record.

Every clip contributes evidence (its Devanagari hypotheses from the Hindi witnesses, its acoustic phones, its
confidence and quality). Candidate spellings are scored by how well their pronunciation explains ALL clips, weighted
by clip quality; nothing is decided by picking the single clearest clip. Stable minority clusters are kept as
linked variants."""
import math, itertools, collections
import numpy as np
from . import deva, phon, roman

# --- phonetic feature distance -------------------------------------------------------------------
_F = {}
def _feat(p):
    """Feature vector (tuple) for a phoneme: consonants (place, manner, voice, aspiration), vowels (height, back, length, nasal)."""
    if p in _F: return _F[p]
    nasal = p.endswith('̃'); b = p.rstrip('̃')
    place = {'k': 'vel', 'kʰ': 'vel', 'ɡ': 'vel', 'ɡʱ': 'vel', 'ŋ': 'vel', 'q': 'uvu', 'x': 'vel', 'ɣ': 'vel',
             't͡ʃ': 'pal', 't͡ʃʰ': 'pal', 'd͡ʒ': 'pal', 'd͡ʒʱ': 'pal', 'ɲ': 'pal', 'ʃ': 'pal', 'ʂ': 'ret', 'j': 'pal',
             'ʈ': 'ret', 'ʈʰ': 'ret', 'ɖ': 'ret', 'ɖʱ': 'ret', 'ɳ': 'ret', 'ɽ': 'ret', 'ɽʱ': 'ret', 'ɭ': 'ret',
             't̪': 'den', 't̪ʰ': 'den', 'd̪': 'den', 'd̪ʱ': 'den', 'n': 'den', 's': 'den', 'z': 'den', 'r': 'den', 'l': 'den',
             'p': 'lab', 'pʰ': 'lab', 'b': 'lab', 'bʱ': 'lab', 'm': 'lab', 'f': 'lab', 'ʋ': 'lab', 'ɦ': 'glo'}
    manner = {'ŋ': 'nas', 'ɲ': 'nas', 'ɳ': 'nas', 'n': 'nas', 'm': 'nas', 'ʃ': 'fri', 'ʂ': 'fri', 's': 'fri', 'z': 'fri', 'f': 'fri', 'x': 'fri', 'ɣ': 'fri', 'ɦ': 'fri',
              'j': 'app', 'ʋ': 'app', 'l': 'lat', 'ɭ': 'lat', 'r': 'tri', 'ɽ': 'fla', 'ɽʱ': 'fla', 't͡ʃ': 'aff', 't͡ʃʰ': 'aff', 'd͡ʒ': 'aff', 'd͡ʒʱ': 'aff'}
    if b in place:
        voiced = b[0] in 'ɡdbzɣd͡ʒɖɽʋjlrmnŋɲɳɭɦ' or b.startswith('d͡ʒ') or b.startswith('d̪')
        f = ('C', place[b], manner.get(b, 'sto'), voiced, 'ʰ' in b or 'ʱ' in b, nasal)
    else:
        height = {'ə': 1, 'aː': 0, 'ɪ': 2, 'iː': 3, 'ʊ': 2, 'uː': 3, 'eː': 2, 'ɛː': 1, 'oː': 2, 'ɔː': 1, 'ɔ': 1, 'æ': 1, 'rɪ': 2}.get(b, 1)
        back = {'ə': 1, 'aː': 1, 'ɪ': 0, 'iː': 0, 'ʊ': 2, 'uː': 2, 'eː': 0, 'ɛː': 0, 'oː': 2, 'ɔː': 2, 'ɔ': 2, 'æ': 0, 'rɪ': 0}.get(b, 1)
        f = ('V', height, back, b.endswith('ː'), nasal, b == 'rɪ')
    _F[p] = f; return f
def sub_cost(a, b):
    if a == b: return 0.0
    fa, fb = _feat(a), _feat(b)
    if fa[0] != fb[0]: return 1.0
    if fa[0] == 'C':
        c = 0.0; c += 0.35 * (fa[1] != fb[1]); c += 0.3 * (fa[2] != fb[2]); c += 0.15 * (fa[3] != fb[3]); c += 0.15 * (fa[4] != fb[4]); c += 0.05 * (fa[5] != fb[5])
        if {fa[1], fb[1]} == {'ret', 'den'}: c -= 0.15   # retroflex/dental confusions are the common accent shift
        return max(0.15, c)
    c = 0.15 * abs(fa[1] - fb[1]) + 0.15 * abs(fa[2] - fb[2]) + 0.2 * (fa[3] != fb[3]) + 0.15 * (fa[4] != fb[4]) + 0.3 * (fa[5] != fb[5])
    return max(0.1, min(1.0, c))
def phone_dist(a, b):
    """Normalised weighted edit distance between two phoneme lists (0 = same)."""
    a = [p for p in a if p != ' ']; b = [p for p in b if p != ' ']
    if not a and not b: return 0.0
    n, m = len(a), len(b); D = np.zeros((n + 1, m + 1))
    for i in range(1, n + 1): D[i, 0] = D[i - 1, 0] + (0.5 if a[i - 1] == 'ə' else 1.0)
    for j in range(1, m + 1): D[0, j] = D[0, j - 1] + (0.5 if b[j - 1] == 'ə' else 1.0)
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            D[i, j] = min(D[i - 1, j] + (0.5 if a[i - 1] == 'ə' else 1.0), D[i, j - 1] + (0.5 if b[j - 1] == 'ə' else 1.0), D[i - 1, j - 1] + sub_cost(a[i - 1], b[j - 1]))
    return float(D[n, m] / max(n, m))

# --- string consensus (ROVER-lite) ----------------------------------------------------------------
def _ed(a, b):
    d = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        prev, d[0] = d[0], i
        for j, cb in enumerate(b, 1): prev, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, prev + (ca != cb))
    return d[len(b)]
def column_vote(seqs, weights=None):
    """Align every string to the medoid and vote per column (weighted); returns the voted string."""
    seqs = [s for s in seqs if s]
    if not seqs: return ''
    if len(seqs) == 1: return seqs[0]
    weights = weights or [1.0] * len(seqs)
    med = min(seqs, key=lambda s: sum(_ed(s, o) for o in seqs))
    cols = [collections.Counter() for _ in range(len(med) + 1)]; sub = [collections.Counter() for _ in range(len(med))]
    for s, w in zip(seqs, weights):
        n, m = len(s), len(med); D = np.zeros((n + 1, m + 1), int); D[:, 0] = range(n + 1); D[0, :] = range(m + 1)
        for i in range(1, n + 1):
            for j in range(1, m + 1): D[i, j] = min(D[i-1, j] + 1, D[i, j-1] + 1, D[i-1, j-1] + (s[i-1] != med[j-1]))
        i, j = n, m; ins = ''
        while i > 0 or j > 0:
            if i > 0 and j > 0 and D[i, j] == D[i-1, j-1] + (s[i-1] != med[j-1]):
                sub[j-1][s[i-1]] += w; cols[j][ins[::-1]] += w; ins = ''; i -= 1; j -= 1
            elif i > 0 and D[i, j] == D[i-1, j] + 1: ins += s[i-1]; i -= 1
            else: sub[j-1][''] += w; cols[j][ins[::-1]] += w; ins = ''; j -= 1
        cols[0][ins[::-1]] += w
    out = ''
    for j in range(len(med) + 1):
        out += cols[j].most_common(1)[0][0] if cols[j] else ''
        if j < len(med): out += sub[j].most_common(1)[0][0]
    return out

# --- the engine ------------------------------------------------------------------------------------
WITNESS_W = {'vakyansh': 1.0, 'indicw2v': 0.8}
def clip_weight(clip):
    """Evidence weight of a clip: mean witness confidence × quality × (synthetic penalty)."""
    confs = [w['conf'] for w in clip['witnesses'] if w['witness'] in WITNESS_W]
    q = np.mean(confs) if confs else 0.3
    snr = clip.get('snr_db', 20.0); qf = 0.5 + 0.5 * min(1.0, max(0.0, (snr - 5) / 20))
    return float(q * qf * (0.4 if clip.get('synthetic') else 1.0))
def gazetteer_neighbours(candidates, gaz, max_d=0.3, k=3):
    """Existing-record names phonetically close to the current candidates."""
    if not gaz: return []
    out = []
    cand_ph = [phon.phonemes(c) for c in candidates[:4]]
    for g in gaz:
        gp = phon.phonemes(g); d = min(phone_dist(gp, c) for c in cand_ph) if cand_ph else 1.0
        if d <= max_d: out.append((d, g))
    return [g for _, g in sorted(out)[:k]]
def reconcile(clips, gazetteer=None, existing=None):
    """clips: list of dicts {id, witnesses:[{witness,text,conf}], phones?, snr_db?, speaker?, synthetic?}.
    gazetteer: iterable of Devanagari names (existing records). existing: {'hi','en','source'} for this case, optional."""
    clips = [c for c in clips if any(w.get('text') for w in c['witnesses'])]
    if not clips: return {'error': 'no usable clips'}
    weights = [clip_weight(c) for c in clips]; W = sum(weights) or 1.0
    # evidence per clip: phoneme lists of each Hindi witness hypothesis
    ev = []
    for c in clips:
        hyps = [(deva.normalise(w['text']), WITNESS_W[w['witness']]) for w in c['witnesses'] if w['witness'] in WITNESS_W and w.get('text')]
        ev.append([(phon.phonemes(h), ww) for h, ww in hyps])
    # candidates
    cands = collections.OrderedDict()
    for c in clips:
        for w in c['witnesses']:
            if w['witness'] in WITNESS_W and w.get('text'): cands.setdefault(deva.normalise(w['text']), 'witness')
    best_texts = [deva.normalise(max((w for w in c['witnesses'] if w['witness'] in WITNESS_W), key=lambda w: w['conf'])['text']) for c in clips]
    voted = deva.normalise(column_vote(best_texts, weights))
    if voted: cands.setdefault(voted, 'vote')
    if existing and existing.get('hi'): cands.setdefault(deva.normalise(existing['hi']), 'existing')
    for g in gazetteer_neighbours(list(cands), gazetteer or []): cands.setdefault(deva.normalise(g), 'gazetteer')
    # merge candidates that differ only by spacing: keep the existing/gazetteer spelling, else the spacing most clips used
    merged = collections.OrderedDict()
    for cand, origin in cands.items():
        k = cand.replace(' ', '')
        if k not in merged: merged[k] = (cand, origin); continue
        old, oo = merged[k]
        if origin in ('existing', 'gazetteer') and oo not in ('existing', 'gazetteer'): merged[k] = (cand, origin)
        elif oo not in ('existing', 'gazetteer') and best_texts.count(cand) > best_texts.count(old): merged[k] = (cand, origin)
    cands = collections.OrderedDict(merged.values())
    # score: how well each candidate explains every clip
    scored = []
    for cand, origin in cands.items():
        if not cand: continue
        cp = phon.phonemes(cand); sims = []
        for e in ev:
            if not e: sims.append(0.0); continue
            d = sum(ww * phone_dist(cp, hp) for hp, ww in e) / sum(ww for _, ww in e)
            sims.append(math.exp(-4.0 * d))
        support = sum(w * s for w, s in zip(weights, sims)) / W
        supporters = [clips[i]['id'] for i, s in enumerate(sims) if s >= 0.55]
        scored.append({'text': cand, 'origin': origin, 'support': round(float(support), 4), 'supporters': supporters, 'sims': [round(float(s), 3) for s in sims]})
    scored.sort(key=lambda x: -x['support'])
    top = scored[0]; second = scored[1]['support'] if len(scored) > 1 else 0.0
    # agreement: share of clips whose best hypothesis matches the top by coarse key
    key = deva.match_key(top['text']); agree = sum(w for w, t in zip(weights, best_texts) if deva.match_key(t) == key) / W
    speakers = {c.get('speaker') or c['id'] for c in clips if not c.get('synthetic')}
    n_spk = len(speakers); mean_conf = float(np.mean([clip_weight(c) for c in clips]))
    gaz_match = bool(gazetteer and top['text'] in set(map(deva.normalise, gazetteer))) or bool(existing and deva.normalise(existing.get('hi', '')) == top['text'])
    spk_factor = min(1.0, n_spk / 5.0)
    conf = 100 * (0.40 * top['support'] + 0.25 * agree + 0.15 * min(1.0, (top['support'] - second) * 3) + 0.10 * spk_factor + 0.10 * mean_conf)
    flags = []
    if n_spk < 3: flags.append('needs more recordings (fewer than 3 real speakers)')
    if agree < 0.6: flags.append('speakers disagree')
    if not gaz_match: flags.append('no matching existing record')
    # variants: clips whose best hypothesis is a different spelling (by coarse key), backed by >= 2 real speakers,
    # and phonetically distinct from the top (not a mere notation difference)
    groups = collections.defaultdict(list)
    for i, t in enumerate(best_texts): groups[deva.match_key(t)].append(i)
    variants = []; tp = phon.phonemes(top['text'])
    for k, g in sorted(groups.items(), key=lambda kv: -sum(weights[i] for i in kv[1])):
        if k == key: continue
        text = deva.normalise(column_vote([best_texts[i] for i in g], [weights[i] for i in g]))
        spk = {clips[i].get('speaker') or clips[i]['id'] for i in g if not clips[i].get('synthetic')}
        if len(spk) >= 2 and phone_dist(tp, phon.phonemes(text)) >= 0.04:
            variants.append({'devanagari': text, 'ipa': phon.ipa(text), 'roman': roman.romanise(text)['scheme'], 'clips': [clips[i]['id'] for i in g], 'speakers': len(spk),
                             'share': round(sum(weights[i] for i in g) / W, 3)})
    n = len(clips)
    if variants: flags.append(f'{len(variants)} regional variant(s) kept as linked alternates')
    rom = roman.romanise(top['text'], existing_en=(existing or {}).get('en'))
    return {'devanagari': top['text'], 'ipa': phon.ipa(top['text']), 'roman': rom,
            'confidence': {'score': round(float(conf), 1), 'band': 'high' if conf >= 75 else 'medium' if conf >= 55 else 'low',
                           'support': top['support'], 'agreement': round(float(agree), 3), 'margin': round(float(top['support'] - second), 3),
                           'speakers': n_spk, 'clips': n, 'mean_clip_weight': round(mean_conf, 3), 'existing_match': gaz_match},
            'candidates': scored[:8], 'variants': variants, 'flags': flags, 'per_clip_best': best_texts}
