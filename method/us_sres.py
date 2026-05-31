"""Modulo off-grid sparse recovery following Guo & Bhandari SRes-IterSiS.

This compact implementation covers the paper's core noiseless computation:
1. modulo low-dynamic-range samples y = M_lambda(g),
2. nonlinear finite-difference filtering M_lambda(Delta y) = Delta g,
3. anti-difference to recover g up to a constant,
4. continuum sparse deconvolution to estimate off-grid spike locations,
5. least-squares amplitudes and signal reconstruction.

The benchmark uses the exact nonlinear filtering path from Theorem 2, which is
the paper's central algorithm. Its P2 spike-estimation objective is solved by
direct continuum least-squares refinement instead of the paper's matrix-pencil
initializer because the synthetic nonperiodic Gaussian substitute is
ill-conditioned for the plain Fourier-ratio pencil.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from data.spectral_utils import sparse_deconvolution_continuum


def modulo(x: np.ndarray, lambda_value: float) -> np.ndarray:
    return 2.0 * lambda_value * (
        np.mod(x / (2.0 * lambda_value) + 0.5, 1.0) - 0.5
    )


def recover_signal_from_modulo(y: np.ndarray, lambda_value: float) -> np.ndarray:
    """Recover g up to an additive constant by nonlinear difference filtering."""

    delta_y = np.diff(y)
    delta_g = modulo(delta_y, lambda_value)
    g_tilde = np.empty_like(y, dtype=np.float64)
    g_tilde[0] = 0.0
    g_tilde[1:] = np.cumsum(delta_g)
    return g_tilde


def recover_trial(
    y: np.ndarray,
    k: int,
    lambda_value: float,
    sigma: float,
    period: float,
    max_freq: int,
) -> dict[str, np.ndarray | float]:
    g_tilde = recover_signal_from_modulo(y, lambda_value)
    del period, max_freq
    taus, amps, offset, reconstruction = sparse_deconvolution_continuum(
        g_tilde, k, sigma
    )
    return {
        "signal_recovered_up_to_offset": g_tilde,
        "taus": taus,
        "amplitudes": amps,
        "offset": offset,
        "reconstruction": reconstruction,
    }


def run_method(input_path: Path, output_path: Path, max_freq: int) -> None:
    data = np.load(input_path, allow_pickle=True)
    config = data["config"][0]
    samples = data["modulo_samples"]
    all_taus = []
    all_recon = []
    all_gtilde = []
    for y in samples:
        recovered = recover_trial(
            y=y,
            k=2,
            lambda_value=float(config["lambda_value"]),
            sigma=float(config["sigma"]),
            period=float(config["period"]),
            max_freq=max_freq,
        )
        all_taus.append(recovered["taus"])
        all_recon.append(recovered["reconstruction"])
        all_gtilde.append(recovered["signal_recovered_up_to_offset"])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        output_path,
        method=np.array("us_sres"),
        taus=np.asarray(all_taus),
        reconstruction=np.asarray(all_recon),
        g_tilde=np.asarray(all_gtilde),
        source=str(input_path),
    )
    metadata = {"input": str(input_path), "output": str(output_path), "max_freq": max_freq}
    output_path.with_suffix(".json").write_text(json.dumps(metadata, indent=2))
    print(f"wrote {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/synthetic/us_sres_benchmark.npz")
    parser.add_argument("--output", default="checkpoints/us_sres_outputs.npz")
    parser.add_argument("--max-freq", type=int, default=12)
    args = parser.parse_args()
    run_method(Path(args.input), Path(args.output), args.max_freq)


if __name__ == "__main__":
    main()
