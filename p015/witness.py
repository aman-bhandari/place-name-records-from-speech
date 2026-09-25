"""Acoustic witnesses: CTC models that turn a clip into Devanagari (or phones) with a confidence."""
import json, numpy as np, torch
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor, Wav2Vec2FeatureExtractor
from huggingface_hub import hf_hub_download
FRAME = 320  # samples per CTC frame at 16 kHz (20 ms)
HINDI_MODELS = {'vakyansh': 'Harveenchadha/vakyansh-wav2vec2-hindi-him-4200', 'indicw2v': 'ai4bharat/indicwav2vec-hindi'}
PHONE_MODEL = 'facebook/wav2vec2-xlsr-53-espeak-cv-ft'

class CTCWitness:
    def __init__(self, repo, device=None, name=None):
        self.repo, self.name = repo, name or repo.split('/')[-1]
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.fe = Wav2Vec2FeatureExtractor.from_pretrained(repo)
        self.vocab = json.load(open(hf_hub_download(repo, 'vocab.json')))
        self.inv = {v: k for k, v in self.vocab.items()}
        self.blank = self.vocab.get('<pad>', 0); self.delim = self.vocab.get('|')
        self.model = Wav2Vec2ForCTC.from_pretrained(repo).to(self.device).eval()
    @torch.no_grad()
    def emissions(self, wav):
        x = self.fe(wav, sampling_rate=16000, return_tensors='pt').input_values.to(self.device)
        return self.model(x).logits[0].log_softmax(-1).float().cpu().numpy()
    def greedy(self, logp):
        ids = logp.argmax(-1); out, prev, confs = [], -1, []
        for t, i in enumerate(ids):
            if i != prev and i != self.blank:
                tok = self.inv.get(int(i), ''); out.append(' ' if tok == '|' else ('' if tok.startswith('<') else tok)); confs.append(float(np.exp(logp[t, i])))
            prev = i
        text = ''.join(out).strip()
        return text, (float(np.mean(confs)) if confs else 0.0)
    def transcribe(self, wav):
        logp = self.emissions(wav); text, conf = self.greedy(logp)
        return {'witness': self.name, 'text': text, 'conf': conf, 'frames': int(logp.shape[0])}
    def tokens(self, text):
        """Map text → (token ids, char index per token); chars not in the vocab are skipped."""
        ids, pos = [], []
        for i, ch in enumerate(text):
            t = '|' if ch.isspace() else ch
            if t in self.vocab and not t.startswith('<'):
                if t == '|' and (not ids or ids[-1] == self.delim): continue
                ids.append(self.vocab[t]); pos.append(i)
        return ids, pos

class PhoneWitness(CTCWitness):
    """Language-independent phone recogniser (espeak phone set); output is space-separated phones."""
    def __init__(self, device=None): super().__init__(PHONE_MODEL, device, 'phones')
    def greedy(self, logp):
        ids = logp.argmax(-1); out, prev, confs = [], -1, []
        for t, i in enumerate(ids):
            if i != prev and i != self.blank:
                tok = self.inv.get(int(i), '')
                if tok and not tok.startswith('<') and tok != '|': out.append(tok); confs.append(float(np.exp(logp[t, i])))
            prev = i
        return ' '.join(out), (float(np.mean(confs)) if confs else 0.0)
