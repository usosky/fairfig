# Figures, marks and text

## Journal presets

`ff.use(journal)` sets the column widths and the text size:

| `ff.use(...)` | single column | 1.5 column | double column | max. height | text |
|---|---|---|---|---|---|
| `"acs"` | 84.6 mm | 127 mm | 177.8 mm | 232.8 mm | 8 pt |
| `"elsevier"` | 90 mm | 140 mm | 190 mm | – | 8 pt |
| `"nature"` | 89 mm | 120 mm | 183 mm | 170 mm | 7 pt |

All text is set in the bundled Liberation Mono, a monospace face with Courier's letter
widths; Elsevier lists Courier among its standard fonts. Nature asks for a sans-serif
face: `ff.use("nature", font="Arial")` (if the font is not installed, Liberation Mono
is used). The other options of `ff.use`:

| Option | Values |
|---|---|
| `palette` | `"fairfig"` (default), `"okabe-ito"` |
| `frame` | `"box"`: closed frame (default); `"open"`: left and bottom spines only |
| `ticks` | `"out"`: outward, left and bottom (default); `"in"`: inward, all four sides |
| `grid` | `True`: faint major and minor grid (default); `False`: none |
| `units` | `"slash"`: *T* / K (IUPAC, default); `"paren"`: *T* (K) |
| `panel` | `"a"` or `"(a)"`; default `"(a)"` for Elsevier, otherwise `"a"` |
| `fontsize` | text size in pt instead of the preset's |
| `subscript` | size of sub- and superscripts (default 0.75; matplotlib uses 0.7) |

## Figures at the final size

```python
fig, ax = ff.figure("single")                    # 84.6 mm wide (ACS), height 0.8 x width
fig, ax = ff.figure("double", aspect=0.5)        # height = 0.5 x width
fig, ax = ff.figure(width=70, height=55)         # any size, in mm
fig, axs = ff.subplots(1, 2)                     # two panels: double column by default
fig, axs = ff.subplots(2, 2, width="onehalf", aspect=1, sharex=True)
```

`aspect` is height/width of each panel; heights from `aspect` are capped at the
journal's maximum height. `ff.width("double")` gives a width in inches for your own
`plt.figure` calls. The layout engine is matplotlib's constrained layout.

## Experiment and model

Experiments are markers, models are lines in the same colour:

```python
ax.plot(x, T, **ff.points(0), label="$x_1$")                 # filled: liquid, phase I
ax.plot(y, T, **ff.points(0, hollow=True), label="$y_1$")    # open: vapour, phase II
ax.plot(x_lit, T_lit, **ff.points(1, lit=True), label="Lit.")  # grey open markers, underneath
ax.plot(xm, Tm, **ff.curve(0), label="NRTL")                 # model line, colour of slot 0
ax.plot(xm, Tm2, **ff.curve(None, style=1), label="UNIQUAC") # black, dashed
ax.errorbar(x, y, yerr=u, **ff.points(2), **ff.ERRORBAR)     # thin error bars
```

- `ff.points(i)` takes `color=` (e.g. from `ff.ramp`; the shape still follows *i*),
  `marker=`, `size=` and any keyword of `ax.plot`. Marker sizes are scaled per shape so
  that a square and a triangle look as heavy as a circle.
- `ff.curve(i, style=s)`: style 0 solid, 1 dashed, 2 dash-dot, 3 dotted. With one model
  use the series colour; with several, black and different styles.

## Guides and bands

```python
ff.diagonal(ax)                                  # y = x (x-y diagrams, parity plots)
ff.hline(ax, 0)                                  # zero line (deviation plots)
ff.vline(ax, x_az)
ff.band(ax, x, -u, u)                            # grey band: uncertainty
ff.band(ax, T, x_I, x_II, i=0, along="y")        # two-phase region between two x limits
```

Guides are light grey and drawn under the data. Bands are transparent (`amount`,
default 0.18), so the grid shows through; on white a band looks like
`ff.tint(colour, amount)`.

## Axes

```python
ff.fraction_axis(ax, "x")                        # 0-1, ticks every 0.2, minor 0.1
ff.grid(ax, False)                               # no grid, e.g. on colour maps
ff.ticks_out(ax)                                 # outward ticks on maps, with ticks="in"
```

## Labels and units

`ff.label(symbol, unit)` writes the quantity in italic and the unit upright, joined by
a slash (IUPAC) or in parentheses with `units="paren"`:

| Call | Gives |
|---|---|
| `ff.label("T", "K")` | *T* / K |
| `ff.label("p", "kPa")` | *p* / kPa |
| `ff.label("x_1, y_1")` | *x*₁, *y*₁ |
| `ff.label(r"\rho", "kg m^-3")` | *ρ* / (kg·m⁻³) |
| `ff.label(r"\eta", "mPa s")` | *η* / (mPa·s) |
| `ff.label("Temperature", "K")` | Temperature / K (words stay upright) |

The symbol is mathtext without dollar signs. Unit factors are separated by spaces and
joined by a middle dot; powers are written with `^`.

## Legends and direct labels

```python
ff.legend(ax)                                    # frameless key above the plot
ff.legend(ax, [h[k] for k in order], [l[k] for k in order])   # your order
ff.legend(ax, loc="right")                       # outside, on the right
ff.legend(ax, loc="upper left")                  # inside
ff.end_label(ax, T[-1], rho[-1], "0.25")         # label at the end of a line
```

Above the plot, the key has as many entries per row as fit the panel width, and reads
left to right, then top to bottom: ordered series stay in order.

## Panel labels and colour bars

```python
ff.panel_labels([a, b])          # bold a, b above the frame, aligned with the y label
ff.panel_labels(fig)             # every panel of a figure (colour bars are skipped)
ff.panel_labels(axs, loc="inside")
ff.colorbar(mappable, ax, label=ff.label(r"G^\mathrm{E}/RT"))   # slim colour bar
```

The [cookbook](../cookbook.md) uses all of these, and the full style guide is the
[identity sheet](../identity_sheet.pdf) (two A4 pages).
