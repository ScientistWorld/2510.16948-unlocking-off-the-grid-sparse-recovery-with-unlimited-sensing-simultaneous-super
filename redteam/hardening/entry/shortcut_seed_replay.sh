#!/bin/bash
# Audit submission 'shortcut_seed_replay' (see redteam/hardening/variants.py).
set -euo pipefail
cd "$(dirname "$0")/../.."
python redteam/hardening/variants.py shortcut_seed_replay "$1" "$2"
