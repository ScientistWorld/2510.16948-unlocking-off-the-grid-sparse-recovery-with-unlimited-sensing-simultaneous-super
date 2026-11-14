"""Fixed comparison: conventional clipping ADC + sparse least-squares recovery.

The conventional ADC has the same input range [-lambda, lambda] and the same
bit budget as the modulo ADC (Section V-A1 of the paper), so a high-dynamic-
range input clips.  Recovery fits K=2 Gaussian atoms plus an offset to the
clipped samples: an exhaustive coarse search over location pairs (solved in
closed form through precomputed normal equations) followed by continuous
least-squares refinement.  This baseline is computed by the evaluator itself
from the second ADC's samples; no file a method can write is involved.
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import least_squares


def _gaussian(t: np.ndarray, sigma: float) -> np.ndarray:
    return np.exp(-0.5 * (t / sigma) ** 2)


class ConventionalSolver:
    def __init__(
        self,
        n: int,
        sigma: float,
        grid_step: float = 4.0,
        margin: float = 35.0,
        min_separation: float = 25.0,
    ) -> None:
        self.n = n
        self.sigma = sigma
        self.t = np.arange(n, dtype=np.float64)
        self.centers = np.arange(margin, n - margin, grid_step)
        atoms = _gaussian(self.t[None, :] - self.centers[:, None], sigma)
        self.atoms = atoms
        gram = atoms @ atoms.T
        asum = atoms.sum(axis=1)
        i, j = np.triu_indices(self.centers.size, k=1)
        keep = self.centers[j] - self.centers[i] >= min_separation
        self.pi, self.pj = i[keep], j[keep]
        normal = np.empty((self.pi.size, 3, 3))
        normal[:, 0, 0] = gram[self.pi, self.pi]
        normal[:, 1, 1] = gram[self.pj, self.pj]
        normal[:, 0, 1] = normal[:, 1, 0] = gram[self.pi, self.pj]
        normal[:, 0, 2] = normal[:, 2, 0] = asum[self.pi]
        normal[:, 1, 2] = normal[:, 2, 1] = asum[self.pj]
        normal[:, 2, 2] = float(n)
        self.normal_inv = np.linalg.inv(normal)

    def _design(self, taus: np.ndarray) -> np.ndarray:
        cols = [_gaussian(self.t - tau, self.sigma) for tau in taus]
        return np.column_stack(cols + [np.ones_like(self.t)])

    def fit(self, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        y = np.asarray(y, dtype=np.float64)
        b = self.atoms @ y
        rhs = np.stack([b[self.pi], b[self.pj], np.full(self.pi.size, y.sum())], axis=1)
        coef = np.einsum("pij,pj->pi", self.normal_inv, rhs)
        sse = y @ y - np.einsum("pi,pi->p", rhs, coef)
        best = int(np.argmin(sse))
        taus0 = np.array([self.centers[self.pi[best]], self.centers[self.pj[best]]])
        x0 = np.concatenate([taus0, coef[best]])

        def residual(params: np.ndarray) -> np.ndarray:
            taus = np.sort(params[:2])
            pred = (
                params[2] * _gaussian(self.t - taus[0], self.sigma)
                + params[3] * _gaussian(self.t - taus[1], self.sigma)
                + params[4]
            )
            return pred - y

        lower = np.array([0.0, 0.0, -np.inf, -np.inf, -np.inf])
        upper = np.array([self.n - 1.0, self.n - 1.0, np.inf, np.inf, np.inf])
        result = least_squares(residual, x0, bounds=(lower, upper), max_nfev=200)
        taus = np.sort(result.x[:2])
        design = self._design(taus)
        coeffs, *_ = np.linalg.lstsq(design, y, rcond=None)
        return taus, design @ coeffs


def conventional_recovery(samples: np.ndarray, sigma: float) -> tuple[np.ndarray, np.ndarray]:
    samples = np.asarray(samples, dtype=np.float64)
    solver = ConventionalSolver(samples.shape[1], sigma)
    taus, recon = [], []
    for y in samples:
        tau, rec = solver.fit(y)
        taus.append(tau)
        recon.append(rec)
    return np.asarray(recon), np.asarray(taus)
