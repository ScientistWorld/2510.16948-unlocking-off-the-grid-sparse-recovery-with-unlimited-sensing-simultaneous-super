#!/bin/bash
# Audit submission 'shortcut_empty' (see redteam/hardening/variants.py).
set -euo pipefail
cd "$(dirname "$0")/../.."
python redteam/hardening/variants.py shortcut_empty "$1" "$2"
