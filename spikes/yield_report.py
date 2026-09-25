"""Gate 0.2 report from the two corpus scans: names by occurrence count and by distinct speakers (IndicVoices)."""
import json, collections, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from p015 import gazetteer
root = pathlib.Path(__file__).resolve().parents[1]; gaz = gazetteer.load()
occ = collections.defaultdict(collections.Counter); spk = collections.defaultdict(set)
for name in ['shrutilipi', 'indicvoices']:
    for l in open(root / f'data/raw/hits_{name}.jsonl'):
        d = json.loads(l); occ[d['name']][name] += 1
        if d.get('speaker_id'): spk[d['name']].add(d['speaker_id'])
tot = {n: sum(c.values()) for n, c in occ.items()}
unamb = {n: c for n, c in tot.items() if not gaz[n]['ambiguous'] and len(n) >= 4}
uk = {n: c for n, c in unamb.items() if gaz[n]['src'] == 'uk'}
print('names total', len(tot), '| unambiguous (len>=4, not a common word)', len(unamb))
for k in (3, 5, 10): print(f'  unambiguous names with >= {k} occurrences:', sum(1 for c in unamb.values() if c >= k))
print('UK names', len(uk), '| >=3', sum(1 for c in uk.values() if c >= 3), '| >=5', sum(1 for c in uk.values() if c >= 5))
print('IndicVoices names with >=3 distinct speakers', sum(1 for n, s in spk.items() if len(s) >= 3 and n in unamb))
print('top UK', sorted(uk.items(), key=lambda x: -x[1])[:50])
print('top all', sorted(unamb.items(), key=lambda x: -x[1])[:40])
json.dump({'occ': {n: dict(c) for n, c in occ.items()}, 'speakers': {n: len(s) for n, s in spk.items()}}, open(root / 'data/raw/yield.json', 'w'), ensure_ascii=False)
