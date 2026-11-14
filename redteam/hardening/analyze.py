"""Summarise the hardening audit: scores, paired comparisons and illustrative ranks.

Reads the audit score files written by the no-argument evaluators (all audit
submissions registered at once), the per-trial error dumps and the official
reference-only scores, and writes ``redteam/hardening/results/summary.json``.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "redteam" / "hardening" / "results"
REFERENCE = "us_sres"
HONEST = [
    "us_sres",
    "conventional_clip_sres",
    "better_ls_refine",
    "better_sensor_fit",
    "reference_seed_alt",
    "weaker_no_itersis",
    "weaker_no_unwrap",
    "shortcut_bruteforce",
]


def load(path: Path):
    return json.loads(path.read_text()) if path.exists() else None


def rank_deltas(scores: dict, ref_json: dict, population: list[str]) -> dict[str, float]:
    exps = scores["experiments"]
    methods = sorted(set().union(*[set(e["results"]) for e in exps.values()]))
    out = {}
    for cand in methods:
        total = 0.0
        for name, exp in exps.items():
            spec = ref_json["experiments"][name]
            res = exp["results"]
            if cand not in res or REFERENCE not in res:
                continue
            contrib = 0.0
            for metric, mdef in spec["metrics"].items():
                vals = [res[m][metric] for m in population if m in res]
                std = float(np.std(vals)) if len(vals) > 1 else 0.0
                if std <= 0.0:
                    continue
                direction = 1.0 if mdef["higher_is_better"] else -1.0
                contrib += abs(mdef["coefficient"]) * direction * (res[cand][metric] - res[REFERENCE][metric]) / std
            total += spec["weight"] * contrib
        out[cand] = total
    return out


def paired(per_dir: Path, cand: str, exp: str, rng: np.random.Generator, reps: int = 2000) -> dict | None:
    a = per_dir / f"{cand}__{exp}.npz"
    b = per_dir / f"{REFERENCE}__{exp}.npz"
    c = per_dir / f"conventional_clip_sres__{exp}.npz"
    if not (a.exists() and b.exists() and c.exists()):
        return None
    with np.load(a) as za, np.load(b) as zb, np.load(c) as zc:
        mse_c, mse_r, mse_b = za["mse"], zb["mse"], zc["mse"]
        err_c, err_r = za["tau_err"].mean(axis=1), zb["tau_err"].mean(axis=1)
        weak_c, weak_r = za["weak_err"], zb["weak_err"]
        psnr_c, psnr_r = za["psnr"], zb["psnr"]
    t = mse_c.size
    idx = rng.integers(0, t, size=(reps, t))
    gain_diff = 10 * np.log10(mse_r[idx].mean(axis=1) / np.maximum(mse_c[idx].mean(axis=1), 1e-12))
    out = {
        "trials": int(t),
        "gain_diff_db": float(10 * np.log10(mse_r.mean() / max(mse_c.mean(), 1e-12))),
        "gain_diff_db_ci95": [float(np.percentile(gain_diff, 2.5)), float(np.percentile(gain_diff, 97.5))],
    }
    for label, x, y in (("psnr_diff_db", psnr_c, psnr_r), ("tau_err_diff", err_c, err_r), ("weak_err_diff", weak_c, weak_r)):
        d = x - y
        boot = d[idx].mean(axis=1)
        out[label] = float(d.mean())
        out[f"{label}_ci95"] = [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))]
    out["trials_better_mse"] = float(np.mean(mse_c < mse_r))
    out["conventional_pooled_mse"] = float(mse_b.mean())
    return out


def main() -> None:
    ref_json = json.loads((ROOT / "scoring" / "reference.json").read_text())
    summary: dict = {}
    rng = np.random.default_rng(0)
    for split in ("test", "train"):
        scores = load(RES / f"audit_scores_{split}.json")
        if scores is None:
            continue
        exps = scores["experiments"]
        methods = sorted(set().union(*[set(e["results"]) for e in exps.values()]))
        block = {"metrics": {}, "status": {}, "paired_vs_reference": {}, "rank_delta": {}}
        for m in methods:
            block["metrics"][m] = {name: exp["results"].get(m) for name, exp in exps.items()}
            block["status"][m] = {name: exp["status"].get(m) for name, exp in exps.items()}
        per_dir = RES / f"per_trial_{split}"
        for m in methods:
            if m == REFERENCE:
                continue
            block["paired_vs_reference"][m] = {name: paired(per_dir, m, name, rng) for name in exps}
        block["rank_delta"]["honest_population"] = rank_deltas(scores, ref_json, [m for m in HONEST if m in methods])
        block["rank_delta"]["all_population"] = rank_deltas(scores, ref_json, methods)
        summary[split] = block

        print(f"\n## {split}: mean over experiments")
        print("| method | gain dB | PSNR dB | time MAE | weak MAE | sep err | dR honest | dR all |")
        print("|---|---:|---:|---:|---:|---:|---:|---:|")
        for m in methods:
            rows = [exps[name]["results"][m] for name in exps]
            mean = {k: float(np.mean([r[k] for r in rows])) for k in rows[0]}
            print(
                f"| {m} | {mean['mse_gain_over_conventional_db']:.2f} | {mean['psnr_db']:.2f} | "
                f"{mean['time_mae_samples']:.3f} | {mean['weak_tau_mae_samples']:.3f} | "
                f"{mean['separation_error_samples']:.3f} | "
                f"{block['rank_delta']['honest_population'].get(m, float('nan')):+.3f} | "
                f"{block['rank_delta']['all_population'].get(m, float('nan')):+.3f} |"
            )
        print(f"\n## {split}: per-experiment gain (dB) / time MAE")
        names = list(exps)
        print("| method | " + " | ".join(names) + " |")
        print("|---|" + "---:|" * len(names))
        for m in methods:
            cells = [
                f"{exps[n]['results'][m]['mse_gain_over_conventional_db']:.2f} / {exps[n]['results'][m]['time_mae_samples']:.3f}"
                for n in names
            ]
            print(f"| {m} | " + " | ".join(cells) + " |")
        print(f"\n## {split}: paired gain difference vs reference (dB, 95% CI)")
        for m, per in block["paired_vs_reference"].items():
            cells = []
            for n in names:
                p = per.get(n)
                cells.append("n/a" if p is None else f"{p['gain_diff_db']:+.2f} [{p['gain_diff_db_ci95'][0]:+.2f},{p['gain_diff_db_ci95'][1]:+.2f}]")
            print(f"| {m} | " + " | ".join(cells) + " |")

    official = load(ROOT / "scoring" / "scores_test.json")
    audit = load(RES / "audit_scores_test.json")
    if official and audit:
        same = all(
            official["experiments"][n]["results"].get(REFERENCE) == audit["experiments"][n]["results"].get(REFERENCE)
            and official["experiments"][n]["results"].get("conventional_clip_sres")
            == audit["experiments"][n]["results"].get("conventional_clip_sres")
            for n in official["experiments"]
        )
        summary["reference_unchanged_by_tampering"] = bool(same)
        print(f"\nreference + baseline scores identical with and without tampering: {same}")
    (RES / "summary.json").write_text(json.dumps(summary, indent=1))
    print(f"wrote {RES / 'summary.json'}")


if __name__ == "__main__":
    main()
