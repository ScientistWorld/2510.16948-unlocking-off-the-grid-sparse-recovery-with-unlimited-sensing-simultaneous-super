#!/bin/bash
# Audit submission 'shortcut_constant' (see redteam/hardening/variants.py).
set -euo pipefail
cd "$(dirname "$0")/../.."
python redteam/hardening/variants.py shortcut_constant "$1" "$2"
