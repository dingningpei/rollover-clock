"""Symbolic derivation of local stability for the rollover-clock model.

State: b (debt/GDP), rb (average effective rate on debt), and optionally s
(primary surplus/GDP) when fiscal policy adjusts with a lag.

  db/dt  = (rb - g) b - s
  drb/dt = Lam (r(b) - rb),      Lam = lam + g   (repricing speed)
  r(b)   = rstar + psi (b - bstar)               (market rate)
  s      = sstar + phi (rb b - rstar bstar)      (Model A: instant response)
  ds/dt  = kap (sstar + phi (rb b - rstar bstar) - s)   (Model B: lagged)
"""
import sympy as sp

b, rb, s = sp.symbols("b r_b s")
g, lam, psi, phi, kap, rstar, bstar = sp.symbols(
    "g lambda psi phi kappa r_star b_star", positive=True)
Lam = lam + g
sstar = (rstar - g) * bstar            # steady state: rb = r*, db/dt = 0
r_mkt = rstar + psi * (b - bstar)
ss = {b: bstar, rb: rstar, s: sstar}

# Model A
sA = sstar + phi * (rb * b - rstar * bstar)
FA = sp.Matrix([(rb - g) * b - sA, Lam * (r_mkt - rb)])
JA = sp.simplify(FA.jacobian([b, rb]).subs(ss))
print("Model A Jacobian:"); sp.pprint(JA)
print("trace =", sp.factor(JA.trace()))
print("det   =", sp.factor(JA.det()))

# Model B
FB = sp.Matrix([(rb - g) * b - s,
                Lam * (r_mkt - rb),
                kap * (sstar + phi * (rb * b - rstar * bstar) - s)])
JB = sp.simplify(FB.jacobian([b, rb, s]).subs(ss))
print("\nModel B Jacobian:"); sp.pprint(JB)
x = sp.symbols("x")
p = sp.Poly(sp.expand((x * sp.eye(3) - JB).det()), x)
a2, a1, a0 = [sp.factor(c) for c in p.all_coeffs()[1:]]
print("char poly: x^3 + a2 x^2 + a1 x + a0")
print("a2 =", a2); print("a1 =", a1); print("a0 =", a0)
print("Routh-Hurwitz: a2>0, a0>0, a2*a1 - a0 > 0")
print("a2*a1 - a0 =", sp.factor(sp.expand(a2 * a1 - a0)))
