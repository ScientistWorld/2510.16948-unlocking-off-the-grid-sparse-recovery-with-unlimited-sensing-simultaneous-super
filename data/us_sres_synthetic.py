"""Synthetic off-grid sparse recovery data for US-SRes reproduction.

The paper's hardware ToF tensors are not distributed with the manuscript.
This module creates a small deterministic substitute with the same signal
model: weak/strong off-grid Dirac spikes convolved with a smooth pulse, then
captured through either conventional clipping or modulo low-bit acquisition.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

from data.spectral_utils import gaussian_kernel


@dataclass(frozen=True)
class SyntheticConfig:
    n: int = 501
    period: float = 501.0
    sigma: float = 45.0
    separation: float = 75.0
    lambda_value: float = 1.0
    quant_bits: int = 3
    dynamic_range_x: float = 20.0
    amplitude_ratio: float = 10.0
    trials: int = 64
    seed: int = 16948


def modulo(x: np.ndarray, lambda_value: float) -> np.ndarray:
    """Centered modulo map M_lambda with range [-lambda, lambda)."""

    return 2.0 * lambda_value * (
        np.mod(x / (2.0 * lambda_value) + 0.5, 1.0) - 0.5
    )


def quantize_midrise(x: np.ndarray, bits: int, low: float, high: float) -> np.ndarray:
    """Uniform quantizer over a bounded ADC range."""

    levels = 2**bits
    step = (high - low) / (levels - 1)
    clipped = np.clip(x, low, high)
    return np.round((clipped - low) / step) * step + low


def synthesize_signal(
    t: np.ndarray, taus: np.ndarray, amplitudes: np.ndarray, sigma: float
) -> np.ndarray:
    g = np.zeros_like(t, dtype=np.float64)
    for amp, tau in zip(amplitudes, taus):
        g += amp * gaussian_kernel(t - tau, sigma)
    return g


def make_dataset(config: SyntheticConfig) -> dict[str, np.ndarray]:
    rng = np.random.default_rng(config.seed)
    t = np.arange(config.n, dtype=np.float64)
    kernel_grid = np.arange(-(config.n // 2), config.n // 2 + 1, dtype=np.float64)
    kernel = gaussian_kernel(kernel_grid, config.sigma)

    clean = np.empty((config.trials, config.n), dtype=np.float64)
    modulo_samples = np.empty_like(clean)
    conventional_samples = np.empty_like(clean)
    taus = np.empty((config.trials, 2), dtype=np.float64)
    amplitudes = np.empty((config.trials, 2), dtype=np.float64)
    folds = np.empty(config.trials, dtype=np.int64)

    for trial in range(config.trials):
        tau0 = rng.uniform(135.0, 225.0)
        jitter = rng.uniform(-4.0, 4.0)
        tau = np.array([tau0, tau0 + config.separation + jitter])
        # Strong/weak mixture; signs are kept positive to match ToF reflectivity.
        amps = np.array([config.amplitude_ratio, 1.0], dtype=np.float64)
        amps *= rng.uniform(0.9, 1.1, size=2)
        g = synthesize_signal(t, tau, amps, config.sigma)
        g *= (config.dynamic_range_x * config.lambda_value) / np.max(np.abs(g))

        y_mod = modulo(g, config.lambda_value)
        y_mod_q = quantize_midrise(
            y_mod, config.quant_bits, -config.lambda_value, config.lambda_value
        )
        y_clip_q = quantize_midrise(
            g, config.quant_bits, -config.lambda_value, config.lambda_value
        )

        clean[trial] = g
        modulo_samples[trial] = y_mod_q
        conventional_samples[trial] = y_clip_q
        taus[trial] = tau
        amplitudes[trial] = amps
        folds[trial] = np.count_nonzero(np.abs(np.diff(g - y_mod)) > config.lambda_value)

    return {
        "clean": clean,
        "modulo_samples": modulo_samples,
        "conventional_samples": conventional_samples,
        "taus": taus,
        "amplitudes": amplitudes,
        "kernel_grid": kernel_grid,
        "kernel": kernel,
        "config": np.array([asdict(config)], dtype=object),
        "folds": folds,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="data/synthetic/us_sres_benchmark.npz")
    parser.add_argument("--trials", type=int, default=64)
    parser.add_argument("--bits", type=int, default=3)
    parser.add_argument("--dynamic-range-x", type=float, default=20.0)
    parser.add_argument("--seed", type=int, default=16948)
    args = parser.parse_args()

    config = SyntheticConfig(
        trials=args.trials,
        quant_bits=args.bits,
        dynamic_range_x=args.dynamic_range_x,
        seed=args.seed,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output, **make_dataset(config))
    print(f"wrote {output}")


if __name__ == "__main__":
    main()
