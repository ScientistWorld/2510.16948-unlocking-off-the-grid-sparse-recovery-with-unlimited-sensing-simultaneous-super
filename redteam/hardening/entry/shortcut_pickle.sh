#!/bin/bash
# Audit submission 'shortcut_pickle' (see redteam/hardening/variants.py).
set -euo pipefail
cd "$(dirname "$0")/../.."
python redteam/hardening/variants.py shortcut_pickle "$1" "$2"
