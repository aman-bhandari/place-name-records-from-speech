"""Hunterian romanisation of Hindi place names, from the phoneme sequence (so schwa deletion is applied), with a
documented exception list for established historical forms. Two renderings: plain (Survey of India map style, no
diacritics) and diacritic (ā ī ū ṭ ḍ ṇ ṛ ṅ ñ ś ṣ)."""
import pathlib, yaml
from . import phon
ROOT = pathlib.Path(__file__).resolve().parents[1]
H = {'k': ('k', 'k'), 'kʰ': ('kh', 'kh'), 'ɡ': ('g', 'g'), 'ɡʱ': ('gh', 'gh'), 'ŋ': ('n', 'ṅ'), 't͡ʃ': ('ch', 'ch'), 't͡ʃʰ': ('chh', 'chh'),
     'd͡ʒ': ('j', 'j'), 'd͡ʒʱ': ('jh', 'jh'), 'ɲ': ('n', 'ñ'), 'ʈ': ('t', 'ṭ'), 'ʈʰ': ('th', 'ṭh'), 'ɖ': ('d', 'ḍ'), 'ɖʱ': ('dh', 'ḍh'), 'ɳ': ('n', 'ṇ'),
     't̪': ('t', 't'), 't̪ʰ': ('th', 'th'), 'd̪': ('d', 'd'), 'd̪ʱ': ('dh', 'dh'), 'n': ('n', 'n'), 'p': ('p', 'p'), 'pʰ': ('ph', 'ph'), 'b': ('b', 'b'),
     'bʱ': ('bh', 'bh'), 'm': ('m', 'm'), 'j': ('y', 'y'), 'r': ('r', 'r'), 'l': ('l', 'l'), 'ʋ': ('w', 'w'), 'ʃ': ('sh', 'ś'), 'ʂ': ('sh', 'ṣ'),
     's': ('s', 's'), 'ɦ': ('h', 'h'), 'ɭ': ('l', 'ḷ'), 'q': ('q', 'q'), 'x': ('kh', 'kh'), 'ɣ': ('gh', 'gh'), 'z': ('z', 'z'), 'ɽ': ('r', 'ṛ'), 'ɽʱ': ('rh', 'ṛh'), 'f': ('f', 'f'),
     'ə': ('a', 'a'), 'aː': ('a', 'ā'), 'ɪ': ('i', 'i'), 'iː': ('i', 'ī'), 'ʊ': ('u', 'u'), 'uː': ('u', 'ū'), 'rɪ': ('ri', 'ri'), 'eː': ('e', 'e'),
     'ɛː': ('ai', 'ai'), 'oː': ('o', 'o'), 'ɔː': ('au', 'au'), 'ɔ': ('o', 'o'), 'æ': ('a', 'a'), ' ': (' ', ' ')}
_exc = None
def exceptions():
    global _exc
    if _exc is None:
        p = ROOT / 'data/exceptions.yaml'; _exc = yaml.safe_load(open(p)) if p.exists() else {}
    return _exc
def from_phonemes(ph, diacritics=False):
    out = []
    for p in ph:
        nasal = p.endswith('̃'); base = p.rstrip('̃')
        r = H.get(base, ('?', '?'))[1 if diacritics else 0]; out.append(r + ('n' if nasal else ''))
    s = ''.join(out)
    # capitalise each word
    return ' '.join(w[:1].upper() + w[1:] for w in s.split(' '))
def romanise(name, existing_en=None):
    """Return dict: scheme (plain Hunterian), scheme_diacritic, recommended, kind, reason."""
    ph = phon.phonemes(name); plain = from_phonemes(ph); dia = from_phonemes(ph, True)
    exc = exceptions().get(name)
    rec = {'scheme': plain, 'scheme_diacritic': dia, 'recommended': plain, 'kind': 'scheme', 'reason': 'Hunterian rendering of the consensus pronunciation'}
    if exc:
        rec.update(recommended=exc['form'], kind='established', reason=exc['reason'])
    elif existing_en and existing_en.strip() and existing_en.replace(' ', '').lower() != plain.replace(' ', '').lower():
        rec.update(recommended=existing_en.strip(), kind='established', reason=f'existing record uses "{existing_en.strip()}"; scheme would give "{plain}" — officer to confirm which stands')
    return rec
