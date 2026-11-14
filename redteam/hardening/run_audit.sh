#!/bin/bash
# Hardening audit.  Registers every audit submission (redteam/hardening/entry)
# next to the reference in scripts/methods/, runs the no-argument train
# evaluator, replays the file-tampering shortcuts, runs the no-argument test
# evaluator, then unregisters the submissions and restores the files.
#
#   bash redteam/hardening/run_audit.sh [jobs]
set -uo pipefail
cd /home/user
JOBS="${1:-1}"
OUT=redteam/hardening/results
mkdir -p "$OUT"
rm -rf "$OUT/per_trial_train" "$OUT/per_trial_test"
for f in redteam/hardening/entry/*.sh; do cp "$f" scripts/methods/; done
echo "registered: $(ls scripts/methods | tr '\n' ' ')"

US_SRES_EVAL_PER_TRIAL_DIR="$OUT/per_trial_train" bash scripts/evaluate_train.sh --jobs "$JOBS" > "$OUT/train.log" 2>&1
echo "audit train evaluator exit status: $?"
cp scoring/scores_train.json "$OUT/audit_scores_train.json"

python redteam/hardening/tamper.py apply
US_SRES_EVAL_PER_TRIAL_DIR="$OUT/per_trial_test" bash scripts/evaluate_test.sh --jobs "$JOBS" > "$OUT/test.log" 2>&1
echo "audit test evaluator exit status: $?"
cp scoring/scores_test.json "$OUT/audit_scores_test.json"

for f in redteam/hardening/entry/*.sh; do rm -f "scripts/methods/$(basename "$f")"; done
python redteam/hardening/tamper.py restore
echo "remaining registered methods: $(ls scripts/methods | tr '\n' ' ')"
