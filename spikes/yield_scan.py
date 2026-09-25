"""Gate 1: how many gazetteer place names occur in Shrutilipi Hindi transcripts (text column only, remote parquet)."""
import csv, json, re, sys, time, pathlib, collections, unicodedata
import pyarrow.parquet as pq
from huggingface_hub import HfFileSystem
root = pathlib.Path(__file__).resolve().parents[1]
NFILES = int(sys.argv[1]) if len(sys.argv) > 1 else 10
def norm(s): return unicodedata.normalize('NFC', s.strip())
gaz = {}
def add(hi, en, item, src):
    hi = norm(hi.split(',')[0]); hi = re.sub(r'\s*(जिला|ज़िला|तहसील|नगर पालिका|ब्लॉक)$', '', hi).strip()
    if len(hi) < 3 or ' ' in hi and len(hi.split()) > 2: return
    gaz.setdefault(hi, {'en': en, 'item': item.rsplit('/', 1)[-1], 'src': src})
for r in csv.DictReader(open(root / 'data/raw/wd_uk.csv')):
    if r['hi']: add(r['hi'], r['en'], r['item'], 'uk')
for r in csv.DictReader(open(root / 'data/raw/wd_in_towns.csv')):
    if r['hi']: add(r['hi'], r['en'], r['item'], 'town')
for r in csv.DictReader(open(root / 'data/raw/wd_in_districts.csv')):
    if r['hi']: add(r['hi'], r['en'], r['item'], 'district')
stop = {'भारत', 'हिन्दी', 'नगर', 'गाँव', 'गांव', 'पुर', 'सिंह', 'राम', 'शहर', 'देश', 'राज्य', 'सरकार', 'मंदिर', 'नदी', 'पहाड़'}
for s in stop: gaz.pop(s, None)
print('gazetteer', len(gaz), 'uk', sum(1 for v in gaz.values() if v['src']=='uk'), flush=True)
names = sorted(gaz, key=len, reverse=True)
pat = re.compile(r'(?<![ऀ-ॿ])(' + '|'.join(re.escape(n) for n in names) + r')(?![ऀ-ॿ])')
fs = HfFileSystem()
files = sorted(p for p in fs.ls('datasets/ai4bharat/Shrutilipi/hindi', detail=False) if p.endswith('.parquet'))
print('files', len(files), flush=True)
hits = collections.defaultdict(list); out = open(root / 'data/raw/shrutilipi_hits.jsonl', 'w')
t0 = time.time(); rows = 0
for fi, p in enumerate(files[:NFILES]):
    t1 = time.time()
    f = pq.ParquetFile(fs.open(p, block_size=4 * 2**20))
    for rg in range(f.metadata.num_row_groups):
        t = f.read_row_group(rg, columns=['text', 'duration']).to_pandas()
        for i, (txt, dur) in enumerate(zip(t['text'], t['duration'])):
            rows += 1
            for m in pat.finditer(norm(txt)):
                n = m.group(1)
                rec = {'file': p, 'rg': rg, 'row': i, 'name': n, 'en': gaz[n]['en'], 'src': gaz[n]['src'], 'dur': dur, 'start': m.start(), 'end': m.end(), 'text': txt}
                hits[n].append(rec); out.write(json.dumps(rec, ensure_ascii=False) + '\n')
    out.flush()
    print(f'file {fi} {p.split("/")[-1]} rows={rows} names={len(hits)} clips={sum(map(len, hits.values()))} {time.time()-t1:.0f}s', flush=True)
print('TOTAL', time.time() - t0, 'rows', rows, flush=True)
cnt = {n: len(v) for n, v in hits.items()}
print('names>=3', sum(1 for c in cnt.values() if c >= 3), 'names>=5', sum(1 for c in cnt.values() if c >= 5))
uk = {n: c for n, c in cnt.items() if gaz[n]['src'] == 'uk'}
print('UK names', len(uk), 'UK>=3', sum(1 for c in uk.values() if c >= 3))
print('top', sorted(cnt.items(), key=lambda x: -x[1])[:40])
print('top UK', sorted(uk.items(), key=lambda x: -x[1])[:40])
json.dump({'gaz': gaz, 'counts': cnt}, open(root / 'data/raw/shrutilipi_yield.json', 'w'), ensure_ascii=False)
