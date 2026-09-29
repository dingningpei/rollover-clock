"""Rollover clock 1980-2002 from Treasury Bulletin FD-5 (privately held marketable debt).

Before October 2008 reserves paid no interest and reverse repos were small, so the
interest-bearing consolidated liability is ~ privately held marketable debt (FD-5
excludes Fed and Government-account holdings). Buckets (remaining maturity):
<1, 1-5, 5-10, 10-20, 20+ years; uniform within bucket (20+ spread over 20-30).

Inflation layer (paper, Section 3.3): the rate clock uses all buckets; the erosion clock
removes TIPS, bucketed by remaining maturity (FD-5 does not split them out). TIPS totals
1997-2002 are from Treasury Bulletin FD-2 (data/manual/tips_fd2_december.csv), with the
maturity profile of the TIPS issues outstanding at each year-end (MSPD 2001 list for
1997-2000). The zero-interest base is currency in circulation plus reserve balances
(unremunerated before October 2008), December averages from FRED.

Validation on 2003-2025: the exact CUSIP-level portfolio is bucketed the same way and both
versions are compared; the 2003-07 mean difference is the bucketing bias.
Source rows: data/manual/fd5_december.csv (hand-transcribed; sums checked).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .consolidated_clock import OVERNIGHT, soma_by_cusip
from .inflation_layer import GRID, HORIZONS, exact_F, integrals, layer, zero_interest_base_december
from .treasury_clock import G_BASELINE, securities

EDGES = np.array([0, 1, 5, 10, 20, 30])
BUCKETS = ["b1", "b1_5", "b5_10", "b10_20", "b20"]
OUT = Path("data/processed/clock")


def F_bucketed(shares: np.ndarray, h: np.ndarray) -> np.ndarray:
    F = np.zeros_like(h, dtype=float)
    for s, lo, hi in zip(shares, EDGES[:-1], EDGES[1:]):
        F += s * np.clip((h - lo) / (hi - lo), 0, 1)
    return F


def bucket_amounts(tau: np.ndarray, w: np.ndarray) -> np.ndarray:
    idx = np.clip(np.searchsorted(EDGES, tau, side="right") - 1, 0, 4)
    return np.array([w[idx == k].sum() for k in range(5)])


def bucket_shares(tau: np.ndarray, w: np.ndarray) -> np.ndarray:
    a = bucket_amounts(tau, w)
    return a / a.sum()


def bucketed_layer(all_b: np.ndarray, tips_b: np.ndarray, zero: float, H: float, g: float = G_BASELINE) -> dict:
    """Inflation-layer integrals from bucket amounts: all marketable, TIPS, zero-interest base."""
    nom_b = all_b - tips_b
    return integrals(F_bucketed(all_b / all_b.sum(), GRID), F_bucketed(nom_b / nom_b.sum(), GRID),
                     nom_b.sum() / all_b.sum(), zero / all_b.sum(), H, g)


def tips_buckets() -> dict:
    """TIPS amounts by remaining-maturity bucket at each December, 1997-2003 ($ millions)."""
    sec = securities(pd.read_csv("data/interim/mspd/table3_market_yearend.csv", dtype=str))
    tips = sec[sec.kind == "tips"]
    totals = pd.read_csv("data/manual/tips_fd2_december.csv")
    totals = dict(zip(totals.year_end.str[:4].astype(int), totals.tips_outstanding))
    raw = pd.read_csv("data/interim/mspd/table3_market_yearend.csv", dtype=str)
    issue = raw.drop_duplicates("security_class2_desc").set_index("security_class2_desc").issue_date
    out = {}
    for y in range(1997, 2004):
        if y >= 2001:
            x = tips[tips.record_date.dt.year == y]
            out[y] = bucket_amounts(x.tau.values, x.par.values)
            continue
        x = tips[tips.record_date.dt.year == 2001].copy()           # issues outstanding at end-y
        x["issued"] = pd.to_datetime(x.cusip.map(issue))
        end = pd.Timestamp(f"{y}-12-31")
        x = x[x.issued <= end]
        tau = (x.maturity_date - end).dt.days / 365.25
        a = bucket_amounts(tau.values, x.par.values)
        out[y] = a * totals[y] / a.sum()
    return out


def validation() -> pd.DataFrame:
    """Exact CUSIP-level vs FD-5-style bucketed, 2003-2025.
    private_tsy: marketable held outside the Fed (the FD-5 concept) + the zero-interest base
    (currency, and reserves before 2008), as in the 1980-2002 construction."""
    sec = securities(pd.read_csv("data/interim/mspd/table3_market_yearend.csv", dtype=str))
    sec["year"] = sec.record_date.dt.year
    soma = soma_by_cusip(pd.read_csv("data/interim/fed/soma_tsy_yearend.csv", dtype=str))
    soma["year"] = soma.year.astype(int)
    h41 = pd.read_csv("data/interim/fed/h41_wednesday_levels.csv")
    rows = []
    for y, s in soma.groupby("year"):
        x = sec[sec.year == y].merge(s[["cusip", "soma_par"]], on="cusip", how="left").fillna({"soma_par": 0})
        lev = h41.loc[h41.date <= s.asOfDate.iloc[0]].iloc[-1]
        priv, ix = (x.par - x.soma_par).values, (x.kind == "tips").values
        zero = lev.currency + (lev.reserves if y < 2008 else 0.0)
        tau = x.tau.values
        row = {"year": y, "total": priv.sum(), **{f"share_{b}": v for b, v in zip(BUCKETS, bucket_shares(tau, priv))}}
        Fe, Fb = exact_F(tau, priv, GRID), F_bucketed(bucket_shares(tau, priv), GRID)
        row["F1_exact"], row["F1_bucket"] = Fe[np.searchsorted(GRID, 1)], Fb[np.searchsorted(GRID, 1)]
        for H in HORIZONS:
            e = layer(tau, priv, ix, zero, H)
            b = bucketed_layer(bucket_amounts(tau, priv), bucket_amounts(tau[ix], priv[ix]), zero, H)
            for k in ("ratio", "intP", "ratio_narrow"):
                row[f"{k}_H{H}_exact"], row[f"{k}_H{H}_bucket"] = e[k], b[k]
        rows.append(row)
    return pd.DataFrame(rows)


def bucket_bias(v: pd.DataFrame) -> dict:
    """Mean bucketed-minus-exact error on 2003-07, before QE (the regime FD-5 years resemble)."""
    s = v[v.year <= 2007]
    return {c[:-7]: (s[c] - s[c.replace("_bucket", "_exact")]).mean() for c in v.columns if c.endswith("_bucket")}


def fd5_series(bias: dict) -> pd.DataFrame:
    d = pd.read_csv("data/manual/fd5_december.csv")
    d["year"] = d.year_end.str[:4].astype(int)
    tips, zero = tips_buckets(), zero_interest_base_december()
    out = []
    for r in d.itertuples():
        all_b = np.array([getattr(r, b) for b in BUCKETS], dtype=float)
        tips_b = tips.get(r.year, np.zeros(5))
        sh = all_b / r.total
        F = F_bucketed(sh, GRID)
        row = {"year": r.year, "total_private": r.total, "tips": tips_b.sum(), "zero_interest": zero[r.year],
               **{f"share_{b}": v for b, v in zip(BUCKETS, sh)},
               "avg_length_reported": r.avg_years + r.avg_months / 12,
               "avg_length_bucket_mid": float((sh * (EDGES[:-1] + EDGES[1:]) / 2).sum()),
               "F1": F[np.searchsorted(GRID, 1)]}
        for H in HORIZONS:
            lay = bucketed_layer(all_b, tips_b, zero[r.year], H)
            for k in ("ratio", "intP", "ratio_narrow", "jump_base"):
                row[f"{k}_H{H}_raw"] = lay[k]
                row[f"{k}_H{H}"] = lay[k] - bias.get(f"{k}_H{H}", 0.0)      # bias-corrected
        out.append(row)
    return pd.DataFrame(out)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    v = validation()
    v.to_csv(OUT / "fd5_bucket_validation.csv", index=False)
    bias = bucket_bias(v)
    pd.Series(bias).to_csv(OUT / "fd5_bucket_bias.csv", header=["bucket_minus_exact_2003_07"])
    f = fd5_series(bias)
    f.to_csv(OUT / "fd5_clock_1980_2003.csv", index=False)
    s = v[v.year <= 2007]
    for k in ("ratio_H10", "intP_H10", "ratio_narrow_H10"):
        e = s[f"{k}_bucket"] - s[f"{k}_exact"]
        print(f"bucket error {k}: mean {e.mean():+.3f}, sd {e.std():.3f}  (2003-07)")
    print(f"F(1) error mean {(v.F1_bucket - v.F1_exact).mean():+.3f}")
    o3, f3 = v[v.year == 2003].iloc[0], f[f.year == 2003].iloc[0]
    print("2003 overlap: MSPD-SOMA %.0f vs FD-5 %.0f; ratio_H10 exact %.3f vs FD-5 corrected %.3f"
          % (o3.total, f3.total_private, o3.ratio_H10_exact, f3.ratio_H10))
    print(f[["year", "total_private", "tips", "zero_interest", "F1", "ratio_narrow_H10", "ratio_H10", "intP_H10"]]
          .round(3).to_string(index=False))


if __name__ == "__main__":
    main()
