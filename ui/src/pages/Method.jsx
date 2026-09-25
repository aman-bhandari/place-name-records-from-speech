import React, { useEffect, useState } from 'react'
import { api } from '../api.js'
export default function Method() {
  const [res, setRes] = useState(null)
  useEffect(() => { fetch('/api/results').then((r) => r.json()).then(setRes).catch(() => {}) }, [])
  return (
    <div className="p-4 md:p-6 max-w-3xl leading-relaxed">
      <h1 className="text-2xl mb-3">How a recommendation is made</h1>
      <p>Each name is a case with several recordings by different speakers, cut from open speech corpora by the recogniser itself (it finds the word inside the sentence it was said in) or uploaded by an officer. Three witnesses listen to every recording: two Hindi recognisers that write Devanagari, and one language-independent phone recogniser that writes what it heard as sounds. Every hypothesis is turned into a pronunciation with the rules below.</p>
      <p className="mt-2">Candidate spellings come from every witness, from a column vote across recordings, from the existing record and from the gazetteer names that sound close. Each candidate is scored by how well its pronunciation explains <em>all</em> recordings, weighted by each recording's quality. The clearest single recording never decides on its own. Confidence combines that score with how many recordings agree, the lead over the runner-up and how many distinct speakers were heard. A minority spelling backed by two or more speakers is kept as a linked variant.</p>
      <h2 className="text-lg mt-6 border-b hair pb-1">Devanagari spelling rules</h2>
      <ul className="list-disc pl-5 mt-2">
        <li>Nasal before a stop is written with anusvara (चंडीगढ़, not चण्डीगढ़); a nasalised vowel takes chandrabindu unless the vowel sign occupies the top line.</li>
        <li>Nukta letters (क़ ख़ ग़ ज़ ड़ ढ़ फ़) are kept as base letter + nukta; halant is kept where written; retroflex/dental and aspirated/plain letters are never merged.</li>
        <li>Pronunciation follows Hindi schwa deletion (देहरादून → /d̪eːɦraːd̪uːn/), anusvara resolves to the class nasal before stops and to nasalisation elsewhere.</li>
      </ul>
      <h2 className="text-lg mt-6 border-b hair pb-1">Roman spelling: Hunterian, with documented exceptions</h2>
      <p className="mt-2">The Roman form is derived from the pronunciation with the Hunterian system used on Survey of India sheets: ch/chh for च/छ, sh for श/ष, w for व, rh for ढ़, ai/au for ऐ/औ, e/o for ए/ओ, plain vowels on the sheet (a for both अ and आ) and a diacritic form (ā ī ū ṭ ḍ ṇ ṛ ś ṣ) for the record. Where an established historical form is in official use, it is recommended instead and the reason is stated (Mussoorie, Roorkee, Tehri, Pithoragarh, Devprayag, Lansdowne…). Every record says whether its Roman spelling is the scheme or an established form.</p>
      <h2 className="text-lg mt-6 border-b hair pb-1">Sources and licences</h2>
      <ul className="list-disc pl-5 mt-2">
        <li>Shrutilipi (AI4Bharat, CC BY 4.0): All India Radio news bulletins with transcripts; names are cut out of sentences. Speakers are told apart by voice embedding.</li>
        <li>IndicVoices (AI4Bharat, CC BY 4.0): everyday speakers with speaker id, district and state.</li>
        <li>Gazetteer and existing records: Wikidata labels (Hindi and English) for Indian settlements, districts and Uttarakhand places.</li>
        <li>Models: vakyansh-wav2vec2-hindi, ai4bharat/indicwav2vec-hindi, wav2vec2-xlsr-53-espeak (phones), wavlm-base-plus-sv (speakers). All run locally.</li>
      </ul>
      {res?.exact && <div className="mt-6">
        <h2 className="text-lg border-b hair pb-1">Measured on this store</h2>
        <p className="text-sm text-ink-soft mt-2">{res.n_cases} names with at least three real recordings ({res.clips_per_case?.toFixed(1)} clips and {res.speakers_per_case?.toFixed(1)} speakers per name). Exact spelling recovered:</p>
        <table className="text-sm mt-2"><tbody>{Object.entries(res.exact).map(([k, v]) => <tr key={k} className="border-b hair"><td className="py-1 pr-6">{k}</td><td className="text-right">{Math.round(v * 100)}%</td></tr>)}</tbody></table>
        {res.clips_sweep_acoustic && <p className="text-sm text-ink-soft mt-3">Acoustic-only consensus by number of clips: {Object.entries(res.clips_sweep_acoustic).map(([k, v]) => `${k} clip${k === '1' ? '' : 's'} ${Math.round(v.exact * 100)}%`).join(' · ')}</p>}
        {res.noise_sweep_acoustic && <p className="text-sm text-ink-soft mt-1">With added white noise: {Object.entries(res.noise_sweep_acoustic).map(([k, v]) => `${k === 'clean' ? 'clean' : k + ' dB SNR'} ${Math.round(v.exact * 100)}%`).join(' · ')}</p>}
        {res.by_band && <p className="text-sm text-ink-soft mt-1">By confidence band: {Object.entries(res.by_band).map(([k, v]) => `${k} ${Math.round(v.exact * 100)}% (${v.n})`).join(' · ')}</p>}
      </div>}
      <p className="mt-4 text-ink-soft">Decision support only. Nothing leaves this workspace as an official name until an officer approves it, and every action is in the audit trail.</p>
    </div>
  )
}
