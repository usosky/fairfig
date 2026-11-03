"""ff.use(), the style sheet, fonts, and figure sizes."""
import os

import matplotlib as mpl
import matplotlib.pyplot as plt
import pytest
from matplotlib import font_manager

import fairfig as ff

MM = 1 / 25.4


# ---------------------------------------------------------------- use()
@pytest.mark.parametrize("bad", [dict(journal="science"), dict(frame="none"),
                                 dict(ticks="both"), dict(units="brackets"),
                                 dict(palette="jet")])
def test_use_rejects_unknown_options(bad):
    with pytest.raises(ValueError):
        ff.use(**{"journal": "acs", **bad})


@pytest.mark.parametrize("journal", sorted(ff.JOURNALS))
def test_journal_presets(journal):
    p = ff.JOURNALS[journal]
    state = ff.use(journal)
    assert state["journal"] == journal and state["fontsize"] == p["font"]
    for key in ("font.size", "axes.labelsize", "xtick.labelsize", "legend.fontsize"):
        assert mpl.rcParams[key] == p["font"]
    w, h = mpl.rcParams["figure.figsize"]
    assert w == pytest.approx(p["single"] * MM) and h == pytest.approx(0.8 * w)
    assert state["panel"] == ("(a)" if journal == "elsevier" else "a")


def test_identity_constants():
    """The documented look: lines 1.0 pt, axes 0.6 pt, markers 4 pt, faint grid,
    frameless legend, editable SVG text, embedded TrueType in PDF."""
    rc = mpl.rcParams
    assert rc["lines.linewidth"] == 1.0 and rc["axes.linewidth"] == 0.6
    assert rc["lines.markersize"] == 4.0 and rc["lines.markeredgewidth"] == 0.6
    assert rc["grid.linewidth"] == 0.5 and mpl.colors.to_hex(rc["grid.color"]) == "#e6e6e6"
    assert rc["axes.grid"] and rc["axes.axisbelow"] is True
    assert rc["axes.spines.top"] and rc["axes.spines.right"]
    assert rc["xtick.direction"] == "out" and not rc["xtick.top"]
    assert rc["legend.frameon"] is False
    assert rc["svg.fonttype"] == "none" and rc["pdf.fonttype"] == 42
    assert rc["savefig.dpi"] == 600 and rc["savefig.bbox"] in (None, "standard")
    assert rc["axes.unicode_minus"] and rc["figure.constrained_layout.use"]


def test_options():
    ff.use("acs", fontsize=9, units="paren", panel="(a)", grid=False)
    assert mpl.rcParams["font.size"] == 9 and ff._STATE["units"] == "paren"
    assert ff._STATE["panel"] == "(a)" and mpl.rcParams["axes.grid"] is False
    ff.use("acs", frame="open")
    assert not mpl.rcParams["axes.spines.top"] and not mpl.rcParams["axes.spines.right"]
    ff.use("acs", ticks="in")
    assert mpl.rcParams["ytick.direction"] == "in"
    assert mpl.rcParams["xtick.top"] and mpl.rcParams["ytick.right"]   # all four sides
    ff.use("acs", frame="open", ticks="in")
    assert not mpl.rcParams["xtick.top"]                              # no box, no top ticks


# ---------------------------------------------------------------- fonts
def test_bundled_font_is_registered_and_preferred():
    """The bundled Liberation Mono wins over any system copy, so every machine
    draws the same glyphs."""
    fonts = os.path.join(os.path.dirname(ff.__file__), "fonts")
    for style in (dict(), dict(style="italic"), dict(weight="bold")):
        path = font_manager.findfont(font_manager.FontProperties(family="Liberation Mono", **style),
                                     fallback_to_default=False)
        assert os.path.dirname(path) == fonts
    assert mpl.rcParams["font.family"][0] == "Liberation Mono"
    assert mpl.rcParams["mathtext.fontset"] == "custom"
    assert mpl.rcParams["mathtext.it"] == "Liberation Mono:italic"


def test_font_override_and_fallback():
    state = ff.use("nature", font="DejaVu Sans")          # ships with matplotlib
    assert state["font"] == "DejaVu Sans"
    assert mpl.rcParams["font.family"] == ["DejaVu Sans", "sans-serif"]
    assert ff.use("acs", font="No Such Font 123")["font"] == "Liberation Mono"


def test_subscript_scale():
    from matplotlib import _mathtext
    try:
        ff.use("acs", subscript=0.8)
        assert _mathtext.SHRINK_FACTOR == 0.8
        ff.use("acs", subscript=None)                      # leaves it
        assert _mathtext.SHRINK_FACTOR == 0.8
    finally:
        ff.use("acs")
    assert _mathtext.SHRINK_FACTOR == 0.75


def test_style_sheet_without_use():
    plt.style.use("default")
    plt.style.use(ff.STYLE)
    assert mpl.rcParams["axes.linewidth"] == 0.6
    plt.style.use("default")
    plt.style.use("fairfig.fairfig")                     # package style, matplotlib >= 3.7
    assert mpl.rcParams["axes.linewidth"] == 0.6
    assert mpl.rcParams["axes.prop_cycle"].by_key()["color"][0].lower() == "#005b90"


# ---------------------------------------------------------------- figure sizes
def test_width():
    assert ff.width() == pytest.approx(84.6 * MM)
    assert ff.width("double", "nature") == pytest.approx(183.0 * MM)
    assert ff.width("onehalf", "elsevier") == pytest.approx(140.0 * MM)
    assert ff.width(70) == pytest.approx(70 * MM) and ff.width(70.5) == pytest.approx(70.5 * MM)
    ff.use("elsevier")
    assert ff.width() == pytest.approx(90.0 * MM)
    with pytest.raises(KeyError):
        ff.width("triple")


def test_figure_size():
    fig, ax = ff.figure()
    assert tuple(fig.get_size_inches()) == pytest.approx((84.6 * MM, 0.8 * 84.6 * MM))
    fig, ax = ff.figure("double", aspect=0.5)
    assert tuple(fig.get_size_inches()) == pytest.approx((177.8 * MM, 88.9 * MM))
    fig, ax = ff.figure(width=60, height=55)
    assert tuple(fig.get_size_inches()) == pytest.approx((60 * MM, 55 * MM))


def test_height_is_capped_at_the_journal_maximum():
    ff.use("nature")                                       # max height 170 mm
    fig, _ = ff.figure("single", aspect=3)
    assert fig.get_figheight() == pytest.approx(170 * MM)
    fig, _ = ff.figure("single", height=200)               # explicit height: not capped
    assert fig.get_figheight() == pytest.approx(200 * MM)
    ff.use("elsevier")                                     # no maximum known
    fig, _ = ff.figure("single", aspect=3)
    assert fig.get_figheight() == pytest.approx(270 * MM)


def test_subplots():
    fig, axs = ff.subplots(1, 2)                           # double width for two columns
    assert len(axs) == 2
    assert tuple(fig.get_size_inches()) == pytest.approx((177.8 * MM, 177.8 / 2 * 0.8 * MM))
    fig, axs = ff.subplots(2, 1)                           # single width, two panels high
    assert tuple(fig.get_size_inches()) == pytest.approx((84.6 * MM, 2 * 84.6 * 0.8 * MM))
    fig, axs = ff.subplots(2, 2, width="onehalf", aspect=1, sharex=True)
    assert axs.shape == (2, 2) and fig.get_figwidth() == pytest.approx(127.0 * MM)


def test_grid():
    fig, ax = ff.figure()
    fig.canvas.draw()
    major = [t.gridline for t in ax.xaxis.get_major_ticks()]
    minor = [t.gridline for t in ax.xaxis.get_minor_ticks()]
    assert all(g.get_visible() for g in major) and all(g.get_visible() for g in minor)
    assert mpl.colors.to_hex(major[0].get_color()) == "#e6e6e6"
    assert mpl.colors.to_hex(minor[0].get_color()) == "#f2f2f2"
    assert ax.get_axisbelow() is True
    ff.grid(ax, False)
    fig.canvas.draw()
    assert not any(t.gridline.get_visible() for t in ax.xaxis.get_major_ticks())
    assert not any(t.gridline.get_visible() for t in ax.yaxis.get_minor_ticks())


def test_no_grid_option():
    ff.use("acs", grid=False)
    fig, ax = ff.figure()
    fig.canvas.draw()
    assert not any(t.gridline.get_visible() for t in ax.xaxis.get_major_ticks())
