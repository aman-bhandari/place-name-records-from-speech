# Romanisation scheme (Hunterian) and Devanagari policy — Eknaam

## Devanagari (output spelling)
| Rule | Example |
|---|---|
| Unicode NFC; nukta letters stored as base + nukta (U+093C); ZWJ/ZWNJ removed | क़ = क + ़ |
| Nasal before a stop → anusvara, not class nasal + halant (Central Hindi Directorate standard orthography) | चण्डीगढ़ → चंडीगढ़ |
| Nasalised vowel → chandrabindu when the top line is clear, anusvara when the vowel sign occupies it | हाँ, नहीं |
| Halant kept wherever written; conjuncts never expanded | हल्द्वानी |
| Retroflex/dental, aspirated/plain never merged (meaning-bearing in names) | डाल ≠ दाल |
| Comparison of candidate spellings ignores nasal notation, ऋ/रि, श/ष, spacing (`deva.match_key`) | रुद्र प्रयाग ≡ रुद्रप्रयाग |

## Pronunciation (IPA), derived by rule from the Devanagari
Consonants: k kʰ ɡ ɡʱ ŋ · t͡ʃ t͡ʃʰ d͡ʒ d͡ʒʱ ɲ · ʈ ʈʰ ɖ ɖʱ ɳ · t̪ t̪ʰ d̪ d̪ʱ n · p pʰ b bʱ m · j r l ʋ · ʃ ʂ s ɦ · nukta: q x ɣ z ɽ ɽʱ f.
Vowels: ə aː ɪ iː ʊ uː rɪ eː ɛː oː ɔː (ऑ ɔ, ॅ æ); nasalisation as ̃.
Schwa deletion: word-final inherent vowel dropped; medial schwa dropped in V C _ C V and before a C+glide/liquid onset
(देहरादून /d̪eːɦraːd̪uːn/, कोटद्वार /koːʈd̪ʋaːr/); kept after a consonant cluster (रुद्रप्रयाग /rʊd̪rəprəjaːɡ/).
Anusvara → class nasal before a stop (चंडीगढ़ /t͡ʃəɳɖiːɡəɽʱ/), nasalisation elsewhere.

## Roman (Hunterian, as on Survey of India sheets), from the pronunciation
| Devanagari | plain | diacritic | | Devanagari | plain | diacritic |
|---|---|---|---|---|---|---|
| अ / आ | a / a | a / ā | | च / छ | ch / chh | ch / chh |
| इ / ई | i / i | i / ī | | ट ठ ड ढ ण | t th d dh n | ṭ ṭh ḍ ḍh ṇ |
| उ / ऊ | u / u | u / ū | | श / ष | sh / sh | ś / ṣ |
| ए / ऐ | e / ai | e / ai | | व | w | w |
| ओ / औ | o / au | o / au | | ड़ / ढ़ | r / rh | ṛ / ṛh |
| ऋ | ri | ri | | ज़ फ़ क़ ख़ ग़ | z f q kh gh | z f q kh gh |
| anusvara / chandrabindu | n | n | | ङ ञ | n n | ṅ ñ |

The plain form is what goes on the sheet; the diacritic form is kept in the record. Words are capitalised.

## Established forms (exceptions), each with its reason
`data/exceptions.yaml` lists names whose official spelling departs from the scheme (Mussoorie, Roorkee, Tehri,
Pithoragarh, Devprayag, Vikasnagar, Lansdowne, Srinagar, Varanasi, Delhi, Lucknow …). When a name has an existing
record whose Roman form differs from the scheme output and is not in the list, the record's form is recommended with
the reason "existing record uses …; scheme would give …; officer to confirm which stands". Every recommendation
carries `kind: scheme | established` and the reason text.
