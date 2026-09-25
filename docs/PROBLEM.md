# P-015 — AI Standardisation of Indian Place Names from Spoken Audio

Source: https://www.axocom.in/UKISHackathon/problems/P-015 (read 25 Sep 2026; published 22 Sep 2026; 0 accepted solutions).
Theme: Speech AI & Linguistic Standardisation. Owner: **Survey of India**, Department of Science & Technology.

> Survey of India is the national authority that fixes the official spelling and pronunciation of every place name used
> on maps, gazetteers and government records. Today the same village, town, river or peak is written in several
> conflicting ways in both Hindi and English, because names are transcribed by ear across different dialects, accents
> and regional languages with no consistent phonetic reference. Build a system that listens to multiple audio recordings
> of different speakers pronouncing the same place name and produces a single consensus record: one standardised
> Devanagari (Hindi) spelling, one Roman (English) spelling and an IPA phonetic transcription. The system must reconcile
> variation across speakers rather than simply picking the clearest recording, and it is a decision-support tool for
> Survey of India officers, not an auto-publisher.

Theme line: *One Authoritative Name, Spelling and Pronunciation for Every Indian Place*

## Proposed capabilities
1. Ingest multiple audio recordings of the same place name from different speakers and align them to a single name entity
2. Reconcile speaker variation into one consensus output instead of selecting the single clearest recording
3. Standardised Devanagari spelling with correct handling of nukta, anusvara, chandrabindu, halant and retroflex or aspirated distinctions
4. Roman spelling using a consistent, documented romanisation scheme, with a clear explanation wherever an established historical form departs from that scheme
5. IPA phonetic transcription showing exactly how the name should be pronounced
6. Robust to strong accents, background noise, poor recording quality and speakers who genuinely disagree
7. Handle sparse evidence for remote locations and names borrowed from non-Hindi regional languages
8. Preserve genuine regional pronunciation variants as linked alternates rather than erasing them
9. Confidence score, the competing spellings considered and the supporting evidence on every recommendation
10. Officer review workspace: replay source clips, compare against existing records, edit any field, approve the final entry with a full audit trail

## Potential applications
Official maps, gazetteers, signage, revenue documents · resolving conflicting Hindi/English spellings in government
records · national pronunciation reference for navigation apps, screen readers, TTS, public announcements · field
surveyors capturing newly recorded or renamed locations.

## Expected outcomes
One authoritative record per place name (Devanagari, Roman, IPA) · consistent, explainable romanisation with
documented exceptions · faster officer review (confidence, ranked alternatives, replayable evidence) · preserved
regional variants linked to the entry · complete audit trail; nothing published without Survey of India officer approval.
