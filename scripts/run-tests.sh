#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}/backend"
export OPENAI_API_KEY="${OPENAI_API_KEY:-ci-dummy-openai-key}"
export AUTH_DISABLED="${AUTH_DISABLED:-true}"
python3 -m pip install -q -r requirements.txt -r requirements-dev.txt
exec python3 -m pytest -v
