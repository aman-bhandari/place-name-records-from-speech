import sys, pathlib, json, os
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import pytest
from fastapi.testclient import TestClient
from p015 import store
@pytest.fixture
def client(tmp_path, monkeypatch):
    db = tmp_path / 't.sqlite'; monkeypatch.setattr(store, 'DB', db)
    c = store.connect(db)
    cur = c.execute("INSERT INTO cases (name_hi, kind, existing_en, existing_src, item, status, created) VALUES ('देहरादून','district','Dehradun','test','Q1',' pending',0)")
    rec = {'devanagari': 'देहरादून', 'ipa': '/d̪eːɦraːd̪uːn/', 'roman': {'scheme': 'Dehradun', 'recommended': 'Dehradun', 'kind': 'scheme', 'reason': 'x'}, 'confidence': {'score': 80, 'band': 'high', 'clips': 3, 'speakers': 3, 'support': .8, 'agreement': .9, 'margin': .2}, 'candidates': [], 'variants': [], 'flags': [], 'existing': {'hi': 'देहरादून', 'en': 'Dehradun'}}
    c.execute('INSERT INTO recommendation (case_id, record, built) VALUES (?,?,0)', (cur.lastrowid, json.dumps(rec, ensure_ascii=False))); c.commit(); store.audit(c, 'system', 'built', cur.lastrowid, {})
    from api import main; monkeypatch.setattr(main, 'db', lambda: store.connect(db))
    return TestClient(main.app)
def test_list_and_case(client):
    r = client.get('/api/cases'); assert r.status_code == 200 and r.json()[0]['devanagari'] == 'देहरादून'
    cid = r.json()[0]['id']; d = client.get(f'/api/cases/{cid}').json(); assert d['record']['roman']['recommended'] == 'Dehradun'
def test_decision_requires_officer_and_reason(client):
    cid = client.get('/api/cases').json()[0]['id']
    assert client.post(f'/api/cases/{cid}/decision', json={'officer': '', 'action': 'approve'}).status_code == 400
    assert client.post(f'/api/cases/{cid}/decision', json={'officer': 'A', 'action': 'reject'}).status_code == 400
    r = client.post(f'/api/cases/{cid}/decision', json={'officer': 'A. Officer', 'action': 'approve', 'devanagari': 'देहरादून', 'roman': 'Dehra Dun'}); assert r.status_code == 200
    assert r.json()['status'] == 'approved' and r.json()['edited_fields'] == ['roman']
    a = client.get('/api/audit').json(); assert a['ok'] and a['entries'][0]['action'] == 'approve'
    csv = client.get('/api/export.csv').text; assert 'Dehra Dun' in csv
def test_preview_derives_ipa_and_roman(client):
    p = client.get('/api/preview', params={'text': 'हल्द्वानी'}).json(); assert p['ipa'] == '/ɦəld̪ʋaːniː/' and p['roman']['scheme'] == 'Haldwani'
def test_audit_chain_detects_tamper(tmp_path):
    db = tmp_path / 'a.sqlite'; c = store.connect(db); store.audit(c, 'x', 'a'); store.audit(c, 'x', 'b')
    assert store.verify_audit(c) == (True, None)
    c.execute("UPDATE audit SET action='z' WHERE id=1"); c.commit(); assert store.verify_audit(c)[0] is False
