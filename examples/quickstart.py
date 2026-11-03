# %% Quick start: one figure in the fairfig identity -> output/quickstart.svg + .pdf
# Isothermal p-x-y diagram of an ideal binary mixture (Raoult's law). The
# "measured" points are SYNTHETIC: replace them with your own arrays.
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
sys.path.insert(0, os.path.dirname(HERE))          # run from a checkout without installing
# --8<-- [start:docs]
import numpy as np

import fairfig as ff

ff.use("acs")                                      # or "elsevier", "nature"

p1, p2 = 101.3, 42.0                               # vapour pressures of 1 and 2 / kPa
x = np.linspace(0, 1, 101)
p = x * p1 + (1 - x) * p2                          # bubble line
y = x * p1 / p                                     # vapour in equilibrium (dew line)

rng = np.random.default_rng(1)
xe = np.array([0.08, 0.21, 0.35, 0.50, 0.64, 0.78, 0.91])
pe = xe * p1 + (1 - xe) * p2 + rng.normal(0, 0.5, xe.size)
ye = xe * p1 / pe + rng.normal(0, 0.004, xe.size)

fig, ax = ff.figure("single")                      # exact column width: 84.6 mm
ax.plot(x, p, **ff.curve(0), label="Raoult's law")  # model: line
ax.plot(y, p, **ff.curve(0))
ax.plot(xe, pe, **ff.points(0), label="$x_1$")      # liquid: filled markers
ax.plot(ye, pe, **ff.points(0, hollow=True), label="$y_1$")   # vapour: open markers
ff.fraction_axis(ax, "x")
ax.set(xlabel=ff.label("x_1, y_1"), ylabel=ff.label("p", "kPa"))
ff.legend(ax)                                      # key above the plot
print(ff.save(fig, os.path.join(HERE, "output", "quickstart")))   # .svg + .pdf
# --8<-- [end:docs]
