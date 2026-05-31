"""Shared signal-model utilities for the US-SRes benchmark."""

from __future__ import annotations

import numpy as np
from scipy.optimize import least_squares


def gaussian_kernel(t: np.ndarray, sigma: float) -> np.ndarray:
    return np.exp(-0.5 * (t / sigma) ** 2)


def positive_fourier_ratio(
    signal: np.ndarray, sigma: float, period: float, max_freq: int
) -> tuple[np.ndarray, np.ndarray]:
    n = signal.size
    freqs = np.arange(1, max_freq + 1)
    signal_fft = np.fft.fft(signal)
    omega = 2.0 * np.pi * freqs / period
    kernel_ft = np.exp(-0.5 * (sigma * omega) ** 2)
    ratio = signal_fft[freqs] / np.maximum(kernel_ft, 1e-12)
    ratio /= n
    return freqs, ratio


def matrix_pencil_spikes(
    signal: np.ndarray,
    k: int,
    sigma: float,
    period: float,
    max_freq: int = 36,
) -> np.ndarray:
    _, s = positive_fourier_ratio(signal, sigma, period, max_freq)
    if max_freq < 2 * k + 1:
        raise ValueError("max_freq must provide at least 2K+1 Fourier samples")

    rows = []
    rhs = []
    for idx in range(k, len(s)):
        rows.append(s[idx - k : idx][::-1])
        rhs.append(-s[idx])
    coeff_tail, *_ = np.linalg.lstsq(np.vstack(rows), np.asarray(rhs), rcond=None)
    roots = np.roots(np.concatenate(([1.0 + 0.0j], coeff_tail)))
    roots = roots[np.argsort(np.abs(np.abs(roots) - 1.0))[:k]]
    tau = (-np.angle(roots) * period / (2.0 * np.pi)) % period
    tau.sort()
    return tau.real


def fit_amplitudes_and_offset(
    signal: np.ndarray, taus: np.ndarray, sigma: float
) -> tuple[np.ndarray, float, np.ndarray]:
    t = np.arange(signal.size, dtype=np.float64)
    atoms = [gaussian_kernel(t - tau, sigma) for tau in taus]
    design = np.column_stack(atoms + [np.ones_like(t)])
    coeffs, *_ = np.linalg.lstsq(design, signal, rcond=None)
    amplitudes = coeffs[:-1]
    offset = float(coeffs[-1])
    reconstruction = design @ coeffs
    return amplitudes, offset, reconstruction


def sparse_deconvolution_continuum(
    signal: np.ndarray,
    k: int,
    sigma: float,
    grid_step: float = 4.0,
    min_separation: float = 25.0,
) -> tuple[np.ndarray, np.ndarray, float, np.ndarray]:
    """Solve the sparse spike fitting objective over continuous locations.

    This is a small-scale solver for Eq. 44/Eq. 45 style spike estimation. It
    performs a coarse off-grid search followed by nonlinear least squares over
    spike locations, amplitudes, and the anti-difference DC offset.
    """

    if k != 2:
        raise NotImplementedError("the synthetic benchmark currently uses K=2")

    n = signal.size
    t = np.arange(n, dtype=np.float64)
    grid = np.arange(35.0, n - 35.0, grid_step)

    best_sse = np.inf
    best_taus = np.array([grid[0], grid[-1]], dtype=np.float64)
    # Remove an arbitrary mean before the coarse search; the offset is fitted
    # explicitly for every candidate.
    y = signal.astype(np.float64)
    for i, tau0 in enumerate(grid[:-1]):
        tau1s = grid[i + 1 :]
        tau1s = tau1s[tau1s - tau0 >= min_separation]
        if tau1s.size == 0:
            continue
        atom0 = gaussian_kernel(t - tau0, sigma)
        for tau1 in tau1s:
            design = np.column_stack(
                [atom0, gaussian_kernel(t - tau1, sigma), np.ones_like(t)]
            )
            coeffs, *_ = np.linalg.lstsq(design, y, rcond=None)
            resid = y - design @ coeffs
            sse = float(resid @ resid)
            if sse < best_sse:
                best_sse = sse
                best_taus = np.array([tau0, tau1], dtype=np.float64)

    amps, offset, _ = fit_amplitudes_and_offset(y, best_taus, sigma)
    x0 = np.concatenate([best_taus, amps, [offset]])

    def residual(params: np.ndarray) -> np.ndarray:
        taus = np.sort(params[:2])
        amps = params[2:4]
        offset_param = params[4]
        pred = (
            amps[0] * gaussian_kernel(t - taus[0], sigma)
            + amps[1] * gaussian_kernel(t - taus[1], sigma)
            + offset_param
        )
        return pred - y

    lower = np.array([0.0, 0.0, -np.inf, -np.inf, -np.inf])
    upper = np.array([n - 1.0, n - 1.0, np.inf, np.inf, np.inf])
    result = least_squares(residual, x0, bounds=(lower, upper), max_nfev=200)
    taus = np.sort(result.x[:2])
    amplitudes, offset, reconstruction = fit_amplitudes_and_offset(y, taus, sigma)
    return taus, amplitudes, offset, reconstruction
