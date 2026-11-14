#!/bin/bash
# Audit submission 'shortcut_copy_input' (see redteam/hardening/variants.py).
set -euo pipefail
cd "$(dirname "$0")/../.."
python redteam/hardening/variants.py shortcut_copy_input "$1" "$2"
