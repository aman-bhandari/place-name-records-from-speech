"""Gazetteer of Hindi place names from Wikidata dumps in data/raw (Uttarakhand items, Indian towns > 15k, districts)."""
import csv, json, re, unicodedata, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
STOP = {'भारत', 'हिन्दी', 'नगर', 'गाँव', 'गांव', 'पुर', 'सिंह', 'राम', 'शहर', 'देश', 'राज्य', 'सरकार', 'मंदिर', 'नदी', 'पहाड़',
        'गया', 'बना', 'बनी', 'सात', 'जाना', 'डाल', 'खेती', 'साल', 'खेत', 'खाली', 'कहना', 'जाल', 'काली', 'खान', 'सिल', 'कुई', 'गाडी',
        'मंडी', 'उना', 'सीम', 'प्यारा', 'बेह', 'भारतीय', 'मन', 'बाद', 'नई', 'नया', 'पानी', 'कला', 'माल', 'बाग', 'भाग', 'सेवा', 'खेड़ा',
        'तला', 'टीला', 'रानी', 'राजा', 'लाल', 'सोना', 'काला', 'नाला', 'ताल', 'गढ़', 'पट्टी', 'टोला', 'कोट', 'बारी', 'हार', 'जीत'}
def nfc(s): return unicodedata.normalize('NFC', s or '').strip()
def clean(hi):
    hi = nfc(hi).split(',')[0]
    hi = re.sub(r'\s*(जिला|ज़िला|तहसील|नगर पालिका|नगर निगम|ब्लॉक|विकासखंड)$', '', hi).strip()
    return hi
def load(min_len=3, drop_common=True):
    """Return {hindi_name: {'en','item','src','ambiguous'}}."""
    common = set(json.load(open(ROOT / 'data/raw/ll_hin_words.json'))) if drop_common else set()
    gaz = {}
    def add(r, src):
        hi = clean(r['hi'])
        if len(hi) < min_len or len(hi.split()) > 2 or hi in STOP: return
        d = gaz.setdefault(hi, {'en': nfc(r['en']), 'item': r['item'].rsplit('/', 1)[-1], 'src': src, 'ambiguous': hi in common})
        if src != 'uk' and d['src'] == 'uk': d.update(en=nfc(r['en']) or d['en'], src=src)   # prefer town/district record
    for r in csv.DictReader(open(ROOT / 'data/raw/wd_in_districts.csv')): r['hi'] and add(r, 'district')
    for r in csv.DictReader(open(ROOT / 'data/raw/wd_in_towns.csv')): r['hi'] and add(r, 'town')
    for r in csv.DictReader(open(ROOT / 'data/raw/wd_uk.csv')): r['hi'] and add(r, 'uk')
    return gaz
def pattern(gaz):
    names = sorted(gaz, key=len, reverse=True)
    return re.compile(r'(?<![ऀ-ॿ])(' + '|'.join(re.escape(n) for n in names) + r')(?![ऀ-ॿ])')
