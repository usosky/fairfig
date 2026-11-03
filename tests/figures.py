"""Figures for the snapshot tests: the cookbook recipes on fixed synthetic data.

Each function draws one figure with the identity that is active, so call
ff.use(...) first. Data come from a simple model (Antoine + Margules) with
seeded noise, so every run draws the same figure.
"""
import matplotlib.colors as mcolors
import numpy as np

import fairfig as ff

P_ATM = 101.325                                    # kPa
SYSTEMS = {   # name: (Antoine 1, Antoine 2, Margules a12, a21)
    "A + B": ((14.110, 2800, 45), (14.315, 3200, 50), 0.35, 0.50),
    "A + C": ((14.110, 2800, 45), (14.050, 2860, 47), 1.10, 0.95),   # azeotrope
    "A + D": ((14.110, 2800, 45), (14.520, 3350, 52), -0.55, -0.45),
}
XM = np.linspace(0, 1, 201)                         # model grid
XE = np.array([0.05, 0.12, 0.20, 0.31, 0.42, 0.53, 0.64, 0.75, 0.86, 0.94])


def psat(T, A, B, C):
    return np.exp(A - B / (T - C))


def gammas(x1, a12, a21):
    x2 = 1 - x1
    return (np.exp(x2**2 * (a12 + 2 * (a21 - a12) * x1)),
            np.exp(x1**2 * (a21 + 2 * (a12 - a21) * x2)))


def bubble_T(x1, p, name):
    (A1, A2, a12, a21) = SYSTEMS[name]
    lo, hi = np.full_like(x1, 250.0), np.full_like(x1, 500.0)
    for _ in range(60):
        T = 0.5 * (lo + hi)
        g1, g2 = gammas(x1, a12, a21)
        f = x1 * g1 * psat(T, *A1) + (1 - x1) * g2 * psat(T, *A2) - p
        hi, lo = np.where(f > 0, T, hi), np.where(f > 0, lo, T)
    g1, _ = gammas(x1, a12, a21)
    return T, x1 * g1 * psat(T, *A1) / p


def bubble_P(x1, T, name):
    (A1, A2, a12, a21) = SYSTEMS[name]
    g1, g2 = gammas(x1, a12, a21)
    p1, p2 = x1 * g1 * psat(T, *A1), (1 - x1) * g2 * psat(T, *A2)
    return p1 + p2, p1 / (p1 + p2)


def txy():
    """T-x-y: experiment (filled/open), model lines, literature, legend on top."""
    rng = np.random.default_rng(7)
    Tm, ym = bubble_T(XM, P_ATM, "A + B")
    Te, ye = bubble_T(XE, P_ATM, "A + B")
    Te = Te + rng.normal(0, 0.08, XE.size)
    ye = ye + rng.normal(0, 0.004, XE.size)
    xl = np.array([0.10, 0.35, 0.60, 0.85])
    Tl, yl = bubble_T(xl, P_ATM, "A + B")
    fig, ax = ff.figure("single")
    ax.plot(XM, Tm, **ff.curve(0), label="NRTL")
    ax.plot(ym, Tm, **ff.curve(0))
    ax.plot(XE, Te, **ff.points(0), label="$x_1$, this work")
    ax.plot(ye, Te, **ff.points(0, hollow=True), label="$y_1$, this work")
    ax.plot(xl, Tl + 0.5, **ff.points(1, lit=True), label="Lit. (ref. 12)")
    ax.plot(yl, Tl + 0.5, **ff.points(1, lit=True))
    h, l = ax.get_legend_handles_labels()
    order = [1, 2, 0, 3]
    ff.fraction_axis(ax, "x")
    ax.set(xlabel=ff.label("x_1, y_1"), ylabel=ff.label("T", "K"))
    ff.legend(ax, [h[k] for k in order], [l[k] for k in order])
    return fig


def pxy_and_xy():
    """Double column: isotherms coloured with a ramp, and x-y for three systems."""
    rng = np.random.default_rng(8)
    temps = [333.15, 353.15, 373.15]
    r = ff.ramp(len(temps))
    fig, (a, b) = ff.subplots(1, 2, width="double")
    for k, T in enumerate(temps):
        pm, ymk = bubble_P(XM, T, "A + B")
        pe, yek = bubble_P(XE, T, "A + B")
        pe = pe * (1 + rng.normal(0, 0.004, XE.size))
        a.plot(XM, pm, **ff.curve(k, color=r[k]))
        a.plot(ymk, pm, **ff.curve(k, color=r[k]))
        a.plot(XE, pe, **ff.points(k, color=r[k]), label=f"{T:.2f} K")
        a.plot(yek + rng.normal(0, 0.004, XE.size), pe, **ff.points(k, color=r[k], hollow=True))
    ff.fraction_axis(a, "x")
    a.set(xlabel=ff.label("x_1, y_1"), ylabel=ff.label("p", "kPa"))
    ff.legend(a)
    S = ff.slots(SYSTEMS)
    ff.diagonal(b)
    for name, i in S.items():
        _, ym_ = bubble_T(XM, P_ATM, name)
        _, ye_ = bubble_T(XE, P_ATM, name)
        b.plot(XM, ym_, **ff.curve(i))
        b.plot(XE, np.clip(ye_ + rng.normal(0, 0.005, XE.size), 0, 1), **ff.points(i), label=name)
    ff.fraction_axis(b, "x")
    ff.fraction_axis(b, "y")
    b.set_aspect("equal")
    b.set(xlabel=ff.label("x_1"), ylabel=ff.label("y_1"))
    ff.legend(b)
    ff.panel_labels([a, b])
    return fig


def lle():
    """Binary LLE: two-phase region shaded along y, filled/open phases."""
    rng = np.random.default_rng(9)
    Tc, xc = 338.0, 0.45

    def binodal(T):
        w = 0.95 * ((Tc - T) / Tc) ** 0.325
        d = xc + 0.35 * (Tc - T) / Tc
        return np.clip(d - w, 0, 1), np.clip(d + w, 0, 1)

    Tb = np.linspace(280, Tc, 400)
    xI, xII = binodal(Tb)
    Te = np.array([295, 305, 315, 322, 328, 332, 335, 337.0])
    eI, eII = binodal(Te)
    fig, ax = ff.figure("single")
    ff.band(ax, Tb, xI, xII, i=0, amount=0.10, along="y")
    ax.plot(xI, Tb, **ff.curve(0), label="NRTL")
    ax.plot(xII, Tb, **ff.curve(0))
    ax.plot(eI + rng.normal(0, 0.005, Te.size), Te, **ff.points(0), label="Phase I")
    ax.plot(eII + rng.normal(0, 0.005, Te.size), Te, **ff.points(0, hollow=True), label="Phase II")
    ax.text(0.47, 312, "two liquid phases", ha="center", va="center", color=ff.C.grey_dk)
    ff.fraction_axis(ax, "x")
    ax.set_ylim(288, 344)
    ax.set(xlabel=ff.label("x_1"), ylabel=ff.label("T", "K"))
    h, l = ax.get_legend_handles_labels()
    ff.legend(ax, [h[k] for k in (1, 2, 0)], [l[k] for k in (1, 2, 0)])
    return fig


def density_and_excess_volume():
    """Ordered series: direct end labels (no legend), and a ramp with a legend."""
    rng = np.random.default_rng(10)
    comps = [0.0, 0.25, 0.50, 0.75, 1.0]
    rc = ff.ramp(len(comps))
    T = np.linspace(288.15, 338.15, 11)
    fig, (a, b) = ff.subplots(1, 2, width="double")
    for k, x1 in enumerate(comps):
        rho = 998 - 215 * x1 + 25 * x1 * (1 - x1) - (0.30 + 0.62 * x1) * (T - 298.15)
        a.plot(T, rho, **ff.curve(k, color=rc[k]))
        a.plot(T, rho + rng.normal(0, 0.4, T.size), **ff.points(k, color=rc[k]))
        ff.end_label(a, T[-1], rho[-1], f"{x1:.2f}", dx=5)
    a.set_xlim(285, 352)
    a.set_xticks(np.arange(290, 341, 10))
    a.set_ylim(730, 1035)
    a.set(xlabel=ff.label("T", "K"), ylabel=ff.label(r"\rho", "kg m^-3"))
    TV = [288.15, 298.15, 308.15, 318.15]
    rv = ff.ramp(len(TV))
    x = np.linspace(0, 1, 201)
    xs = np.arange(0.05, 1.0, 0.1)
    for k, TT in enumerate(TV):
        A0 = -0.30 - 0.012 * (TT - 298.15)
        ve = x * (1 - x) * (A0 + 1.5 * (2 * x - 1) + 0.3 * (2 * x - 1) ** 2)
        ves = xs * (1 - xs) * (A0 + 1.5 * (2 * xs - 1) + 0.3 * (2 * xs - 1) ** 2)
        b.plot(x, ve, **ff.curve(k, color=rv[k]))
        b.plot(xs, ves + rng.normal(0, 0.004, xs.size), **ff.points(k, color=rv[k]),
               label=f"{TT:.2f} K")
    ff.hline(b, 0)
    ff.fraction_axis(b, "x")
    b.set(xlabel=ff.label("x_1"), ylabel=ff.label(r"V_\mathrm{m}^\mathrm{E}", "cm^3 mol^-1"))
    ff.legend(b)
    ff.panel_labels([a, b])
    return fig


def deviations():
    """Residuals of three systems inside a grey uncertainty band."""
    rng = np.random.default_rng(11)
    fig, ax = ff.figure("single", aspect=0.62)
    ff.band(ax, [0, 1], -0.005, 0.005)
    ff.hline(ax, 0)
    for name, i in ff.slots(SYSTEMS).items():
        dy = rng.normal(0, 0.003, XE.size) + 0.002 * (i - 1)
        ax.plot(XE + 0.006 * (i - 1), dy, **ff.points(i), label=name)
    ff.fraction_axis(ax, "x")
    ax.set_ylim(-0.0125, 0.0125)
    ax.set(xlabel=ff.label("x_1"), ylabel=ff.label(r"y_1^\mathrm{exp} - y_1^\mathrm{calc}"))
    ff.legend(ax)
    return fig


def maps():
    """Sequential (batlow) and diverging (vik, centred at zero) maps with colour bars."""
    xg, Tg = np.meshgrid(np.linspace(0, 1, 61), np.linspace(288.15, 348.15, 61))
    GE = xg * (1 - xg) * (0.35 + 0.15 * (2 * xg - 1)) * (1 + 0.004 * (Tg - 298.15))
    VE = xg * (1 - xg) * ((-0.30 - 0.012 * (Tg - 298.15)) + 1.5 * (2 * xg - 1)
                          + 0.3 * (2 * xg - 1) ** 2)
    fig, (a, b) = ff.subplots(1, 2, width="double", aspect=0.75)
    m1 = a.contourf(xg, Tg, GE, levels=12, cmap=ff.cmap("seq"))
    ff.colorbar(m1, a, label=ff.label(r"G^\mathrm{E}/RT"))
    lim = np.abs(VE).max()
    m2 = b.pcolormesh(xg, Tg, VE, cmap=ff.cmap("div"), norm=mcolors.CenteredNorm(0, lim),
                      shading="auto")
    b.contour(xg, Tg, VE, levels=[0], colors="black", linewidths=0.6)
    ff.colorbar(m2, b, label=ff.label(r"V_\mathrm{m}^\mathrm{E}", "cm^3 mol^-1"))
    for ax in (a, b):
        ff.grid(ax, False)
        ff.fraction_axis(ax, "x")
        ax.set(xlabel=ff.label("x_1"), ylabel=ff.label("T", "K"))
    ff.panel_labels([a, b])
    return fig


def all_slots():
    """Every slot: filled and open markers, model line styles, literature data."""
    fig, ax = ff.figure("single", aspect=0.7)
    x = np.linspace(0, 1, 7)
    for i in range(len(ff.COLORS)):
        ax.plot(x, x * 0 + i, **ff.points(i), label=ff.NAMES[i])
        ax.plot(x + 0.06, x * 0 + i + 0.3, **ff.points(i, hollow=True))
    ax.plot(x, x * 0 - 1.0, **ff.points(0, lit=True), label="Lit.")
    for s in range(4):
        ax.plot([0, 1], [6.5 + 0.35 * s] * 2, **ff.curve(None, style=s))
    ax.set(xlabel=ff.label("x_1"), ylabel=ff.label("slot"))
    ff.legend(ax)
    return fig


def errorbars():
    """Error bars with ff.ERRORBAR, an open frame and the legend on the right."""
    rng = np.random.default_rng(12)
    fig, ax = ff.figure("single")
    T = np.linspace(290, 340, 8)
    for i in range(3):
        y = 1.2 - 0.004 * (T - 290) * (1 + 0.3 * i)
        ax.errorbar(T, y + rng.normal(0, 0.01, T.size), yerr=0.02, **ff.points(i),
                    **ff.ERRORBAR, label=f"set {i + 1}")
        ax.plot(T, y, **ff.curve(i, style=i))
    ax.set(xlabel=ff.label("T", "K"), ylabel=ff.label(r"\eta", "mPa s"))
    ff.legend(ax, loc="right")
    return fig


def cvd_source():
    """Small x-y figure whose colour-blind preview is snapshot-tested."""
    fig, ax = ff.figure(width=60, height=55)
    ff.diagonal(ax)
    for name, i in ff.slots(SYSTEMS).items():
        _, ym_ = bubble_T(XM, P_ATM, name)
        _, ye_ = bubble_T(XE, P_ATM, name)
        ax.plot(XM, ym_, **ff.curve(i))
        ax.plot(XE, ye_, **ff.points(i), label=name)
    ff.fraction_axis(ax, "x")
    ff.fraction_axis(ax, "y")
    ax.set(xlabel=ff.label("x_1"), ylabel=ff.label("y_1"))
    ff.legend(ax)
    return fig
