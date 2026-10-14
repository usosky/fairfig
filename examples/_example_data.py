# Synthetic VLE data for the identity sheet (same model as the cookbook demo).
import numpy as np

_rng = np.random.default_rng(7)
_P = 101.325
_SYS = {"A + B": ((14.110, 2800, 45), (14.315, 3200, 50), 0.35, 0.50),
        "A + C": ((14.110, 2800, 45), (14.050, 2860, 47), 1.10, 0.95),
        "A + D": ((14.110, 2800, 45), (14.520, 3350, 52), -0.55, -0.45)}


def _bubble_T(x1, name):
    (A1, A2, a12, a21) = _SYS[name]
    ps = lambda T, A, B, C: np.exp(A - B / (T - C))
    x2 = 1 - x1
    g1 = np.exp(x2**2 * (a12 + 2 * (a21 - a12) * x1))
    g2 = np.exp(x1**2 * (a21 + 2 * (a12 - a21) * x2))
    lo, hi = np.full_like(x1, 250.0), np.full_like(x1, 500.0)
    for _ in range(60):
        T = 0.5 * (lo + hi)
        f = x1 * g1 * ps(T, *A1) + x2 * g2 * ps(T, *A2) - _P
        hi, lo = np.where(f > 0, T, hi), np.where(f > 0, lo, T)
    return T, x1 * g1 * ps(T, *A1) / _P


xm = np.linspace(0, 1, 201)
xe = np.array([0.05, 0.12, 0.20, 0.31, 0.42, 0.53, 0.64, 0.75, 0.86, 0.94])
Tm, ym = _bubble_T(xm, "A + B")
Te, ye = _bubble_T(xe, "A + B")
Te = Te + _rng.normal(0, 0.08, xe.size)
ye = ye + _rng.normal(0, 0.004, xe.size)
xl = np.array([0.10, 0.35, 0.60, 0.85])
Tl, yl = _bubble_T(xl, "A + B")
S = {n: i for i, n in enumerate(_SYS)}
YM = {n: _bubble_T(xm, n)[1] for n in _SYS}
YE = {n: np.clip(_bubble_T(xe, n)[1] + _rng.normal(0, 0.005, xe.size), 0, 1) for n in _SYS}
