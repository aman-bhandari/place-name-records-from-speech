"""Read chosen columns / row groups of a remote Hugging Face parquet file with parallel HTTP range requests.

Why: HfFileSystem issues one serial round trip per column chunk (~1 s each). For a 500 MB Shrutilipi shard the
text column is 460 KB but takes 70 s to read. Here the byte ranges are computed from the footer and fetched in
parallel straight from the CDN, into a sparse buffer that pyarrow reads as if it were the whole file."""
import io, os, threading, concurrent.futures as cf
import requests, pyarrow as pa, pyarrow.parquet as pq

_tok = None
def token():
    global _tok
    if _tok is None:
        p = os.path.expanduser('~/.cache/huggingface/token'); _tok = open(p).read().strip() if os.path.exists(p) else ''
    return _tok

class RemoteParquet:
    def __init__(self, repo, path, repo_type='dataset', revision='main', workers=16, session=None):
        self.url = f'https://huggingface.co/{"datasets/" if repo_type=="dataset" else ""}{repo}/resolve/{revision}/{path}'
        self.s = session or requests.Session(); self.s.headers['Authorization'] = f'Bearer {token()}'
        r = self.s.head(self.url, allow_redirects=True, timeout=60); r.raise_for_status()
        self.cdn = r.url; self.size = int(r.headers['Content-Length']); self.workers = workers
        self.buf = bytearray(self.size); self._have = []
        tail = self._get(max(0, self.size - 2**20), self.size - 1)
        self.buf[self.size - len(tail):] = tail
        self.meta = pq.ParquetFile(pa.BufferReader(bytes(tail))).metadata if False else pq.read_metadata(pa.BufferReader(self._sparse()))
        self.schema = self.meta.schema.to_arrow_schema()
    def _get(self, a, b):
        for attempt in range(4):
            try:
                r = self.s.get(self.cdn, headers={'Range': f'bytes={a}-{b}'}, timeout=120); r.raise_for_status(); return r.content
            except Exception as e:
                if attempt == 3: raise
        return b''
    def _sparse(self): return pa.py_buffer(self.buf)
    def ranges(self, row_groups, columns):
        out = []
        for rg in row_groups:
            g = self.meta.row_group(rg)
            for i in range(g.num_columns):
                c = g.column(i)
                if c.path_in_schema in columns:
                    start = min(x for x in (c.data_page_offset, c.dictionary_page_offset) if x is not None)
                    out.append((start, start + c.total_compressed_size - 1))
        out.sort(); merged = []
        for a, b in out:
            if merged and a <= merged[-1][1] + 1: merged[-1] = (merged[-1][0], max(merged[-1][1], b))
            else: merged.append((a, b))
        return merged
    def fetch(self, row_groups, columns):
        rs = self.ranges(row_groups, columns)
        def job(ab):
            a, b = ab; data = self._get(a, b); self.buf[a:a + len(data)] = data
        with cf.ThreadPoolExecutor(self.workers) as ex: list(ex.map(job, rs))
        return sum(b - a + 1 for a, b in rs)
    def read(self, row_groups=None, columns=None):
        row_groups = list(range(self.meta.num_row_groups)) if row_groups is None else list(row_groups)
        columns = list(columns) if columns else self.schema.names
        leaf = [c for c in self._leaves() if c.split('.')[0] in columns or c in columns]
        self.fetch(row_groups, leaf)
        f = pq.ParquetFile(pa.BufferReader(self._sparse()))
        return f.read_row_groups(row_groups, columns=columns)
    def _leaves(self):
        g = self.meta.row_group(0); return [g.column(i).path_in_schema for i in range(g.num_columns)]
