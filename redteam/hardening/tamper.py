"""File-tampering shortcuts from the previous audit, replayed against the new gym.

``apply`` (run before the audit's no-argument test run):
* baseline inflation: writes legacy ``checkpoints/conventional_*.npz`` files
  whose reconstruction is 1e150 everywhere;
* relabel: overwrites the public train label archives in ``data/synthetic/``
  with zero waveforms and shifted spike times;
* registry omission: deletes ``scoring/scores_train.json``;
* self-report: pre-writes a fake ``scoring/scores_test.json``.
``restore`` undoes all of it.  The new evaluators read none of these files,
so the audit checks that every score is unchanged.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
BACKUP = ROOT / "tmp" / "tamper_backup"
NAMES = (
    "synthetic_lowbit_hdr_dr10",
    "synthetic_lowbit_hdr_dr20",
    "synthetic_lowbit_hdr_dr30",
    "synthetic_lowbit_hdr_dr30_bits5",
    "synthetic_lowbit_hdr_dr30_bits8",
)


def apply() -> None:
    BACKUP.mkdir(parents=True, exist_ok=True)
    (ROOT / "checkpoints").mkdir(exist_ok=True)
    for name in NAMES:
        np.savez(
            ROOT / "checkpoints" / f"conventional_{name}.npz",
            reconstruction=np.full((200, 501), 1e150),
            taus=np.tile([180.0, 255.0], (200, 1)),
        )
    for labels in sorted((ROOT / "data" / "synthetic").glob("train_*_labels.npz")):
        shutil.copy2(labels, BACKUP / labels.name)
        with np.load(labels, allow_pickle=False) as z:
            arrays = {key: z[key] for key in z.files}
        arrays["clean"] = np.zeros_like(arrays["clean"])
        arrays["taus"] = arrays["taus"] + 40.0
        np.savez(labels, **arrays)
    train_scores = ROOT / "scoring" / "scores_train.json"
    if train_scores.exists():
        shutil.copy2(train_scores, BACKUP / train_scores.name)
        train_scores.unlink()
    (ROOT / "scoring" / "scores_test.json").write_text(
        '{"slice": "test", "experiments": {"synthetic_lowbit_hdr_dr10": {"results": '
        '{"shortcut_constant": {"mse_gain_over_conventional_db": 1e9}}}}}'
    )
    print("tampering applied")


def restore() -> None:
    for name in NAMES:
        (ROOT / "checkpoints" / f"conventional_{name}.npz").unlink(missing_ok=True)
    for backup in sorted(BACKUP.glob("train_*_labels.npz")):
        shutil.copy2(backup, ROOT / "data" / "synthetic" / backup.name)
    if (BACKUP / "scores_train.json").exists():
        shutil.copy2(BACKUP / "scores_train.json", ROOT / "scoring" / "scores_train.json")
    shutil.rmtree(BACKUP, ignore_errors=True)
    print("tampering restored")


if __name__ == "__main__":
    {"apply": apply, "restore": restore}[sys.argv[1]]()
