#!/usr/bin/env bash
# Eknaam (P-015) — build | serve | test | mine | ui
set -e; cd "$(dirname "$0")"; PY=.venv/bin/python
case "${1:-serve}" in
  serve) exec .venv/bin/uvicorn api.main:app --host 127.0.0.1 --port 8015 ;;
  test)  exec $PY -m pytest -q tests ;;
  mine)  shift; exec $PY p015/mine.py "$@" ;;
  build) shift; exec $PY p015/build.py "$@" ;;
  eval)  shift; exec $PY eval/consensus_eval.py "$@" ;;
  ui)    (cd ui && npm install --silent && npm run build) ;;
  *) echo "usage: $0 serve|test|mine|build|eval|ui"; exit 1 ;;
esac
