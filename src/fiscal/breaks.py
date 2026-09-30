"""Where does the U.S. fiscal response break? Multiple structural breaks estimated from the data
(Bai and Perron 1998, 2003), instead of imposing 2004.

Regression (as in src/fiscal/fiscal_response.py, static):
    S_t = c + rho * x_{t-1} + beta * gap_t + gamma * gvar_t + e_t,   x = debt (b) or interest (IC),
with all coefficients free to change at each break (pure structural change). 2020-21 are dropped
instead of dummied. Minimum segment length: 15% of the sample.
  - Break dates for m = 1..3: global minimum of the sum of squared residuals (dynamic programming).
  - Tests: supF(m) against no break, UDmax, and sequential supF(l+1 | l); p-values by wild
    bootstrap (Rademacher) under the null, B = 499, so no tabulated critical values are needed.
  - Number of breaks: BIC and the sequential procedure at 5%.
Samples: NIPA calendar years 1971-2024 (primary surplus excluding Fed remittances) and CBO
fiscal years 1967-2025 with the automatic stabilizers removed.
Output: data/processed/fiscal/breaks.csv, breaks_segments.csv
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.fiscal.fiscal_response import build, build_cbo

OUT = Path("data/processed/fiscal")
TRIM, MAXB, BOOT = 0.15, 3, 499
RNG = np.random.default_rng(20260930)


def ssr_table(y: np.ndarray, X: np.ndarray, h: int) -> np.ndarray:
    T = len(y)
    S = np.full((T, T), np.inf)
    for i in range(T):
        for j in range(i + h - 1, T):
            b, res, *_ = np.linalg.lstsq(X[i:j + 1], y[i:j + 1], rcond=None)
            e = y[i:j + 1] - X[i:j + 1] @ b
            S[i, j] = e @ e
    return S


def best_breaks(S: np.ndarray, m: int, h: int) -> tuple[float, list[int]]:
    """Global SSR minimum with m breaks; a break at k means a new segment starts at index k."""
    T = S.shape[0]
    # V[k][j]: min SSR of y[0..j] with k breaks
    V = [S[0].copy()]
    arg = [None]
    for k in range(1, m + 1):
        v, a = np.full(T, np.inf), np.zeros(T, int)
        for j in range((k + 1) * h - 1, T):
            cands = [(V[k - 1][t - 1] + S[t, j], t) for t in range(k * h, j - h + 2)]
            if cands:
                v[j], a[j] = min(cands)
        V.append(v)
        arg.append(a)
    j, br = T - 1, []
    for k in range(m, 0, -1):
        t = arg[k][j]
        br.append(t)
        j = t - 1
    return float(V[m][T - 1]), sorted(br)


def stats(y, X, h):
    S = ssr_table(y, X, h)
    T, q = X.shape
    ssr0 = S[0, T - 1]
    out = {"ssr": [ssr0], "breaks": [[]]}
    for m in range(1, MAXB + 1):
        s, br = best_breaks(S, m, h)
        out["ssr"].append(s)
        out["breaks"].append(br)
    F = [((ssr0 - out["ssr"][m]) / (m * q)) / (out["ssr"][m] / (T - (m + 1) * q)) for m in range(1, MAXB + 1)]
    # sequential supF(l+1 | l): best extra break inside the l-break segments
    seq = []
    for l in range(0, MAXB):
        br = out["breaks"][l]
        edges = [0] + br + [T]
        best = 0.0
        for a, z in zip(edges[:-1], edges[1:]):
            if z - a < 2 * h:
                continue
            base = S[a, z - 1]
            for t in range(a + h, z - h + 1):
                best = max(best, base - S[a, t - 1] - S[t, z - 1])
        seq.append(best / q / (out["ssr"][l] / (T - (l + 1) * q)))
    bic = [T * np.log(out["ssr"][m] / T) + (m + 1) * q * np.log(T) + m * np.log(T) for m in range(MAXB + 1)]
    return out, F, seq, bic


def run(name: str, d: pd.DataFrame, x: str) -> tuple[dict, list[dict]]:
    k = d.dropna(subset=["S", x, "gap", "gvar"])
    k = k[~k.index.isin([2020, 2021])]
    y = k.S.values
    X = np.column_stack([np.ones(len(k)), k[x].values, k.gap.values, k.gvar.values])
    T = len(y)
    h = int(np.ceil(TRIM * T))
    out, F, seq, bic = stats(y, X, h)
    # wild bootstrap under the null of no break
    b0 = np.linalg.lstsq(X, y, rcond=None)[0]
    e0 = y - X @ b0
    bF, bS = [], []
    for _ in range(BOOT):
        yb = X @ b0 + e0 * RNG.choice([-1.0, 1.0], T)
        _, Fb, sb, _ = stats(yb, X, h)
        bF.append(Fb)
        bS.append(sb)
    bF, bS = np.array(bF), np.array(bS)
    udmax = max(F)
    p = {f"p_supF{m}": float((bF[:, m - 1] >= F[m - 1]).mean()) for m in range(1, MAXB + 1)}
    p_ud = float((bF.max(axis=1) >= udmax).mean())
    p_seq = [float((bS[:, 0] >= s).mean()) for s in seq]     # approximation: null distribution of supF(1|0)
    n_seq = next((l for l, pv in enumerate(p_seq) if pv > 0.05), MAXB)
    n_bic = int(np.argmin(bic))
    years = k.index.values
    summary = {"sample": name, "x": x, "T": T, "years": f"{years[0]}-{years[-1]}", "min_seg": h,
               **{f"supF{m}": F[m - 1] for m in range(1, MAXB + 1)}, **p, "UDmax": udmax, "p_UDmax": p_ud,
               **{f"seq{l + 1}|{l}": seq[l] for l in range(MAXB)}, **{f"p_seq{l + 1}|{l}": p_seq[l] for l in range(MAXB)},
               "n_breaks_seq": n_seq, "n_breaks_bic": n_bic,
               **{f"breaks_m{m}": ",".join(str(years[t]) for t in out["breaks"][m]) for m in range(1, MAXB + 1)}}
    segs = []
    for m in sorted({1, 2, max(n_seq, n_bic, 1)}):
        edges = [0] + out["breaks"][m] + [T]
        for a, z in zip(edges[:-1], edges[1:]):
            Xs, ys = X[a:z], y[a:z]
            b = np.linalg.lstsq(Xs, ys, rcond=None)[0]
            e = ys - Xs @ b
            V = np.linalg.pinv(Xs.T @ Xs) * (e @ e) / max(len(ys) - Xs.shape[1], 1)
            mm = k.m.values[a:z]
            segs.append({"sample": name, "x": x, "m": m, "from": int(years[a]), "to": int(years[z - 1]),
                         "n": z - a, "rho": b[1], "se": float(np.sqrt(V[1, 1])),
                         "phi_implied": b[1] / np.nanmean(mm) if x != "IC_l" and np.isfinite(mm).any() else b[1]})
    return summary, segs


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cal = build()
    cbo = build_cbo(cal)
    sums, segs = [], []
    for name, d in (("NIPA 1971-2024", cal.loc[1971:2024]), ("CBO cyc.adj. 1967-2025", cbo.loc[1967:2025])):
        for x in ("b_l", "IC_l"):
            s, g = run(name, d, x)
            sums.append(s)
            segs += g
    s, g = pd.DataFrame(sums), pd.DataFrame(segs)
    s.to_csv(OUT / "breaks.csv", index=False)
    g.to_csv(OUT / "breaks_segments.csv", index=False)
    pd.set_option("display.width", 250)
    print(s.round(3).T.to_string())
    print(g.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
