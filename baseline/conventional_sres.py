"""Conventional clipping-ADC sparse recovery on the exported train slice.

The scored comparison row ``conventional_clip_sres`` is computed by the
evaluators themselves (``eval/*/conventional.py``).  This public copy runs the
same kind of clipping-unaware least-squares fit on the train slice's second-ADC
samples (stored with the train labels) so the baseline can be inspected.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from data.spectral_utils import sparse_deconvolution_continuum


def main() -> None:
    out_dir = Path("checkpoints")
    out_dir.mkdir(parents=True, exist_ok=True)
    for labels_path in sorted(Path("data/synthetic").glob("train_*_labels.npz")):
        inputs_path = labels_path.with_name(labels_path.name.replace("_labels", ""))
        with np.load(inputs_path, allow_pickle=False) as inputs, np.load(labels_path, allow_pickle=False) as labels:
            sigma = float(inputs["kernel_sigma"])
            samples = labels["conventional_samples"]
            clean = labels["clean"]
        taus, recon = [], []
        for y in samples:
            tau, _, _, rec = sparse_deconvolution_continuum(y, 2, sigma)
            taus.append(tau)
            recon.append(rec)
        recon = np.asarray(recon)
        name = inputs_path.stem.replace("train_", "")
        np.savez(out_dir / f"conventional_{name}.npz", reconstruction=recon, taus=np.asarray(taus))
        print(f"{name}: conventional MSE {np.mean((recon - clean) ** 2):.4g}")


if __name__ == "__main__":
    main()
