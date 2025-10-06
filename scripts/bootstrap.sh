#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PATH="$PROJECT_ROOT/.venv"
PYTHON_BIN="${PYTHON_BIN:-python3}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "[bootstrap] Cannot find Python interpreter '$PYTHON_BIN'." >&2
  exit 1
fi

if [ ! -d "$VENV_PATH" ]; then
  echo "[bootstrap] Creating virtual environment in $VENV_PATH"
  "$PYTHON_BIN" -m venv "$VENV_PATH"
else
  echo "[bootstrap] Reusing existing virtual environment in $VENV_PATH"
fi

"$VENV_PATH/bin/pip" install --upgrade pip
"$VENV_PATH/bin/pip" install -r "$PROJECT_ROOT/requirements.txt"

echo "\n[bootstrap] Environment ready."
echo "[bootstrap] Activate it with: source $VENV_PATH/bin/activate"
echo "[bootstrap] Run the web UI with: flask --app app run"
echo "[bootstrap] Or execute the CLI demo with: python example_usage.py"
