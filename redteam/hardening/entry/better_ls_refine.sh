#!/bin/bash
# Audit submission 'better_ls_refine' (see redteam/hardening/variants.py).
set -euo pipefail
cd "$(dirname "$0")/../.."
python redteam/hardening/variants.py better_ls_refine "$1" "$2"
