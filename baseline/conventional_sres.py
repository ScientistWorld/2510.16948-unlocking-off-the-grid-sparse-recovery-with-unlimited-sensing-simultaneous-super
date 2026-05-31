"""Conventional clipped-ADC sparse recovery baseline."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from data.spectral_utils import sparse_deconvolution_continuum


def run_baseline(input_path: Path, output_path: Path, max_freq: int) -> None:
    data = np.load(input_path, allow_pickle=True)
    config = data["config"][0]
    samples = data["conventional_samples"]
    all_taus = []
    all_recon = []
    for y in samples:
        taus, _, _, reconstruction = sparse_deconvolution_continuum(
            y, k=2, sigma=float(config["sigma"])
        )
        all_taus.append(taus)
        all_recon.append(reconstruction)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        output_path,
        method=np.array("conventional_clip_sres"),
        taus=np.asarray(all_taus),
        reconstruction=np.asarray(all_recon),
        source=str(input_path),
    )
    print(f"wrote {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/synthetic/us_sres_benchmark.npz")
    parser.add_argument("--output", default="checkpoints/conventional_outputs.npz")
    parser.add_argument("--max-freq", type=int, default=12)
    args = parser.parse_args()
    run_baseline(Path(args.input), Path(args.output), args.max_freq)


if __name__ == "__main__":
    main()
