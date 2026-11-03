"""ff.save() and the colour-blind preview."""
import re

import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.colors import to_hex
from matplotlib.patches import Rectangle
from PIL import Image

import fairfig as ff

PT = 72 / 25.4      # points per mm


@pytest.fixture
def fig():
    f, ax = ff.figure()
    ax.plot([0, 1], [0, 1], **ff.points(0), label="data")
    ax.set(xlabel=ff.label("x_1"), ylabel=ff.label("T", "K"))
    ff.legend(ax)
    return f


def test_svg_and_pdf_by_default(fig, tmp_path):
    written = ff.save(fig, tmp_path / "new" / "folder" / "fig1")
    assert [p[-8:] for p in written] == ["fig1.svg", "fig1.pdf"]
    assert all((tmp_path / "new" / "folder" / f"fig1.{e}").stat().st_size > 1000 for e in ("svg", "pdf"))


def test_extension_picks_one_format(fig, tmp_path):
    assert ff.save(fig, tmp_path / "f.png") == [str(tmp_path / "f.png")]
    assert ff.save(fig, tmp_path / "g.SVG") == [str(tmp_path / "g.svg")]
    assert ff.save(fig, tmp_path / "h", formats=(".PDF", "png"))[-1].endswith("h.png")


def test_exact_journal_size(fig, tmp_path):
    svg, pdf = ff.save(fig, tmp_path / "f")
    with open(svg, encoding="utf-8") as fh:
        s = fh.read()
    w, h = (float(v) for v in re.search(r'width="([\d.]+)pt" height="([\d.]+)pt"', s).groups())
    assert (w, h) == pytest.approx((84.6 * PT, 0.8 * 84.6 * PT), abs=0.01)
    with open(pdf, "rb") as fh:
        box = [float(v) for v in re.search(rb"/MediaBox \[([^\]]+)\]", fh.read()).group(1).split()]
    assert box[2:] == pytest.approx([84.6 * PT, 0.8 * 84.6 * PT], abs=0.01)


def test_svg_has_live_text_with_font_fallback(fig, tmp_path):
    with open(ff.save(fig, tmp_path / "f.svg")[0], encoding="utf-8") as fh:
        s = fh.read()
    assert "<text" in s                                    # editable text, not paths
    decls = re.findall(r"font(?:-family)?: [^;\"]*'Liberation Mono'[^;\"]*", s)
    assert decls and all(d.endswith("'Liberation Mono', 'Courier New', monospace") for d in decls)
    assert f"fairfig {ff.__version__}" in s


def test_svg_fallback_for_a_sans_serif_font(fig, tmp_path):
    ff.use("nature", font="DejaVu Sans")
    f, ax = ff.figure()
    ax.set_xlabel("x")
    with open(ff.save(f, tmp_path / "f.svg")[0], encoding="utf-8") as fh:
        s = fh.read()
    assert "'DejaVu Sans', 'Arial', sans-serif" in s


def test_pdf_embeds_truetype(fig, tmp_path):
    with open(ff.save(fig, tmp_path / "f.pdf")[0], "rb") as fh:
        pdf = fh.read()
    assert b"/FontFile2" in pdf and b"LiberationMono" in pdf      # Type 42: editable text
    assert f"fairfig {ff.__version__}".encode() in pdf


def test_png_and_tiff(fig, tmp_path):
    png = ff.save(fig, tmp_path / "f.png", dpi=100)[0]
    with Image.open(png) as im:
        assert im.size == (round(84.6 / 25.4 * 100), round(0.8 * 84.6 / 25.4 * 100))
    tif = ff.save(fig, tmp_path / "f.tif", dpi=300)[0]
    with Image.open(tif) as im:
        assert im.mode == "RGB" and im.info.get("compression") == "tiff_lzw"
        assert tuple(round(float(v)) for v in im.info["dpi"]) == (300, 300)


def test_cvd_copy(fig, tmp_path):
    assert ff.save(fig, tmp_path / "f", cvd=True)[-1].endswith("f_cvd.svg")
    assert ff.save(fig, tmp_path / "g.tif", dpi=100, cvd=True)[-1].endswith("g_cvd.png")


# ---------------------------------------------------------------- preview
def test_cvd_preview_layout(fig):
    prev = ff.cvd_preview(fig, dpi=100)
    titles = [ax.get_title() for ax in prev.axes]
    assert titles == ["Normal vision", "Deuteranopia", "Protanopia", "Tritanopia",
                      "Greyscale (luminance)"]
    w = fig.get_figwidth()
    assert prev.get_figwidth() == pytest.approx(3 * round(w * 100) / 100, abs=0.02)   # 3 per row
    one_row = ff.cvd_preview(fig, kinds=("normal", "deutan"), dpi=100, ncols=2)
    assert len(one_row.axes) == 2


def test_cvd_preview_shows_simulated_colours():
    f = plt.figure(figsize=(0.5, 0.5), layout="none")
    ax = f.add_axes((0, 0, 1, 1))
    ax.set_axis_off()
    ax.add_patch(Rectangle((0, 0), 1, 1, color=ff.C.vermillion, transform=ax.transAxes))
    prev = ff.cvd_preview(f, kinds=("normal", "deutan"), dpi=40, ncols=2)
    normal, deutan = (np.asarray(a.images[0].get_array()) for a in prev.axes)
    assert to_hex(normal[10, 10]) == ff.C.vermillion.lower()
    assert to_hex(deutan[10, 10]) == ff.simulate(ff.C.vermillion, "deutan")
