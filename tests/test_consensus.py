import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from p015 import consensus, phon
def clip(i, text, conf=0.9, spk=None, synthetic=False):
    return {'id': f'c{i}', 'witnesses': [{'witness': 'vakyansh', 'text': text, 'conf': conf}], 'speaker': spk or f's{i}', 'synthetic': synthetic}
def test_phone_dist_orders_confusions():
    d_ret = consensus.phone_dist(phon.phonemes('डाल'), phon.phonemes('दाल'))
    d_far = consensus.phone_dist(phon.phonemes('डाल'), phon.phonemes('माल'))
    assert 0 < d_ret < d_far
def test_reconcile_majority_not_clearest():
    # the "clearest" (highest conf) clip is wrong; three ordinary clips agree
    clips = [clip(1, 'देहरादून', 0.8), clip(2, 'देहरादुन', 0.7), clip(3, 'देहरादून', 0.75), clip(4, 'देरादून', 0.99)]
    r = consensus.reconcile(clips)
    assert r['devanagari'] == 'देहरादून' and r['ipa'] == '/d̪eːɦraːd̪uːn/' and r['roman']['scheme'] == 'Dehradun'
    assert r['confidence']['speakers'] == 4 and r['candidates'][0]['text'] == 'देहरादून'
def test_reconcile_flags_sparse_and_variant():
    clips = [clip(1, 'अल्मोड़ा'), clip(2, 'अल्मोड़ा'), clip(3, 'अल्मोड़ा'), clip(4, 'अलमोरा'), clip(5, 'अलमोरा')]
    r = consensus.reconcile(clips)
    assert r['devanagari'] == 'अल्मोड़ा'
    assert any(v['devanagari'] == 'अलमोरा' for v in r['variants'])
    r2 = consensus.reconcile(clips[:2]); assert any('needs more' in f for f in r2['flags'])
def test_existing_record_is_a_candidate_not_a_dictator():
    clips = [clip(1, 'कोटद्वार'), clip(2, 'कोटद्वार'), clip(3, 'कोटद्वार')]
    r = consensus.reconcile(clips, gazetteer=['कोटद्वारा', 'कोटद्वार'], existing={'hi': 'कोटद्वारा', 'en': 'Kotdwar'})
    assert r['devanagari'] == 'कोटद्वार' and any(c['origin'] == 'existing' for c in r['candidates'])

def test_confidence_capped_by_speakers():
    r = consensus.reconcile([clip(1, 'ईटानगर', 0.99)]); assert r['confidence']['score'] <= 54 and r['confidence']['band'] != 'high'
    r = consensus.reconcile([clip(1, 'ईटानगर'), clip(2, 'ईटानगर')]); assert r['confidence']['score'] <= 70

def test_spacing_variants_share_the_best_score():
    clips = [clip(1, 'कर्ण प्रयाग'), clip(2, 'कण प्रयाग'), clip(3, 'कर्ण प्रयाग'), clip(4, 'करण प्रयाग')]
    r = consensus.reconcile(clips, existing={'hi': 'कर्णप्रयाग', 'en': 'Karnaprayag'})
    assert r['devanagari'] == 'कर्णप्रयाग'
    r2 = consensus.reconcile(clips); assert r2['devanagari'].replace(' ', '') == 'कर्णप्रयाग'
