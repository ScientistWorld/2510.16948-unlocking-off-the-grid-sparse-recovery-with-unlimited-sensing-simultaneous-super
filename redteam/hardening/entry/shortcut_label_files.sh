#!/bin/bash
# Audit submission 'shortcut_label_files' (see redteam/hardening/variants.py).
set -euo pipefail
cd "$(dirname "$0")/../.."
python redteam/hardening/variants.py shortcut_label_files "$1" "$2"
