#!/bin/bash

set -e

SCRIPT_DIR="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"
cd "$SCRIPT_DIR"
source .venv/bin/activate
python -m scripts.copilot_login

