# %% [markdown]
# # fairfig cookbook - phase-equilibrium & property figures
# Run cell by cell (VSCodium / Jupyter "# %%" cells) or as a script.
# All data below are SYNTHETIC (generated from a simple model) - replace them
# with your own arrays; keep the plotting lines. Each figure is written as
# SVG (editable text) + PDF (fonts embedded) to examples/output/.

# %% Setup
import os
import sys

import numpy as np
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
sys.path.insert(0, os.path.dirname(HERE))          # folder that contains fairfig/
import fairfig as ff

ff.use("acs")                  # "elsevier" | "nature";  ticks="in", grid=False, units="paren"
OUT = os.path.join(HERE, "output")
rng = np.random.default_rng(7)

# %% Synthetic thermodynamics (ignore - just makes realistic-looking data)
P_ATM = 101.325                                    # kPa


def psat(T, A, B, C):                              # Antoine, ln(p/kPa) = A - B/(T - C)
    return np.exp(A - B / (T - C))


def gammas(x1, a12, a21):                          # two-parameter Margules
    x2 = 1 - x1
    return (np.exp(x2**2 * (a12 + 2 * (a21 - a12) * x1)),
            np.exp(x1**2 * (a21 + 2 * (a12 - a21) * x2)))


SYSTEMS = {   # name: (Antoine 1, Antoine 2, Margules a12, a21)
    "A + B": ((14.110, 2800, 45), (14.315, 3200, 50), 0.35, 0.50),
    "A + C": ((14.110, 2800, 45), (14.050, 2860, 47), 1.10, 0.95),   # azeotrope
    "A + D": ((14.110, 2800, 45), (14.520, 3350, 52), -0.55, -0.45),
}


def bubble_T(x1, p, sysname, n_iter=60):
    (A1, A2, a12, a21) = SYSTEMS[sysname]
    lo, hi = np.full_like(x1, 250.0), np.full_like(x1, 500.0)
    for _ in range(n_iter):                         # vectorised bisection
        T = 0.5 * (lo + hi)
        g1, g2 = gammas(x1, a12, a21)
        f = x1 * g1 * psat(T, *A1) + (1 - x1) * g2 * psat(T, *A2) - p
        hi, lo = np.where(f > 0, T, hi), np.where(f > 0, lo, T)
    g1, _ = gammas(x1, a12, a21)
    return T, x1 * g1 * psat(T, *A1) / p


def bubble_P(x1, T, sysname):
    (A1, A2, a12, a21) = SYSTEMS[sysname]
    g1, g2 = gammas(x1, a12, a21)
    p1, p2 = x1 * g1 * psat(T, *A1), (1 - x1) * g2 * psat(T, *A2)
    return p1 + p2, p1 / (p1 + p2)


xm = np.linspace(0, 1, 201)                         # model grid
xe = np.array([0.05, 0.12, 0.20, 0.31, 0.42, 0.53, 0.64, 0.75, 0.86, 0.94])  # "measured"

# %% Fig. 1 - isobaric T-x-y (single column)
# Experiment: filled = liquid x1, open = vapour y1 (same colour & shape);
# model = line in the same colour; literature = grey open markers.
Tm, ym = bubble_T(xm, P_ATM, "A + B")
Te, ye = bubble_T(xe, P_ATM, "A + B")
Te += rng.normal(0, 0.08, xe.size)
ye += rng.normal(0, 0.004, xe.size)
xl = np.array([0.10, 0.35, 0.60, 0.85])
Tl, yl = bubble_T(xl, P_ATM, "A + B")

fig, ax = ff.figure("single")
ax.plot(xm, Tm, **ff.curve(0), label="NRTL")
ax.plot(ym, Tm, **ff.curve(0))
ax.plot(xe, Te, **ff.points(0), label="$x_1$, this work")
ax.plot(ye, Te, **ff.points(0, hollow=True), label="$y_1$, this work")
ax.plot(xl, Tl + 0.5, **ff.points(1, lit=True), label="Lit. (ref. 12)")
ax.plot(yl, Tl + 0.5, **ff.points(1, lit=True))
h, l = ax.get_legend_handles_labels()
order = [1, 2, 0, 3]                                # this work, model, literature
ff.fraction_axis(ax, "x")
ax.set(xlabel=ff.label("x_1, y_1"), ylabel=ff.label("T", "K"))
ff.legend(ax, [h[k] for k in order], [l[k] for k in order])   # key above the plot
ff.save(fig, os.path.join(OUT, "fig1_Txy"))                     # -> fig1_Txy.svg + .pdf

# %% Fig. 2 - isotherms P-x-y (ordered -> ramp) + x-y for three systems (categorical)
temps = [333.15, 353.15, 373.15]
r = ff.ramp(len(temps))                             # dark -> light = low -> high T
fig, (a, b) = ff.subplots(1, 2, width="double")

for k, T in enumerate(temps):
    pm, ymk = bubble_P(xm, T, "A + B")
    pe, yek = bubble_P(xe, T, "A + B")
    pe *= 1 + rng.normal(0, 0.004, xe.size)
    a.plot(xm, pm, **ff.curve(k, color=r[k]))
    a.plot(ymk, pm, **ff.curve(k, color=r[k]))
    a.plot(xe, pe, **ff.points(k, color=r[k]), label=f"{T:.2f} K")
    a.plot(yek + rng.normal(0, 0.004, xe.size), pe, **ff.points(k, color=r[k], hollow=True))
ff.fraction_axis(a, "x")
a.set(xlabel=ff.label("x_1, y_1"), ylabel=ff.label("p", "kPa"))
ff.legend(a)

S = ff.slots(SYSTEMS)                               # system -> fixed colour/marker slot
ff.diagonal(b)
for name, i in S.items():
    Tm_, ym_ = bubble_T(xm, P_ATM, name)
    _, ye_ = bubble_T(xe, P_ATM, name)
    b.plot(xm, ym_, **ff.curve(i))
    b.plot(xe, np.clip(ye_ + rng.normal(0, 0.005, xe.size), 0, 1), **ff.points(i), label=name)
ff.fraction_axis(b, "x")
ff.fraction_axis(b, "y")
b.set_aspect("equal")
b.set(xlabel=ff.label("x_1"), ylabel=ff.label("y_1"))
ff.legend(b)
ff.panel_labels([a, b])
ff.save(fig, os.path.join(OUT, "fig2_Pxy_xy"))

# %% Fig. 3 - binary LLE with UCST (single column)
# Phase I (filled) and phase II (open) share colour; the two-phase region is shaded
# with a transparent band, so the grid stays visible.
Tc, xc = 338.0, 0.45


def binodal(T):                                     # simple scaling-law binodal
    w = 0.95 * ((Tc - T) / Tc) ** 0.325
    d = xc + 0.35 * (Tc - T) / Tc
    return np.clip(d - w, 0, 1), np.clip(d + w, 0, 1)


Tb = np.linspace(280, Tc, 400)
xI, xII = binodal(Tb)
Te = np.array([295, 305, 315, 322, 328, 332, 335, 337.0])
eI, eII = binodal(Te)
Tlit = np.array([300.0, 318.0])
lI, lII = binodal(Tlit)
fig, ax = ff.figure("single")
ff.band(ax, Tb, xI, xII, i=0, amount=0.10, along="y")   # two-phase region
ax.plot(xI, Tb, **ff.curve(0), label="NRTL")
ax.plot(xII, Tb, **ff.curve(0))
ax.plot(eI + rng.normal(0, 0.005, Te.size), Te, **ff.points(0), label="Phase I")
ax.plot(eII + rng.normal(0, 0.005, Te.size), Te, **ff.points(0, hollow=True), label="Phase II")
ax.plot(np.r_[lI, lII] + 0.012, np.r_[Tlit, Tlit], **ff.points(1, lit=True), label="Lit.")
ax.text(0.47, 312, "two liquid phases", ha="center", va="center", color=ff.C.grey_dk)
ff.fraction_axis(ax, "x")
ax.set_ylim(288, 344)
ax.set(xlabel=ff.label("x_1"), ylabel=ff.label("T", "K"))
h, l = ax.get_legend_handles_labels()
ff.legend(ax, [h[k] for k in (1, 2, 0, 3)], [l[k] for k in (1, 2, 0, 3)])
ff.save(fig, os.path.join(OUT, "fig3_LLE"))

# %% Fig. 4 - density vs T (ordered compositions) + excess volume (ordered T)
comps = [0.0, 0.25, 0.50, 0.75, 1.0]
rc = ff.ramp(len(comps))
T = np.linspace(288.15, 338.15, 11)
fig, (a, b) = ff.subplots(1, 2, width="double")
for k, x1 in enumerate(comps):
    rho = 998 - 215 * x1 + 25 * x1 * (1 - x1) - (0.30 + 0.62 * x1) * (T - 298.15)
    a.plot(T, rho, **ff.curve(k, color=rc[k]))
    a.plot(T, rho + rng.normal(0, 0.4, T.size), **ff.points(k, color=rc[k]))
    ff.end_label(a, T[-1], rho[-1], f"{x1:.2f}", dx=5)   # direct label, no legend
a.text(T[-1], 1022, ff.label("x_1"), ha="left", va="center")
a.set_xlim(285, 352)
a.set_xticks(np.arange(290, 341, 10))              # no tick under the labels
a.set_ylim(730, 1035)
a.set(xlabel=ff.label("T", "K"), ylabel=ff.label(r"\rho", "kg m^-3"))

TV = [288.15, 298.15, 308.15, 318.15]
rv = ff.ramp(len(TV))
x = np.linspace(0, 1, 201)
xs = np.arange(0.05, 1.0, 0.1)
for k, TT in enumerate(TV):
    A0, A1, A2 = -0.30 - 0.012 * (TT - 298.15), 1.5, 0.3

    def VE(z):
        return z * (1 - z) * (A0 + A1 * (2 * z - 1) + A2 * (2 * z - 1) ** 2)

    b.plot(x, VE(x), **ff.curve(k, color=rv[k]))
    b.plot(xs, VE(xs) + rng.normal(0, 0.004, xs.size), **ff.points(k, color=rv[k]),
           label=f"{TT:.2f} K")
ff.hline(b, 0)
ff.fraction_axis(b, "x")
b.set(xlabel=ff.label("x_1"), ylabel=ff.label(r"V_\mathrm{m}^\mathrm{E}", "cm^3 mol^-1"))
ff.legend(b)
ff.panel_labels([a, b])
ff.save(fig, os.path.join(OUT, "fig4_density_VE"))

# %% Fig. 5 - deviations (residuals) with an uncertainty band (single column)
fig, ax = ff.figure("single", aspect=0.62)
ff.band(ax, [0, 1], -0.005, 0.005)                # +/- u(y1)
ff.hline(ax, 0)
for name, i in S.items():
    dy = rng.normal(0, 0.003, xe.size) + 0.002 * (i - 1)
    ax.plot(xe + 0.006 * (i - 1), dy, **ff.points(i), label=name)
ff.fraction_axis(ax, "x")
ax.set_ylim(-0.0125, 0.0125)
ax.set(xlabel=ff.label("x_1"), ylabel=ff.label(r"y_1^\mathrm{exp} - y_1^\mathrm{calc}"))
ff.legend(ax)
ff.save(fig, os.path.join(OUT, "fig5_deviations"))

# %% Fig. 6 - maps: sequential (batlow) and diverging (vik, centred at zero)
import matplotlib.colors as mcolors

xg, Tg = np.meshgrid(np.linspace(0, 1, 121), np.linspace(288.15, 348.15, 121))
GE = xg * (1 - xg) * (0.35 + 0.15 * (2 * xg - 1)) * (1 + 0.004 * (Tg - 298.15))
VEg = xg * (1 - xg) * ((-0.30 - 0.012 * (Tg - 298.15)) + 1.5 * (2 * xg - 1) + 0.3 * (2 * xg - 1) ** 2)
fig, (a, b) = ff.subplots(1, 2, width="double", aspect=0.75)
m1 = a.contourf(xg, Tg, GE, levels=12, cmap=ff.cmap("seq"))
a.contour(xg, Tg, GE, levels=m1.levels, colors="white", linewidths=0.3, alpha=0.6)
ff.colorbar(m1, a, label=ff.label(r"G^\mathrm{E}/RT"))
lim = np.abs(VEg).max()
m2 = b.pcolormesh(xg, Tg, VEg, cmap=ff.cmap("div"), norm=mcolors.CenteredNorm(0, lim),
                  shading="auto", rasterized=True)
b.contour(xg, Tg, VEg, levels=[0], colors="black", linewidths=0.6)
ff.colorbar(m2, b, label=ff.label(r"V_\mathrm{m}^\mathrm{E}", "cm^3 mol^-1"))
for ax_ in (a, b):
    ff.grid(ax_, False)                             # no grid on colour maps
    ff.fraction_axis(ax_, "x")
    ax_.set(xlabel=ff.label("x_1"), ylabel=ff.label("T", "K"))
ff.panel_labels([a, b])
ff.save(fig, os.path.join(OUT, "fig6_maps"))

# %% Checks: palette numbers, palette card, and how the last figure looks with CVD
ff.check_palette()                                  # contrast + CVD distances (printed)
card = ff.swatches()
ff.save(card, os.path.join(OUT, "palette_card"))
card = ff.swatches("okabe-ito")                     # the alternative: ff.use("acs", palette="okabe-ito")
ff.save(card, os.path.join(OUT, "palette_card_okabe-ito"))
ff.cvd_preview(fig)                                 # shown in the notebook, not saved
plt.show()
