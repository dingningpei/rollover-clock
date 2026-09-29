"""Numerical scan: does repricing speed lambda change local stability?"""
import numpy as np

def jac_B(g, r, b, psi, phi, lam, kap):
    L = lam + g
    return np.array([[r - g, b, -1.0],
                     [psi * L, -L, 0.0],
                     [kap * phi * r, kap * phi * b, -kap]])

def jac_A(g, r, b, psi, phi, lam):
    L = lam + g
    return np.array([[(1 - phi) * r - g, b * (1 - phi)], [psi * L, -L]])

g, b, psi = 0.04, 1.0, 0.015
flips = 0; checked = 0
for r in np.linspace(0.02, 0.08, 13):
    for phi in np.linspace(0, 2, 41):
        if abs(g - (1 - phi) * (r + psi * b)) < 1e-9:
            continue  # exactly on the long-run boundary (det = 0)
        for kap in [0.1, 0.25, 0.5, 1, 2, 5]:
            st = []
            for lam in np.linspace(0.05, 5, 100):
                ev = np.linalg.eigvals(jac_B(g, r, b, psi, phi, lam, kap))
                st.append(ev.real.max() < 0)
            checked += 1
            if len(set(st)) > 1:
                flips += 1
                if flips <= 8:
                    lams = np.linspace(0.05, 5, 100)
                    cut = lams[np.argmax(np.diff(st) != 0) + 1]
                    print(f"r={r:.3f} phi={phi:.2f} kappa={kap}: stability changes at lambda~{cut:.2f} (stable at low lambda: {st[0]})")
            # Model A invariance check
            sa = {np.linalg.eigvals(jac_A(g, r, b, psi, phi, l)).real.max() < 0 for l in np.linspace(0.05, 5, 50)}
            assert len(sa) == 1, "Model A stability depends on lambda"
print(f"Model A: stability independent of lambda in all {checked} cases")
print(f"Model B: lambda flips stability in {flips} of {checked} (r, phi, kappa) cases")
