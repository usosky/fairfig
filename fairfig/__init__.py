"""
fairfig - a colour-blind-safe visual identity for scientific figures (matplotlib)
==============================================================================

    import fairfig as ff
    ff.use("acs")                                   # or "elsevier", "nature"
    # ff.use("acs", palette="B")                    # palettes "A" (default), "B", "C"
    fig, ax = ff.figure("single")                   # exact column width
    ax.plot(x_exp, T_exp, **ff.points(0))           # experiment: filled marker
    ax.plot(y_exp, T_exp, **ff.points(0, hollow=True))  # 2nd phase: open marker
    ax.plot(x_mod, T_mod, **ff.curve(0))            # model: line, same colour
    ax.set(xlabel=ff.label("x_1, y_1"), ylabel=ff.label("T", "K"))
    ff.legend(ax)                                   # frameless key above the plot
    ff.save(fig, "figures/fig1_Txy")                # fig1_Txy.svg + fig1_Txy.pdf

Identity (v1.2)
  colour      Okabe-Ito hues, fixed order: blue, vermillion, bluish green, orange,
              sky blue, reddish purple (Okabe & Ito 2008; Wong 2011, Nat.
              Methods 8, 441). Order chosen by computing CVD separation; blue
              and vermillion darkened so slots 1-3 also differ in brightness.
              Other palettes: ff.use(palette="B") = fairfig 1.0 (published
              Okabe-Ito values), palette="C" = Okabe-Ito in its published order.
  ordered     batlow (sequential), vik (diverging) - Crameri, Nat. Commun.
              11, 5444 (2020). Never rainbow/jet.
  marks       experiment = markers, model = lines, filled/open = phase or
              branch, grey open markers = literature data.
  type        Liberation Mono (bundled, SIL OFL), one size per figure, bold
              panel labels.
  layout      closed box, outward ticks, faint major + minor grid, legend on top.
  export      SVG (live text) + PDF (embedded TrueType); png/tif on request.

Numbers given for widths/heights are millimetres.
"""
from __future__ import annotations

import io
import itertools
import os
import re
from types import SimpleNamespace

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.colors import ListedColormap, to_hex, to_rgb

from ._cmapdata import BATLOW, VIK

__version__ = "1.2.0"
__all__ = [
    "use", "C", "COLORS", "INK", "NAMES", "PALETTES", "MARKERS", "LINESTYLES", "JOURNALS",
    "figure", "subplots", "width", "points", "curve", "ramp", "cmap", "ink",
    "tint", "slots", "label", "legend", "panel_labels", "diagonal", "hline",
    "vline", "band", "fraction_axis", "grid", "ticks_out", "end_label", "colorbar",
    "save", "simulate", "ERRORBAR",
    "cvd_preview", "check_palette", "swatches", "STYLE",
]

STYLE = os.path.join(os.path.dirname(__file__), "fairfig.mplstyle")
MM = 1 / 25.4  # inches per millimetre

# =============================================================================
# 1. Colour
# =============================================================================
#: Categorical palettes, chosen with ff.use(palette=...): colours in slot order.
#: All three use the same six Okabe-Ito hues, so ff.C.<hue> always exists.
PALETTES = {
    # A (default) - fairfig. Blue and vermillion are darker than the published
    # Okabe-Ito values: a colour-blind reader found vermillion and bluish green
    # hard to tell apart at equal brightness (1.13:1). Slots 1-3 now sit at three
    # brightness levels (pairwise 1.3-2.1:1), so they separate wherever hue is
    # lost: CVD, small markers, greyscale print. The reader confirmed it.
    "A": dict(name="fairfig",
              colors=["#005B90", "#BB4000", "#009E73", "#E69F00", "#56B4E9", "#CC79A7"],
              names=["blue", "vermillion", "green", "orange", "sky", "purple"]),
    # B - fairfig 1.0: published Okabe-Ito values in fairfig's CVD-optimised order.
    "B": dict(name="fairfig-1.0",
              colors=["#0072B2", "#D55E00", "#009E73", "#E69F00", "#56B4E9", "#CC79A7"],
              names=["blue", "vermillion", "green", "orange", "sky", "purple"]),
    # C - Okabe-Ito in its published order (Wong 2011), the most widely
    # recommended colour-blind-safe palette. Its black stays reserved for text and
    # models, its yellow for areas (1.3:1 on white: too faint for lines).
    "C": dict(name="okabe-ito",
              colors=["#E69F00", "#56B4E9", "#009E73", "#0072B2", "#D55E00", "#CC79A7"],
              names=["orange", "sky", "green", "blue", "vermillion", "purple"]),
}

#: Named colours: the six hues of the active palette (ff.C.vermillion, ...) plus
#: reserved colours, which never change.
C = SimpleNamespace(
    # categorical: set from the active palette (default A)
    **dict(zip(PALETTES["A"]["names"], PALETTES["A"]["colors"])),
    # reserved
    yellow="#F0E442",     # large areas/highlight fills only - never lines or markers
    black="#000000",      # text, axes, single reference model
    grey_dk="#404040",    # secondary model / annotations
    grey="#808080",       # literature & context data (3.9:1 on white)
    grey_lt="#B3B3B3",    # guides: y = x, zero line
    grey_xlt="#E6E6E6",   # bands, shaded regions
    grid="#E6E6E6",       # major grid, 0.5 pt
    grid_minor="#F2F2F2", # minor grid, 0.5 pt
    white="#FFFFFF",
)
#: Active palette, slot order (changed in place by ff.use(palette=...)).
NAMES = list(PALETTES["A"]["names"])
COLORS = list(PALETTES["A"]["colors"])

MARKERS = ["o", "s", "^", "D", "v", "p"]
# size factors so every shape has roughly the same visual weight as the circle
_MSCALE = {"o": 1.0, "s": 0.89, "^": 1.2, "v": 1.2, "<": 1.2, ">": 1.2,
           "D": 0.85, "d": 1.0, "p": 1.12, "h": 1.08, "H": 1.08, "*": 1.35,
           "X": 1.0, "P": 1.0, "x": 1.0, "+": 1.1}
LINESTYLES = ["-", "--", "-.", ":"]

# Journal presets: widths in mm; font in pt; max_height in mm (None = unknown)
JOURNALS = {
    # ACS (J. Chem. Eng. Data, I&EC Res.): single <= 240 pt, double 300-504 pt,
    # max depth 660 pt incl. caption, lettering >= 4.5 pt, lines >= 0.5 pt.
    "acs": dict(single=84.6, onehalf=127.0, double=177.8, max_height=232.8, font=8.0),
    # Elsevier (Fluid Phase Equilib., J. Chem. Thermodyn.): 90/140/190 mm,
    # 7 pt normal text, >= 6 pt sub/superscripts.
    "elsevier": dict(single=90.0, onehalf=140.0, double=190.0, max_height=None, font=8.0),
    # Nature research figure guide: 89/183 mm, max height 170 mm, text 5-7 pt.
    "nature": dict(single=89.0, onehalf=120.0, double=183.0, max_height=170.0, font=7.0),
}

# Liberation Mono is bundled in fairfig/fonts and registered on import, so it works
# on any machine. Courier New comes next: same letter widths, so an SVG opened
# where Liberation Mono is not installed keeps its layout.
_FONTS = ["Liberation Mono", "Courier New", "Courier", "Nimbus Mono PS",
          "FreeMono", "DejaVu Sans Mono"]
_FONT_DIR = os.path.join(os.path.dirname(__file__), "fonts")

_STATE = dict(journal="acs", units="slash", frame="box", ticks="out", grid=True,
              panel="a", fontsize=8.0, font="Liberation Mono", palette="A")


# ---------------------------------------------------------------- colour maths
def _lin(c):
    c = np.asarray(c, float)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def _srgb(c):
    c = np.clip(np.asarray(c, float), 0, 1)
    return np.where(c <= 0.0031308, 12.92 * c, 1.055 * c ** (1 / 2.4) - 0.055)


_M1 = np.array([[0.4122214708, 0.5363325363, 0.0514459929],
                [0.2119034982, 0.6806995451, 0.1073969566],
                [0.0883024619, 0.2817188376, 0.6299787005]])
_M2 = np.array([[0.2104542553, 0.7936177850, -0.0040720468],
                [1.9779984951, -2.4285922050, 0.4505937099],
                [0.0259040371, 0.7827717662, -0.8086757660]])


def _oklab(rgb_lin):
    return np.cbrt(np.asarray(rgb_lin) @ _M1.T) @ _M2.T


def _oklab_to_lin(lab):
    lms = (np.asarray(lab) @ np.linalg.inv(_M2).T) ** 3
    return lms @ np.linalg.inv(_M1).T


def _luminance(color):
    return float(_lin(to_rgb(color)) @ np.array([0.2126, 0.7152, 0.0722]))


def _contrast(a, b="#FFFFFF"):
    ya, yb = sorted((_luminance(a), _luminance(b)))
    return (yb + 0.05) / (ya + 0.05)


def ink(color, amount=0.14):
    """Darker tone of the same hue (OKLab lightness - amount); used for marker
    edges so light hues keep >= 3:1 contrast against white."""
    lab = _oklab(_lin(to_rgb(color)))
    lab[0] -= amount
    for f in np.linspace(1.0, 0.3, 36):          # pull chroma in until in gamut
        trial = lab.copy()
        trial[1:] *= f
        rgb = _oklab_to_lin(trial)
        if rgb.min() >= -1e-6 and rgb.max() <= 1 + 1e-6:
            break
    return to_hex(_srgb(np.clip(rgb, 0, 1)))


def tint(color, amount=0.18):
    """Light tint (mix with white) for bands and shaded regions."""
    c = np.asarray(to_rgb(color))
    return to_hex(amount * c + (1 - amount) * np.ones(3))


#: Marker-edge tones matching COLORS (same order).
INK = [ink(c) for c in COLORS]


def _palette_key(palette):
    """'A' / 'B' / 'C' (any case) or the long names 'fairfig', 'fairfig-1.0',
    'okabe-ito' -> key of PALETTES."""
    p = str(palette).strip().lower().replace("_", "-").replace(" ", "-")
    for key, d in PALETTES.items():
        if p in (key.lower(), d["name"]):
            return key
    opts = ", ".join(f"'{k}' ({d['name']})" for k, d in PALETTES.items())
    raise ValueError(f"palette must be one of {opts}; got {palette!r}")


def _set_palette(palette):
    """Make a palette active: slot colours, marker edges, ff.C.<hue> and the
    matplotlib colour cycle. Lists are changed in place, so names imported
    with 'from fairfig import COLORS' follow too."""
    key = _palette_key(palette)
    d = PALETTES[key]
    COLORS[:] = d["colors"]
    NAMES[:] = d["names"]
    INK[:] = [ink(c) for c in COLORS]
    for n, c in zip(NAMES, COLORS):
        setattr(C, n, c)
    mpl.rcParams["axes.prop_cycle"] = mpl.cycler(color=list(COLORS))
    _STATE["palette"] = key
    return key


def slots(names):
    """Fix colour/marker slots to entities, e.g. systems or components:
    S = ff.slots(["A+B", "A+C"]);  ax.plot(..., **ff.points(S["A+C"])).
    Keep one mapping per paper so every entity keeps its colour."""
    names = list(names)
    if len(names) > len(COLORS):
        raise ValueError(f"{len(names)} entities > {len(COLORS)} identity colours: "
                         "facet the figure, or use ff.ramp() if the series are ordered.")
    return {n: i for i, n in enumerate(names)}


# ---------------------------------------------------------------- colormaps
def _register_cmaps():
    for name, data in (("batlow", BATLOW), ("vik", VIK)):
        cm = ListedColormap(["#" + h for h in data], name=name)
        for nm, c in ((name, cm), (name + "_r", cm.reversed())):
            if nm not in mpl.colormaps:
                mpl.colormaps.register(c, name=nm)


_register_cmaps()


def _register_fonts():
    """Make the bundled Liberation Mono available to matplotlib (this session
    only; nothing is installed on the system)."""
    if not os.path.isdir(_FONT_DIR):
        return
    for fn in sorted(os.listdir(_FONT_DIR)):
        if fn.lower().endswith((".ttf", ".otf")):
            try:
                font_manager.fontManager.addfont(os.path.join(_FONT_DIR, fn))
            except Exception:
                pass


_register_fonts()


def cmap(kind="seq"):
    """'seq' -> batlow (magnitudes), 'div' -> vik (signed deviations, centre 0),
    or any registered matplotlib name."""
    return mpl.colormaps[{"seq": "batlow", "div": "vik"}.get(kind, kind)]


def ramp(n, cmap="batlow", lo=0.0, hi=0.72, reverse=False):
    """n colours for an *ordered* series (isotherms, isobars, compositions),
    sampled from a perceptually uniform map. The light end is capped (hi) so
    thin lines stay visible on white. Low value -> dark blue."""
    cm = mpl.colormaps[cmap]
    cols = [to_hex(cm(t)) for t in np.linspace(lo, hi, n)]
    return cols[::-1] if reverse else cols


# =============================================================================
# 2. Style
# =============================================================================
def _first_font(candidates):
    have = {f.name for f in font_manager.fontManager.ttflist}
    for name in candidates:
        if name in have:
            return name
    return "DejaVu Sans Mono"


def _set_subscript_scale(scale):
    # Matplotlib shrinks sub/superscripts to 0.7x (private constant). 0.75 keeps
    # them >= 6 pt at 8 pt text (Elsevier) and >= 5 pt at 7 pt text (Nature).
    try:
        from matplotlib import _mathtext
        if hasattr(_mathtext, "SHRINK_FACTOR"):
            _mathtext.SHRINK_FACTOR = float(scale)
            from matplotlib.mathtext import MathTextParser
            MathTextParser._parse_cached.cache_clear()
    except Exception:  # never fail because of a cosmetic tweak
        pass


def use(journal="acs", *, palette="A", frame="box", ticks="out", grid=True,
        units="slash", panel=None, fontsize=None, font=None, subscript=0.75):
    """Apply the identity.

    journal   'acs' | 'elsevier' | 'nature'  - widths and text size
    palette   categorical colours (see ff.PALETTES):
              'A' fairfig (default) - three brightness levels in slots 1-3
              'B' fairfig 1.0 - published Okabe-Ito values, fairfig order
              'C' Okabe-Ito in its published order
              long names work too: 'fairfig', 'fairfig-1.0', 'okabe-ito'
    frame     'box'  closed frame (default)  |  'open' left/bottom spines only
    ticks     'out'  outward, left/bottom (default)  |  'in' inward, all four sides
    grid      True: faint major + minor grid (minor added by ff.figure/ff.subplots)
    units     'slash' -> T / K (IUPAC)      'paren' -> T (K)
    panel     'a' (bold a, b, c) or '(a)'; default: '(a)' for elsevier, else 'a'
    fontsize  override the preset text size (pt)
    font      override the typeface (default Liberation Mono), e.g. font="Arial"
              for a Nature submission
    subscript sub/superscript scale (matplotlib default 0.7)
    """
    if journal not in JOURNALS:
        raise ValueError(f"journal must be one of {list(JOURNALS)}")
    if frame not in ("box", "open"):
        raise ValueError("frame must be 'box' or 'open'")
    if ticks not in ("out", "in"):
        raise ValueError("ticks must be 'out' or 'in'")
    if units not in ("slash", "paren"):
        raise ValueError("units must be 'slash' or 'paren'")
    _palette_key(palette)                      # fail before touching any setting
    plt.style.use(STYLE)
    fs = float(fontsize or JOURNALS[journal]["font"])
    face = _first_font([font] + _FONTS if font else _FONTS)
    have = {f.name for f in font_manager.fontManager.ttflist}
    mono = face in _FONTS
    w = JOURNALS[journal]["single"] * MM
    rc = {
        "figure.figsize": (w, 0.8 * w),
        "font.size": fs, "axes.labelsize": fs, "axes.titlesize": fs,
        "xtick.labelsize": fs, "ytick.labelsize": fs, "legend.fontsize": fs,
        "legend.title_fontsize": fs, "figure.titlesize": fs, "figure.labelsize": fs,
        "font.family": [face, "monospace" if mono else "sans-serif"],
        "font.monospace": [face] + [f for f in _FONTS if f != face and f in have],
        "mathtext.rm": face, "mathtext.sf": face, "mathtext.cal": face,
        "mathtext.tt": face, "mathtext.it": f"{face}:italic",
        "mathtext.bf": f"{face}:bold",
        "image.cmap": "batlow",
        "axes.grid": bool(grid),
        "axes.spines.top": frame == "box", "axes.spines.right": frame == "box",
        "xtick.direction": ticks, "ytick.direction": ticks,
        "xtick.top": ticks == "in" and frame == "box",
        "ytick.right": ticks == "in" and frame == "box",
    }
    mpl.rcParams.update(rc)
    _set_palette(palette)
    if subscript:
        _set_subscript_scale(subscript)
    _STATE.update(journal=journal, units=units, frame=frame, ticks=ticks,
                  grid=bool(grid), fontsize=fs, font=face,
                  panel=panel or ("(a)" if journal == "elsevier" else "a"))
    return dict(_STATE)


# =============================================================================
# 3. Figures
# =============================================================================
def width(w="single", journal=None):
    """Column width in inches: 'single' | 'onehalf' | 'double' | number (mm)."""
    if isinstance(w, (int, float)):
        return w * MM
    return JOURNALS[journal or _STATE["journal"]][w] * MM


def _height(w_in, ncols, nrows, aspect, height):
    if height is not None:
        return height * MM
    h = w_in / ncols * aspect * nrows
    mh = JOURNALS[_STATE["journal"]]["max_height"]
    return min(h, mh * MM) if mh else h


def grid(ax, on=True, minor=True):
    """Faint background grid: major #E6E6E6 and minor #F2F2F2, both 0.5 pt,
    drawn under the data. ff.grid(ax, False) removes it (e.g. on colour maps)."""
    for a in np.atleast_1d(ax).ravel():
        if not on:
            a.grid(False, which="both")
            continue
        a.grid(True, which="major", color=C.grid, linewidth=0.5, linestyle="-")
        a.grid(minor, which="minor", color=C.grid_minor, linewidth=0.5, linestyle="-")
        a.set_axisbelow(True)


def figure(width="single", aspect=0.8, height=None, **kw):
    """One axes at the exact journal width. aspect = height/width;
    height (mm) overrides aspect. Returns (fig, ax)."""
    w = globals()["width"](width)
    fig, ax = plt.subplots(figsize=(w, _height(w, 1, 1, aspect, height)), **kw)
    if _STATE["grid"]:
        grid(ax)
    return fig, ax


def subplots(nrows=1, ncols=1, width=None, aspect=0.8, height=None, **kw):
    """Grid of panels. width defaults to 'double' when ncols > 1. aspect is the
    height/width of each panel. Returns (fig, axs)."""
    w = globals()["width"](width or ("double" if ncols > 1 else "single"))
    fig, axs = plt.subplots(nrows, ncols, figsize=(w, _height(w, ncols, nrows, aspect, height)), **kw)
    if _STATE["grid"]:
        grid(axs)
    return fig, axs


# =============================================================================
# 4. Marks  (never colour alone: slot i = colour i + marker i)
# =============================================================================
def _slot_color(i, color):
    if color is not None:
        return to_hex(color)
    if not 0 <= i < len(COLORS):
        raise IndexError(f"slot {i}: only {len(COLORS)} identity colours. Facet, or use "
                         "ff.ramp(n) for ordered series (points(i, color=r[i])).")
    return COLORS[i]


def points(i=0, *, color=None, hollow=False, lit=False, marker=None, size=None,
           **kw):
    """Keyword dict for experimental data with ax.plot / ax.errorbar.

    i       slot -> colour i and marker shape i
    hollow  open marker (vapour/dew branch, 2nd liquid phase, ...)
    lit     literature/context data: grey open marker, drawn under your data
    color   override colour (e.g. from ff.ramp) - marker shape still follows i
    """
    m = marker or MARKERS[i % len(MARKERS)]
    ms = (size or mpl.rcParams["lines.markersize"]) * _MSCALE.get(m, 1.0)
    mew = mpl.rcParams["lines.markeredgewidth"]
    if lit:
        c = to_hex(color) if color is not None else C.grey
        d = dict(color=c, marker=m, markersize=ms, markerfacecolor="white",
                 markeredgecolor=c, markeredgewidth=mew * 1.25, zorder=2.5)
    else:
        c = _slot_color(i, color)
        if hollow:
            d = dict(color=c, marker=m, markersize=ms, markerfacecolor="white",
                     markeredgecolor=ink(c, 0.07), markeredgewidth=mew * 1.4, zorder=3)
        else:
            d = dict(color=c, marker=m, markersize=ms, markerfacecolor=c,
                     markeredgecolor=ink(c), markeredgewidth=mew, zorder=3)
    d.update(linestyle="none")
    d.update(kw)
    return d


def curve(i=0, *, color=None, style=0, lw=None, **kw):
    """Keyword dict for a model/correlation line. style: 0 solid, 1 dashed,
    2 dash-dot, 3 dotted (use style to tell several models apart)."""
    c = C.black if (i is None and color is None) else _slot_color(i, color)
    d = dict(color=c, linestyle=LINESTYLES[style % len(LINESTYLES)],
             linewidth=lw or mpl.rcParams["lines.linewidth"], marker="none", zorder=2)
    d.update(kw)
    return d


#: extra keywords for ax.errorbar(x, y, yerr=u, **ff.points(i), **ff.ERRORBAR)
ERRORBAR = dict(elinewidth=0.5, capsize=1.5, capthick=0.5)


def diagonal(ax, **kw):
    """y = x guide (x-y diagrams, parity plots)."""
    d = dict(color=C.grey_lt, lw=0.6, zorder=1)
    d.update(kw)
    return ax.axline((0, 0), (1, 1), **d)


def hline(ax, y=0.0, **kw):
    d = dict(color=C.grey_lt, lw=0.6, zorder=1)
    d.update(kw)
    return ax.axhline(y, **d)


def vline(ax, x=0.0, **kw):
    d = dict(color=C.grey_lt, lw=0.6, zorder=1)
    d.update(kw)
    return ax.axvline(x, **d)


def band(ax, x, y1, y2, i=None, color=None, amount=0.18, **kw):
    """Shaded band (uncertainty, two-phase region): tint of slot i, or light grey."""
    c = tint(color if color is not None else COLORS[i], amount) if (i is not None or color is not None) else C.grey_xlt
    d = dict(color=c, lw=0, zorder=0.8)
    d.update(kw)
    return ax.fill_between(x, y1, y2, **d)


def fraction_axis(ax, which="x", major=0.2, minor=0.1):
    """0-1 axis for mole/mass fractions with ticks every 0.2 (minor 0.1)."""
    axis = ax.xaxis if which == "x" else ax.yaxis
    (ax.set_xlim if which == "x" else ax.set_ylim)(0, 1)
    axis.set_major_locator(mpl.ticker.MultipleLocator(major))
    axis.set_minor_locator(mpl.ticker.MultipleLocator(minor))
    axis.set_major_formatter(mpl.ticker.FormatStrFormatter("%.1f"))


def ticks_out(ax):
    """Outward ticks, no top/right ticks (already the default with ticks='out').
    With ticks='in', use it on image/contour maps where inward ticks would be
    hidden by the colours."""
    ax.tick_params(which="both", direction="out", top=False, right=False)


def end_label(ax, x, y, text, dx=3, **kw):
    """Direct label at the end of a line (black text) - an alternative to a
    legend when lines are well separated."""
    d = dict(xytext=(dx, 0), textcoords="offset points", va="center", ha="left",
             fontsize=_STATE["fontsize"])
    d.update(kw)
    return ax.annotate(text, xy=(x, y), **d)


def colorbar(mappable, ax=None, label=None, **kw):
    """Slim colour bar matching the frame style."""
    ax = ax if ax is not None else mappable.axes
    d = dict(fraction=0.05, pad=0.02, aspect=25)
    d.update(kw)
    cb = ax.figure.colorbar(mappable, ax=ax, **d)
    cb.outline.set_linewidth(mpl.rcParams["axes.linewidth"])
    cb.ax.tick_params(which="both", direction="out")
    cb.ax.minorticks_off()
    cb.ax.grid(False, which="both")
    if label:
        cb.set_label(label)
    return cb


# =============================================================================
# 5. Text
# =============================================================================
def _unit_tex(unit):
    """'kg m^-3' -> mathtext with upright units joined by a middle dot."""
    parts = re.split(r"[\s·*]+", unit.strip())
    out = []
    for p in parts:
        m = re.fullmatch(r"(.+?)\^\{?([-+−]?[\d.]+)\}?", p)
        if m:
            base, exp = m.group(1), m.group(2).replace("−", "-")
            out.append(r"\mathrm{%s}^{%s}" % (base, exp))
        else:
            out.append(r"\mathrm{%s}" % p)
    return "$" + "\u00b7".join(out) + "$"        # kg\u00b7m^-3: unambiguous in monospace


def label(symbol, unit=None, *, style=None):
    """Axis label: quantity symbol in italic, unit upright.

    label('T', 'K')              -> T / K      (IUPAC; style='paren' -> T (K))
    label(r'\\rho', 'kg m^-3')    -> rho / (kg m^-3)
    label('x_1')                  -> x_1
    label('Temperature', 'K')     -> plain words stay upright
    """
    style = style or _STATE["units"]
    s = symbol.strip()
    if s.startswith("$") or (" " in s and not re.search(r"[\\_^]", s)) or (
            s.isalpha() and len(s) > 3):
        q = s                                            # already math, or words
    else:
        q = "$" + s + "$"
    if not unit:
        return q
    simple = re.fullmatch(r"[A-Za-z%°µμΩ]+", unit.strip()) is not None
    u = unit.strip() if simple else _unit_tex(unit)
    if style == "paren":
        return f"{q} ({u})"
    if q.startswith("$") and q.endswith("$") and q.count("$") == 2:
        # one math string: thin spaces around the slash (full spaces look loose
        # in a monospaced face)
        um = (r"\mathrm{%s}" % unit.strip().replace("%", r"\%")) if simple else "(" + u[1:-1] + ")"
        return "$" + q[1:-1] + r"\,/\," + um + "$"
    return f"{q} / {u}" if simple else f"{q} / ({u})"


def _text_width_pt(s, size):
    from matplotlib.font_manager import FontProperties
    from matplotlib.textpath import TextToPath
    try:
        return TextToPath().get_text_width_height_descent(
            s, FontProperties(size=size), ismath=s.count("$") >= 2)[0]
    except Exception:
        return 0.6 * size * len(s)


def _axes_width_pt(ax):
    """Width of the axes box in points, after the layout engine has run."""
    import warnings
    fig = ax.figure
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            eng = fig.get_layout_engine()
            if eng is not None:
                eng.execute(fig)
            ax.apply_aspect()
        except Exception:
            pass
    return ax.get_position().width * fig.get_figwidth() * 72


def _fit_ncol(ax, labels, d):
    """Largest number of columns whose row fits inside the axes width."""
    fs = mpl.rcParams["legend.fontsize"]
    fs = fs if isinstance(fs, (int, float)) else _STATE["fontsize"]
    hl = d.get("handlelength", mpl.rcParams["legend.handlelength"])
    tp = d.get("handletextpad", mpl.rcParams["legend.handletextpad"])
    cs = d.get("columnspacing", mpl.rcParams["legend.columnspacing"])
    w = [(hl + tp) * fs + _text_width_pt(t, fs) for t in labels]
    avail = 0.97 * _axes_width_pt(ax)
    n = len(w)
    for ncol in range(n, 1, -1):
        rows = int(np.ceil(n / ncol))
        cols = [[w[r * ncol + c] for r in range(rows) if r * ncol + c < n] for c in range(ncol)]
        if sum(max(c) for c in cols if c) + (ncol - 1) * cs * fs <= avail:
            return ncol
    return 1


def legend(ax, *args, loc="top", ncol=None, **kw):
    """Frameless legend. Default: key above the plot, as many entries per row
    as fit the panel width, read left-to-right then top-to-bottom.
    loc='right' puts it outside on the right; any matplotlib loc
    ('upper right', 'best', ...) puts it inside the axes."""
    if loc == "top":
        d = dict(loc="lower center", bbox_to_anchor=(0.5, 1.0), borderaxespad=0.3,
                 columnspacing=1.0, handletextpad=0.4)
        d.update(kw)
        if len(args) >= 2:
            handles, labels = list(args[0]), list(args[1])
        else:
            handles, labels = ax.get_legend_handles_labels()
        n = len(labels)
        if n == 0:
            return None
        ncol = ncol or _fit_ncol(ax, labels, d)
        rows = int(np.ceil(n / ncol))
        # matplotlib fills legends column by column; reorder so the key reads
        # row by row in the order given (matters for ordered series).
        idx = [r * ncol + c for c in range(ncol) for r in range(rows) if r * ncol + c < n]
        return ax.legend([handles[i] for i in idx], [labels[i] for i in idx], ncol=ncol, **d)
    if loc == "right":
        d = dict(loc="center left", bbox_to_anchor=(1.0, 0.5), ncol=ncol or 1)
    else:
        d = dict(loc=loc, ncol=ncol or 1)
    d.update(kw)
    return ax.legend(*args, **d)


def panel_labels(axes, labels=None, *, style=None, loc="margin", **kw):
    """Bold panel labels a, b, c ... at the top-left of each panel.

    loc 'margin' (default): just above the frame, left-aligned with the y-axis
         label (Nature style; never collides with tick labels).
         'inside': inside the frame, top-left corner.
    style 'a' or '(a)' (default from ff.use).
    Pass a Figure to label all its panels (colour bars are skipped).
    """
    if isinstance(axes, mpl.figure.Figure):
        axes = [a for a in axes.axes if a.get_label() != "<colorbar>"]
    axes = list(np.atleast_1d(axes).ravel())
    style = style or _STATE["panel"]
    labels = labels or [chr(ord("a") + k) for k in range(len(axes))]
    fmt = "({})" if style == "(a)" else "{}"
    fs = _STATE["fontsize"] + 1
    out = []
    for ax, lab in zip(axes, labels):
        d = dict(fontsize=fs, fontweight="bold", textcoords="offset points")
        d.update(kw)
        txt = fmt.format(lab)
        if loc == "inside":
            t = ax.annotate(txt, xy=(0, 1), xycoords="axes fraction", xytext=(4, -4),
                            ha="left", va="top", **d)
        elif ax.yaxis.label.get_text() and ax.yaxis.label.get_visible():
            t = ax.annotate(txt, xy=(0, 1), xycoords=(ax.yaxis.label, "axes fraction"),
                            xytext=(0, 3.5), ha="left", va="bottom", **d)
        else:
            t = ax.annotate(txt, xy=(0, 1), xycoords="axes fraction", xytext=(-3, 3.5),
                            ha="right", va="bottom", **d)
        out.append(t)
    return out


# =============================================================================
# 6. Export
# =============================================================================
def _svg_font_fallback(path):
    """Give every SVG font declaration a fallback chain, so an editor without
    the main face uses one with the same letter widths (Courier New for
    Liberation Mono) instead of its default serif font."""
    face = _STATE["font"]
    chain = ["Courier New", "monospace"] if face in _FONTS else ["Arial", "sans-serif"]
    tail = ", ".join(x if x in ("monospace", "sans-serif") else f"'{x}'"
                     for x in chain if x != face)
    with open(path, encoding="utf-8") as fh:
        s = fh.read()
    s = re.sub(r"font-family: '%s'[^;\"]*" % re.escape(face),
               f"font-family: '{face}', {tail}", s)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(s)


def save(fig, path, formats=("svg", "pdf"), dpi=None, cvd=False, **kw):
    """Save at the designed size. 'fig1' -> fig1.svg (editable text) + fig1.pdf
    (fonts embedded; the file to submit to ACS/Elsevier).
    formats=("pdf",) etc. to change; a path ending in .svg/.pdf/.eps/.png/.tif
    saves that format only (TIFF is written RGB + LZW, raster at 600 dpi).
    cvd=True also writes fig1_cvd.<first format> with the colour-blind check."""
    root, ext = os.path.splitext(os.fspath(path))
    fmts = [ext[1:].lower()] if ext else [f.lower().lstrip(".") for f in formats]
    folder = os.path.dirname(root)
    if folder:
        os.makedirs(folder, exist_ok=True)
    dpi = dpi or mpl.rcParams["savefig.dpi"]
    meta = {"pdf": {"Creator": f"fairfig {__version__} / matplotlib {mpl.__version__}"},
            "svg": {"Creator": f"fairfig {__version__}"},
            "png": {"Software": f"fairfig {__version__}"}}
    written = []
    for f in fmts:
        out = f"{root}.{f}"
        if f in ("tif", "tiff"):
            from PIL import Image
            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=dpi, **kw)
            Image.open(buf).convert("RGB").save(out, dpi=(dpi, dpi), compression="tiff_lzw")
        else:
            fig.savefig(out, format=f, dpi=dpi, metadata=meta.get(f), **kw)
            if f == "svg":
                _svg_font_fallback(out)
        written.append(out)
    if cvd:
        f0 = "png" if fmts[0] in ("tif", "tiff") else fmts[0]
        prev = cvd_preview(fig)
        prev.savefig(f"{root}_cvd.{f0}", dpi=150)
        plt.close(prev)
        written.append(f"{root}_cvd.{f0}")
    return written


# =============================================================================
# 7. Checks: colour-vision deficiency and greyscale
# =============================================================================
# Machado, Oliveira & Fernandes (2009), severity 1.0, applied in linear RGB.
_MACHADO = {
    "protan": np.array([[0.152286, 1.052583, -0.204868],
                        [0.114503, 0.786281, 0.099216],
                        [-0.003882, -0.048116, 1.051998]]),
    "deutan": np.array([[0.367322, 0.860646, -0.227968],
                        [0.280085, 0.672501, 0.047413],
                        [-0.011820, 0.042940, 0.968881]]),
    "tritan": np.array([[1.255528, -0.076749, -0.178779],
                        [-0.078411, 0.930809, 0.147602],
                        [0.004733, 0.691367, 0.303900]]),
}
_KIND_TITLE = {"normal": "Normal vision", "deutan": "Deuteranopia",
               "protan": "Protanopia", "tritan": "Tritanopia",
               "gray": "Greyscale (luminance)"}


def simulate(rgb, kind):
    """Simulate CVD ('deutan', 'protan', 'tritan') or 'gray' on an sRGB array
    (..., 3) in 0-1 or on a single colour (returns hex)."""
    single = isinstance(rgb, str) or np.ndim(rgb) == 1
    a = np.atleast_2d(to_rgb(rgb) if isinstance(rgb, str) else np.asarray(rgb, float)[..., :3])
    lin = _lin(a)
    if kind == "normal":
        out = a
    elif kind in ("gray", "grey"):
        y = _srgb(lin @ np.array([0.2126, 0.7152, 0.0722]))
        out = np.repeat(y[..., None], 3, axis=-1)
    else:
        out = _srgb(np.clip(lin @ _MACHADO[kind].T, 0, 1))
    return to_hex(out.reshape(-1, 3)[0]) if single else out.reshape(np.shape(rgb)[:-1] + (3,))


def cvd_preview(fig, kinds=("normal", "deutan", "protan", "tritan", "gray"), dpi=200):
    """Render fig and show it as seen with deuteranopia, protanopia, tritanopia
    and in greyscale. Returns the preview figure."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi)
    buf.seek(0)
    img = plt.imread(buf)[..., :3]
    h, w = img.shape[:2]
    ncols = min(3, len(kinds))
    nrows = int(np.ceil(len(kinds) / ncols))
    title_h = 0.22
    prev = plt.figure(figsize=(ncols * w / dpi, nrows * (h / dpi + title_h)), layout="none")
    for k, kind in enumerate(kinds):
        r, c = divmod(k, ncols)
        ax = prev.add_axes([c / ncols, 1 - (r + 1) / nrows, 1 / ncols,
                            (h / dpi) / (nrows * (h / dpi + title_h))])
        ax.imshow(simulate(img, kind), interpolation="lanczos")
        ax.set_axis_off()
        ax.set_title(_KIND_TITLE.get(kind, kind), fontsize=8, fontweight="bold", pad=3)
    return prev


def _dE(a, b, kind="normal"):
    sa = np.asarray(to_rgb(simulate(a, kind) if kind != "normal" else a))
    sb = np.asarray(to_rgb(simulate(b, kind) if kind != "normal" else b))
    return 100 * float(np.linalg.norm(_oklab(_lin(sa)) - _oklab(_lin(sb))))


def check_palette(colors=None, background="#FFFFFF", show=True):
    """Contrast vs background and, for every pair, OKLab dE (x100) under normal
    vision and simulated CVD (Machado 2009) plus the brightness ratio ('bright',
    the WCAG luminance ratio that online contrast checkers report).
    Rules of thumb: contrast >= 3 for lines; dE >= 8 under CVD (6-8 only with
    distinct marker shapes); dE >= 15 normal; pairs that are close under CVD
    (dE < 15) also need bright >= 1.25, better 1.5, because colour-blind readers
    and small markers lose hue first and brightness last. (3:1 between data
    colours is out of reach for any 3 colours that also stand out on white.)
    colors: list of colours, a palette name ('A', 'B', 'C'), or None = active."""
    if isinstance(colors, str):
        colors = PALETTES[_palette_key(colors)]["colors"]
    colors = list(colors or COLORS)
    rows, pairs = [], []
    for c in colors:
        rows.append((to_hex(c).upper(), _contrast(c, background),
                     float(_oklab(_lin(to_rgb(c)))[0])))
    for (i, a), (j, b) in itertools.combinations(enumerate(colors), 2):
        d = {k: _dE(a, b, k) for k in ("normal", "deutan", "protan", "tritan")}
        d["bright"] = _contrast(a, b)
        pairs.append((i, j, d))
    if show:
        print(f"{'slot':>4} {'colour':>8} {'contrast':>9} {'L(OKLab)':>9}")
        for k, (h, cr, L) in enumerate(rows):
            flag = "" if cr >= 3 else "  <3:1 -> dark edge + marker shape"
            print(f"{k:>4} {h:>8} {cr:>9.2f} {L:>9.3f}{flag}")
        print(f"\n{'pair':>6} {'normal':>7} {'deutan':>7} {'protan':>7} {'tritan':>7} {'bright':>7}")
        for i, j, d in pairs:
            worst = min(d["deutan"], d["protan"])
            flags = []
            if d["normal"] < 15:
                flags.append("similar in normal vision")
            if worst < 6:
                flags.append("TOO CLOSE under CVD")
            elif worst < 8:
                flags.append("needs distinct marker shapes")
            if worst < 15 and d["bright"] < 1.25:
                flags.append("same brightness: hard with CVD")
            flag = ("  " + "; ".join(flags)) if flags else ""
            print(f"{i:>3}-{j:<2} " + " ".join(f"{d[k]:>7.1f}" for k in
                  ("normal", "deutan", "protan", "tritan"))
                  + f" {d['bright']:>6.2f}:1" + flag)
    return dict(colors=rows, pairs=pairs)


def swatches(colors=None, names=None):
    """Quick palette card: each colour with its ink tone, hex, contrast and
    its appearance under deuteranopia, protanopia, tritanopia, greyscale.
    colors: list of colours, a palette name ('A', 'B', 'C'), or None = active."""
    key = None
    if isinstance(colors, str):
        key = _palette_key(colors)
        colors, names = PALETTES[key]["colors"], names or PALETTES[key]["names"]
    elif colors is None:
        key = _STATE["palette"]
    colors = list(colors or COLORS)
    names = names or (NAMES if colors == COLORS else [f"{k}" for k in range(len(colors))])
    kinds = ["normal", "deutan", "protan", "tritan", "gray"]
    fig, ax = plt.subplots(figsize=(width("double"), 0.36 * len(colors) + 0.5), layout="none")
    fig.subplots_adjust(left=0.01, right=0.99, top=0.88, bottom=0.02)
    ax.set_xlim(0, 10)
    ax.set_ylim(len(colors), 0)
    ax.set_axis_off()
    if key:
        ax.text(0.05, -0.15, f"palette {key} ({PALETTES[key]['name']})", ha="left",
                va="bottom", fontsize=6.5, fontweight="bold")
    for k, kind in enumerate(kinds):
        ax.text(4.2 + k * 1.16 + 0.5, -0.15, _KIND_TITLE[kind].split(" (")[0],
                ha="center", va="bottom", fontsize=6.5)
    for r, (c, n) in enumerate(zip(colors, names)):
        ax.plot([0.25], [r + 0.5], marker=MARKERS[r % 6], ms=7 * _MSCALE[MARKERS[r % 6]],
                mfc=c, mec=ink(c), mew=0.8, ls="none")
        ax.text(0.55, r + 0.5, f"{r + 1} {n}", va="center", fontsize=7, fontweight="bold")
        ax.text(2.0, r + 0.5, to_hex(c).upper(), va="center", fontsize=7)
        ax.text(3.0, r + 0.5, f"{_contrast(c):.1f}:1", va="center", fontsize=7)
        for k, kind in enumerate(kinds):
            ax.add_patch(mpl.patches.Rectangle((4.2 + k * 1.16, r + 0.12), 1.0, 0.76,
                                               color=simulate(c, kind), lw=0))
    return fig
