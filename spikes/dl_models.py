import sys
from huggingface_hub import snapshot_download
for m in sys.argv[1:]:
    try:
        p = snapshot_download(m, allow_patterns=['*.json', '*.txt', '*.safetensors', 'pytorch_model.bin', '*.model', '*.py', '*.yaml', '*.tiktoken'])
        print('OK', m, p, flush=True)
    except Exception as e:
        print('FAIL', m, type(e).__name__, str(e)[:200], flush=True)
