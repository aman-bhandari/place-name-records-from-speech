"""Gate 1 (fast): scan transcripts of a whole HF corpus for gazetteer place names using parallel range reads.
usage: scan_corpora.py shrutilipi|indicvoices [max_shards]"""
import sys, json, time, pathlib, collections, concurrent.futures as cf
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from p015.hfparquet import RemoteParquet
from p015 import gazetteer
from huggingface_hub import HfApi
root = pathlib.Path(__file__).resolve().parents[1]
CORP = {'shrutilipi': ('ai4bharat/Shrutilipi', 'hindi', 'text', ['duration']),
        'indicvoices': ('ai4bharat/IndicVoices', 'hindi', 'text', ['duration', 'speaker_id', 'district', 'state', 'gender', 'age_group', 'task_name'])}
name = sys.argv[1]; repo, sub, tcol, extra = CORP[name]; maxs = int(sys.argv[2]) if len(sys.argv) > 2 else 9999
gaz = gazetteer.load(); pat = gazetteer.pattern(gaz)
files = sorted(f.path for f in HfApi().list_repo_tree(repo, path_in_repo=sub, repo_type='dataset') if f.path.endswith('.parquet'))[:maxs]
print(name, 'gazetteer', len(gaz), 'shards', len(files), flush=True)
out = open(root / f'data/raw/hits_{name}.jsonl', 'w'); lock = __import__('threading').Lock(); t0 = time.time(); stats = collections.Counter()
def scan(path):
    try:
        r = RemoteParquet(repo, path, workers=8); t = r.read(columns=[tcol] + extra); rows = t.to_pylist(); recs = []
        rg_sizes = [r.meta.row_group(i).num_rows for i in range(r.meta.num_row_groups)]; bounds = []; s = 0
        for n in rg_sizes: bounds.append((s, s + n)); s += n
        for idx, row in enumerate(rows):
            txt = gazetteer.nfc(row[tcol])
            for m in pat.finditer(txt):
                rg = next(i for i, (a, b) in enumerate(bounds) if a <= idx < b)
                rec = {'corpus': name, 'path': path, 'rg': rg, 'row': idx - bounds[rg][0], 'name': m.group(1), 'start': m.start(), 'end': m.end(), 'text': txt}
                rec.update({k: row.get(k) for k in extra}); recs.append(rec)
        with lock:
            for rec in recs: out.write(json.dumps(rec, ensure_ascii=False) + '\n')
            out.flush(); stats['rows'] += len(rows); stats['hits'] += len(recs); stats['shards'] += 1
            print(f'{stats["shards"]}/{len(files)} {path.split("/")[-1]} rows={len(rows)} hits={len(recs)} total_hits={stats["hits"]} {time.time()-t0:.0f}s', flush=True)
    except Exception as e:
        print('FAIL', path, type(e).__name__, str(e)[:200], flush=True)
with cf.ThreadPoolExecutor(6) as ex: list(ex.map(scan, files))
out.close(); print('DONE', dict(stats), f'{time.time()-t0:.0f}s', flush=True)
