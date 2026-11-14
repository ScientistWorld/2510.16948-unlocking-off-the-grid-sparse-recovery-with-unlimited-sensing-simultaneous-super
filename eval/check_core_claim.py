"""Quality gate: does the reference reproduce the paper's core claim?

Checks that the registered reference method (``us_sres``) recovers the
waveform with at least ``--min-gain-db`` lower MSE than the conventional
clipping ADC in every experiment of a score file.  Diagnostic only; it is not
part of any score.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scores", default="scoring/scores_test.json")
    parser.add_argument("--method", default="us_sres")
    parser.add_argument("--min-gain-db", type=float, default=30.0)
    args = parser.parse_args()
    scores = json.loads(Path(args.scores).read_text())
    failures = []
    for name, exp in scores.get("experiments", {}).items():
        gain = exp.get("results", {}).get(args.method, {}).get("mse_gain_over_conventional_db")
        print(f"{name}: {args.method} gain = {gain}")
        if gain is None or gain < args.min_gain_db:
            failures.append(name)
    if failures:
        raise SystemExit(f"core claim NOT met (< {args.min_gain_db} dB) in: {', '.join(failures)}")
    print(f"core claim met: gain >= {args.min_gain_db} dB in every experiment")


if __name__ == "__main__":
    main()
