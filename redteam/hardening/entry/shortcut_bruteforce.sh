#!/bin/bash
# Audit submission 'shortcut_bruteforce' (see redteam/hardening/variants.py).
set -euo pipefail
cd "$(dirname "$0")/../.."
python redteam/hardening/variants.py shortcut_bruteforce "$1" "$2"
