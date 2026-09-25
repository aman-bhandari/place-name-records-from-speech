"""Devanagari → Hindi phoneme sequence (IPA symbols) with schwa deletion, anusvara resolution and nasalisation."""
from . import deva
C = {'क': 'k', 'ख': 'kʰ', 'ग': 'ɡ', 'घ': 'ɡʱ', 'ङ': 'ŋ', 'च': 't͡ʃ', 'छ': 't͡ʃʰ', 'ज': 'd͡ʒ', 'झ': 'd͡ʒʱ', 'ञ': 'ɲ',
     'ट': 'ʈ', 'ठ': 'ʈʰ', 'ड': 'ɖ', 'ढ': 'ɖʱ', 'ण': 'ɳ', 'त': 't̪', 'थ': 't̪ʰ', 'द': 'd̪', 'ध': 'd̪ʱ', 'न': 'n',
     'प': 'p', 'फ': 'pʰ', 'ब': 'b', 'भ': 'bʱ', 'म': 'm', 'य': 'j', 'र': 'r', 'ल': 'l', 'व': 'ʋ', 'श': 'ʃ', 'ष': 'ʂ', 'स': 's', 'ह': 'ɦ', 'ळ': 'ɭ',
     'क़': 'q', 'ख़': 'x', 'ग़': 'ɣ', 'ज़': 'z', 'ड़': 'ɽ', 'ढ़': 'ɽʱ', 'फ़': 'f', 'ऩ': 'n', 'ऱ': 'r', 'य़': 'j'}
V = {'अ': 'ə', 'आ': 'aː', 'इ': 'ɪ', 'ई': 'iː', 'उ': 'ʊ', 'ऊ': 'uː', 'ऋ': 'rɪ', 'ए': 'eː', 'ऐ': 'ɛː', 'ओ': 'oː', 'औ': 'ɔː', 'ऑ': 'ɔ', 'ऍ': 'æ'}
S = {'ा': 'aː', 'ि': 'ɪ', 'ी': 'iː', 'ु': 'ʊ', 'ू': 'uː', 'ृ': 'rɪ', 'े': 'eː', 'ै': 'ɛː', 'ो': 'oː', 'ौ': 'ɔː', 'ॉ': 'ɔ', 'ॅ': 'æ'}
VOWEL_PH = set(V.values()) | set(S.values()) | {'ə'}
NASAL_OF = {'k': 'ŋ', 'kʰ': 'ŋ', 'ɡ': 'ŋ', 'ɡʱ': 'ŋ', 't͡ʃ': 'ɲ', 't͡ʃʰ': 'ɲ', 'd͡ʒ': 'ɲ', 'd͡ʒʱ': 'ɲ', 'ʈ': 'ɳ', 'ʈʰ': 'ɳ', 'ɖ': 'ɳ', 'ɖʱ': 'ɳ',
            't̪': 'n', 't̪ʰ': 'n', 'd̪': 'n', 'd̪ʱ': 'n', 'p': 'm', 'pʰ': 'm', 'b': 'm', 'bʱ': 'm'}
def is_vowel(p): return p.rstrip('̃') in VOWEL_PH
def letters_to_phones(word):
    """First pass: letter-by-letter with inherent schwa marked as 'ə?' (deletable) ; nasals resolved."""
    units = deva.split(word); out = []
    for i, u in enumerate(units):
        nxt = units[i + 1] if i + 1 < len(units) else ''
        if u in C:
            out.append(C[u])
            if nxt not in deva.SIGNS and nxt != deva.VIRAMA: out.append('ə?')
        elif u in V: out.append(V[u])
        elif u in S:
            if out and out[-1] == 'ə?': out.pop()
            out.append(S[u])
        elif u == deva.VIRAMA:
            if out and out[-1] == 'ə?': out.pop()
        elif u in (deva.ANUSVARA, deva.CHANDRABINDU):
            if out and out[-1] == 'ə?': out[-1] = 'ə'  # a nasalised inherent vowel is real, keep it
            nxt_ph = C.get(nxt)
            if u == deva.ANUSVARA and nxt_ph in NASAL_OF: out.append(NASAL_OF[nxt_ph])
            elif out and is_vowel(out[-1]): out[-1] = out[-1] + '̃'
            else: out.append('n')
        elif u == 'ः': out.append('ɦ')
    return out
def schwa_delete(ph):
    """Hindi schwa deletion (Ohala 1983 style): a deletable schwa is dropped in V C _ C V, applied right to left;
    word-final deletable schwa is always dropped; a schwa is never dropped if that would leave a consonant cluster
    with no vowel in the word."""
    ph = list(ph)
    if ph and ph[-1] == 'ə?': ph.pop()
    for i in range(len(ph) - 1, -1, -1):
        if ph[i] != 'ə?': continue
        prev_c = i >= 1 and not is_vowel(ph[i - 1]) and ph[i - 1] != 'ə?'
        prev_v = i >= 2 and (is_vowel(ph[i - 2]) or ph[i - 2] == 'ə?')
        next_c = i + 1 < len(ph) and not is_vowel(ph[i + 1]) and ph[i + 1] != 'ə?'
        next_v = i + 2 < len(ph) and (is_vowel(ph[i + 2]) or ph[i + 2] == 'ə?')
        # C + glide/liquid onset cluster before a vowel also licenses deletion (कोटद्वार → koːʈd̪ʋaːr, देवप्रयाग → d̪eːʋprəjaːɡ)
        cluster_v = i + 3 < len(ph) and ph[i + 2] in ('ʋ', 'r', 'j', 'l') and (is_vowel(ph[i + 3]) or ph[i + 3] == 'ə?')
        if prev_c and prev_v and next_c and (next_v or cluster_v): ph.pop(i)
    return [p if p != 'ə?' else 'ə' for p in ph]
def phonemes(name):
    """Phoneme list for a (possibly multi-word) Devanagari name; words separated by ' '."""
    out = []
    for w in deva.normalise(name).split(' '):
        if out: out.append(' ')
        out += schwa_delete(letters_to_phones(w))
    return out
def ipa(name, slashes=True):
    s = ''.join(phonemes(name)); return f'/{s}/' if slashes else s
