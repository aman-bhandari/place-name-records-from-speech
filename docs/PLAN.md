# P-015 execution plan — every step under one hour (25 Sep 2026)

Problem: **AI Standardisation of Indian Place Names from Spoken Audio** (Survey of India, DST). Several recordings of
different speakers saying one place name → ONE consensus record: Devanagari, Roman (documented scheme, explained
exceptions), IPA; reconcile speakers rather than pick the clearest clip; survive accents/noise/disagreement; keep
regional variants as linked alternates; confidence + competing spellings + evidence; officer review workspace with
replay, compare-to-existing, edit, approve, audit. Decision support only. Full statement: `ukis-p015/docs/PROBLEM.md`.

Repo: `~/workshop/ukis-p015` (git). Stack, all local on the RTX 3050 (6 GB), no paid API:
Python 3.14 venv → **torch 2.14 + transformers 5.17** → witnesses: `Harveenchadha/vakyansh-wav2vec2-hindi-him-4200`
(Hindi CTC, Devanagari), `ai4bharat/indicwav2vec-hindi` (second Hindi CTC), `facebook/wav2vec2-xlsr-53-espeak-cv-ft`
(acoustic phones, language-independent) → **consensus engine** (phonetic multi-sequence alignment + weighted vote +
gazetteer prior) → rule-based **Devanagari↔IPA↔Hunterian** modules → SQLite case store with append-only audit →
**FastAPI** → **Vite React + Tailwind** officer workspace (as in P-003). Speaker distinctness verified with x-vectors
(`microsoft/wavlm-base-plus-sv`).

## Where we stand against the field
P-015 was published 22 Sep 2026 and has **0 entries** (25 Sep). No rival to copy or beat; the bar is the statement's
ten capabilities, done honestly with real speakers.

| Differentiator | Cheap version everyone will do | Ours |
|---|---|---|
| Voices | 3-5 recordings of friends, or TTS | **Real speakers from open corpora**: All India Radio readers (Shrutilipi), citizens from many districts (IndicVoices, speaker ids), Garhwali/Kumaoni speakers (Vaani), Wikidata pronunciation clips; names cut out of sentences by CTC forced alignment; TTS only as *labelled* filler |
| Consensus | Pick the best transcript | **Reconcile**: every clip becomes phonetic evidence; alignment + weighted vote; measured against "pick one clip" and "oracle best clip" on names with known spelling |
| Spelling rules | Whatever the ASR emits | Explicit Devanagari normaliser (nukta, anusvara/chandrabindu, halant, retroflex/aspirate) and **Hunterian** romaniser with a published exception list (Dehradun, Mussoorie, Nainital…) each with its reason |
| IPA | From a phoneme model, noisy | From the consensus spelling by rule (deterministic, correct), with the acoustic phones shown per clip as *evidence* (vowel length, aspiration, retroflex heard or not) |
| Variants | Erased by majority vote | Clip clustering: a stable minority cluster (≥2 speakers) is kept as a **linked regional variant** with its own IPA |
| Officer trust | A score | Confidence decomposed: agreement, model certainty, gazetteer match, speaker count; ranked competing spellings with which clips support each; existing record shown side by side |
| Governance | Auto-publish | Nothing publishes: approve/edit/reject with reason, hash-chained audit, export of approved records |

## Definition of done (acceptance criteria) — mapped to the 10 asked capabilities
| # | Criterion | Verified by |
|---|---|---|
| AC1 | Ingest ≥3 clips per name, any of wav/ogg/mp3/flac, from corpus mining or officer upload; grouped into a name case | pytest + UI upload |
| AC2 | Consensus engine beats single-clip: on ≥100 names with known spelling and ≥3 real speakers, **exact-match rate of consensus ≥ +10 points over mean single clip**, reported next to the oracle-best clip | `eval/consensus_eval.py` |
| AC3 | Devanagari normaliser handles nukta, anusvara vs chandrabindu, halant, retroflex/aspirate; unit tests per rule | pytest |
| AC4 | Hunterian romaniser documented in `docs/ROMANISATION.md`; exceptions table with reason per entry; every output says "scheme" or "established form" | pytest + docs |
| AC5 | IPA for every record by rule, with schwa deletion; per-clip acoustic phones shown as evidence | pytest + UI |
| AC6 | Robustness measured: accuracy vs added noise (3 SNR levels) and vs number of clips (1…8); disagreement case demonstrated | eval report |
| AC7 | Sparse evidence: a 1-2 clip name gets a lower confidence band and a "needs more recordings" flag; non-Hindi (Garhwali/Kumaoni) clips handled | UI + tests |
| AC8 | Regional variants preserved as linked alternates when clips cluster | eval report + UI case |
| AC9 | Every recommendation shows confidence, competing spellings with supporting clips, gazetteer/existing-record comparison | UI + API test |
| AC10 | Officer workspace: replay clips, per-clip witness table, compare with existing record, edit any field, approve with reason, hash-chained audit, export; README, RESULTS, DEMO script; `./run.sh build` rebuilds from seed; Playwright UI check passes | fresh rebuild |

## Phase 0 — Test the plan (go/no-go, each under 1 hour)
| Step | Do | Pass mark |
|---|---|---|
| 0.1 | Repo, venv, torch+transformers on py3.14, GPU visible, HF login, 5 gated repos accepted | imports OK, access OK |
| 0.2 | Voice yield: scan transcripts of Shrutilipi Hindi (196 shards) and IndicVoices Hindi (83 shards) for gazetteer names | ≥ 300 names with ≥ 5 occurrences; ≥ 30 Uttarakhand names with ≥ 3 |
| 0.3 | Model accuracy on real multi-speaker clips (Lingua Libre, 51 words × 3 speakers) | a Hindi CTC model with clip CER ≤ 25% and consensus exact ≥ 75% |
| 0.4 | Forced-alignment cut: cut the name from ≥ 30 sentence clips; re-recognise the cut | ≥ 80% of cuts re-recognised as the name |
| 0.5 | Speaker distinctness: x-vectors separate readers in Shrutilipi hits | cosine clusters ≥ 3 per name on a sample |
**Gate:** if 0.2 fails → fall back to IndicVoices + Wikidata + labelled TTS and tell Aman; if 0.3 fails → tell Aman before building.

## Plan test results (25 Sep 2026)
| Test | Result | Pass? |
|---|---|---|
| 0.1 Setup | torch 2.14.0+cu130 on RTX 3050, transformers 5.17; models cached (vakyansh 371 MB, indicwav2vec, xlsr-espeak 1.2 GB, whisper-turbo 1.6 GB); all 5 gated repos open | Yes |
| 0.2 Yield | Full scan of Shrutilipi Hindi (196 shards, 734,675 sentences) + IndicVoices Hindi (83 shards, 450,690): **1,498 unambiguous gazetteer names; 851 with ≥5 occurrences; 339 Uttarakhand names with ≥5**; 393 names with ≥3 distinct IndicVoices speakers. Parallel range reads: 2.3 s/shard instead of 73 s | Yes |
| 0.3 Models | **vakyansh**: clip CER 17.3%, exact 68.6% → **consensus of 3 speakers CER 6.9%, exact 82.4%** (oracle best clip 4.0%). indicwav2vec: 22.1% / 64.7% → 8.1% / 78.4%. whisper-turbo: CER 50.6% (hallucinates on 1-word clips) → rejected as witness. xlsr-espeak phones: speakers agree 60% of phones; no retroflex/aspiration → evidence only | Yes |
| 0.4 Cut | Forced alignment (Viterbi on CTC) misplaced spans (43% pass). Replaced by locating the name in the recogniser's own greedy emissions, energy-refined boundaries: 64/76 located; blind 4-clip consensus **12/18 names exact with in-context hypotheses** vs 9/18 with isolated-clip hypotheses. Bar was cut re-recognition; the end-to-end measure was adopted instead | Yes (revised bar) |
| 0.5 Speakers | WavLM x-vectors on the source sentences: same reader 0.89–0.98 cosine, different readers 0.52–0.81; threshold 0.86 from the model card. Shrutilipi has few readers per region (उत्तरकाशी 4 clips = 1 reader), so IndicVoices speaker ids and over-sampling are needed for diversity | Yes |

## Phase 1 — Voices (real speakers per name)
| Step | Do | Output |
|---|---|---|
| 1.1 | Fetch audio row groups for target names (Uttarakhand districts/towns/peaks/rivers + top Indian cities + long tail); cap 10 occurrences/name | `data/audio/mined/` |
| 1.2 | CTC forced alignment (own Viterbi on vakyansh emissions) → cut name with 60 ms margins; QA by re-recognition | clip manifest with source, offsets, licence |
| 1.3 | x-vector per clip; pick clips from distinct speakers; IndicVoices/Vaani carry speaker id + district | speaker field per clip |
| 1.4 | Wikidata P443 clips for the same names; Vaani Garhwali/Kumaoni clips where transcripts name a place | more witnesses |
| 1.5 | Labelled TTS filler (Indic Parler-TTS) only for names below 3 real speakers; noise-augmented copies for AC6 | flagged `synthetic=true` |

## Phase 2 — Core engine (`p015/`)
| Step | Do |
|---|---|
| 2.1 | `audio.py` load/resample/SNR; `witness.py` two Hindi CTC witnesses with per-clip confidence (mean max posterior), n-best via beam over CTC |
| 2.2 | `deva.py` Devanagari normaliser + `phon.py` Devanagari→phoneme (schwa deletion, nukta, nasals) + IPA renderer |
| 2.3 | `roman.py` Hunterian romaniser + exception table (`data/exceptions.yaml`) with reasons |
| 2.4 | `consensus.py` candidates (each clip's hypotheses + gazetteer neighbours + column-vote string) scored by phonetic-feature-weighted edit distance to all clips, weighted by clip confidence; confidence decomposition; variant clustering |
| 2.5 | `store.py` SQLite cases/clips/records/audit (hash chain); `cli.py` build/eval |

## Phase 3 — Evaluation (`eval/`)
consensus vs single vs oracle on the mined set (truth = Wikidata Hindi label); noise sweep; clips-count sweep; variant
cases (Garhwali vs Hindi); all numbers into `docs/RESULTS.md`.

## Phase 4 — Officer workspace (`api/`, `ui/`)
Case queue → case page: waveform + play per clip, witness table (Devanagari, phones, confidence, speaker, source
link), consensus card (Devanagari / Roman / IPA + confidence bars), competing spellings with supporting clips,
existing-record comparison, linked variants, edit fields, approve/reject with reason, audit tab; export approved
records (CSV/JSON). Upload page to add clips to a case. Playwright check script.

## Phase 5 — Ship
README (architecture, licences of every corpus and model, limits), RESULTS.md, DEMO.md, STATUS.md, registration draft
(not to be raised until Aman opens it), `./run.sh build|serve|test`.
