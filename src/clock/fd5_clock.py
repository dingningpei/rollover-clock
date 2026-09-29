"""Rollover clock 1980-2002 from Treasury Bulletin FD-5 (privately held marketable debt).

Before October 2008 reserves paid no interest and reverse repos were small, so the
interest-bearing consolidated liability is ~ privately held marketable debt (FD-5
excludes Fed and Government-account holdings). Buckets (remaining maturity):
<1, 1-5, 5-10, 10-20, 20+ years; uniform within bucket (20+ spread over 20-30).

Validation on 2003-2025: the exact CUSIP-level consolidated portfolio is bucketed the
same way and both versions are compared (F(h) and required-inflation ratio).
Source rows: data/manual/fd5_december.csv (hand-transcribed; sums checked).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .consolidated_clock import OVERNIGHT, soma_by_cusip
from .inflation_layer import GRID
from .treasury_clock import G_BASELINE, securities

EDGES = np.array([0, 1, 5, 10, 20, 30])
BUCKETS = ["b1", "b1_5", "b5_10", "b10_20", "b20"]
OUT = Path("data/processed/clock")


def F_bucketed(shares: np.ndarray, h: np.ndarray) -> np.ndarray:
    F = np.zeros_like(h, dtype=float)
    for s, lo, hi in zip(shares, EDGES[:-1], EDGES[1:]):
        F += s * np.clip((h - lo) / (hi - lo), 0, 1)
    return F


def ratio_from_F(F: np.ndarray, h: np.ndarray, H: float, g: float = G_BASELINE) -> float:
    m = h <= H
    P = 1 - (1 - F[m]) * np.exp(-g * h[m])
    return np.trapezoid(P, h[m]) / np.trapezoid(1 - P, h[m])


def exact_F(tau: np.ndarray, w: np.ndarray, h: np.ndarray) -> np.ndarray:
    o = np.argsort(tau)
    cw = np.cumsum(w[o]) / w.sum()
    F = np.interp(h, tau[o], cw, left=0.0, right=1.0)
    F[h < tau[o][0]] = 0.0
    return F


def bucket_shares(tau: np.ndarray, w: np.ndarray) -> np.ndarray:
    idx = np.clip(np.searchsorted(EDGES, tau, side="right") - 1, 0, 4)
    return np.array([w[idx == k].sum() for k in range(5)]) / w.sum()


def validation() -> pd.DataFrame:
    sec = securities(pd.read_csv("data/interim/mspd/table3_market_yearend.csv", dtype=str))
    sec["year"] = sec.record_date.dt.year
    soma = soma_by_cusip(pd.read_csv("data/interim/fed/soma_tsy_yearend.csv", dtype=str))
    soma["year"] = soma.year.astype(int)
    h41 = pd.read_csv("data/interim/fed/h41_wednesday_levels.csv")
    rows = []
    for y, s in soma.groupby("year"):
        x = sec[sec.year == y].merge(s[["cusip", "soma_par"]], on="cusip", how="left").fillna({"soma_par": 0})
        lev = h41.loc[h41.date <= s.asOfDate.iloc[0]].iloc[-1]
        for version, tau, w in (
            ("private_tsy", x.tau.values, (x.par - x.soma_par).values),
            ("consolidated", np.r_[x.tau.values, OVERNIGHT], np.r_[(x.par - x.soma_par).values, lev.reserves + lev.reverse_repo]),
        ):
            sh = bucket_shares(tau, w)
            Fe, Fb = exact_F(tau, w, GRID), F_bucketed(sh, GRID)
            rows.append({"year": y, "version": version, **{f"share_{b}": v for b, v in zip(BUCKETS, sh)},
                         "total": w.sum(),
                         "ratio10_exact": ratio_from_F(Fe, GRID, 10), "ratio10_bucket": ratio_from_F(Fb, GRID, 10),
                         "ratio5_exact": ratio_from_F(Fe, GRID, 5), "ratio5_bucket": ratio_from_F(Fb, GRID, 5),
                         "F1_exact": Fe[np.searchsorted(GRID, 1)], "F1_bucket": Fb[np.searchsorted(GRID, 1)]})
    return pd.DataFrame(rows)


def fd5_series() -> pd.DataFrame:
    d = pd.read_csv("data/manual/fd5_december.csv")
    d["year"] = d.year_end.str[:4].astype(int)
    out = []
    for r in d.itertuples():
        sh = np.array([getattr(r, b) for b in BUCKETS], dtype=float) / r.total
        F = F_bucketed(sh, GRID)
        out.append({"year": r.year, "total_private": r.total, **{f"share_{b}": v for b, v in zip(BUCKETS, sh)},
                    "avg_length_reported": r.avg_years + r.avg_months / 12,
                    "avg_length_bucket_mid": float((sh * (EDGES[:-1] + EDGES[1:]) / 2).sum()),
                    "F1": F[np.searchsorted(GRID, 1)], "ratio5": ratio_from_F(F, GRID, 5), "ratio10": ratio_from_F(F, GRID, 10)})
    return pd.DataFrame(out)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    v = validation()
    v.to_csv(OUT / "fd5_bucket_validation.csv", index=False)
    f = fd5_series()
    f.to_csv(OUT / "fd5_clock_1980_2003.csv", index=False)
    for ver in ("private_tsy", "consolidated"):
        s = v[v.version == ver]
        e10 = s.ratio10_bucket - s.ratio10_exact
        print(f"{ver}: bucket error ratio10 mean {e10.mean():+.3f}, max |.| {e10.abs().max():.3f}; "
              f"F(1) err mean {(s.F1_bucket - s.F1_exact).mean():+.3f}")
    o3 = v[(v.year == 2003) & (v.version == "private_tsy")].iloc[0]
    f3 = f[f.year == 2003].iloc[0]
    print("2003 overlap, private Treasuries: total MSPD-SOMA %.0f vs FD-5 %.0f" % (o3.total, f3.total_private))
    print("  shares MSPD-SOMA:", [round(o3[f'share_{b}'], 3) for b in BUCKETS])
    print("  shares FD-5     :", [round(f3[f'share_{b}'], 3) for b in BUCKETS])
    print(f[["year", "total_private", "avg_length_reported", "avg_length_bucket_mid", "F1", "ratio5", "ratio10"]].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
