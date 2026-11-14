#!/bin/bash
# Audit submission 'shortcut_nan' (see redteam/hardening/variants.py).
set -euo pipefail
cd "$(dirname "$0")/../.."
python redteam/hardening/variants.py shortcut_nan "$1" "$2"
