"""Modulo off-grid sparse recovery following Guo & Bhandari SRes-IterSiS.

This compact implementation covers the paper's core Theorem 2 computation:
1. modulo low-dynamic-range samples y = M_lambda(g),
2. nonlinear finite-difference filtering M_lambda(Delta^h y) = Delta^h g,
3. anti-difference to recover g up to a constant,
4. continuum sparse deconvolution to estimate off-grid spike locations,
5. least-squares amplitudes and signal reconstruction.

The full robust SRes-IterSiS residue-sieving loop from Section III is not
implemented here. The benchmark targets the central acquisition claim: modulo
finite-difference recovery can preserve high-dynamic-range information under
low-bit sensing where a conventional clipped ADC loses it.
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


def finite_difference(x: np.ndarray, order: int) -> np.ndarray:
    out = np.asarray(x, dtype=np.float64)
    for _ in range(order):
        out = np.diff(out)
    return out


def anti_difference(delta: np.ndarray, order: int, length: int) -> np.ndarray:
    """Invert an h-th finite difference with zero integration constants."""

    recovered = np.asarray(delta, dtype=np.float64)
    for _ in range(order):
        integrated = np.empty(recovered.size + 1, dtype=np.float64)
        integrated[0] = 0.0
        integrated[1:] = np.cumsum(recovered)
        recovered = integrated
    if recovered.size != length:
        raise ValueError(f"expected length {length}, got {recovered.size}")
    return recovered


def recover_signal_from_modulo(
    y: np.ndarray, lambda_value: float, diff_order: int = 1
) -> np.ndarray:
    """Recover g up to polynomial integration constants by nonlinear filtering."""

    if diff_order < 1:
        raise ValueError("diff_order must be at least 1")
    delta_y = finite_difference(y, diff_order)
    delta_g = modulo(delta_y, lambda_value)
    return anti_difference(delta_g, diff_order, y.size)


def recover_trial(
    y: np.ndarray,
    k: int,
    lambda_value: float,
    sigma: float,
    period: float,
    max_freq: int,
    diff_order: int,
) -> dict[str, np.ndarray | float]:
    g_tilde = recover_signal_from_modulo(y, lambda_value, diff_order=diff_order)
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


def run_method(input_path: Path, output_path: Path, max_freq: int, diff_order: int) -> None:
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
            diff_order=diff_order,
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
        diff_order=np.array(diff_order),
        source=str(input_path),
    )
    metadata = {
        "input": str(input_path),
        "output": str(output_path),
        "max_freq": max_freq,
        "diff_order": diff_order,
    }
    output_path.with_suffix(".json").write_text(json.dumps(metadata, indent=2))
    print(f"wrote {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/synthetic/us_sres_benchmark.npz")
    parser.add_argument("--output", default="checkpoints/us_sres_outputs.npz")
    parser.add_argument("--max-freq", type=int, default=12)
    parser.add_argument("--diff-order", type=int, default=1)
    args = parser.parse_args()
    run_method(Path(args.input), Path(args.output), args.max_freq, args.diff_order)


if __name__ == "__main__":
    main()
