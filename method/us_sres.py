"""SRes-IterSiS: robust off-the-grid US-SRes recovery (Guo & Bhandari, Algorithm 1).

Input: low-bit modulo samples y[n] of g(t) = sum_k Gamma_k psi(t - tau_k),
the known kernel psi and K.  Output: spike times tau_k, amplitudes Gamma_k and
the high-dynamic-range waveform g[n] = sum_k Gamma_k psi(n - tau_k).

Algorithm 1 (Section III), with the difference-domain model of Eq. (32):

    y_ = Delta y
    eps_tilde^[0] = -y_              (residue seed; g_ = 0 before any fit)
    for i = 1 .. i_max:
        P1 (Eqs. 35-43): fit eps_tilde with a rational model P/Q, deg Q = M,
            deg P = M - 1, by the iterative weighted least squares of Eq. (38)
            (Q^[j-1] fixed in the weights), from several Q^[0] seeds; keep the
            iterate whose lattice-quantized reconstruction (Eq. 43) is closest
            to eps_tilde (Algorithm 1, lines 10-12)                -> eps^[i]
        g_tilde = Delta^{-1}(y_ + eps^[i])                         (Eq. 45)
        P2 (Eqs. 45-47): s[l] = DFT(g_tilde)[l] / DFT(psi)[l], |l| <= I_psi;
            initial spectral fit on l = 1..I_psi gives s[0]; the residual
            constant c0 is the small eigenvalue of the Toeplitz matrix G(s)
            (Eqs. 46-47); matrix pencil -> tau_k; least squares -> Gamma_k
        g_ = Delta( sum_k Gamma_k psi(n - tau_k) );  eps_tilde^[i] = g_ - y_   (Eq. 34)

Implementation notes.
* The weighted least squares of Eq. (38) is solved in the partial-fraction
  (barycentric) basis relative to the previous denominator Q^[j-1]: with
  sigma = Q / Q^[j-1] and (sigma f) = P / Q^[j-1], minimising
  sum_n |sigma(z_n) f_n - (sigma f)(z_n)|^2 is exactly Eq. (38).  New poles are
  the zeros of sigma.  Q is normalised to be monic, which plays the role of
  the paper's linear normalisation <q^[0], q> = 1.  This avoids the
  catastrophic conditioning of a degree-M monomial Q when folds cluster.
* The fold residues c_m (Eq. 39) of on-grid folds are read on the grid at the
  pole positions n_m (Eq. 36) and quantised onto 2 lambda Z (Eq. 43).
* The number of folds M is not given to the method; it is estimated at each
  outer iteration as the number of non-zero lattice residues of eps_tilde.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

DEFAULTS = {
    "outer_iters": 6,
    "inner_iters": 3,
    "initializations": 2,
    "bandwidth_rel": 0.05,
    "toeplitz_order": 4,
    "seed": 16948,
}


def modulo(x: np.ndarray, lambda_value: float) -> np.ndarray:
    return 2.0 * lambda_value * (np.mod(x / (2.0 * lambda_value) + 0.5, 1.0) - 0.5)


def quantize_residue(x: np.ndarray, lambda_value: float) -> np.ndarray:
    """Eq. (43): Q_lambda(x) = 2 lambda floor((x + lambda) / (2 lambda))."""

    return 2.0 * lambda_value * np.floor((np.real(x) + lambda_value) / (2.0 * lambda_value))


def anti_difference(delta: np.ndarray) -> np.ndarray:
    return np.concatenate([[0.0], np.cumsum(delta)])


def gaussian_atoms(n: int, taus: np.ndarray, sigma: float) -> np.ndarray:
    t = np.arange(n, dtype=np.float64)
    return np.exp(-0.5 * ((t[:, None] - np.asarray(taus)[None, :]) / sigma) ** 2)


# ----------------------------------------------------------------------------
# P1: residue recovery by rational (P/Q) sparse approximation on the continuum
# ----------------------------------------------------------------------------


def _clamp_poles(poles: np.ndarray) -> np.ndarray:
    """Reflect poles into the unit disc and keep them off the sampling points."""

    mag = np.abs(poles)
    out = np.where(mag > 1.0, poles / np.maximum(mag, 1e-300) ** 2, poles)
    mag = np.abs(out)
    too_close = mag > 1.0 - 1e-6
    out = np.where(too_close, out / np.maximum(mag, 1e-300) * (1.0 - 1e-6), out)
    tiny = mag < 1e-3
    return np.where(tiny, 1e-3 + 0j, out)


def _candidates(
    eps_tilde: np.ndarray,
    zn: np.ndarray,
    poles: np.ndarray,
    lambda_value: float,
) -> list[np.ndarray]:
    """Lattice residues from the current rational model (Eqs. 35, 36, 39, 43)."""

    length = eps_tilde.size
    cauchy = 1.0 / (zn[:, None] - poles[None, :])
    residues, *_ = np.linalg.lstsq(cauchy, eps_tilde.astype(np.complex128), rcond=None)
    model = cauchy @ residues  # P/Q evaluated on the grid, Eq. (35)
    out = []
    if np.all(np.isfinite(model)):
        out.append(quantize_residue(model.real, lambda_value))  # Eq. (43)
    positions = np.unique(np.mod(np.rint(length * np.angle(poles) / (2.0 * np.pi)), length).astype(int))
    sieved = np.zeros(length)
    sieved[positions] = quantize_residue(eps_tilde[positions], lambda_value)  # Eqs. (36), (39), (43)
    out.append(sieved)
    return out


def rational_residue_recovery(
    eps_tilde: np.ndarray,
    num_folds: int,
    lambda_value: float,
    inner_iters: int,
    initializations: int,
    rng: np.random.Generator,
) -> np.ndarray:
    eps_tilde = np.asarray(eps_tilde, dtype=np.float64)
    length = eps_tilde.size
    m = int(min(max(num_folds, 0), length // 4))
    if m == 0:
        return np.zeros(length)
    zn = np.exp(2j * np.pi * np.arange(length) / length)
    f = eps_tilde.astype(np.complex128)
    anchor = np.sort(np.argsort(-np.abs(eps_tilde), kind="stable")[:m]).astype(np.float64)
    radius = 1.0 - 1.0 / length
    best_err, best = np.inf, None
    for init in range(initializations):
        positions = anchor if init == 0 else anchor + rng.uniform(-0.5, 0.5, size=m)
        poles = radius * np.exp(2j * np.pi * positions / length)  # roots of Q^[0]
        for _ in range(inner_iters):
            cauchy = 1.0 / (zn[:, None] - poles[None, :])
            system = np.hstack([cauchy, -f[:, None] * cauchy])
            try:
                sol, *_ = np.linalg.lstsq(system, f, rcond=None)
            except np.linalg.LinAlgError:
                break
            if not np.all(np.isfinite(sol)):
                break
            sigma_res = sol[m:]
            # zeros of sigma(z) = 1 + sum_m sigma_res_m / (z - a_m): new roots of Q
            new_poles = np.linalg.eigvals(np.diag(poles) - np.outer(np.ones(m), sigma_res))
            if not np.all(np.isfinite(new_poles)):
                break
            poles = _clamp_poles(new_poles)
            for cand in _candidates(eps_tilde, zn, poles, lambda_value):
                err = float(np.mean((eps_tilde - cand) ** 2))
                if err < best_err:
                    best_err, best = err, cand
    if best is None:  # every weighted solve failed numerically
        return quantize_residue(eps_tilde, lambda_value)
    return best


# ----------------------------------------------------------------------------
# P2: spike estimation by spectral fitting (Eqs. 45-47) and the matrix pencil
# ----------------------------------------------------------------------------


def kernel_spectrum(kernel_grid: np.ndarray, kernel: np.ndarray, n: int) -> np.ndarray:
    circ = np.zeros(n)
    idx = np.mod(np.rint(kernel_grid).astype(np.int64), n)
    np.add.at(circ, idx, kernel)
    return np.fft.fft(circ)


def spectral_bandwidth(psi_hat: np.ndarray, k: int, rel: float) -> int:
    mag = np.abs(psi_hat[: psi_hat.size // 2])
    above = mag >= rel * mag[0]
    count = int(np.argmin(above)) if not np.all(above) else mag.size
    return int(min(max(count - 1, 2 * k + 1), psi_hat.size // 2 - 1))


def matrix_pencil(x: np.ndarray, k: int) -> np.ndarray:
    """Hua-Sarkar matrix pencil: poles z_k of x[i] = sum_k a_k z_k^i."""

    length = x.size
    pencil = min(max(length // 2, k), length - k - 1)
    hankel = np.lib.stride_tricks.sliding_window_view(x, pencil + 1)
    u, _, _ = np.linalg.svd(hankel, full_matrices=False)
    uk = u[:, :k]
    return np.linalg.eigvals(np.linalg.pinv(uk[:-1]) @ uk[1:])


def taus_from_poles(z: np.ndarray, n: int) -> np.ndarray:
    return np.mod(-np.angle(z) * n / (2.0 * np.pi), n)


def fit_real_amplitudes(s: np.ndarray, ls: np.ndarray, taus: np.ndarray, n: int) -> np.ndarray:
    vander = np.exp(-2j * np.pi * np.outer(ls, taus) / n)
    stacked = np.vstack([vander.real, vander.imag])
    rhs = np.concatenate([s.real, s.imag])
    gam, *_ = np.linalg.lstsq(stacked, rhs, rcond=None)
    return gam


def spectral_spike_fit(
    g_tilde: np.ndarray,
    k: int,
    psi_hat: np.ndarray,
    bandwidth: int,
    toeplitz_order: int,
) -> tuple[np.ndarray, np.ndarray]:
    n = g_tilde.size
    ls = np.arange(-bandwidth, bandwidth + 1)
    s = np.fft.fft(g_tilde)[ls % n] / psi_hat[ls % n]  # Eq. (45): s[l] = g_hat / psi_hat
    zero = bandwidth  # index of l = 0

    # Initial spectral fit on l = 1..I_psi provides s[0] (Section III-C).
    positive = s[zero + 1 :]
    try:
        taus0 = taus_from_poles(matrix_pencil(positive, k), n)
        gam0 = fit_real_amplitudes(positive, ls[zero + 1 :], taus0, n)
        s0 = float(np.sum(gam0))
    except np.linalg.LinAlgError:
        s0 = float(np.real(s[zero]))
    fixed = s.copy()
    if np.isfinite(s0):
        fixed[zero] = s0
    # Residual constant c0: G(s~) = G(s) + c0 I with rank G(s) = K (Eqs. 46-47).
    order = int(min(max(toeplitz_order, k), bandwidth))
    idx = np.arange(order + 1)
    toeplitz = fixed[zero + idx[:, None] - idx[None, :]]
    toeplitz = 0.5 * (toeplitz + toeplitz.conj().T)
    try:
        eig = np.linalg.eigvalsh(toeplitz)
        c0 = float(np.mean(eig[: order + 1 - k]))
        if np.isfinite(c0):
            fixed[zero] = fixed[zero] - c0
    except np.linalg.LinAlgError:
        pass

    taus = taus_from_poles(matrix_pencil(fixed, k), n)
    gam = fit_real_amplitudes(fixed, ls, taus, n)
    order_idx = np.argsort(taus)
    return taus[order_idx], gam[order_idx]


# ----------------------------------------------------------------------------
# Algorithm 1
# ----------------------------------------------------------------------------


def sres_itersis(
    y: np.ndarray,
    lambda_value: float,
    sigma: float,
    k: int,
    psi_hat: np.ndarray,
    params: dict | None = None,
    rng: np.random.Generator | None = None,
) -> dict[str, np.ndarray | int]:
    p = dict(DEFAULTS)
    p.update(params or {})
    rng = rng if rng is not None else np.random.default_rng(p["seed"])
    y = np.asarray(y, dtype=np.float64)
    n = y.size
    bandwidth = spectral_bandwidth(psi_hat, k, p["bandwidth_rel"])
    dy = np.diff(y)
    eps_tilde = -dy
    previous = None
    taus = np.linspace(n / 3.0, 2.0 * n / 3.0, k)
    amps = np.zeros(k)
    g_tilde = anti_difference(modulo(dy, lambda_value))
    eps = np.zeros(n - 1)
    iterations = 0
    for _ in range(int(p["outer_iters"])):
        num_folds = int(np.count_nonzero(quantize_residue(eps_tilde, lambda_value)))
        eps = rational_residue_recovery(
            eps_tilde, num_folds, lambda_value, int(p["inner_iters"]), int(p["initializations"]), rng
        )
        if previous is not None and np.array_equal(eps, previous):
            break  # residues stopped changing: P2 already holds the matching fit
        iterations += 1
        g_tilde = anti_difference(dy + eps)
        try:
            new_taus, new_amps = spectral_spike_fit(g_tilde, k, psi_hat, bandwidth, int(p["toeplitz_order"]))
        except np.linalg.LinAlgError:
            break
        if not (np.all(np.isfinite(new_taus)) and np.all(np.isfinite(new_amps))):
            break
        taus, amps = new_taus, new_amps
        model = gaussian_atoms(n, taus, sigma) @ amps
        eps_tilde = np.diff(model) - dy  # Eq. (34)
        previous = eps

    taus = np.clip(taus, 0.0, n - 1.0)
    recon = gaussian_atoms(n, taus, sigma) @ amps
    # Numerical safeguard: a recovered waveform cannot exceed the unwrapped data range by much.
    bound = 2.0 * float(np.max(np.abs(g_tilde))) + 2.0 * lambda_value
    recon = np.clip(recon, -bound, bound)
    return {
        "taus": taus,
        "amplitudes": amps,
        "reconstruction": recon,
        "g_tilde": g_tilde,
        "residue": eps,
        "iterations": iterations,
    }


def load_inputs(path: Path) -> dict[str, np.ndarray]:
    with np.load(path, allow_pickle=False) as data:
        return {key: data[key] for key in data.files}


def recover_all(inputs: dict[str, np.ndarray], params: dict | None = None) -> dict[str, np.ndarray]:
    p = dict(DEFAULTS)
    p.update(params or {})
    samples = np.asarray(inputs["modulo_samples"], dtype=np.float64)
    n = samples.shape[1]
    lam = float(inputs["lambda_value"])
    sigma = float(inputs["kernel_sigma"])
    k = int(inputs["num_spikes"])
    psi_hat = kernel_spectrum(inputs["kernel_grid"], inputs["kernel"], n)
    rng = np.random.default_rng(p["seed"])
    out = {"taus": [], "reconstruction": [], "amplitudes": [], "g_tilde": [], "iterations": []}
    for y in samples:
        res = sres_itersis(y, lam, sigma, k, psi_hat, p, rng)
        for key in out:
            out[key].append(res[key])
    return {key: np.asarray(val) for key, val in out.items()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input", type=Path, help="method input archive (modulo samples + sensor constants)")
    parser.add_argument("output", type=Path, help="where to write reconstruction and taus")
    parser.add_argument("--seed", type=int, default=DEFAULTS["seed"])
    args = parser.parse_args()
    result = recover_all(load_inputs(args.input), {"seed": args.seed})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    np.savez(
        args.output,
        reconstruction=result["reconstruction"],
        taus=result["taus"],
        amplitudes=result["amplitudes"],
        iterations=result["iterations"],
    )
    print(f"wrote {args.output} (mean outer iterations {np.mean(result['iterations']):.2f})")


if __name__ == "__main__":
    main()
