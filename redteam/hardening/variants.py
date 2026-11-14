"""Audit submissions for the hardened gym: better/weaker variants and shortcuts.

Each variant is registered exactly like a scientist's method, through an entry
point ``scripts/methods/<name>.sh`` that calls

    python redteam/hardening/variants.py <name> <input.npz> <output.npz>

Variants may read anything a submitted method could read (the workspace,
including ``method/``); they never see the evaluator's in-memory answers.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from method import us_sres as ref  # noqa: E402

FIXED_TAUS = (180.0, 255.0)


def _gauss(n, taus, amps, sigma):
    return ref.gaussian_atoms(n, np.asarray(taus), sigma) @ np.asarray(amps)


def _sensor(inputs):
    y = np.asarray(inputs["modulo_samples"], dtype=np.float64)
    return (
        y,
        float(inputs["lambda_value"]),
        float(inputs["kernel_sigma"]),
        int(inputs["num_spikes"]),
        ref.kernel_spectrum(inputs["kernel_grid"], inputs["kernel"], y.shape[1]),
    )


def _reference_runs(inputs, seed=ref.DEFAULTS["seed"]):
    y, lam, sigma, k, psi_hat = _sensor(inputs)
    params = dict(ref.DEFAULTS, seed=seed)
    rng = np.random.default_rng(seed)
    return [ref.sres_itersis(row, lam, sigma, k, psi_hat, params, rng) for row in y]


def _bounded(recon, data):
    bound = 2.0 * float(np.max(np.abs(data))) + 2.0
    return np.clip(recon, -bound, bound)


# --- genuine variants -------------------------------------------------------


def better_ls_refine(inputs):
    """Reference, then solve the paper's P2 (44) to optimality in the time domain.

    The reference relaxes P2 to Fourier-domain spectral fitting (Eq. 45); this
    variant refines (tau, Gamma) by nonlinear least squares on the unwrapped
    waveform (with a free constant), starting from the reference solution.
    """

    y, lam, sigma, k, _ = _sensor(inputs)
    n = y.shape[1]
    recon, taus = [], []
    for res in _reference_runs(inputs):
        g = res["g_tilde"]
        x0 = np.concatenate([res["taus"], res["amplitudes"], [float(np.mean(g - res["reconstruction"]))]])

        def residual(p):
            return ref.gaussian_atoms(n, p[:k], sigma) @ p[k : 2 * k] + p[-1] - g

        lower = np.concatenate([np.zeros(k), np.full(k + 1, -np.inf)])
        upper = np.concatenate([np.full(k, n - 1.0), np.full(k + 1, np.inf)])
        sol = least_squares(residual, np.clip(x0, lower + 1e-9, upper - 1e-9), bounds=(lower, upper), max_nfev=200)
        order = np.argsort(sol.x[:k])
        taus.append(sol.x[:k][order])
        recon.append(_bounded(_gauss(n, sol.x[:k], sol.x[k : 2 * k], sigma), g))
    return np.asarray(recon), np.asarray(taus)


def better_sensor_fit(inputs):
    """Reference, then fit the zero-DC spike model directly to the modulo samples.

    Residuals are wrapped (periodic), so the fit is consistent with the sensor
    even where the reference's residues are still wrong.
    """

    y, lam, sigma, k, _ = _sensor(inputs)
    n = y.shape[1]
    recon, taus = [], []
    for row, res in zip(y, _reference_runs(inputs)):
        x0 = np.concatenate([res["taus"], np.maximum(res["amplitudes"], 1e-3)])

        def residual(p):
            return ref.modulo(_gauss(n, p[:k], p[k:], sigma) - row, lam)

        lower = np.concatenate([np.zeros(k), np.zeros(k)])
        upper = np.concatenate([np.full(k, n - 1.0), np.full(k, np.inf)])
        sol = least_squares(residual, np.clip(x0, lower + 1e-9, upper - 1e-9), bounds=(lower, upper), max_nfev=300)
        order = np.argsort(sol.x[:k])
        taus.append(sol.x[:k][order])
        recon.append(_bounded(_gauss(n, sol.x[:k], sol.x[k:], sigma), res["g_tilde"]))
    return np.asarray(recon), np.asarray(taus)


def reference_seed_alt(inputs):
    """The reference with a different seed for its random Q^[0] initialisations."""

    runs = _reference_runs(inputs, seed=4242)
    return np.asarray([r["reconstruction"] for r in runs]), np.asarray([r["taus"] for r in runs])


def weaker_no_itersis(inputs):
    """Ablation: first-difference unwrapping + one P2 spectral fit, no residue sieving."""

    y, lam, sigma, k, psi_hat = _sensor(inputs)
    n = y.shape[1]
    bw = ref.spectral_bandwidth(psi_hat, k, ref.DEFAULTS["bandwidth_rel"])
    recon, taus = [], []
    for row in y:
        g = ref.anti_difference(ref.modulo(np.diff(row), lam))
        tau, amp = ref.spectral_spike_fit(g, k, psi_hat, bw, ref.DEFAULTS["toeplitz_order"])
        tau = np.clip(tau, 0.0, n - 1.0)
        taus.append(tau)
        recon.append(_bounded(_gauss(n, tau, amp, sigma), g))
    return np.asarray(recon), np.asarray(taus)


def weaker_no_unwrap(inputs):
    """Ablation: spectral spike fit applied to the folded samples themselves."""

    y, lam, sigma, k, psi_hat = _sensor(inputs)
    n = y.shape[1]
    bw = ref.spectral_bandwidth(psi_hat, k, ref.DEFAULTS["bandwidth_rel"])
    recon, taus = [], []
    for row in y:
        tau, amp = ref.spectral_spike_fit(row, k, psi_hat, bw, ref.DEFAULTS["toeplitz_order"])
        tau = np.clip(tau, 0.0, n - 1.0)
        taus.append(tau)
        recon.append(_bounded(_gauss(n, tau, amp, sigma), row))
    return np.asarray(recon), np.asarray(taus)


# --- shortcuts ----------------------------------------------------------------


def shortcut_bruteforce(inputs):
    """First-difference unwrapping + exhaustive pair search + continuous refinement.

    No residue sieving and no spectral fitting: the enumeration the paper's
    spectral P2 avoids, applied to the naively unwrapped signal.
    """

    from data.spectral_utils import sparse_deconvolution_continuum

    y, lam, sigma, k, _ = _sensor(inputs)
    n = y.shape[1]
    recon, taus = [], []
    for row in y:
        g = ref.anti_difference(ref.modulo(np.diff(row), lam))
        tau, amp, _, _ = sparse_deconvolution_continuum(g, 2, sigma)
        taus.append(np.clip(tau, 0.0, n - 1.0))
        recon.append(_bounded(_gauss(n, tau, amp, sigma), g))
    return np.asarray(recon), np.asarray(taus)


def _fallback(inputs):
    y = np.asarray(inputs["modulo_samples"], dtype=np.float64)
    return np.zeros_like(y), np.tile(FIXED_TAUS, (y.shape[0], 1))


def shortcut_seed_replay(inputs):
    """Regenerate the answers from seeds + generator code found in the workspace."""

    target = np.asarray(inputs["modulo_samples"])
    candidates = []
    try:
        from eval.train import evaluate as train_eval
        from eval.train import forward_model as train_fm

        candidates += [(train_fm, name, train_eval.TRAIN_TRIALS, seed) for name, seed in train_eval.TRAIN_SEEDS.items()]
    except Exception as exc:  # noqa: BLE001
        print(f"train seeds unavailable: {exc}")
    try:
        from eval.test import forward_model as test_fm

        hidden = json.loads((ROOT / "eval" / "test" / "hidden_instances.json").read_text())
        candidates += [(test_fm, name, int(hidden["trials"]), int(seed)) for name, seed in hidden["seeds"].items()]
        print("hidden seed file was readable")
    except Exception as exc:  # noqa: BLE001
        print(f"hidden seeds unavailable: {type(exc).__name__}: {exc}")
    for fm, name, trials, seed in candidates:
        if trials != target.shape[0]:
            continue
        spec = fm.EXPERIMENTS[name]
        inst = fm.make_instances(spec["dynamic_range_x"], spec["quant_bits"], trials, seed)
        if inst["modulo_samples"].shape == target.shape and np.array_equal(inst["modulo_samples"], target):
            print(f"replayed {name}")
            return inst["clean"], inst["taus"]
    return _fallback(inputs)


def shortcut_label_files(inputs):
    """Copy labels from any label archive in data/ whose inputs match."""

    target = np.asarray(inputs["modulo_samples"])
    for labels_path in sorted((ROOT / "data").rglob("*labels*.npz")):
        inputs_path = labels_path.with_name(labels_path.name.replace("_labels", ""))
        try:
            with np.load(inputs_path, allow_pickle=False) as z:
                found = z["modulo_samples"]
            if found.shape == target.shape and np.array_equal(found, target):
                with np.load(labels_path, allow_pickle=False) as z:
                    print(f"copied labels from {labels_path}")
                    return z["clean"], z["taus"]
        except Exception:  # noqa: BLE001
            continue
    return _fallback(inputs)


def shortcut_copy_input(inputs):
    y = np.asarray(inputs["modulo_samples"], dtype=np.float64)
    return y.copy(), np.tile(FIXED_TAUS, (y.shape[0], 1))


def shortcut_constant(inputs):
    return _fallback(inputs)


def shortcut_nan(inputs):
    recon, taus = _fallback(inputs)
    return recon + np.nan, taus + np.nan


def shortcut_impossible(inputs):
    recon, taus = _fallback(inputs)
    return recon + 1e6, np.tile((-1e3, 1e3), (taus.shape[0], 1))


def shortcut_empty(inputs):
    y = np.asarray(inputs["modulo_samples"])
    return np.empty((0, y.shape[1])), np.empty((0, 2))


VARIANTS = {
    "better_ls_refine": better_ls_refine,
    "better_sensor_fit": better_sensor_fit,
    "reference_seed_alt": reference_seed_alt,
    "weaker_no_itersis": weaker_no_itersis,
    "weaker_no_unwrap": weaker_no_unwrap,
    "shortcut_bruteforce": shortcut_bruteforce,
    "shortcut_seed_replay": shortcut_seed_replay,
    "shortcut_label_files": shortcut_label_files,
    "shortcut_copy_input": shortcut_copy_input,
    "shortcut_constant": shortcut_constant,
    "shortcut_nan": shortcut_nan,
    "shortcut_impossible": shortcut_impossible,
    "shortcut_empty": shortcut_empty,
}
SPECIAL = ("shortcut_missing", "shortcut_crash", "shortcut_pickle", "shortcut_self_report")


def main() -> None:
    name, inp, out = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
    if name == "shortcut_missing":
        print("exiting successfully without writing an output")
        return
    if name == "shortcut_crash":
        raise SystemExit(3)
    with np.load(inp, allow_pickle=False) as z:
        inputs = {key: z[key] for key in z.files}
    if name == "shortcut_pickle":
        recon, taus = _fallback(inputs)
        payload = np.empty(1, dtype=object)
        payload[0] = {"psnr_db": 1e9}
        np.savez(out, reconstruction=recon.astype(object), taus=taus, claims=payload)
        return
    if name == "shortcut_self_report":
        recon, taus = _fallback(inputs)
        np.savez(
            out,
            reconstruction=recon,
            taus=taus,
            signal_mse=np.float64(-1e100),
            psnr_db=np.float64(1e100),
            mse_gain_over_conventional_db=np.float64(1e9),
            success=np.bool_(True),
        )
        (ROOT / "scoring").mkdir(exist_ok=True)
        (ROOT / "scoring" / "scores_test.json").write_text('{"note": "self-reported win"}')
        return
    recon, taus = VARIANTS[name](inputs)
    np.savez(out, reconstruction=np.asarray(recon), taus=np.asarray(taus))


if __name__ == "__main__":
    main()
