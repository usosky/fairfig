# %% README images -> docs/preview.png, gallery.png, palettes.png, cvd_check.png
# Re-runs the cookbook without writing its files, rasterises its figures and
# draws the palette and colour-vision cards. Run again after changing the identity.
import io
import os
import runpy
import sys

import matplotlib.pyplot as plt
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
import fairfig as ff

DOCS = os.path.join(ROOT, "docs")
os.makedirs(DOCS, exist_ok=True)


def raster(fig, height_px):
    """Figure -> RGB image of the given pixel height."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=height_px / fig.get_figheight())
    buf.seek(0)
    return Image.open(buf).convert("RGB")


# %% 1. Cookbook figures, captured instead of saved
figs = {}


def _capture(fig, path, *args, **kwargs):
    figs[os.path.basename(path)] = fig
    return []


_save = ff.save
ff.save = _capture
try:
    runpy.run_path(os.path.join(HERE, "demo_phase_equilibria.py"), run_name="__main__")
finally:
    ff.save = _save

figs["fig2_Pxy_xy"].savefig(os.path.join(DOCS, "preview.png"), dpi=200)

# %% 2. Gallery: four cookbook figures at one common scale (single + double per row)
W, GAP = 1600, 24
rows = [["fig1_Txy", "fig4_density_VE"], ["fig6_maps", "fig3_LLE"]]
dpi = (W - GAP) / sum(figs[n].get_figwidth() for n in rows[0])
tiles = [[raster(figs[n], round(figs[n].get_figheight() * dpi)) for n in row] for row in rows]
row_h = [max(im.height for im in r) for r in tiles]
gallery = Image.new("RGB", (W, sum(row_h) + GAP * (len(rows) - 1)), "white")
draw = ImageDraw.Draw(gallery)
y = 0
for r, h in zip(tiles, row_h):
    x = 0
    for im in r:
        yy = y + (h - im.height) // 2                     # centre shorter figures
        gallery.paste(im, (x, yy))
        draw.rectangle([x, yy, x + im.width - 1, yy + im.height - 1], outline="#D9D9D9")
        x += im.width + GAP
    y += h + GAP
gallery.save(os.path.join(DOCS, "gallery.png"), optimize=True)

# %% 3. The two palettes in normal vision, with CVD and in greyscale
ff.use("acs")
views = [("normal", "Normal vision"), ("deutan", "Deuteranopia"),
         ("protan", "Protanopia"), ("gray", "Greyscale")]
labels = {"fairfig": ("fairfig", "default"), "okabe-ito": ("Okabe–Ito", "published order")}
W_MM, H_MM = 177.8, 28.5                          # card size, mm
x0, gap_view, s, gap_sw, pitch, top = 36.0, 3.6, 4.6, 0.86, 10.0, 8.0
fig = plt.figure(figsize=(W_MM / 25.4, H_MM / 25.4), layout="none")
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, W_MM)
ax.set_ylim(H_MM, 0)
ax.set_axis_off()
cell = 6 * s + 5 * gap_sw
for j, (kind, title) in enumerate(views):
    ax.text(x0 + j * (cell + gap_view) + cell / 2, top - 3.2, title, ha="center",
            va="center", fontsize=7, color="#555555")
for r, (key, d) in enumerate(ff.PALETTES.items()):
    y = top + r * pitch
    name, note = labels[key]
    ax.text(1.5, y + s / 2 - 0.9, name, va="center", fontsize=8, fontweight="bold")
    ax.text(1.5, y + s / 2 + 2.3, note, va="center", fontsize=6.5, color="#555555")
    for j, (kind, _) in enumerate(views):
        for i, c in enumerate(d["colors"]):
            xx = x0 + j * (cell + gap_view) + i * (s + gap_sw)
            ax.add_patch(plt.Rectangle((xx, y), s, s, lw=0,
                                       color=c if kind == "normal" else ff.simulate(c, kind)))
fig.savefig(os.path.join(DOCS, "palettes.png"), dpi=200)

# %% 4. What ff.cvd_preview(fig) shows, on the x-y diagram of three systems
d = {}
exec(open(os.path.join(HERE, "_example_data.py")).read(), d)     # xm, xe, YM, YE, S
fig, ax = ff.figure(width=70, height=70)          # square panel, little white space
ff.diagonal(ax)
for name, i in d["S"].items():
    ax.plot(d["xm"], d["YM"][name], **ff.curve(i))
    ax.plot(d["xe"], d["YE"][name], **ff.points(i), label=name)
ff.fraction_axis(ax, "x")
ff.fraction_axis(ax, "y")
ax.set_aspect("equal")
ax.set(xlabel=ff.label("x_1"), ylabel=ff.label("y_1"))
ff.legend(ax)
prev = ff.cvd_preview(fig, kinds=[k for k, _ in views], dpi=120, ncols=4)
prev.savefig(os.path.join(DOCS, "cvd_check.png"), dpi=120)
plt.close("all")
print("wrote", ", ".join(f"docs/{n}.png" for n in ("preview", "gallery", "palettes", "cvd_check")))
