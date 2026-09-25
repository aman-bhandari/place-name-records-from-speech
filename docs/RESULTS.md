# Results — Eknaam (P-015), measured 25 Sep 2026

Store: **200 names** (81 Uttarakhand, 119 all-India towns/districts), **1,059 real clips** chosen from 1,949 mined
(≤8 per name, speaker-diverse), **224 distinct speakers** (IndicVoices ids + WavLM voice clusters for AIR readers).
Evaluation set: the 197 names with ≥3 real clips (5.35 clips, 3.3 speakers per name). Truth = the gazetteer/curated
Devanagari spelling the clips were mined for; match ignores nasal notation, spacing and ऋ/रि. `eval/consensus_eval.py`.

## Reconciling beats picking (AC2)
| Method | Exact spelling |
|---|---|
| One random clip | 71.0% |
| The clearest clip (highest witness confidence × quality) | 74.6% |
| **Consensus, acoustic evidence only** | **84.8%** |
| Consensus + existing record and gazetteer as candidates | 84.8% |
| Oracle: any single clip right | 92.9% |
Consensus is **+13.8 points** over a random clip and +10.2 over the clearest clip (bar: +10).

## More speakers, better spelling (acoustic only, random subsets, 3 draws per name)
| clips | 1 | 2 | 3 | 4 | 6 | 8 |
|---|---|---|---|---|---|---|
| exact | 59.6% | 77.3% | 82.7% | 82.8% | 91.0% | 92.5% |

## Confidence is calibrated
| band | names | exact |
|---|---|---|
| high (≥75) | 54 | 100% |
| medium (55–74) | 69 | 87.0% |
| low (<55) | 74 | 71.6% |
Low is mostly the speaker cap: a name heard from one reader can score at most 54, two readers 70.

## Noise (AC6): white noise added to every clip, 40 names, acoustic only
| clean | 20 dB SNR | 10 dB | 5 dB |
|---|---|---|---|
| 75.0% | 72.5% | 57.5% | 35.0% |

## Other counts
Names flagged "speakers disagree": 58 · flagged "needs more recordings" (<3 speakers): 105 · with a linked regional
variant (≥2 speakers on a different spelling): 15.

## Gate results that shaped the design
* Whisper-large-v3-turbo on 1-word clips: CER 50.6% (hallucinates) → rejected. vakyansh CTC 17.3% / indicwav2vec 22.1%.
* Consensus of 3 Lingua Libre speakers on common words: vakyansh CER 17.3% → 6.9%, exact 68.6% → 82.4%.
* Forced alignment misplaced 57% of name spans; locating the name in the recogniser's own emissions and taking the
  hypothesis *in sentence context* raised blind consensus from 9/18 to 12/18 names on the gate sample.
* xlsr-53-espeak phones: speakers agree on 60% of phones; no retroflex/aspiration → shown as evidence, not scored.

## Known misses (honest)
कोटद्वार → कोरद्वार (ट/र), जोशीमठ → जोशीम (final ठ lost in cuts), पिथौरागढ़ → पिथोरागढ़ (ौ/ो: readers say it that way),
अल्मोड़ा → अलमोड़ा (halant is orthographic, not audible). The existing record is shown beside each so an officer sees it.
