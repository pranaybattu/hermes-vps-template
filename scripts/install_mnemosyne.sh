#!/bin/sh
set -eu

if [ "$(id -u)" = 0 ]; then
  echo "Run this installer as the container hermes user; root would create inaccessible runtime state." >&2
  exit 1
fi

HERMES_HOME="${HERMES_HOME:-/opt/data}"
HERMES_PYTHON="${HERMES_PYTHON:-/opt/hermes/.venv/bin/python}"
VENV="$HERMES_HOME/venvs/mnemosyne"

if [ ! -x "$HERMES_PYTHON" ] || ! command -v hermes >/dev/null 2>&1; then
  echo "Hermes runtime was not found; Mnemosyne setup stopped." >&2
  exit 1
fi

mkdir -p "$HERMES_HOME/venvs" "$HERMES_HOME/mnemosyne/data"
if [ ! -e "$VENV" ]; then
  "$HERMES_PYTHON" -m venv "$VENV"
elif [ ! -x "$VENV/bin/python" ]; then
  echo "Mnemosyne environment exists but is incomplete; refusing to replace it." >&2
  exit 1
fi

if [ "$("$HERMES_PYTHON" -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')" != \
     "$("$VENV/bin/python" -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')" ]; then
  echo "Hermes Python version changed; review the Mnemosyne venv before upgrading it." >&2
  exit 1
fi

# A venv left by an interrupted run can lack pip; ensurepip is idempotent.
"$VENV/bin/python" -m ensurepip --upgrade
"$VENV/bin/python" -m pip install --disable-pip-version-check \
  'mnemosyne-memory[embeddings]==3.15.1' 'mnemosyne-hermes==0.7.1'

export HERMES_HOME
export MNEMOSYNE_DATA_DIR="$HERMES_HOME"
if [ -e "$HERMES_HOME/plugins/mnemosyne" ] || [ -L "$HERMES_HOME/plugins/mnemosyne" ]; then
  "$VENV/bin/mnemosyne-hermes" status
else
  # Keep the wrapper and its interpreter on Hermes' persistent data mount across image updates.
  "$VENV/bin/mnemosyne-hermes" install --mode wrapper --python "$VENV/bin/python"
fi

hermes plugins enable hermes-mnemosyne --no-allow-tool-override
hermes config set memory.provider mnemosyne
hermes memory status
