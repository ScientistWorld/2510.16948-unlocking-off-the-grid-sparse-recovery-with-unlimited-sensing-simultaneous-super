#!/bin/bash
# Audit submission 'shortcut_self_report' (see redteam/hardening/variants.py).
set -euo pipefail
cd "$(dirname "$0")/../.."
python redteam/hardening/variants.py shortcut_self_report "$1" "$2"
