#!/bin/bash
# Audit submission 'better_sensor_fit' (see redteam/hardening/variants.py).
set -euo pipefail
cd "$(dirname "$0")/../.."
python redteam/hardening/variants.py better_sensor_fit "$1" "$2"
