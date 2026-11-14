#!/bin/bash
# Audit submission 'weaker_no_itersis' (see redteam/hardening/variants.py).
set -euo pipefail
cd "$(dirname "$0")/../.."
python redteam/hardening/variants.py weaker_no_itersis "$1" "$2"
