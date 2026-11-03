"""Axis labels, legends and panel labels."""
import pytest
from matplotlib.mathtext import MathTextParser

import fairfig as ff


@pytest.mark.parametrize("args, expected", [
    (("T", "K"), r"$T\,/\,\mathrm{K}$"),
    (("p", "kPa"), r"$p\,/\,\mathrm{kPa}$"),
    (("x_1",), r"$x_1$"),
    (("x_1, y_1",), r"$x_1, y_1$"),
    ((r"\rho", "kg m^-3"), "$\\rho\\,/\\,(\\mathrm{kg}·\\mathrm{m}^{-3})$"),
    (("u", "m s^-1"), "$u\\,/\\,(\\mathrm{m}·\\mathrm{s}^{-1})$"),
    ((r"\eta", "mPa s"), "$\\eta\\,/\\,(\\mathrm{mPa}·\\mathrm{s})$"),
    (("w", "%"), r"$w\,/\,\mathrm{\%}$"),
    (("$T$", "K"), r"$T\,/\,\mathrm{K}$"),
    (("Temperature", "K"), "Temperature / K"),
    (("Mole fraction",), "Mole fraction"),
    (("T", ""), "$T$"),
])
def test_label(args, expected):
    out = ff.label(*args)
    assert out == expected
    if "$" in out:
        MathTextParser("path").parse(out[out.index("$"):out.rindex("$") + 1])   # valid mathtext


def test_label_paren_style():
    assert ff.label("T", "K", style="paren") == "$T$ (K)"
    assert ff.label(r"\rho", "kg m^-3", style="paren") == "$\\rho$ ($\\mathrm{kg}·\\mathrm{m}^{-3}$)"
    ff.use("acs", units="paren")
    assert ff.label("T", "K") == "$T$ (K)"


@pytest.mark.parametrize("unit", ["kg m^-3", "kg·m^-3", "kg*m^-3", "kg m^{-3}", "kg m^−3"])
def test_unit_spellings(unit):
    assert ff._unit_tex(unit) == "$\\mathrm{kg}·\\mathrm{m}^{-3}$"


def test_unit_with_several_powers():
    assert ff._unit_tex("J mol^-1 K^-1") == "$\\mathrm{J}·\\mathrm{mol}^{-1}·\\mathrm{K}^{-1}$"


# ---------------------------------------------------------------- legend
def ncols(legend):
    return getattr(legend, "_ncols", getattr(legend, "_ncol", None))


def test_legend_on_top_reads_row_by_row():
    fig, ax = ff.figure("double")
    for k, name in enumerate("abcde"):
        ax.plot([0, 1], [k, k], label=name)
    leg = ff.legend(ax, ncol=3)
    # matplotlib fills columns first; fairfig reorders so rows read a b c / d e
    assert [t.get_text() for t in leg.get_texts()] == ["a", "d", "b", "e", "c"]
    assert ncols(leg) == 3 and leg.get_frame_on() is False


def test_legend_fits_the_panel_width():
    labels = ["first series", "second series", "third series", "fourth series"]
    wide, ax_w = ff.figure("double")
    narrow, ax_n = ff.figure(width=50)
    for ax in (ax_w, ax_n):
        for k, name in enumerate(labels):
            ax.plot([0, 1], [k, k], label=name)
    assert ncols(ff.legend(ax_w)) == 4                      # one row
    assert ncols(ff.legend(ax_n)) < 4


def test_legend_sits_above_the_axes():
    fig, ax = ff.figure()
    ax.plot([0, 1], [0, 1], label="data")
    leg = ff.legend(ax)
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    assert leg.get_window_extent(r).y0 >= ax.get_window_extent(r).y1 - 1


def test_legend_options():
    fig, ax = ff.figure()
    assert ff.legend(ax) is None                            # nothing labelled
    h1, = ax.plot([0, 1], label="one")
    h2, = ax.plot([1, 0], label="two")
    leg = ff.legend(ax, [h2, h1], ["two", "one"])
    assert [t.get_text() for t in leg.get_texts()] == ["two", "one"]
    assert ff.legend(ax, loc="right").get_bbox_to_anchor() is not None
    inside = ff.legend(ax, loc="upper right")
    assert ncols(inside) == 1 and inside.get_frame_on() is False


# ---------------------------------------------------------------- panel labels
def test_panel_labels():
    fig, axs = ff.subplots(1, 2)
    for ax in axs:
        ax.set_ylabel("y")
    a, b = ff.panel_labels(axs)
    assert (a.get_text(), b.get_text()) == ("a", "b")
    assert a.get_fontweight() == "bold" and a.get_fontsize() == 9.0
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    assert a.get_window_extent(r).y0 >= axs[0].get_window_extent(r).y1 - 1   # above the frame


def test_panel_label_styles():
    ff.use("elsevier")
    fig, axs = ff.subplots(1, 3)
    assert [t.get_text() for t in ff.panel_labels(axs)] == ["(a)", "(b)", "(c)"]
    assert [t.get_text() for t in ff.panel_labels(axs, ["x", "y", "z"], style="a")] == ["x", "y", "z"]
    t = ff.panel_labels(axs[0], loc="inside")[0]
    assert t.get_ha() == "left" and t.get_va() == "top"


def test_panel_labels_for_a_figure_skip_colour_bars():
    fig, axs = ff.subplots(1, 2)
    m = axs[0].pcolormesh([[0, 1], [2, 3]])
    ff.colorbar(m, axs[0])
    assert [t.get_text() for t in ff.panel_labels(fig)] == ["a", "b"]
