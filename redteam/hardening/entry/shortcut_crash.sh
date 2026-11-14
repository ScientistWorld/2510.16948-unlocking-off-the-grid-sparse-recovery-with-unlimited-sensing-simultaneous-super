#!/bin/bash
# Audit submission 'shortcut_crash' (see redteam/hardening/variants.py).
set -euo pipefail
cd "$(dirname "$0")/../.."
python redteam/hardening/variants.py shortcut_crash "$1" "$2"
