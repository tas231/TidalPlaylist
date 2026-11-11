#!/usr/bin/env bash
# ==============================================================================
# TIDAL Playlist Manager - Launcher Script
# ==============================================================================
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

# Check if .venv exists
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    if command -v uv &> /dev/null; then
        uv venv .venv
        uv pip install -e .
    else
        python3 -m venv .venv
        source .venv/bin/activate
        pip install -e .
    fi
fi

# Activate virtual environment
source .venv/bin/activate

# Execute manager
exec python3 main.py "$@"
