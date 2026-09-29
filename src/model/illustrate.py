"""Illustrative numbers for the model (not calibrated results)."""
import numpy as np

g, b, psi = 0.04, 1.0, 0.015

def phi_star(r):
    """Minimum instant fiscal offset of marginal interest cost for stability."""
    return 1 - g / (r + psi * b)

def divergence_rate(r, phi, lam):
    L = lam + g
    J = np.array([[(1 - phi) * r - g, b * (1 - phi)], [psi * L, -L]])
    return np.linalg.eigvals(J).real.max()

def required_inflation(dr, theta, lam, H):
    """Sustained surprise inflation that offsets the unfinanced share (1-theta)
    of the extra interest from a permanent real-rate rise dr over H years,
    with exponential repricing P(h) = 1 - exp(-(lam+g) h)."""
    L = lam + g
    unrepriced = (1 - np.exp(-L * H)) / L        # int_0^H (1 - P)
    repriced = H - unrepriced                    # int_0^H P
    return (1 - theta) * dr * repriced / unrepriced

print("phi* (minimum instant offset share):")
for r in [0.03, 0.04, 0.045, 0.05, 0.06]:
    print(f"  r={r:.3f}: phi* = {phi_star(r):.2f}")

print("\nDivergence rate (per year) when unstable, r=0.05, phi=0:")
for lam, lab in [(0.20, "WAM ~5y, Treasury-only"), (0.35, "shorter, consolidated")]:
    mu = divergence_rate(0.05, 0.0, lam)
    print(f"  lambda={lam:.2f} ({lab}): mu = {mu:.4f}, doubling time of deviation = {np.log(2)/mu:.1f}y")

print("\nRequired sustained inflation (pp/yr) to offset a permanent +1pp real-rate shock, theta=0:")
for H in [5, 10]:
    for lam, lab in [(0.20, "Treasury-only"), (0.35, "consolidated")]:
        print(f"  H={H:>2}y lambda={lam:.2f} ({lab}): {100*required_inflation(0.01, 0.0, lam, H):.2f}")
