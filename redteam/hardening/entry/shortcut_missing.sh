#!/bin/bash
# Audit submission 'shortcut_missing' (see redteam/hardening/variants.py).
set -euo pipefail
cd "$(dirname "$0")/../.."
python redteam/hardening/variants.py shortcut_missing "$1" "$2"
