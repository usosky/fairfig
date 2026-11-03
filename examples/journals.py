# %% One figure, three journals -> output/journal_acs.svg/.pdf, _elsevier, _nature
# The plotting code stays the same; ff.use() sets each journal's column width,
# text size and panel-label style. Data are SYNTHETIC.
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
sys.path.insert(0, os.path.dirname(HERE))
import fairfig as ff

T = np.linspace(283.15, 343.15, 7)                 # K
x1 = [0.2, 0.5, 0.8]                               # ordered series -> colour ramp


def draw(a, b):
    """a: viscosity with a model line; b: deviations inside a +/- 1 % band."""
    rng = np.random.default_rng(3)
    r = ff.ramp(len(x1))
    ff.band(b, [T[0], T[-1]], -1, 1)               # +/- 1 % uncertainty
    ff.hline(b, 0)
    for k, x in enumerate(x1):
        model = 1.6 * np.exp(-0.022 * (T - 283.15)) * (1 + 0.9 * x)   # mPa s
        measured = model * (1 + rng.normal(0, 0.005, T.size))
        a.plot(T, model, **ff.curve(k, color=r[k]))
        a.plot(T, measured, **ff.points(k, color=r[k]), label=f"$x_1$ = {x:.1f}")
        b.plot(T, 100 * (measured / model - 1), **ff.points(k, color=r[k]))
    a.set(xlabel=ff.label("T", "K"), ylabel=ff.label(r"\eta", "mPa s"))
    b.set(xlabel=ff.label("T", "K"), ylabel=ff.label(r"\Delta\eta/\eta", "%"), ylim=(-2, 2))
    ff.legend(a)


for journal in ff.JOURNALS:                        # "acs", "elsevier", "nature"
    # Nature asks for a sans-serif face: ff.use("nature", font="Arial")
    state = ff.use(journal)
    fig, (a, b) = ff.subplots(1, 2)                # two panels: double column
    draw(a, b)
    ff.panel_labels([a, b])                        # a, b  (Elsevier: (a), (b))
    ff.save(fig, os.path.join(HERE, "output", f"journal_{journal}"))
    w, h = fig.get_size_inches() * 25.4
    print(f"{journal:9} {w:5.1f} x {h:4.1f} mm, text {state['fontsize']:g} pt, "
          f"panels {state['panel']}")
