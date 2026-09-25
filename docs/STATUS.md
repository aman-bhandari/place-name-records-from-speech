# Status: P-015 core built — Eknaam (25 Sep 2026)

Against the definition of done in `docs/PLAN.md`:

| # | Criterion | State | Evidence |
|---|---|---|---|
| AC1 | Ingest ≥3 clips per name, any format, corpus-mined or uploaded | **Met** | 1,949 mined clips; upload of 3 Lingua Libre speakers of असम → असम / Assam / /əsəm/ high 91 |
| AC2 | Consensus ≥ +10 points over mean single clip, reported with oracle | **Met**: +13.8 (84.8% vs 71.0%; oracle 92.9%) | `docs/RESULTS.md` |
| AC3 | Devanagari normaliser: nukta, anusvara/chandrabindu, halant, retroflex/aspirate | **Met** | `p015/deva.py`, `tests/test_phon.py` |
| AC4 | Hunterian romaniser documented; exceptions with reasons; scheme/established on every output | **Met** | `docs/ROMANISATION.md`, `data/exceptions.yaml` |
| AC5 | Rule-based IPA with schwa deletion; per-clip phones as evidence | **Met** | `p015/phon.py`; evidence table |
| AC6 | Robustness: noise sweep, clips sweep, disagreement demonstrated | **Met** | RESULTS; 58 names flagged disagreement |
| AC7 | Sparse evidence flagged and capped; non-Hindi regional clips | **Partly**: flags + caps done; Garhwali/Kumaoni corpora have no usable transcripts | 105 names flagged |
| AC8 | Regional variants as linked alternates | **Met (mechanism)**: 15 names carry a variant; true dialect variants need Garhwali/Kumaoni speakers | case pages |
| AC9 | Confidence decomposed, competing spellings with supporters, existing-record comparison | **Met** | case page |
| AC10 | Officer workspace, audit chain, export, upload; README/RESULTS/DEMO; rebuild; UI check | **Met** | `./run.sh`; 13 tests pass; Playwright check passes |

## What is left
1. **Look at the demo** (`docs/DEMO.md`): `./run.sh serve` → http://127.0.0.1:8015. Review a few names, approve one.
2. **Decide on synthetic voices**: none are used (they would manufacture evidence from the record). Decide whether
   labelled TTS filler after all.
3. **Regional variants**: to show Garhwali/Kumaoni pronunciation as linked alternates we need speakers from those
   languages saying place names; Vaani has the voices but almost no transcripts. Options: a small field recording set
   from Uttarakhand contacts, or transcribe Vaani Garhwali clips with the phone recogniser and search phonetically.
4. **Registration**: deferred; the draft is written once the team decides.

## Running it
```bash
cd ukis-p015
./run.sh serve      # http://127.0.0.1:8015
./run.sh test       # 13 tests
./run.sh build --rebuild && ./run.sh eval --noise    # ~3 min + ~5 min on the RTX 3050
./run.sh ui-check
```
