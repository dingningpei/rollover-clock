"""Check the repricing law  d rb/dt = (lam + Bdot/B) (r - rb)  against a
cohort-level simulation of debt that matures at Poisson rate lam."""
import numpy as np

dt, T, lam = 0.001, 20.0, 0.25
n = int(T / dt)
t = np.arange(n) * dt
r = np.where(t < 2, 0.03, 0.05)                 # market-rate step at t=2
Bdot_over_B = np.where(t < 10, 0.06, 0.02)      # debt growth (deficits)

# cohort bookkeeping: total face value F and coupon flow C
F, C = 1.0, 0.03
rb_cohort = np.empty(n)
rb_law = np.empty(n); rb_law[0] = 0.03
for i in range(n):
    rb_cohort[i] = C / F
    new = (lam + Bdot_over_B[i]) * F * dt       # rollover + net new issuance
    C += r[i] * new - lam * C * dt              # maturing debt carries avg coupon
    F += new - lam * F * dt
    if i + 1 < n:
        rb_law[i + 1] = rb_law[i] + (lam + Bdot_over_B[i]) * (r[i] - rb_law[i]) * dt
print("max |cohort - law| =", np.abs(rb_cohort - rb_law).max())
