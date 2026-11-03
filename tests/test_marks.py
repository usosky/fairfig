"""Markers, lines, guides, bands, axes helpers and colour bars."""
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.colors import to_hex, to_rgba

import fairfig as ff


# ---------------------------------------------------------------- points / curve
@pytest.mark.parametrize("i", range(6))
def test_points_use_slot_colour_and_marker(i):
    d = ff.points(i)
    assert d["marker"] == ff.MARKERS[i] and d["color"] == ff.COLORS[i]
    assert d["markerfacecolor"] == ff.COLORS[i] and d["markeredgecolor"] == ff.INK[i]
    assert d["markeredgewidth"] == 0.6 and d["linestyle"] == "none" and d["zorder"] == 3
    assert d["markersize"] == pytest.approx(4.0 * ff._MSCALE[ff.MARKERS[i]])


def test_points_variants():
    h = ff.points(1, hollow=True)
    assert h["markerfacecolor"] == "white" and h["markeredgecolor"] == ff.ink(ff.COLORS[1], 0.07)
    assert h["markeredgewidth"] == pytest.approx(0.84)
    lit = ff.points(2, lit=True)
    assert lit["color"] == ff.C.grey and lit["markerfacecolor"] == "white"
    assert lit["marker"] == "^" and lit["zorder"] < 3 and lit["markeredgewidth"] == pytest.approx(0.75)
    assert ff.points(0, lit=True, color="#123456")["markeredgecolor"] == "#123456"
    r = ff.points(3, color="#ABCDEF")
    assert r["color"] == "#abcdef" and r["marker"] == "D"           # shape still follows i
    assert ff.points(0, marker="*", size=5)["markersize"] == pytest.approx(5 * 1.35)
    k = ff.points(0, zorder=10, label="x", linestyle="-")
    assert k["zorder"] == 10 and k["label"] == "x" and k["linestyle"] == "-"


def test_points_beyond_six_slots():
    with pytest.raises(IndexError, match="ff.ramp"):
        ff.points(6)
    assert ff.points(6, color="#000000")["marker"] == ff.MARKERS[0]  # colour given: fine


def test_curve():
    d = ff.curve(1)
    assert d["color"] == ff.COLORS[1] and d["linestyle"] == "-" and d["linewidth"] == 1.0
    assert d["marker"] == "none" and d["zorder"] == 2
    assert [ff.curve(0, style=s)["linestyle"] for s in range(6)] == ["-", "--", "-.", ":", "-", "--"]
    assert ff.curve(None)["color"] == ff.C.black
    assert ff.curve(None, color="red")["color"] == "#ff0000"
    assert ff.curve(0, lw=2)["linewidth"] == 2
    with pytest.raises(IndexError):
        ff.curve(7)


def test_marks_draw_as_specified():
    fig, ax = ff.figure()
    (pt,) = ax.plot([0, 1], [0, 1], **ff.points(2, hollow=True))
    (ln,) = ax.plot([0, 1], [1, 0], **ff.curve(2, style=1))
    assert pt.get_marker() == "^" and pt.get_linestyle() == "None"
    assert to_hex(pt.get_markerfacecolor()) == "#ffffff"
    assert ln.get_linestyle() == "--" and to_hex(ln.get_color()) == ff.COLORS[2].lower()
    eb = ax.errorbar([0, 1], [1, 2], yerr=0.1, **ff.points(0), **ff.ERRORBAR)
    assert eb.lines[2][0].get_linewidth() == ff.ERRORBAR["elinewidth"]


# ---------------------------------------------------------------- guides and bands
def test_guides():
    fig, ax = ff.figure()
    d = ff.diagonal(ax)
    h = ff.hline(ax, 0.5)
    v = ff.vline(ax, 0.2, color="red")
    for line in (d, h):
        assert to_hex(line.get_color()) == ff.C.grey_lt.lower() and line.get_zorder() == 1
    assert to_hex(v.get_color()) == "#ff0000"
    assert h.get_ydata()[0] == 0.5 and v.get_xdata()[0] == 0.2


def test_band_colours():
    fig, ax = ff.figure()
    grey = ff.band(ax, [0, 1], -1, 1)
    slot = ff.band(ax, [0, 1], -1, 1, i=0)
    own = ff.band(ax, [0, 1], -1, 1, color="red", amount=0.3)
    assert grey.get_alpha() == pytest.approx(0.20) and slot.get_alpha() == pytest.approx(0.18)
    assert own.get_alpha() == pytest.approx(0.3)
    assert to_hex(slot.get_facecolor()[0]) == ff.COLORS[0].lower()
    assert grey.get_zorder() < 1                                    # under the grid guides


def test_band_on_white_looks_like_tint():
    """alpha over white = tint(colour, alpha); the grey band matches the grid colour."""
    for c, a in ((ff.COLORS[0], 0.18), (ff.C.grey, 0.20)):
        rgb = np.array(to_rgba(c)[:3])
        assert to_hex(a * rgb + (1 - a)) == ff.tint(c, a)
    assert ff.tint(ff.C.grey, 0.20) == ff.C.grid.lower()


def test_band_along_y():
    fig, ax = ff.figure()
    T = np.linspace(280, 330, 5)
    band = ff.band(ax, T, np.full(5, 0.2), np.full(5, 0.6), i=0, along="y")
    xy = band.get_paths()[0].vertices
    assert xy[:, 0].min() == pytest.approx(0.2) and xy[:, 0].max() == pytest.approx(0.6)
    assert xy[:, 1].min() == pytest.approx(280) and xy[:, 1].max() == pytest.approx(330)


# ---------------------------------------------------------------- axes helpers
def test_fraction_axis():
    fig, ax = ff.figure()
    ff.fraction_axis(ax, "x")
    ff.fraction_axis(ax, "y", major=0.25, minor=0.05)
    fig.canvas.draw()
    assert ax.get_xlim() == (0, 1) and ax.get_ylim() == (0, 1)
    def inside(locs):
        return [v for v in locs if -1e-9 <= v <= 1 + 1e-9]

    assert np.allclose(inside(ax.get_xticks()), np.arange(0, 1.01, 0.2))
    assert np.allclose(inside(ax.get_yticks()), np.arange(0, 1.01, 0.25))
    assert np.allclose(inside(ax.xaxis.get_minorticklocs()), np.arange(0.1, 1.0, 0.2))
    labels = {round(t.get_position()[0], 2): t.get_text() for t in ax.get_xticklabels()}
    assert (labels[0.0], labels[0.2], labels[1.0]) == ("0.0", "0.2", "1.0")


def test_ticks_out():
    ff.use("acs", ticks="in")
    fig, ax = ff.figure()
    ff.ticks_out(ax)
    fig.canvas.draw()
    assert ax.xaxis.get_tick_params(which="major")["direction"] == "out"
    ticks = ax.xaxis.get_major_ticks() + ax.yaxis.get_minor_ticks()
    assert not any(t.tick2line.get_visible() for t in ticks)     # none on top or right
    assert all(t.tick1line.get_visible() for t in ticks)


def test_end_label():
    fig, ax = ff.figure()
    a = ff.end_label(ax, 1.0, 2.0, "0.25", dx=5)
    assert a.get_text() == "0.25" and a.xy == (1.0, 2.0)
    assert a.get_fontsize() == 8.0 and a.get_ha() == "left"


def test_colorbar():
    fig, ax = ff.figure()
    m = ax.pcolormesh(np.arange(12).reshape(3, 4), cmap=ff.cmap())
    cb = ff.colorbar(m, label="value")
    assert cb.ax.get_ylabel() == "value"
    assert cb.outline.get_linewidth() == pytest.approx(0.6)
    assert len(cb.ax.yaxis.get_minorticklocs()) == 0
    with pytest.raises(ValueError, match="pass ax="):
        ff.colorbar(mpl.cm.ScalarMappable(cmap=ff.cmap()))
    assert ff.colorbar(mpl.cm.ScalarMappable(cmap=ff.cmap()), ax=ax) is not None
    plt.close(fig)
