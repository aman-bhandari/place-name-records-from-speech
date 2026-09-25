"""Speaker embeddings (WavLM x-vectors) to tell distinct speakers apart when a corpus has no speaker ids."""
import numpy as np, torch
from transformers import WavLMForXVector, Wav2Vec2FeatureExtractor
REPO = 'microsoft/wavlm-base-plus-sv'; SAME = 0.86   # cosine threshold from the model card
class SpeakerModel:
    def __init__(self, device=None):
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.fe = Wav2Vec2FeatureExtractor.from_pretrained(REPO); self.m = WavLMForXVector.from_pretrained(REPO).to(self.device).eval()
    @torch.no_grad()
    def embed(self, wav, max_s=12):
        x = self.fe(wav[:16000 * max_s], sampling_rate=16000, return_tensors='pt').input_values.to(self.device)
        e = self.m(x).embeddings[0]; return torch.nn.functional.normalize(e, dim=-1).cpu().numpy().astype('float32')
def cluster(embs, thr=SAME):
    """Single-link clustering by cosine similarity; returns cluster id per embedding."""
    n = len(embs); parent = list(range(n))
    def find(x):
        while parent[x] != x: x = parent[x]
        return x
    for i in range(n):
        for j in range(i + 1, n):
            if float(embs[i] @ embs[j]) >= thr: parent[find(i)] = find(j)
    roots = {}; return [roots.setdefault(find(i), len(roots)) for i in range(n)]
