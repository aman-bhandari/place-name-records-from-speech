# Eknaam (एकनाम): place-name records from spoken audio

Problem: Survey of India needs one authoritative spelling of each place name in Devanagari, Roman and IPA, reconciled from how different speakers say it rather than copied from the clearest recording, with the evidence kept for an officer to review.

Several speakers' recordings of one place name go in; one record comes out: Devanagari, Roman (Hunterian, with a
documented exception list), IPA, confidence, competing spellings, linked regional variants and per-clip evidence.
Officers review, edit, approve and export; every action goes into a hash-chained audit log. Runs on one laptop
(RTX 3050, 6 GB); no paid API.

## What is in this repository

| Path | Contents |
|---|---|
| `p015/mine.py` | Finds gazetteer names in the transcripts of Shrutilipi (All India Radio bulletins) and IndicVoices, cuts the clips |
| `p015/witness.py` | Two Hindi CTC recognisers (vakyansh, ai4bharat/indicwav2vec-hindi) and a phone recogniser (wav2vec2-xlsr-53-espeak) |
| `p015/align.py`, `p015/speaker.py` | Name cutting from recogniser emissions; WavLM speaker embeddings for speakers without ids |
| `p015/consensus.py` | Scores candidate spellings by how well their pronunciation explains all clips: phonetic-feature edit distance, clip-quality weights |
| `p015/deva.py`, `phon.py`, `roman.py` | Devanagari normaliser (nukta, anusvara/chandrabindu, halant); rule-based IPA with schwa deletion; Hunterian romaniser |
| `p015/store.py`, `p015/build.py` | SQLite store and audit chain; build from clips |
| `api/main.py` | FastAPI: queue, cases, audio, decisions, audit, export, upload; serves `ui/dist` |
| `ui/` | React + Vite interface; `ui/check/ui_check.cjs` page check |
| `eval/consensus_eval.py` | Consensus vs single clip vs oracle; noise sweep; calibration |
| `data/p015.sqlite` | Full store: 200 names with witnesses, consensus and evidence (committed) |
| `data/clips.jsonl`, `targets_uk.yaml`, `exceptions.yaml`, `eval.json` | Clip provenance, gazetteer, Roman exceptions with reasons, evaluation output |
| `spikes/` | Model and yield experiments from the gate phase |
| `tests/` | 13 tests: phonology, consensus, API, audit chain |
| `docs/` | STATUS, ROMANISATION, RESULTS, DEMO |

## Status (25 September 2026)

| Item | State |
|---|---|
| Data | 200 names (81 in Uttarakhand), 1,059 clips kept of 1,949 mined, 224 speakers |
| Consensus, normaliser, IPA, Hunterian | Done |
| Confidence | Five components; capped at 54 for one speaker and 70 for two |
| Officer workspace | Done: replay, compare with existing record, edit with live re-derivation, approve / hold / reject, audit chain, CSV export, upload |
| Regional variants | Mechanism done (15 names carry one); no Garhwali or Kumaoni speakers yet, since the Vaani corpora have no usable transcripts |
| Sparse names | 105 names rest on one or two speakers; flagged and capped |
| Synthetic voices | Not used |
| Tests, page check | 13 pass; page check passes |
| Audio | Not in git; release asset `demo-audio` (40 MB), fetched by `./run.sh audio` |
| Demo video, hosted demo | Not done |

Acceptance table: `docs/STATUS.md` (AC7 partly met, the rest met).

## Results

| Measure | Value |
|---|---|
| Consensus, exact match | 84.8% |
| Single clip, mean | 71.0% |
| Oracle (best clip) | 92.9% |
| High-confidence band correct | 100% |

Noise sweep, clip-count sweep and calibration by band: `docs/RESULTS.md`.

## Run

Tested on Ubuntu (WSL2), 16 GB RAM, RTX 3050 6 GB. Serving and tests need no GPU.

| Requirement | Note |
|---|---|
| Python 3.12+ | tested 3.14 |
| PyTorch 2.14 | CUDA build for a GPU, CPU build otherwise |
| Node 20+ | tested 24; builds the interface |
| GPU | for mine and build, and for fast uploads; a CPU works but is slow |
| Disk | under 100 MB to serve; about 4 GB of models on first upload or build |
| Internet | pip and npm; model download on first upload or build; Hugging Face login for mine only |

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install torch==2.14.0 --index-url https://download.pytorch.org/whl/cu130   # or: pip install torch==2.14.0
pip install -r requirements.txt
./run.sh ui
./run.sh serve            # http://127.0.0.1:8015
./run.sh audio            # optional: clips for replay (GitHub CLI, logged in)
./run.sh test
```

Rebuild from the corpora:

```bash
hf auth login             # then accept the terms on ai4bharat/Shrutilipi and ai4bharat/IndicVoices
./run.sh mine             # GPU; resumable
./run.sh build --rebuild  # about 3 min on the RTX 3050
./run.sh eval --noise     # about 5 min
./run.sh ui-check         # needs npm install && npx playwright install chromium
```

Not committed: `data/audio/` (release asset), `data/cache/` (sentence audio for "in sentence" replay), `data/raw/`,
model weights (Hugging Face cache).

## Data and licences

Shrutilipi and IndicVoices: CC BY 4.0 (AI4Bharat). Lingua Libre clips: CC BY-SA (Wikimedia Commons). Gazetteer:
Wikidata (CC0). Models: vakyansh-wav2vec2-hindi (Apache-2.0), ai4bharat/indicwav2vec-hindi (gated, terms accepted),
facebook/wav2vec2-xlsr-53-espeak-cv-ft (Apache-2.0), microsoft/wavlm-base-plus-sv (MIT).

## Limits

- Accuracy is bounded by recogniser quality on short words.
- Shrutilipi has few readers per region; 105 names rest on one or two speakers.
- No Garhwali or Kumaoni variants until speakers of those languages are recorded.
- No synthetic voices; sparse names are flagged, not padded.
