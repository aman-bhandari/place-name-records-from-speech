# Eknaam (एकनाम) — one authoritative name for every place

**UKIS 2026 · Problem P-015 · Survey of India, Department of Science and Technology**

Several recordings of different speakers saying a place name go in; one consensus record comes out: Devanagari,
Roman (Hunterian, with exceptions explained) and IPA, with confidence, competing spellings, evidence, linked
regional variants, and an officer review workspace with a hash-chained audit trail. Everything runs on one laptop
(RTX 3050, 6 GB); no paid API.

## Status at a glance (25 September 2026)

| | |
|---|---|
| **Solved** | 200 names (81 in Uttarakhand) with 1,059 real clips from 224 speakers, mined from open speech corpora rather than recorded by a few friends. Three witnesses per clip (two Hindi recognisers, one language-independent phone recogniser). Consensus that reconciles all clips instead of picking the clearest. Devanagari normaliser, rule-based IPA, documented Hunterian romaniser with an exception list. Decomposed confidence, capped when fewer than three speakers were heard. Officer workspace: replay, compare with the existing record, edit with live re-derivation, approve or hold or reject with reason, hash-chained audit, CSV export, upload of field recordings. 13 tests and a Playwright interface check pass. |
| **Measured** | Consensus 84.8% exact against 71.0% for a single clip and 92.9% for an oracle; the high-confidence band is 100% right; noise and clip-count sweeps in `docs/RESULTS.md`. |
| **Known gaps** | Garhwali and Kumaoni corpora (Vaani) have almost no transcripts, so true dialect variants are not yet shown; the variant mechanism exists (15 names carry one) but is fed by Hindi speakers' clusters. 105 names rest on one or two speakers and are flagged. No synthetic voices by decision (they would manufacture evidence). Audio is not in git: see "audio" below. |
| **Deferred (team to decide)** | Demo video (`docs/DEMO.md`), a hosted demo, hackathon registration. Whether to allow labelled synthetic filler voices. How to get Garhwali and Kumaoni speakers. |

Acceptance table against the definition of done: `docs/STATUS.md`. The plan: `docs/PLAN.md`. Romanisation rules:
`docs/ROMANISATION.md`. Problem statement as published: `docs/PROBLEM.md`.

## Run it on any machine

The committed `data/p015.sqlite` already holds all 200 names with their witnesses, consensus and evidence, so the
review workspace works minutes after cloning. Tested on Ubuntu under WSL2, 16 GB RAM, RTX 3050 6 GB.

| Need | Version / note |
|---|---|
| Python | 3.12 or newer (tested 3.14) |
| PyTorch | 2.14 (CUDA build for a GPU, CPU build otherwise). Serving and tests need no GPU |
| Node | 20 or newer (tested 24), to build the interface |
| GPU | Only for re-mining and re-building the store, and to make uploads fast; a CPU works but is slow |
| Disk | Under 100 MB to serve; the four recogniser models (~4 GB) download on first upload or build |
| Internet | pip and npm installs; model downloads on first upload or build; Hugging Face login only for re-mining |

### Quick start: about 5 minutes

```bash
git clone <this repo> && cd ukis-p015
python3 -m venv .venv && source .venv/bin/activate
pip install torch==2.14.0 --index-url https://download.pytorch.org/whl/cu130   # NVIDIA; or just: pip install torch==2.14.0
pip install -r requirements.txt
./run.sh ui              # build the interface into ui/dist
./run.sh serve           # http://127.0.0.1:8015
./run.sh test            # 13 tests
```

**Audio.** The clips (53 MB, 2,211 files) are published as a release asset on this repository rather than committed.
`./run.sh audio` fetches and unpacks them with the GitHub CLI so replay works in the workspace. Without them every
page still works; only the play buttons return nothing.

**Uploads.** "Add recordings" runs the three recognisers on the uploaded clips. The first upload downloads the
models from Hugging Face (about 4 GB); on a CPU expect a minute or so per clip.

### Rebuilding the store from the corpora

```bash
hf auth login                              # then accept the terms on the ai4bharat/Shrutilipi and ai4bharat/IndicVoices dataset pages
./run.sh mine                              # find gazetteer names in the transcripts, cut the clips; GPU; resumable
./run.sh build --rebuild                   # witnesses + consensus -> data/p015.sqlite (~3 min on the RTX 3050)
./run.sh eval --noise                      # docs/RESULTS numbers -> data/eval.json (~5 min)
./run.sh ui-check                          # Playwright page check (npm install && npx playwright install chromium first)
```

`data/clips.jsonl` records the exact corpus, shard and row of every clip, so the mined set is reproducible.

### What is committed, what is generated

| Committed | Not committed |
|---|---|
| Code, `data/p015.sqlite` (the full store), `data/clips.jsonl` (provenance of every clip), `data/targets_uk.yaml` (the gazetteer), `data/exceptions.yaml` (Roman exceptions with reasons), `data/eval.json`, docs, interface screenshots | `data/audio/` (release asset, see above), `data/cache/` (sentence audio for "in sentence" replay, from re-mining), `data/raw/`, the models (Hugging Face cache) |

## What it does

1. **Voices from open corpora, not a few friends.** Place names are found in the transcripts of AI4Bharat's Shrutilipi
   (All India Radio bulletins) and IndicVoices (citizens from many districts, with speaker ids), then cut out of the
   sentence by the Hindi recogniser's own emissions. Speakers without ids are told apart by WavLM voice embeddings.
2. **Three witnesses per clip.** Two Hindi CTC recognisers (vakyansh, ai4bharat/indicwav2vec-hindi) write Devanagari;
   a language-independent phone recogniser (wav2vec2-xlsr-53-espeak) writes what it heard.
3. **Reconcile, don't pick.** Candidate spellings (every witness, a column vote, the existing record, gazetteer names
   that sound close) are scored by how well their pronunciation explains *all* clips, weighted by clip quality, with a
   phonetic-feature edit distance (retroflex/dental and aspiration confusions cost less than unrelated sounds).
4. **Rules you can read.** Devanagari normaliser (nukta, anusvara/chandrabindu, halant), rule-based IPA with schwa
   deletion, Hunterian romaniser with a documented exception list: `docs/ROMANISATION.md`.
5. **Confidence decomposed**: spelling explains clips · clips agree · lead over runner-up · speakers · clip quality;
   capped when fewer than three real speakers were heard. Minority spellings backed by two or more speakers stay as linked variants.
6. **Officer workspace**: replay each clip and its source sentence, see every witness, compare with the existing
   record, edit any field (IPA and Roman re-derive live), approve / hold / reject with reason, hash-chained audit,
   CSV export of approved records, upload of field recordings.

## Repository map

| Path | What it is |
|---|---|
| `p015/` | The engine: `deva.py` normaliser · `phon.py` IPA · `roman.py` Hunterian · `consensus.py` reconciliation · `witness.py` CTC models · `align.py` name cutting · `speaker.py` voice embeddings · `hfparquet.py` parallel remote parquet reads · `gazetteer.py` · `mine.py` · `build.py` · `store.py` SQLite and audit chain |
| `api/main.py` | FastAPI: queue, cases, clips and audio, decisions, audit, export, upload; serves `ui/dist` |
| `ui/` | React + Vite + Tailwind interface; `ui/check/ui_check.cjs` the Playwright page check |
| `eval/consensus_eval.py` | Consensus vs single clip vs oracle, noise sweep, calibration |
| `spikes/` | The gate experiments that chose the models and proved the mining yield (kept for the record) |
| `tests/` | Phonology, consensus, API and audit-chain tests |
| `docs/` | STATUS, PLAN, PROBLEM, ROMANISATION, RESULTS, DEMO |

## Data and licences

Shrutilipi and IndicVoices: CC BY 4.0 (AI4Bharat); Lingua Libre clips: CC BY-SA (Wikimedia Commons); gazetteer:
Wikidata (CC0). Models: vakyansh-wav2vec2-hindi (Apache-2.0), ai4bharat/indicwav2vec-hindi (gated, terms accepted),
facebook/wav2vec2-xlsr-53-espeak-cv-ft (Apache-2.0), microsoft/wavlm-base-plus-sv (MIT). All code in `p015/`,
`api/`, `ui/src/`, `eval/` and `tests/` is original to this entry.

## Limits (honest)

- Names are only as good as the recognisers on short words; the acoustic-only number in RESULTS is the fair one.
- Shrutilipi readers are few per region, so some Uttarakhand names have one or two distinct speakers and are flagged.
- Garhwali and Kumaoni corpora (Vaani) have almost no transcripts, so regional variants come from Hindi speakers' clusters.
- No synthetic voices: they would manufacture evidence from the record. Sparse names are flagged, not padded.
