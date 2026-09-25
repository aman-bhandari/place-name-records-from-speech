"""Fetch Lingua Libre Hindi word clips (Commons, CC BY-SA) for words said by >= MIN speakers."""
import json, sys, time, urllib.request, urllib.parse, pathlib
UA = {'User-Agent': 'ukis-p015-research/0.1 (bhandari.aman0101@gmail.com)'}
MIN = int(sys.argv[1]) if len(sys.argv) > 1 else 3
root = pathlib.Path(__file__).resolve().parents[1]
words = json.load(open(root / 'data/raw/ll_hin_words.json'))
out = root / 'data/audio/lingualibre'; out.mkdir(parents=True, exist_ok=True)
titles = []
for w, spk in words.items():
    if len(spk) >= MIN:
        titles += [f'File:LL-Q1568 (hin)-{s}-{w}.wav' for s in spk]
manifest = []
for i in range(0, len(titles), 40):
    q = {'action': 'query', 'titles': '|'.join(titles[i:i+40]), 'prop': 'imageinfo', 'iiprop': 'url', 'format': 'json'}
    d = json.load(urllib.request.urlopen(urllib.request.Request('https://commons.wikimedia.org/w/api.php?' + urllib.parse.urlencode(q), headers=UA)))
    for p in d['query']['pages'].values():
        if 'imageinfo' not in p: continue
        url = p['imageinfo'][0]['url']; t = p['title']
        spk, word = t[len('File:LL-Q1568 (hin)-'):].rsplit('.', 1)[0].split('-', 1)
        fn = out / urllib.parse.unquote(url.split('/')[-1])
        if not fn.exists():
            for a in range(3):
                try: fn.write_bytes(urllib.request.urlopen(urllib.request.Request(url, headers=UA)).read()); break
                except Exception: time.sleep(2)
        manifest.append({'file': str(fn.relative_to(root)), 'speaker': spk, 'word': word, 'source': 'https://commons.wikimedia.org/wiki/' + urllib.parse.quote(t.replace(' ', '_'))})
json.dump(manifest, open(root / f'data/raw/ll_manifest_min{MIN}.json', 'w'), ensure_ascii=False, indent=0)
print(len(manifest), 'clips')
