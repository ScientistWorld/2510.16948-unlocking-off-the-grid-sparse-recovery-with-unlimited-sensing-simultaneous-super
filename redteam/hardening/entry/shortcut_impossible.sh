#!/bin/bash
# Audit submission 'shortcut_impossible' (see redteam/hardening/variants.py).
set -euo pipefail
cd "$(dirname "$0")/../.."
python redteam/hardening/variants.py shortcut_impossible "$1" "$2"
