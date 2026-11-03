"""
fairfig - a colour-blind-safe visual identity for scientific figures (matplotlib)
==============================================================================

    import fairfig as ff
    ff.use("acs")                                   # or "elsevier", "nature"
    # ff.use("acs", palette="okabe-ito")            # Okabe-Ito in its published order
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
              Alternative: ff.use(palette="okabe-ito") = Okabe-Ito as published.
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
from collections.abc import Hashable, Iterable, Sequence
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any, TypeVar, overload

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib import ticker as mticker
from matplotlib.colors import ListedColormap, to_hex, to_rgb
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
from matplotlib.rcsetup import cycler

from ._cmapdata import BATLOW, VIK

if TYPE_CHECKING:
    from typing import Literal

    from matplotlib.axes import Axes
    from matplotlib.axis import Axis
    from matplotlib.cm import ScalarMappable
    from matplotlib.collections import PolyCollection
    from matplotlib.colorbar import Colorbar
    from matplotlib.colors import Colormap
    from matplotlib.legend import Legend
    from matplotlib.lines import Line2D
    from matplotlib.text import Annotation
    from matplotlib.typing import ColorType
    from numpy.typing import ArrayLike, NDArray

__version__ = "1.3.0"
__all__ = [
    "use", "C", "COLORS", "INK", "NAMES", "PALETTES", "MARKERS", "LINESTYLES", "JOURNALS",
    "figure", "subplots", "width", "points", "curve", "ramp", "cmap", "ink",
    "tint", "slots", "label", "legend", "panel_labels", "diagonal", "hline",
    "vline", "band", "fraction_axis", "grid", "ticks_out", "end_label", "colorbar",
    "save", "simulate", "ERRORBAR",
    "cvd_preview", "check_palette", "swatches", "STYLE",
]

STYLE = os.path.join(os.path.dirname(__file__), "fairfig.mplstyle")
"""Path of the bundled style sheet, for ``plt.style.use(ff.STYLE)`` without `use`."""
MM = 1 / 25.4  # inches per millimetre

_K = TypeVar("_K", bound=Hashable)

# =============================================================================
# 1. Colour
# =============================================================================
PALETTES: dict[str, dict[str, list[str]]] = {
    # fairfig (default). Blue and vermillion are darker than the published
    # Okabe-Ito values: a colour-blind reader found vermillion and bluish green
    # hard to tell apart at equal brightness (1.13:1). Slots 1-3 now sit at three
    # brightness levels (pairwise 1.3-2.1:1), so they separate wherever hue is
    # lost: CVD, small markers, greyscale print. The reader confirmed it.
    "fairfig": dict(
        colors=["#005B90", "#BB4000", "#009E73", "#E69F00", "#56B4E9", "#CC79A7"],
        names=["blue", "vermillion", "green", "orange", "sky", "purple"]),
    # Okabe-Ito in its published order (Wong 2011), the most widely recommended
    # colour-blind-safe palette. Its black stays reserved for text and models,
    # its yellow for areas (1.3:1 on white: too faint for lines).
    "okabe-ito": dict(
        colors=["#E69F00", "#56B4E9", "#009E73", "#0072B2", "#D55E00", "#CC79A7"],
        names=["orange", "sky", "green", "blue", "vermillion", "purple"]),
}
"""Categorical palettes, chosen with ``use(palette=...)``: colours and names in slot
order. Both use the same six Okabe-Ito hues, so ``C.<hue>`` always exists."""

C = SimpleNamespace(
    # categorical: set from the active palette (default fairfig)
    **dict(zip(PALETTES["fairfig"]["names"], PALETTES["fairfig"]["colors"])),
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
"""Named colours: the six hues of the active palette (``C.blue``, ``C.vermillion``,
``C.green``, ``C.orange``, ``C.sky``, ``C.purple``) and reserved colours that never
change (``yellow``, ``black``, ``grey_dk``, ``grey``, ``grey_lt``, ``grey_xlt``,
``grid``, ``grid_minor``, ``white``)."""

NAMES: list[str] = list(PALETTES["fairfig"]["names"])
"""Names of the active palette's colours, in slot order (changed in place by `use`)."""
COLORS: list[str] = list(PALETTES["fairfig"]["colors"])
"""Colours of the active palette, in slot order (changed in place by `use`)."""

MARKERS = ["o", "s", "^", "D", "v", "p"]
"""Marker shape of each slot."""
# size factors so every shape has roughly the same visual weight as the circle
_MSCALE = {"o": 1.0, "s": 0.89, "^": 1.2, "v": 1.2, "<": 1.2, ">": 1.2,
           "D": 0.85, "d": 1.0, "p": 1.12, "h": 1.08, "H": 1.08, "*": 1.35,
           "X": 1.0, "P": 1.0, "x": 1.0, "+": 1.1}
LINESTYLES = ["-", "--", "-.", ":"]
"""Line styles of ``curve(style=0..3)``: solid, dashed, dash-dot, dotted."""

JOURNALS: dict[str, dict[str, Any]] = {
    # ACS (J. Chem. Eng. Data, I&EC Res.): single <= 240 pt, double 300-504 pt,
    # max depth 660 pt incl. caption, lettering >= 4.5 pt, lines >= 0.5 pt.
    "acs": dict(single=84.6, onehalf=127.0, double=177.8, max_height=232.8, font=8.0),
    # Elsevier (Fluid Phase Equilib., J. Chem. Thermodyn.): 90/140/190 mm,
    # 7 pt normal text, >= 6 pt sub/superscripts.
    "elsevier": dict(single=90.0, onehalf=140.0, double=190.0, max_height=None, font=8.0),
    # Nature research figure guide: 89/183 mm, max height 170 mm, text 5-7 pt.
    "nature": dict(single=89.0, onehalf=120.0, double=183.0, max_height=170.0, font=7.0),
}
"""Journal presets: column widths (``single``, ``onehalf``, ``double``) and
``max_height`` in mm (``None``: no limit known), text size (``font``) in pt."""

# Liberation Mono is bundled in fairfig/fonts and registered on import, so it works
# on any machine. Courier New comes next: same letter widths, so an SVG opened
# where Liberation Mono is not installed keeps its layout.
_FONTS = ["Liberation Mono", "Courier New", "Courier", "Nimbus Mono PS",
          "FreeMono", "DejaVu Sans Mono"]
_FONT_DIR = os.path.join(os.path.dirname(__file__), "fonts")

_STATE: dict[str, Any] = dict(journal="acs", units="slash", frame="box", ticks="out",
                              grid=True, panel="a", fontsize=8.0, font="Liberation Mono",
                              palette="fairfig")


# ---------------------------------------------------------------- colour maths
def _lin(c: ArrayLike) -> NDArray[np.float64]:
    a = np.asarray(c, float)
    return np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)


def _srgb(c: ArrayLike) -> NDArray[np.float64]:
    a = np.clip(np.asarray(c, float), 0, 1)
    return np.where(a <= 0.0031308, 12.92 * a, 1.055 * a ** (1 / 2.4) - 0.055)  # type: ignore[no-any-return]


_M1 = np.array([[0.4122214708, 0.5363325363, 0.0514459929],
                [0.2119034982, 0.6806995451, 0.1073969566],
                [0.0883024619, 0.2817188376, 0.6299787005]])
_M2 = np.array([[0.2104542553, 0.7936177850, -0.0040720468],
                [1.9779984951, -2.4285922050, 0.4505937099],
                [0.0259040371, 0.7827717662, -0.8086757660]])


def _oklab(rgb_lin: ArrayLike) -> NDArray[np.float64]:
    return np.cbrt(np.asarray(rgb_lin) @ _M1.T) @ _M2.T  # type: ignore[no-any-return]


def _oklab_to_lin(lab: ArrayLike) -> NDArray[np.float64]:
    lms = (np.asarray(lab) @ np.linalg.inv(_M2).T) ** 3
    return lms @ np.linalg.inv(_M1).T


def _luminance(color: ColorType) -> float:
    return float(_lin(to_rgb(color)) @ np.array([0.2126, 0.7152, 0.0722]))


def _contrast(a: ColorType, b: ColorType = "#FFFFFF") -> float:
    ya, yb = sorted((_luminance(a), _luminance(b)))
    return (yb + 0.05) / (ya + 0.05)


def ink(color: ColorType, amount: float = 0.14) -> str:
    """Darker tone of the same hue, used for marker edges so that light hues keep
    at least 3:1 contrast against white.

    Parameters
    ----------
    color
        Any matplotlib colour.
    amount
        How much darker: OKLab lightness subtracted (0-1).

    Returns
    -------
    str
        Hex colour.
    """
    lab = _oklab(_lin(to_rgb(color)))
    lab[0] -= amount
    for f in np.linspace(1.0, 0.3, 36):          # pull chroma in until in gamut
        trial = lab.copy()
        trial[1:] *= f
        rgb = _oklab_to_lin(trial)
        if rgb.min() >= -1e-6 and rgb.max() <= 1 + 1e-6:
            break
    return to_hex(_srgb(np.clip(rgb, 0, 1)))  # type: ignore[arg-type]


def tint(color: ColorType, amount: float = 0.18) -> str:
    """Light tint (the colour mixed with white) for bands and shaded regions.

    Parameters
    ----------
    color
        Any matplotlib colour.
    amount
        Share of the colour, 0-1; the rest is white.

    Returns
    -------
    str
        Hex colour.
    """
    c = np.asarray(to_rgb(color))
    return to_hex(amount * c + (1 - amount) * np.ones(3))  # type: ignore[arg-type]


INK: list[str] = [ink(c) for c in COLORS]
"""Marker-edge tones matching `COLORS` (same order)."""


def _palette_key(palette: str) -> str:
    """'fairfig' or 'okabe-ito' (any case; '_' or ' ' for '-') -> key of PALETTES."""
    p = str(palette).strip().lower().replace("_", "-").replace(" ", "-")
    if p in PALETTES:
        return p
    raise ValueError(f"palette must be one of {list(PALETTES)}; got {palette!r}")


def _set_palette(palette: str) -> str:
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
    mpl.rcParams["axes.prop_cycle"] = cycler(color=list(COLORS))
    _STATE["palette"] = key
    return key


def slots(names: Iterable[_K]) -> dict[_K, int]:
    """Fix colour and marker slots to entities, e.g. systems or components.

    Keep one mapping per paper, so every entity keeps its colour in every figure.

    Parameters
    ----------
    names
        The entities, in slot order.

    Returns
    -------
    dict
        Entity -> slot number, for `points` and `curve`.

    Raises
    ------
    ValueError
        More entities than identity colours (six): facet the figure, or use
        `ramp` if the series are ordered.

    Examples
    --------
    >>> S = ff.slots(["A+B", "A+C"])
    >>> ax.plot(x, y, **ff.points(S["A+C"]))
    """
    names = list(names)
    if len(names) > len(COLORS):
        raise ValueError(f"{len(names)} entities > {len(COLORS)} identity colours: "
                         "facet the figure, or use ff.ramp() if the series are ordered.")
    return {n: i for i, n in enumerate(names)}


# ---------------------------------------------------------------- colormaps
def _register_cmaps() -> None:
    for name, data in (("batlow", BATLOW), ("vik", VIK)):
        cm = ListedColormap(["#" + h for h in data], name=name)
        for nm, c in ((name, cm), (name + "_r", cm.reversed())):
            if nm not in mpl.colormaps:
                mpl.colormaps.register(c, name=nm)


_register_cmaps()


def _is_bundled(path: str) -> bool:
    folder = os.path.normcase(os.path.dirname(os.path.abspath(path)))
    return folder == os.path.normcase(os.path.abspath(_FONT_DIR))


def _register_fonts() -> None:
    """Make the bundled Liberation Mono available to matplotlib (this session
    only; nothing is installed on the system). A system copy of the same face,
    possibly an older version, would otherwise win: matplotlib keeps the first
    of equally good matches. So the bundled files go first, and every machine
    draws the same glyphs."""
    if not os.path.isdir(_FONT_DIR):
        return
    fm = font_manager.fontManager
    for fn in sorted(os.listdir(_FONT_DIR)):
        if fn.lower().endswith((".ttf", ".otf")):
            try:
                fm.addfont(os.path.join(_FONT_DIR, fn))
            except Exception:
                pass
    fm.ttflist.sort(key=lambda entry: not _is_bundled(entry.fname))   # stable sort
    cache = getattr(fm, "_findfont_cached", None)
    if cache is not None and hasattr(cache, "cache_clear"):
        cache.cache_clear()


_register_fonts()


def cmap(kind: str = "seq") -> Colormap:
    """Colour map for ordered data.

    Parameters
    ----------
    kind
        ``"seq"``: batlow, for magnitudes; ``"div"``: vik, for signed deviations
        (centre it at 0); or the name of any registered matplotlib colour map.

    Returns
    -------
    Colormap
    """
    return mpl.colormaps[{"seq": "batlow", "div": "vik"}.get(kind, kind)]


def ramp(n: int, cmap: str = "batlow", lo: float = 0.0, hi: float = 0.72,
         reverse: bool = False) -> list[str]:
    """*n* colours for an *ordered* series (isotherms, isobars, compositions),
    sampled from a perceptually uniform colour map: low value -> dark blue.

    Parameters
    ----------
    n
        Number of colours.
    cmap
        Name of a registered colour map.
    lo, hi
        Part of the map to sample (0-1). The light end is capped (`hi`) so thin
        lines stay visible on white.
    reverse
        Return the colours light to dark.

    Returns
    -------
    list of str
        Hex colours; pass them as ``points(k, color=r[k])`` and
        ``curve(k, color=r[k])``.
    """
    cm = mpl.colormaps[cmap]
    cols = [to_hex(cm(t)) for t in np.linspace(lo, hi, n)]
    return cols[::-1] if reverse else cols


# =============================================================================
# 2. Style
# =============================================================================
def _first_font(candidates: Iterable[str]) -> str:
    have = {f.name for f in font_manager.fontManager.ttflist}
    for name in candidates:
        if name in have:
            return name
    return "DejaVu Sans Mono"


def _set_subscript_scale(scale: float) -> None:
    # Matplotlib shrinks sub/superscripts to 0.7x (private constant). 0.75 keeps
    # them >= 6 pt at 8 pt text (Elsevier) and >= 5 pt at 7 pt text (Nature).
    try:
        from matplotlib import _mathtext
        if hasattr(_mathtext, "SHRINK_FACTOR"):
            setattr(_mathtext, "SHRINK_FACTOR", float(scale))  # noqa: B010 (private name)
            from matplotlib.mathtext import MathTextParser
            getattr(MathTextParser, "_parse_cached").cache_clear()  # noqa: B009 (private name)
    except Exception:  # never fail because of a cosmetic tweak
        pass


def use(journal: str = "acs", *, palette: str = "fairfig",
        frame: Literal["box", "open"] = "box", ticks: Literal["out", "in"] = "out",
        grid: bool = True, units: Literal["slash", "paren"] = "slash",
        panel: Literal["a", "(a)"] | None = None, fontsize: float | None = None,
        font: str | None = None, subscript: float | None = 0.75) -> dict[str, Any]:
    """Apply the identity: style sheet, journal preset, palette and font.

    Call it once, before making figures.

    Parameters
    ----------
    journal
        ``"acs"``, ``"elsevier"`` or ``"nature"`` (see `JOURNALS`): column
        widths and text size.
    palette
        Categorical colours (see `PALETTES`): ``"fairfig"`` (default) sets
        slots 1-3 at three brightness levels; ``"okabe-ito"`` is Okabe-Ito in
        its published order.
    frame
        ``"box"``: closed frame (default); ``"open"``: left and bottom spines only.
    ticks
        ``"out"``: outward, left and bottom (default); ``"in"``: inward, on all
        four sides.
    grid
        Faint major and minor grid (`figure` and `subplots` add the minor grid).
    units
        ``"slash"``: *T* / K (IUPAC, default); ``"paren"``: *T* (K).
    panel
        Panel labels ``"a"`` (bold a, b, c) or ``"(a)"``; default ``"(a)"``
        for Elsevier, otherwise ``"a"``.
    fontsize
        Text size in pt, overriding the preset's.
    font
        Typeface instead of Liberation Mono, e.g. ``font="Arial"`` for a Nature
        submission. If it is not installed, the bundled face is used.
    subscript
        Size of sub- and superscripts relative to the text (matplotlib uses
        0.7); ``None`` or 0 leaves the current value.

    Returns
    -------
    dict
        The settings now in force.

    Raises
    ------
    ValueError
        An option that is not one of the values listed.
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
    rc: dict[str, Any] = {
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
    mpl.rcParams.update(rc)   # type: ignore[arg-type]
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
def width(w: str | float = "single", journal: str | None = None) -> float:
    """Column width in inches.

    Parameters
    ----------
    w
        ``"single"``, ``"onehalf"``, ``"double"``, or a width in mm.
    journal
        Preset to take the width from; default: the active one.

    Returns
    -------
    float
    """
    if isinstance(w, (int, float)):
        return w * MM
    return float(JOURNALS[journal or _STATE["journal"]][w]) * MM


def _height(w_in: float, ncols: int, nrows: int, aspect: float,
            height: float | None) -> float:
    if height is not None:
        return height * MM
    h = w_in / ncols * aspect * nrows
    mh = JOURNALS[_STATE["journal"]]["max_height"]
    return min(h, mh * MM) if mh else h


def grid(ax: Axes | Iterable[Axes], on: bool = True, minor: bool = True) -> None:
    """Faint background grid, drawn under the data: major ``#E6E6E6`` and minor
    ``#F2F2F2``, both 0.5 pt.

    Parameters
    ----------
    ax
        One axes or an array of axes.
    on
        ``False`` removes the grid (e.g. on colour maps).
    minor
        Also draw the minor grid.
    """
    for a in np.atleast_1d(ax).ravel():   # type: ignore[call-overload]
        if not on:
            a.grid(False, which="both")
            continue
        a.grid(True, which="major", color=C.grid, linewidth=0.5, linestyle="-")
        a.grid(minor, which="minor", color=C.grid_minor, linewidth=0.5, linestyle="-")
        a.set_axisbelow(True)


def figure(width: str | float = "single", aspect: float = 0.8, height: float | None = None,
           **kw: Any) -> tuple[Figure, Axes]:
    """One axes at the exact journal width.

    Parameters
    ----------
    width
        ``"single"``, ``"onehalf"``, ``"double"``, or a width in mm.
    aspect
        Height/width. The height is capped at the preset's maximum height.
    height
        Height in mm; overrides `aspect`.
    **kw
        Passed to `matplotlib.pyplot.subplots`.

    Returns
    -------
    fig : Figure
    ax : Axes
    """
    w = globals()["width"](width)
    fig, ax = plt.subplots(figsize=(w, _height(w, 1, 1, aspect, height)), **kw)
    if _STATE["grid"]:
        grid(ax)
    return fig, ax


def subplots(nrows: int = 1, ncols: int = 1, width: str | float | None = None,
             aspect: float = 0.8, height: float | None = None,
             **kw: Any) -> tuple[Figure, Any]:
    """Grid of panels at the exact journal width.

    Parameters
    ----------
    nrows, ncols
        Number of rows and columns of panels.
    width
        ``"single"``, ``"onehalf"``, ``"double"``, or a width in mm; default
        ``"double"`` when ``ncols > 1``, otherwise ``"single"``.
    aspect
        Height/width of each panel. The height is capped at the preset's
        maximum height.
    height
        Figure height in mm; overrides `aspect`.
    **kw
        Passed to `matplotlib.pyplot.subplots`.

    Returns
    -------
    fig : Figure
    axs : Axes or array of Axes
    """
    w = globals()["width"](width or ("double" if ncols > 1 else "single"))
    fig, axs = plt.subplots(nrows, ncols, figsize=(w, _height(w, ncols, nrows, aspect, height)), **kw)
    if _STATE["grid"]:
        grid(axs)
    return fig, axs


# =============================================================================
# 4. Marks  (never colour alone: slot i = colour i + marker i)
# =============================================================================
def _slot_color(i: int | None, color: ColorType | None) -> str:
    if color is not None:
        return to_hex(color)
    if i is None or not 0 <= i < len(COLORS):
        raise IndexError(f"slot {i}: only {len(COLORS)} identity colours. Facet, or use "
                         "ff.ramp(n) for ordered series (points(i, color=r[i])).")
    return COLORS[i]


def points(i: int = 0, *, color: ColorType | None = None, hollow: bool = False,
           lit: bool = False, marker: str | None = None, size: float | None = None,
           **kw: Any) -> dict[str, Any]:
    """Keywords for experimental data, for ``ax.plot`` or ``ax.errorbar``.

    Slot *i* has its own colour and marker shape, so series stay apart without
    colour.

    Parameters
    ----------
    i
        Slot: colour *i* and marker shape *i*.
    color
        Colour instead of the slot's (e.g. from `ramp`); the marker shape still
        follows *i*.
    hollow
        Open marker: vapour/dew branch, second liquid phase, ...
    lit
        Literature or context data: grey open marker, drawn under your data.
    marker
        Marker shape instead of the slot's.
    size
        Marker size in pt (default: ``lines.markersize``), scaled per shape so
        all shapes look equally heavy.
    **kw
        Added to the keywords, overriding them.

    Returns
    -------
    dict
        Keywords for `matplotlib.axes.Axes.plot`.

    Examples
    --------
    >>> ax.plot(x, T, **ff.points(0), label="$x_1$")
    >>> ax.plot(y, T, **ff.points(0, hollow=True), label="$y_1$")
    >>> ax.errorbar(x, T, yerr=u, **ff.points(1), **ff.ERRORBAR)
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


def curve(i: int | None = 0, *, color: ColorType | None = None, style: int = 0,
          lw: float | None = None, **kw: Any) -> dict[str, Any]:
    """Keywords for a model or correlation line, for ``ax.plot``.

    Parameters
    ----------
    i
        Slot whose colour the line takes; ``None``: black (a single reference
        model).
    color
        Colour instead of the slot's.
    style
        0 solid, 1 dashed, 2 dash-dot, 3 dotted: tells several models apart.
    lw
        Line width in pt (default: ``lines.linewidth``).
    **kw
        Added to the keywords, overriding them.

    Returns
    -------
    dict
        Keywords for `matplotlib.axes.Axes.plot`.
    """
    c = C.black if (i is None and color is None) else _slot_color(i, color)
    d = dict(color=c, linestyle=LINESTYLES[style % len(LINESTYLES)],
             linewidth=lw or mpl.rcParams["lines.linewidth"], marker="none", zorder=2)
    d.update(kw)
    return d


ERRORBAR = dict(elinewidth=0.5, capsize=1.5, capthick=0.5)
"""Extra keywords for error bars: ``ax.errorbar(x, y, yerr=u, **ff.points(i), **ff.ERRORBAR)``."""


def diagonal(ax: Axes, **kw: Any) -> Line2D:
    """y = x guide (x-y diagrams, parity plots), light grey, under the data.

    ``**kw`` is passed to `matplotlib.axes.Axes.axline`.
    """
    d = dict(color=C.grey_lt, lw=0.6, zorder=1)
    d.update(kw)
    return ax.axline((0, 0), (1, 1), **d)


def hline(ax: Axes, y: float = 0.0, **kw: Any) -> Line2D:
    """Horizontal guide at *y* (default the zero line), light grey, under the data.

    ``**kw`` is passed to `matplotlib.axes.Axes.axhline`.
    """
    d = dict(color=C.grey_lt, lw=0.6, zorder=1)
    d.update(kw)
    return ax.axhline(y, **d)


def vline(ax: Axes, x: float = 0.0, **kw: Any) -> Line2D:
    """Vertical guide at *x*, light grey, under the data.

    ``**kw`` is passed to `matplotlib.axes.Axes.axvline`.
    """
    d = dict(color=C.grey_lt, lw=0.6, zorder=1)
    d.update(kw)
    return ax.axvline(x, **d)


def band(ax: Axes, x: ArrayLike, y1: ArrayLike, y2: ArrayLike, i: int | None = None,
         color: ColorType | None = None, amount: float = 0.18,
         along: Literal["x", "y"] = "x", **kw: Any) -> PolyCollection:
    """Shaded band (uncertainty, two-phase region) in the colour of slot *i*, or grey.

    The band is transparent (alpha = `amount`), so the grid shows through; on
    white it looks like ``tint(colour, amount)``.

    Parameters
    ----------
    ax
        Axes to draw on.
    x
        Coordinate along the band: x, or the vertical coordinate with ``along="y"``.
    y1, y2
        Limits of the band: y values, or x values with ``along="y"``.
    i
        Slot whose colour the band takes; default grey (as light as the grid).
    color
        Colour instead of the slot's.
    amount
        Opacity, 0-1.
    along
        ``"x"``: between two y limits (`fill_between`); ``"y"``: between two x
        limits (`fill_betweenx`), e.g. ``ff.band(ax, T, x_I, x_II, i=0,
        along="y")`` for a liquid-liquid two-phase region.
    **kw
        Passed to `matplotlib.axes.Axes.fill_between` (``fill_betweenx``).

    Returns
    -------
    PolyCollection
    """
    if color is not None:
        c, a = color, amount
    elif i is not None:
        c, a = COLORS[i], amount
    else:
        c, a = C.grey, amount + 0.02           # grey 0.2 on white = #E6E6E6
    d: dict[str, Any] = dict(color=c, alpha=a, lw=0, zorder=0.8)
    d.update(kw)
    if along == "y":
        return ax.fill_betweenx(x, y1, y2, **d)
    return ax.fill_between(x, y1, y2, **d)


def fraction_axis(ax: Axes, which: Literal["x", "y"] = "x", major: float = 0.2,
                  minor: float = 0.1) -> None:
    """0-1 axis for mole or mass fractions, ticks every 0.2 (minor 0.1).

    Parameters
    ----------
    ax
        Axes.
    which
        ``"x"`` or ``"y"``.
    major, minor
        Tick spacing.
    """
    axis: Axis
    if which == "x":
        axis = ax.xaxis
        ax.set_xlim(0, 1)
    else:
        axis = ax.yaxis
        ax.set_ylim(0, 1)
    axis.set_major_locator(mticker.MultipleLocator(major))
    axis.set_minor_locator(mticker.MultipleLocator(minor))
    axis.set_major_formatter(mticker.FormatStrFormatter("%.1f"))


def ticks_out(ax: Axes) -> None:
    """Outward ticks, no top/right ticks (already the default with ticks='out').
    With ticks='in', use it on image/contour maps where inward ticks would be
    hidden by the colours."""
    ax.tick_params(which="both", direction="out", top=False, right=False)


def end_label(ax: Axes, x: float, y: float, text: str, dx: float = 3,
              **kw: Any) -> Annotation:
    """Direct label at the end of a line, in black: an alternative to a legend
    when the lines are well apart.

    Parameters
    ----------
    ax
        Axes.
    x, y
        End of the line, in data coordinates.
    text
        Label.
    dx
        Gap to the right of the point, in pt.
    **kw
        Passed to `matplotlib.axes.Axes.annotate`.

    Returns
    -------
    Annotation
    """
    d = dict(xytext=(dx, 0), textcoords="offset points", va="center", ha="left",
             fontsize=_STATE["fontsize"])
    d.update(kw)
    return ax.annotate(text, xy=(x, y), **d)


def colorbar(mappable: ScalarMappable, ax: Axes | None = None, label: str | None = None,
             **kw: Any) -> Colorbar:
    """Slim colour bar matching the frame style.

    Parameters
    ----------
    mappable
        What the bar describes: the result of ``contourf``, ``pcolormesh``,
        ``imshow``, ...
    ax
        Axes to take the room from; default: the axes `mappable` is drawn on.
    label
        Label of the bar, e.g. from `label`.
    **kw
        Passed to `matplotlib.figure.Figure.colorbar`.

    Returns
    -------
    Colorbar
    """
    if ax is None:
        ax = getattr(mappable, "axes", None)
        if ax is None:
            raise ValueError("this mappable is not drawn on an Axes: pass ax=...")
    d: dict[str, Any] = dict(fraction=0.05, pad=0.02, aspect=25)
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
def _unit_tex(unit: str) -> str:
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
    return "$" + "·".join(out) + "$"        # kg·m^-3: unambiguous in monospace


def label(symbol: str, unit: str | None = None, *,
          style: Literal["slash", "paren"] | None = None) -> str:
    r"""Axis label: quantity symbol in italic, unit upright.

    Parameters
    ----------
    symbol
        Quantity in mathtext, without dollar signs: ``"T"``, ``"x_1, y_1"``,
        ``r"\rho"``. Text already in ``$...$`` and plain words
        (``"Temperature"``) are kept as they are.
    unit
        Unit: factors separated by spaces, powers with ``^``, e.g.
        ``"kg m^-3"``. Factors are joined by a middle dot.
    style
        ``"slash"`` (IUPAC: *T* / K) or ``"paren"`` (*T* (K)); default from `use`.

    Returns
    -------
    str
        The label, as mathtext.

    Examples
    --------
    >>> ff.label("T", "K")               # T / K   (style="paren": T (K))
    >>> ff.label(r"\rho", "kg m^-3")     # rho / (kg m^-3)
    >>> ff.label("x_1")                  # x_1
    >>> ff.label("Temperature", "K")     # plain words stay upright
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
    simple = re.fullmatch(r"[A-Za-z%°µμΩ]+", unit.strip()) is not None
    u = unit.strip() if simple else _unit_tex(unit)
    if style == "paren":
        return f"{q} ({u})"
    if q.startswith("$") and q.endswith("$") and q.count("$") == 2:
        # one math string: thin spaces around the slash (full spaces look loose
        # in a monospaced face)
        um = (r"\mathrm{%s}" % unit.strip().replace("%", r"\%")) if simple else "(" + u[1:-1] + ")"
        return "$" + q[1:-1] + r"\,/\," + um + "$"
    return f"{q} / {u}" if simple else f"{q} / ({u})"


def _text_width_pt(s: str, size: float) -> float:
    from matplotlib.font_manager import FontProperties
    from matplotlib.textpath import TextToPath
    try:
        return float(TextToPath().get_text_width_height_descent(
            s, FontProperties(size=size), ismath=s.count("$") >= 2)[0])
    except Exception:
        return 0.6 * size * len(s)


def _axes_width_pt(ax: Axes) -> float:
    """Width of the axes box in points, after the layout engine has run."""
    import warnings
    fig: Any = ax.figure
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            eng = fig.get_layout_engine()
            if eng is not None:
                eng.execute(fig)
            ax.apply_aspect()
        except Exception:
            pass
    return float(ax.get_position().width * fig.get_figwidth() * 72)


def _fit_ncol(ax: Axes, labels: Sequence[str], d: dict[str, Any]) -> int:
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


def legend(ax: Axes, *args: Any, loc: str = "top", ncol: int | None = None,
           **kw: Any) -> Legend | None:
    """Frameless legend; by default the key goes above the plot.

    Parameters
    ----------
    ax
        Axes.
    *args
        ``handles, labels``, as for `matplotlib.axes.Axes.legend` (e.g. to put
        the entries in another order).
    loc
        ``"top"`` (default): above the plot, with as many entries per row as
        fit the panel width, read left to right, then top to bottom.
        ``"right"``: outside, on the right. Any matplotlib location
        (``"upper right"``, ``"best"``, ...): inside the axes.
    ncol
        Number of columns; default: as many as fit (``"top"``), otherwise 1.
    **kw
        Passed to `matplotlib.axes.Axes.legend`.

    Returns
    -------
    Legend or None
        ``None`` with ``loc="top"`` when there is nothing to show.
    """
    d: dict[str, Any]
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


def panel_labels(axes: Figure | Axes | Iterable[Axes], labels: Sequence[str] | None = None,
                 *, style: Literal["a", "(a)"] | None = None,
                 loc: Literal["margin", "inside"] = "margin", **kw: Any) -> list[Annotation]:
    """Bold panel labels a, b, c, ... at the top left of each panel.

    Parameters
    ----------
    axes
        Axes to label, in order; or a Figure, to label all its panels (colour
        bars are skipped).
    labels
        Letters; default a, b, c, ...
    style
        ``"a"`` or ``"(a)"``; default from `use`.
    loc
        ``"margin"`` (default): just above the frame, left-aligned with the
        y-axis label (Nature style; never collides with tick labels).
        ``"inside"``: inside the frame, in the top-left corner.
    **kw
        Passed to `matplotlib.axes.Axes.annotate`.

    Returns
    -------
    list of Annotation
    """
    if isinstance(axes, Figure):
        axes = [a for a in axes.axes if a.get_label() != "<colorbar>"]
    axs = list(np.atleast_1d(axes).ravel())   # type: ignore[call-overload]
    style = style or _STATE["panel"]
    labels = labels or [chr(ord("a") + k) for k in range(len(axs))]
    fmt = "({})" if style == "(a)" else "{}"
    fs = _STATE["fontsize"] + 1
    out = []
    for ax, lab in zip(axs, labels):
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
def _svg_font_fallback(path: str) -> None:
    """Give every SVG font declaration a fallback chain, so an editor without
    the main face uses one with the same letter widths (Courier New for
    Liberation Mono) instead of its default serif font."""
    face = _STATE["font"]
    chain = ["Courier New", "monospace"] if face in _FONTS else ["Arial", "sans-serif"]
    tail = ", ".join(x if x in ("monospace", "sans-serif") else f"'{x}'"
                     for x in chain if x != face)
    with open(path, encoding="utf-8") as fh:
        s = fh.read()
    # matplotlib >= 3.10 writes "font-family: 'Face', ...", older versions the
    # shorthand "font: italic 8px 'Face', ..."; the face ends both.
    s = re.sub(r"(font(?:-family)?: [^;\"]*?'%s')[^;\"]*" % re.escape(face),
               lambda m: f"{m.group(1)}, {tail}", s)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(s)


def save(fig: Figure, path: str | os.PathLike[str], formats: Sequence[str] = ("svg", "pdf"),
         dpi: float | None = None, cvd: bool = False, **kw: Any) -> list[str]:
    """Save at the designed size: ``"fig1"`` -> ``fig1.svg`` (editable text) +
    ``fig1.pdf`` (fonts embedded: the file to submit to ACS or Elsevier).

    Parameters
    ----------
    fig
        Figure to save.
    path
        File name without extension, to write every format in `formats`; or
        ending in ``.svg``, ``.pdf``, ``.eps``, ``.png`` or ``.tif`` to write that
        format only. Missing folders are created.
    formats
        Formats written when `path` has no extension.
    dpi
        Resolution of raster output (PNG, TIFF); default ``savefig.dpi`` (600).
        TIFF is written RGB with LZW compression.
    cvd
        Also write ``<path>_cvd.<first format>`` (PNG for TIFF) with the
        colour-blind check of `cvd_preview`.
    **kw
        Passed to `matplotlib.figure.Figure.savefig`.

    Returns
    -------
    list of str
        The files written.
    """
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


@overload
def simulate(rgb: ColorType, kind: str) -> str: ...
@overload
def simulate(rgb: NDArray[Any], kind: str) -> NDArray[np.float64]: ...
def simulate(rgb: ColorType | NDArray[Any], kind: str) -> str | NDArray[np.float64]:
    """Simulate colour-vision deficiency, or greyscale.

    Parameters
    ----------
    rgb
        A colour (the result is a hex string), or an sRGB image array of shape
        ``(..., 3)`` or ``(..., 4)`` with values 0-1 (the result is an array of
        shape ``(..., 3)``).
    kind
        ``"deutan"``, ``"protan"`` or ``"tritan"`` (Machado, Oliveira &
        Fernandes 2009, severity 1), ``"gray"`` (luminance), or ``"normal"``
        (unchanged).

    Returns
    -------
    str or numpy.ndarray
    """
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


def cvd_preview(fig: Figure,
                kinds: Sequence[str] = ("normal", "deutan", "protan", "tritan", "gray"),
                dpi: float = 200, ncols: int | None = None) -> Figure:
    """Show a figure as seen with deuteranopia, protanopia, tritanopia and in
    greyscale, next to normal vision.

    Parameters
    ----------
    fig
        Figure to check.
    kinds
        Views to show, in order (see `simulate`).
    dpi
        Resolution at which `fig` is rendered.
    ncols
        Views per row; default up to 3.

    Returns
    -------
    Figure
        The preview. Save it with the same `dpi` to keep it pixel for pixel.
    """
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi)
    buf.seek(0)
    img = plt.imread(buf)[..., :3]
    h, w = img.shape[:2]
    ncols = int(ncols or min(3, len(kinds)))
    nrows = int(np.ceil(len(kinds) / ncols))
    title_h = 0.22
    prev = plt.figure(figsize=(ncols * w / dpi, nrows * (h / dpi + title_h)), layout="none")
    for k, kind in enumerate(kinds):
        r, c = divmod(k, ncols)
        ax = prev.add_axes((c / ncols, 1 - (r + 1) / nrows, 1 / ncols,
                            (h / dpi) / (nrows * (h / dpi + title_h))))
        ax.imshow(simulate(img, kind), interpolation="lanczos")
        ax.set_axis_off()
        ax.set_title(_KIND_TITLE.get(kind, kind), fontsize=8, fontweight="bold", pad=3)
    return prev


def _dE(a: ColorType, b: ColorType, kind: str = "normal") -> float:
    sa = np.asarray(to_rgb(simulate(a, kind) if kind != "normal" else a))
    sb = np.asarray(to_rgb(simulate(b, kind) if kind != "normal" else b))
    return 100 * float(np.linalg.norm(_oklab(_lin(sa)) - _oklab(_lin(sb))))


def check_palette(colors: str | Sequence[ColorType] | None = None,
                  background: ColorType = "#FFFFFF", show: bool = True) -> dict[str, list[Any]]:
    """Contrast and colour-vision-deficiency check of a palette.

    For every colour: contrast against `background` and OKLab lightness. For
    every pair: OKLab ΔE×100 in normal vision and under simulated deuteranopia,
    protanopia and tritanopia (Machado 2009), and the brightness ratio
    (``bright``: the WCAG luminance ratio that online contrast checkers report).

    Rules of thumb: contrast ≥ 3 for lines; ΔE ≥ 8 under CVD (6-8 only with
    distinct marker shapes); ΔE ≥ 15 in normal vision; pairs that are close
    under CVD (ΔE < 15) also need bright ≥ 1.25, better 1.5, because
    colour-blind readers and small markers lose hue first and brightness last.
    (3:1 between data colours is out of reach for any three colours that also
    stand out on white.)

    Parameters
    ----------
    colors
        List of colours, a palette name (``"fairfig"``, ``"okabe-ito"``), or
        ``None`` for the active palette.
    background
        Colour the contrast is measured against.
    show
        Print the two tables.

    Returns
    -------
    dict
        ``"colors"``: ``(hex, contrast, OKLab L)`` per colour; ``"pairs"``:
        ``(i, j, {"normal", "deutan", "protan", "tritan", "bright"})`` per pair.
    """
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


def swatches(colors: str | Sequence[ColorType] | None = None,
             names: Sequence[str] | None = None) -> Figure:
    """Palette card: each colour with its marker and edge tone, hex value,
    contrast on white, and its look with deuteranopia, protanopia, tritanopia
    and in greyscale.

    Parameters
    ----------
    colors
        List of colours, a palette name (``"fairfig"``, ``"okabe-ito"``), or
        ``None`` for the active palette.
    names
        Names to print; default the palette's names (numbers for a list).

    Returns
    -------
    Figure
    """
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
        ax.text(0.05, -0.15, f"palette: {key}", ha="left",
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
            ax.add_patch(Rectangle((4.2 + k * 1.16, r + 0.12), 1.0, 0.76,
                                   color=simulate(c, kind), lw=0))
    return fig
