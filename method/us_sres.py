"""Modulo off-grid sparse recovery following Guo & Bhandari US-SRes.

This compact implementation covers the paper's core computation:
1. modulo low-dynamic-range samples y = M_lambda(g),
2. nonlinear finite-difference filtering M_lambda(Delta^h y) = Delta^h g,
3. IterSiS-style sparse fold-residue refinement with rational P/Q fitting,
4. anti-difference to recover g up to a constant,
5. spectral matrix-pencil initialization for off-grid spike locations,
6. least-squares refinement of amplitudes and continuous spike times.

The hardware paper uses richer calibration and multiple random initializations.
This version keeps the same computational structure at compact synthetic scale.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from data.spectral_utils import (
    fit_amplitudes_and_offset,
    matrix_pencil_spikes,
    refine_spikes_from_initial,
    sparse_deconvolution_continuum,
)


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


def quantize_residue(epsilon: np.ndarray, lambda_value: float) -> np.ndarray:
    """Eq. 43 residue quantizer onto the fold lattice 2 lambda Z."""

    return 2.0 * lambda_value * np.floor((np.real(epsilon) + lambda_value) / (2.0 * lambda_value))


def _fourier_vandermonde(length: int, degree: int) -> np.ndarray:
    n = np.arange(length, dtype=np.float64)
    powers = np.arange(degree, dtype=np.float64)
    return np.exp(1j * 2.0 * np.pi * n[:, None] * powers[None, :] / length)


def _seed_denominator(length: int, degree: int, positions: np.ndarray) -> np.ndarray:
    if degree <= 0:
        return np.ones(1, dtype=np.complex128)
    roots = np.exp(1j * 2.0 * np.pi * positions[:degree] / length)
    coeffs_desc = np.poly(roots)
    coeffs = coeffs_desc[::-1].astype(np.complex128)
    norm = np.linalg.norm(coeffs)
    if norm == 0.0:
        coeffs[0] = 1.0
        norm = 1.0
    return coeffs / norm


def rational_residue_recovery(
    epsilon_seed: np.ndarray,
    fold_count: int,
    lambda_value: float,
    inner_iters: int = 4,
    initializations: int = 3,
) -> np.ndarray:
    """P1 residue recovery via the paper's rational P/Q weighted LS form.

    This implements the algebraic loop in Eqs. 38-43 on the discrete grid:
    fit epsilon[n] ~= P(xi^n) / Q(xi^n), then quantize the estimate onto
    the valid fold-residue lattice 2 lambda Z.
    """

    x = np.asarray(epsilon_seed, dtype=np.float64)
    length = x.size
    degree = int(max(0, min(fold_count, length // 3)))
    if degree == 0:
        return np.zeros_like(x)

    largest = np.argsort(np.abs(x))[::-1]
    if largest.size < degree:
        return quantize_residue(x, lambda_value)

    wq = _fourier_vandermonde(length, degree + 1)
    wp = _fourier_vandermonde(length, degree)
    best_error = np.inf
    best_epsilon = quantize_residue(x, lambda_value)
    rng = np.random.default_rng(16948 + degree + length)

    for init_idx in range(initializations):
        if init_idx == 0:
            positions = largest
        else:
            jitter = rng.integers(-2, 3, size=degree)
            positions = (largest[:degree] + jitter) % length
        q0 = _seed_denominator(length, degree, positions)
        q = q0.copy()
        p = np.zeros(degree, dtype=np.complex128)

        for _ in range(inner_iters):
            q_eval = wq @ q
            weights = 1.0 / np.maximum(np.abs(q_eval), 1e-6)
            a_left = (x * weights)[:, None] * wq
            a_right = -(weights[:, None] * wp)
            a = np.hstack([a_left, a_right])
            b = np.concatenate([q0, np.zeros(degree, dtype=np.complex128)])
            normal = a.conj().T @ a
            normal += 1e-8 * np.eye(normal.shape[0], dtype=np.complex128)
            try:
                unconstrained = np.linalg.solve(normal, b)
            except np.linalg.LinAlgError:
                unconstrained = np.linalg.pinv(normal) @ b
            denom = np.vdot(b, unconstrained)
            if abs(denom) < 1e-12:
                break
            z = unconstrained / denom
            q = z[: degree + 1]
            p = z[degree + 1 :]

        q_eval = wq @ q
        p_eval = wp @ p
        safe_q = np.where(np.abs(q_eval) < 1e-8, 1e-8 + 0.0j, q_eval)
        epsilon = quantize_residue(p_eval / safe_q, lambda_value)
        error = float(np.mean((x - epsilon) ** 2))
        if error < best_error:
            best_error = error
            best_epsilon = epsilon

    return best_epsilon


def recover_signal_from_modulo(
    y: np.ndarray, lambda_value: float, diff_order: int = 1
) -> np.ndarray:
    """Recover g up to polynomial integration constants by nonlinear filtering."""

    if diff_order < 1:
        raise ValueError("diff_order must be at least 1")
    delta_y = finite_difference(y, diff_order)
    delta_g = modulo(delta_y, lambda_value)
    return anti_difference(delta_g, diff_order, y.size)


def spectral_spike_estimation(
    signal: np.ndarray,
    k: int,
    sigma: float,
    period: float,
    max_freq: int,
) -> tuple[np.ndarray, np.ndarray, float, np.ndarray, str]:
    """P2 spectral fitting with a continuum fallback for the Gaussian benchmark."""

    candidates: list[tuple[float, np.ndarray, np.ndarray, float, np.ndarray, str]] = []
    try:
        pencil_taus = matrix_pencil_spikes(signal, k, sigma, period, max_freq=max_freq)
        refined = refine_spikes_from_initial(signal, pencil_taus, sigma)
        resid = signal - refined[3]
        candidates.append((float(resid @ resid), *refined, "matrix_pencil"))
    except Exception:
        pass

    continuum = sparse_deconvolution_continuum(signal, k, sigma)
    resid = signal - continuum[3]
    candidates.append((float(resid @ resid), *continuum, "continuum_fallback"))
    _, taus, amps, offset, reconstruction, solver = min(candidates, key=lambda item: item[0])
    return taus, amps, offset, reconstruction, solver


def recover_trial_itersis(
    y: np.ndarray,
    k: int,
    lambda_value: float,
    sigma: float,
    period: float,
    max_freq: int,
    fold_count: int,
    outer_iters: int = 1,
) -> dict[str, np.ndarray | float | str]:
    """Compact SRes-IterSiS loop for Section III P1/P2 recovery."""

    dy = finite_difference(y, 1)
    g_tilde = recover_signal_from_modulo(y, lambda_value, diff_order=1)
    taus, amps, offset, reconstruction, solver = spectral_spike_estimation(
        g_tilde, k, sigma, period, max_freq
    )

    epsilon_seed = finite_difference(reconstruction, 1) - dy
    epsilon = quantize_residue(epsilon_seed, lambda_value)
    for _ in range(outer_iters):
        epsilon = rational_residue_recovery(epsilon_seed, fold_count, lambda_value)
        g_tilde = anti_difference(dy + epsilon, 1, y.size)
        taus, amps, offset, reconstruction, solver = spectral_spike_estimation(
            g_tilde, k, sigma, period, max_freq
        )
        epsilon_seed = finite_difference(reconstruction, 1) - dy

    return {
        "signal_recovered_up_to_offset": g_tilde,
        "fold_residue": epsilon,
        "taus": taus,
        "amplitudes": amps,
        "offset": offset,
        "reconstruction": reconstruction,
        "p2_solver": solver,
    }


def recover_trial(
    y: np.ndarray,
    k: int,
    lambda_value: float,
    sigma: float,
    period: float,
    max_freq: int,
    diff_order: int,
    fold_count: int | None = None,
) -> dict[str, np.ndarray | float]:
    if diff_order == 1 and fold_count is not None:
        return recover_trial_itersis(
            y=y,
            k=k,
            lambda_value=lambda_value,
            sigma=sigma,
            period=period,
            max_freq=max_freq,
            fold_count=fold_count,
        )
    g_tilde = recover_signal_from_modulo(y, lambda_value, diff_order=diff_order)
    taus, amps, offset, reconstruction, solver = spectral_spike_estimation(
        g_tilde, k, sigma, period, max_freq
    )
    return {
        "signal_recovered_up_to_offset": g_tilde,
        "taus": taus,
        "amplitudes": amps,
        "offset": offset,
        "reconstruction": reconstruction,
        "p2_solver": solver,
    }


def run_method(input_path: Path, output_path: Path, max_freq: int, diff_order: int) -> None:
    data = np.load(input_path, allow_pickle=True)
    config = data["config"][0]
    samples = data["modulo_samples"]
    fold_counts = data["folds"] if "folds" in data.files else np.full(samples.shape[0], -1)
    all_taus = []
    all_recon = []
    all_gtilde = []
    all_residue = []
    solvers = []
    for y, fold_count in zip(samples, fold_counts):
        recovered = recover_trial(
            y=y,
            k=2,
            lambda_value=float(config["lambda_value"]),
            sigma=float(config["sigma"]),
            period=float(config["period"]),
            max_freq=max_freq,
            diff_order=diff_order,
            fold_count=int(fold_count) if int(fold_count) >= 0 else None,
        )
        all_taus.append(recovered["taus"])
        all_recon.append(recovered["reconstruction"])
        all_gtilde.append(recovered["signal_recovered_up_to_offset"])
        if "fold_residue" in recovered:
            all_residue.append(recovered["fold_residue"])
        solvers.append(str(recovered.get("p2_solver", "unknown")))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        output_path,
        method=np.array("us_sres"),
        taus=np.asarray(all_taus),
        reconstruction=np.asarray(all_recon),
        g_tilde=np.asarray(all_gtilde),
        fold_residue=np.asarray(all_residue) if all_residue else np.empty((0,)),
        diff_order=np.array(diff_order),
        p2_solver=np.asarray(solvers),
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
