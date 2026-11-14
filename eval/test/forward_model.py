"""Forward model used by the test-slice evaluator (a private copy).

Identical to the public generator in ``data/us_sres_synthetic.py``; the
evaluator keeps its own copy so that editing ``data/`` cannot change how a
method is scored.  ``eval/train`` and ``eval/test`` share no code.
"""

from __future__ import annotations

import numpy as np

N_SAMPLES = 501
NUM_SPIKES = 2
LAMBDA_VALUE = 1.0
KERNEL_SIGMA = 20.0
THERMAL_NOISE_STD = 0.03
FIRST_SPIKE_RANGE = (110.0, 300.0)
SEPARATION_RANGE = (60.0, 90.0)
AMPLITUDE_RATIO_RANGE = (7.0, 13.0)

EXPERIMENTS = {
    "synthetic_lowbit_hdr_dr10": {"dynamic_range_x": 10.0, "quant_bits": 3},
    "synthetic_lowbit_hdr_dr20": {"dynamic_range_x": 20.0, "quant_bits": 3},
    "synthetic_lowbit_hdr_dr30": {"dynamic_range_x": 30.0, "quant_bits": 3},
    "synthetic_lowbit_hdr_dr30_bits5": {"dynamic_range_x": 30.0, "quant_bits": 5},
    "synthetic_lowbit_hdr_dr30_bits8": {"dynamic_range_x": 30.0, "quant_bits": 8},
}

def modulo(x: np.ndarray, lambda_value: float) -> np.ndarray:
    """Centered modulo map M_lambda with range [-lambda, lambda)."""

    return 2.0 * lambda_value * (np.mod(x / (2.0 * lambda_value) + 0.5, 1.0) - 0.5)


def quantize(x: np.ndarray, bits: int, low: float, high: float) -> np.ndarray:
    """Uniform B-bit quantizer with 2**B levels spanning [low, high]; clips."""

    step = (high - low) / (2**bits - 1)
    return np.round((np.clip(x, low, high) - low) / step) * step + low


def gaussian(t: np.ndarray, sigma: float) -> np.ndarray:
    return np.exp(-0.5 * (t / sigma) ** 2)


def kernel_samples(sigma: float = KERNEL_SIGMA, n: int = N_SAMPLES) -> tuple[np.ndarray, np.ndarray]:
    grid = np.arange(-(n // 2), n // 2 + 1, dtype=np.float64)
    return grid, gaussian(grid, sigma)


def make_instances(
    dynamic_range_x: float,
    quant_bits: int,
    trials: int,
    seed: int,
    kernel_sigma: float = KERNEL_SIGMA,
    noise_std: float = THERMAL_NOISE_STD,
) -> dict[str, np.ndarray]:
    """Draw ``trials`` scenes and both ADC acquisitions from one seeded stream."""

    rng = np.random.default_rng(seed)
    n, k, lam = N_SAMPLES, NUM_SPIKES, LAMBDA_VALUE
    t = np.arange(n, dtype=np.float64)
    clean = np.empty((trials, n))
    modulo_samples = np.empty((trials, n))
    conventional_samples = np.empty((trials, n))
    taus = np.empty((trials, k))
    amplitudes = np.empty((trials, k))
    folds = np.empty(trials, dtype=np.int64)
    for i in range(trials):
        first = rng.uniform(*FIRST_SPIKE_RANGE)
        separation = rng.uniform(*SEPARATION_RANGE)
        ratio = rng.uniform(*AMPLITUDE_RATIO_RANGE)
        strong_first = bool(rng.integers(0, 2))
        noise = rng.normal(0.0, noise_std, size=n)
        tau = np.array([first, first + separation])
        amp = np.array([ratio, 1.0]) if strong_first else np.array([1.0, ratio])
        g = (amp[None, :] * gaussian(t[:, None] - tau[None, :], kernel_sigma)).sum(axis=1)
        scale = dynamic_range_x * lam / np.max(np.abs(g))
        g = g * scale
        amp = amp * scale
        analog = g + noise
        clean[i] = g
        modulo_samples[i] = quantize(modulo(analog, lam), quant_bits, -lam, lam)
        conventional_samples[i] = quantize(analog, quant_bits, -lam, lam)
        taus[i] = tau
        amplitudes[i] = amp
        folds[i] = np.count_nonzero(np.diff(np.floor(analog / (2.0 * lam) + 0.5)))
    grid, kernel = kernel_samples(kernel_sigma, n)
    return {
        "clean": clean,
        "taus": taus,
        "amplitudes": amplitudes,
        "fold_count": folds,
        "modulo_samples": modulo_samples,
        "conventional_samples": conventional_samples,
        "kernel_grid": grid,
        "kernel": kernel,
        "lambda_value": np.float64(lam),
        "kernel_sigma": np.float64(kernel_sigma),
        "num_spikes": np.int64(k),
        "quant_bits": np.int64(quant_bits),
        "thermal_noise_std": np.float64(noise_std),
    }


PUBLIC_KEYS = (
    "modulo_samples",
    "kernel_grid",
    "kernel",
    "lambda_value",
    "kernel_sigma",
    "num_spikes",
    "quant_bits",
    "thermal_noise_std",
)
LABEL_KEYS = ("clean", "taus", "amplitudes", "fold_count", "conventional_samples")


def public_inputs(instances: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    """The arrays a recovery method receives (no labels, no second ADC)."""

    return {key: instances[key] for key in PUBLIC_KEYS}
