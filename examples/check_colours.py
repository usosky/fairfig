# %% Check colours before you submit -> output/check_colours.svg/.pdf + _cvd.png
# 1. the palette's numbers; 2. a figure as colour-blind readers see it;
# 3. a palette that fails, for comparison. Data are SYNTHETIC.
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
sys.path.insert(0, os.path.dirname(HERE))
import fairfig as ff

ff.use("acs")

# %% 1. Contrast on white and the distance between every pair of colours, in normal
# vision and with simulated deuteranopia, protanopia and tritanopia (OKLab dE x 100)
ff.check_palette()

# %% 2. A figure with three systems, and the same figure as colour-blind readers see it
x = np.linspace(0, 1, 101)
xe = np.linspace(0.05, 0.95, 8)
fig, ax = ff.figure("single")
ff.diagonal(ax)
for name, i in ff.slots(["A + B", "A + C", "A + D"]).items():
    alpha = [2.4, 1.6, 0.8][i]                       # relative volatility
    ax.plot(x, alpha * x / (1 + (alpha - 1) * x), **ff.curve(i))
    ax.plot(xe, alpha * xe / (1 + (alpha - 1) * xe), **ff.points(i), label=name)
ff.fraction_axis(ax, "x")
ff.fraction_axis(ax, "y")
ax.set(xlabel=ff.label("x_1"), ylabel=ff.label("y_1"))
ff.legend(ax)
print(ff.save(fig, os.path.join(HERE, "output", "check_colours")))          # .svg + .pdf
prev = ff.cvd_preview(fig, dpi=120)               # in a notebook this alone shows the check
prev.savefig(os.path.join(HERE, "output", "check_colours_cvd.png"), dpi=120)
# ff.save(fig, path, cvd=True) writes the same check next to the figure.

# %% 3. For comparison: red and green from matplotlib's default colours are flagged
# as too close with deuteranopia, the most common colour-vision deficiency
ff.check_palette(["#d62728", "#2ca02c"])
