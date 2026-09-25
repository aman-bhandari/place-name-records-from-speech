"""Audio loading: any container/rate → float32 mono 16 kHz; simple SNR estimate."""
import io, numpy as np, soundfile as sf, librosa
SR = 16000
def load_bytes(b, sr=SR):
    y, r = sf.read(io.BytesIO(b), dtype='float32', always_2d=True); y = y.mean(1)
    return librosa.resample(y, orig_sr=r, target_sr=sr) if r != sr else y
def load_file(path, sr=SR):
    y, _ = librosa.load(str(path), sr=sr, mono=True); return y.astype('float32')
def save(path, y, sr=SR): sf.write(str(path), y, sr, subtype='PCM_16')
def snr_db(y, frame=400, hop=160):
    """Energy-based SNR proxy: 90th-percentile frame energy over 10th-percentile (noise floor)."""
    if len(y) < frame: return 0.0
    e = np.array([np.mean(y[i:i+frame] ** 2) for i in range(0, len(y) - frame, hop)]) + 1e-10
    return float(10 * np.log10(np.percentile(e, 90) / np.percentile(e, 10)))
