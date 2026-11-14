#!/bin/bash
# Audit submission 'weaker_no_unwrap' (see redteam/hardening/variants.py).
set -euo pipefail
cd "$(dirname "$0")/../.."
python redteam/hardening/variants.py weaker_no_unwrap "$1" "$2"
