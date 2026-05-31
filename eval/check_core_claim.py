"""Quality gate for reproduction jobs.

This does not replace the reusable evaluator. It only makes job failures
explicit when regenerated scores no longer support the paper's core claim.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scores", default="scoring/scores.json")
    parser.add_argument("--reference", default="scoring/reference.json")
    parser.add_argument("--min-gain-db", type=float, default=20.0)
    args = parser.parse_args()

    scores = json.loads(Path(args.scores).read_text())
    reference = json.loads(Path(args.reference).read_text())
    failures = []
    scored_experiments = scores.get("experiments", {})
    for name in reference.get("experiments", {}):
        if name not in scored_experiments:
            failures.append((name, None))
            continue
        result = scored_experiments[name].get("results", {}).get("us_sres", {})
        gain = result.get("mse_gain_over_conventional_db")
        if gain is None or gain < args.min_gain_db:
            failures.append((name, gain))

    if failures:
        details = ", ".join(
            f"{name}={gain if gain is not None else 'missing'} dB"
            for name, gain in failures
        )
        raise SystemExit(
            f"core-claim quality gate failed: expected US-SRes MSE gain "
            f">= {args.min_gain_db:.1f} dB for every experiment; got {details}"
        )

    print(
        f"core-claim quality gate passed: US-SRes gain >= "
        f"{args.min_gain_db:.1f} dB for every experiment"
    )


if __name__ == "__main__":
    main()
