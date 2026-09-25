#!/usr/bin/env bash
# Eknaam (UKIS 2026 P-015) — one entry point for everything.
#   ./run.sh serve              API + interface on http://127.0.0.1:8015 (needs ui/dist: run ./run.sh ui once)
#   ./run.sh test               pytest: phonology, consensus, API, audit chain (uses the committed data/p015.sqlite)
#   ./run.sh ui                 build the interface into ui/dist
#   ./run.sh dev                Vite dev server on http://127.0.0.1:5185 (proxies /api to 8015)
#   ./run.sh audio              fetch the mined clips (53 MB) from the GitHub release so replay works without re-mining
#   ./run.sh ui-check [url]     Playwright interface check (npm install && npx playwright install chromium first)
#   ./run.sh mine [...]         mine clips from Shrutilipi / IndicVoices (Hugging Face login + accepted terms; GPU; resumable)
#   ./run.sh build [--rebuild]  witnesses + consensus -> data/p015.sqlite (downloads ~4 GB of models on first use)
#   ./run.sh eval [--noise]     docs/RESULTS numbers -> data/eval.json
set -e; cd "$(dirname "$0")"
PY=.venv/bin/python; [ -x "$PY" ] || PY=python
REPO="${REPO:-aman-bhandari/ukis-p015}"   # GitHub repo that carries the demo-audio release

# Playwright scripts run with the repo's own node_modules; a global launcher is used only as a fallback.
pw() {
  if [ -d node_modules/playwright ]; then node "$@"
  else echo "Playwright is not installed here. Run:  npm install && npx playwright install chromium"; exit 1; fi
}

case "${1:-serve}" in
  serve) [ -d ui/dist ] || echo "ui/dist missing: the API will run without the interface (./run.sh ui builds it)"
         exec .venv/bin/uvicorn api.main:app --host 127.0.0.1 --port "${PORT:-8015}" ;;
  test)  exec $PY -m pytest -q tests ;;
  ui)    (cd ui && npm install --silent && npm run build) ;;
  dev)   (cd ui && npm install --silent && exec npm run dev) ;;
  audio) command -v gh >/dev/null || { echo "needs the GitHub CLI (https://cli.github.com), logged in with access to $REPO"; exit 1; }
         gh release download demo-audio --repo "$REPO" --pattern 'eknaam-audio.tar.gz' --clobber -D data
         tar xzf data/eknaam-audio.tar.gz -C data && rm -f data/eknaam-audio.tar.gz
         echo "clips restored under data/audio ($(find data/audio -type f | wc -l) files)" ;;
  ui-check) shift; pw ui/check/ui_check.cjs "$@" ;;
  mine)  shift; exec $PY p015/mine.py "$@" ;;
  build) shift; exec $PY p015/build.py "$@" ;;
  eval)  shift; exec $PY eval/consensus_eval.py "$@" ;;
  *) echo "usage: $0 serve|test|ui|dev|audio|ui-check|mine|build|eval"; exit 1 ;;
esac
