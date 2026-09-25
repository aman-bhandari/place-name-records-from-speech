# Eknaam (एकनाम) — one authoritative name for every place

Entry for UKIS 2026 problem **P-015** (Survey of India): several recordings of different speakers saying a place name →
one consensus record — Devanagari, Roman (Hunterian, exceptions explained), IPA — with confidence, competing
spellings, evidence, linked regional variants and an officer review workspace with a hash-chained audit trail.
Everything runs on one laptop (RTX 3050, 6 GB); no paid API.

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
   deletion, Hunterian romaniser with a documented exception list — `docs/ROMANISATION.md`.
5. **Confidence decomposed**: spelling explains clips · clips agree · lead over runner-up · speakers · clip quality;
   capped when fewer than three real speakers were heard. Minority spellings backed by ≥2 speakers stay as linked variants.
6. **Officer workspace**: replay each clip and its source sentence, see every witness, compare with the existing
   record, edit any field (IPA and Roman re-derive live), approve / hold / reject with reason, hash-chained audit,
   CSV export of approved records, upload of field recordings.

## Run
```bash
cd ~/workshop/ukis-p015
./run.sh serve            # http://127.0.0.1:8015 (UI is prebuilt in ui/dist)
./run.sh test             # pytest: phonology, consensus, API, audit chain
./run.sh mine             # mine clips from the corpora (needs HF login + accepted terms; resumable)
./run.sh build --rebuild  # witnesses + consensus → data/p015.sqlite
./run.sh eval --noise     # docs/RESULTS numbers → data/eval.json
~/.claude/browser/run.sh ui/check/ui_check.cjs   # Playwright UI check
```
Python 3.14 venv in `.venv` (torch 2.14 cu130, transformers 5.17). Node for the UI (`cd ui && npm install && npm run build`).

## Layout
`p015/` engine — `deva.py` normaliser · `phon.py` IPA · `roman.py` Hunterian · `consensus.py` reconciliation ·
`witness.py` CTC models · `align.py` name cutting · `speaker.py` x-vectors · `hfparquet.py` parallel remote parquet
reads · `gazetteer.py` · `mine.py` · `build.py` · `store.py` SQLite + audit. `api/main.py` FastAPI. `ui/` Vite React.
`eval/consensus_eval.py`. `spikes/` gate experiments. `docs/` PLAN, PROBLEM, ROMANISATION, RESULTS, DEMO, STATUS.

## Data and licences
Shrutilipi and IndicVoices: CC BY 4.0 (AI4Bharat); Lingua Libre clips: CC BY-SA (Wikimedia Commons); gazetteer:
Wikidata (CC0). Models: vakyansh-wav2vec2-hindi (Apache-2.0), ai4bharat/indicwav2vec-hindi (gated, accepted),
facebook/wav2vec2-xlsr-53-espeak-cv-ft (Apache-2.0), microsoft/wavlm-base-plus-sv (MIT). Audio is not committed;
`data/clips.jsonl` records the exact source row of every clip.

## Limits (honest)
* Names are only as good as the recognisers on short words; the acoustic-only number in RESULTS is the fair one.
* Shrutilipi readers are few per region, so some Uttarakhand names have 1–2 distinct speakers and are flagged.
* Garhwali/Kumaoni corpora (Vaani) have almost no transcripts, so regional variants come from Hindi speakers' clusters.
* No synthetic voices: they would manufacture evidence from the record. Sparse names are flagged, not padded.
