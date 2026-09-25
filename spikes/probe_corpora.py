"""Gate 1b: IndicVoices Hindi and Vaani Uttarakhand layouts: speaker ids, transcript availability, place-name hits."""
import pyarrow.parquet as pq, time, re, json, pathlib, csv, unicodedata, collections
from huggingface_hub import HfFileSystem
fs = HfFileSystem(); root = pathlib.Path(__file__).resolve().parents[1]
def head(p, n=3):
    t0 = time.time(); f = pq.ParquetFile(fs.open(p, block_size=4 * 2**20))
    cols = [c for c in f.schema_arrow.names if c not in ('audio', 'audio_filepath')]
    print('==', p, f.metadata.num_rows, 'rows', f.metadata.num_row_groups, 'rgs', f'{time.time()-t0:.1f}s open')
    print(f.schema_arrow.names)
    d = f.read_row_group(0, columns=cols).to_pandas()
    print(d.head(n).T.to_string()[:2500]); return f, cols
f, cols = head('datasets/ai4bharat/IndicVoices/hindi/train-00000-of-00082.parquet')
t = f.read(columns=cols).to_pandas()
print('rows', len(t)); 
for c in t.columns:
    if t[c].dtype == object and t[c].nunique() < 50: print(c, dict(t[c].value_counts().head(12)))
    elif c.lower().find('speaker') >= 0: print(c, 'unique', t[c].nunique())
tcol = [c for c in t.columns if c.lower() in ('text', 'transcript', 'transcription')]
print('text col', tcol); print(t[tcol[0]].head(8).tolist() if tcol else '')
gaz = set()
for fn in ['wd_uk.csv', 'wd_in_towns.csv', 'wd_in_districts.csv']:
    for r in csv.DictReader(open(root / 'data/raw' / fn)):
        h = unicodedata.normalize('NFC', r['hi'].split(',')[0]).strip(); h = re.sub(r'\s*जिला$', '', h)
        if len(h) >= 3: gaz.add(h)
pat = re.compile(r'(?<![ऀ-ॿ])(' + '|'.join(re.escape(n) for n in sorted(gaz, key=len, reverse=True)) + r')(?![ऀ-ॿ])')
if tcol:
    c = collections.Counter(m.group(1) for s in t[tcol[0]].fillna('') for m in pat.finditer(s))
    print('IndicVoices file0 place hits', sum(c.values()), 'names', len(c), c.most_common(30))
for p in ['datasets/ARTPARK-IISc/Vaani/audio/Uttarakhand/TehriGarhwal/train-00000-of-00048.parquet', 'datasets/ARTPARK-IISc/Vaani/audio/Garhwali/train-00000-of-00056.parquet']:
    f, cols = head(p, 2); t = f.read(columns=cols).to_pandas()
    print('rows', len(t), 'transcribed', dict(t['isTranscriptionAvailable'].value_counts()), 'speakers', t['speakerID'].nunique(), 'districts', dict(t['district'].value_counts().head()))
    c = collections.Counter(m.group(1) for s in t['transcript'].fillna('') for m in pat.finditer(s))
    print('place hits', sum(c.values()), c.most_common(20))
