#!/bin/bash
# Audit submission 'reference_seed_alt' (see redteam/hardening/variants.py).
set -euo pipefail
cd "$(dirname "$0")/../.."
python redteam/hardening/variants.py reference_seed_alt "$1" "$2"
