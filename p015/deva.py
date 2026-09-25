"""Devanagari normaliser for Hindi place names.

Policy (documented in docs/ROMANISATION.md):
* Unicode NFC; precomposed nukta letters (क़ ख़ ग़ ज़ ड़ ढ़ फ़) become base + nukta (U+093C); ZWJ/ZWNJ removed.
* Nasal before a stop consonant is written with anusvara (ं), not the class nasal + halant (चण्डीगढ़ → चंडीगढ़),
  following the Central Hindi Directorate standard orthography (मानक हिंदी वर्तनी).
* A nasalised vowel takes chandrabindu (ँ) when the vowel sign leaves the top clear (ा ि ु ू ृ or none),
  and anusvara when the sign occupies the top line (ि ी े ै ो ौ), as in standard print.
* Halant (्) is kept wherever it is written; conjuncts are not expanded.
* Retroflex / dental and aspirated / plain letters are never changed: they are meaning-bearing in names.
"""
import unicodedata, re
STOPS = {  # consonant → class nasal for anusvara expansion, per varga
    'क': 'ङ', 'ख': 'ङ', 'ग': 'ङ', 'घ': 'ङ', 'च': 'ञ', 'छ': 'ञ', 'ज': 'ञ', 'झ': 'ञ',
    'ट': 'ण', 'ठ': 'ण', 'ड': 'ण', 'ढ': 'ण', 'त': 'न', 'थ': 'न', 'द': 'न', 'ध': 'न', 'प': 'म', 'फ': 'म', 'ब': 'म', 'भ': 'म'}
CLASS_NASALS = {'ङ', 'ञ', 'ण', 'न', 'म'}
TOP_SIGNS = set('िीेैोौॅॉ')
CONSONANTS = set('कखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसहळ')
VOWELS = set('अआइईउऊऋएऐओऔऑऍ'); SIGNS = set('ािीुूृेैोौॅॉ')
VIRAMA, NUKTA, ANUSVARA, CHANDRABINDU = '्', '़', 'ं', 'ँ'
def normalise(s):
    s = unicodedata.normalize('NFC', s or '').replace('‍', '').replace('‌', '').strip()
    s = re.sub(r'\s+', ' ', s)
    out = list(s)
    # class nasal + virama + same-class stop → anusvara
    i = 0
    while i < len(out) - 2:
        if out[i] in CLASS_NASALS and out[i + 1] == VIRAMA and out[i + 2] in STOPS and STOPS[out[i + 2]] == out[i]:
            out[i:i + 2] = [ANUSVARA]
        i += 1
    # chandrabindu / anusvara by top-line rule (only where it marks a nasalised vowel, i.e. not before a stop)
    for i, ch in enumerate(out):
        if ch in (ANUSVARA, CHANDRABINDU):
            nxt = out[i + 1] if i + 1 < len(out) else ''
            before_stop = nxt in STOPS or nxt in CLASS_NASALS
            if before_stop: out[i] = ANUSVARA; continue
            prev = out[i - 1] if i else ''
            out[i] = ANUSVARA if prev in TOP_SIGNS else CHANDRABINDU
    return ''.join(out)
def match_key(s):
    """Coarse key for comparing candidate spellings: merges nasal notations, ऋ/रि, श/ष, ambiguous vowel length marks."""
    s = normalise(s)
    for a, b in [('ँ', 'ं'), ('ऋ', 'रि'), ('ृ', '्रि'), ('ष', 'श'), ('ॉ', 'ो'), ('ॅ', 'े'), (' ', '')]: s = s.replace(a, b)
    return s
def split(s):
    """Tokenise a normalised string into units: consonant(+nukta), vowel, sign, virama, anusvara, chandrabindu, space."""
    units, i = [], 0
    while i < len(s):
        ch = s[i]
        if ch in CONSONANTS and i + 1 < len(s) and s[i + 1] == NUKTA: units.append(ch + NUKTA); i += 2; continue
        units.append(ch); i += 1
    return units
