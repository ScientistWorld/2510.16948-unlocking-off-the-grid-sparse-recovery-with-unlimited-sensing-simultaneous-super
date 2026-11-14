#!/bin/bash
set -euo pipefail
cd /home/user
python -u redteam/audit.py weaker_no_unwrap
