"""CTC forced alignment (Viterbi over the blank-extended label sequence) and cutting a span out of a sentence."""
import numpy as np
from .witness import FRAME
def force_align(logp, tokens, blank):
    """logp [T,V] log-probs, tokens list[int]. Returns per-token (start_frame, end_frame_inclusive) and path score."""
    T, L = logp.shape[0], len(tokens)
    if L == 0: return [], 0.0
    ext = [blank] * (2 * L + 1); ext[1::2] = tokens; S = len(ext)
    NEG = -1e30; dp = np.full((T, S), NEG, dtype=np.float32); bp = np.zeros((T, S), dtype=np.int8)
    dp[0, 0] = logp[0, ext[0]]; dp[0, 1] = logp[0, ext[1]]
    same = np.array([s >= 2 and ext[s] != blank and ext[s] != ext[s - 2] for s in range(S)])
    for t in range(1, T):
        prev = dp[t - 1]
        c0 = prev; c1 = np.concatenate(([NEG], prev[:-1])); c2 = np.where(same, np.concatenate(([NEG, NEG], prev[:-2])), NEG)
        stack = np.stack([c0, c1, c2]); k = stack.argmax(0); dp[t] = stack[k, np.arange(S)] + logp[t, ext]; bp[t] = k
    s = S - 1 if dp[T - 1, S - 1] >= dp[T - 1, S - 2] else S - 2; score = float(dp[T - 1, s]); states = np.zeros(T, dtype=int)
    s = int(s)
    for t in range(T - 1, -1, -1):
        states[t] = s
        if t: s -= int(bp[t, s])
    spans = []
    for k in range(L):
        fr = np.where(states == 2 * k + 1)[0]
        spans.append((int(fr[0]), int(fr[-1])) if len(fr) else (spans[-1][1] if spans else 0,) * 2)
    return spans, score / T
def cut_span(wav, witness, text, start, end, margin_s=0.04):
    """Cut text[start:end] out of wav using forced alignment with the given CTC witness.
    Returns (clip, info) or (None, info) if the span has no alignable tokens."""
    logp = witness.emissions(wav); ids, pos = witness.tokens(text)
    spans, score = force_align(logp, ids, witness.blank)
    idx = [k for k, p in enumerate(pos) if start <= p < end and ids[k] != witness.delim]
    if not idx: return None, {'error': 'no tokens'}
    f0, f1 = spans[idx[0]][0], spans[idx[-1]][1]
    a = max(0, int(f0 * FRAME - margin_s * 16000)); b = min(len(wav), int((f1 + 1) * FRAME + margin_s * 16000))
    return wav[a:b], {'start_s': a / 16000, 'end_s': b / 16000, 'align_score': score, 'frames': (f0, f1)}

def greedy_frames(logp, witness):
    """Greedy CTC decode with the frame index of every emitted token: [(char, frame)] where char is ' ' for '|'."""
    ids = logp.argmax(-1); out, prev = [], -1
    for t, i in enumerate(ids):
        if i != prev and i != witness.blank:
            tok = witness.inv.get(int(i), '')
            if tok and not tok.startswith('<'): out.append((' ' if tok == '|' else tok, t))
        prev = i
    return out
def locate(emitted, name):
    """Best-matching window of the emitted char sequence for `name` (min edit distance, then shortest); returns (i, j) token index range inclusive or None."""
    chars = [c for c, _ in emitted]; s = ''.join(chars); target = name.replace(' ', '')
    if not s: return None
    n, m = len(s), len(target); best = None
    # DP: edit distance of target against any substring of s (free start), standard approximate matching
    D = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1): D[i][0] = i
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            c = 0 if target[i - 1] == s[j - 1] else 1
            D[i][j] = min(D[i - 1][j] + 1, D[i][j - 1] + (0 if s[j - 1] == ' ' else 1), D[i - 1][j - 1] + c)
    end = min(range(n + 1), key=lambda j: (D[m][j], j)); dist = D[m][end]
    if end == 0: return None
    # backtrack to find the start
    i, j = m, end
    while i > 0 and j > 0:
        c = 0 if target[i - 1] == s[j - 1] else 1
        if D[i][j] == D[i - 1][j - 1] + c: i -= 1; j -= 1
        elif D[i][j] == D[i][j - 1] + (0 if s[j - 1] == ' ' else 1): j -= 1
        else: i -= 1
    start = j
    # trim spaces at the edges
    while start < end and s[start] == ' ': start += 1
    while end - 1 > start and s[end - 1] == ' ': end -= 1
    return (start, end - 1, dist / max(1, m))
def _rms(wav, f, win=FRAME):
    a = max(0, f * FRAME - win // 2); seg = wav[a:a + win]; return float(np.sqrt(np.mean(seg ** 2)) + 1e-9) if len(seg) else 1e-9
def _min_energy_frame(wav, lo, hi):
    lo, hi = max(0, lo), max(lo, hi)
    if hi <= lo: return lo
    return min(range(lo, hi + 1), key=lambda f: _rms(wav, f))
def cut_name(wav, witness, name, logp=None, pre_s=0.05, post_s=0.03):
    """Cut `name` out of `wav` using the witness's own greedy emissions. CTC spikes lag the acoustics, so the
    boundaries are refined to the lowest-energy frame between the name's edge spikes and the neighbouring tokens'
    spikes, then padded a little."""
    logp = witness.emissions(wav) if logp is None else logp
    em = greedy_frames(logp, witness); loc = locate(em, name)
    if loc is None: return None, {'error': 'name not heard in sentence'}
    i, j, dist = loc; T = logp.shape[0]
    f0, f1 = em[i][1], em[j][1]
    prev_f = em[i - 1][1] if i > 0 else max(0, f0 - 12); next_f = em[j + 1][1] if j + 1 < len(em) else min(T - 1, f1 + 12)
    a_f = _min_energy_frame(wav, max(prev_f, f0 - 14), max(prev_f, f0 - 2))
    b_f = _min_energy_frame(wav, f1 + 1, max(f1 + 1, min(next_f, f1 + 12)))
    a = max(0, int(a_f * FRAME - pre_s * 16000)); b = min(len(wav), int(b_f * FRAME + post_s * 16000))
    return wav[a:b], {'start_s': a / 16000, 'end_s': b / 16000, 'heard': ''.join(c for c, _ in em[i:j + 1]), 'locate_dist': dist, 'frames': (int(f0), int(f1))}
