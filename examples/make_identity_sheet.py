# %% Build the 2-page identity sheet (A4) -> docs/identity_sheet.pdf
import itertools
import os
import sys
import textwrap

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
import fairfig as ff

ff.use("acs")
mpl.rcParams["figure.constrained_layout.use"] = False   # manual mm layout on the sheet
MM = 1 / 25.4
PT = 25.4 / 72                         # mm per point
W, H = 210, 297                        # A4 portrait, mm
X0, X1 = 15, 195                       # text column
GREY = "#555555"


def cw(size):
    """Character width in mm for the monospaced face at `size` pt."""
    return 0.6 * size * PT


class Page:
    """A4 page with a millimetre coordinate system (origin top-left)."""

    def __init__(self, n, subtitle):
        self.fig = plt.figure(figsize=(W * MM, H * MM), layout="none")
        bg = self.fig.add_axes([0, 0, 1, 1])
        bg.set_xlim(0, W)
        bg.set_ylim(H, 0)
        bg.set_axis_off()
        bg.set_autoscale_on(False)
        self.bg = bg
        self.text(X0, 16, "Figure identity", size=17, weight="bold", va="baseline")
        self.text(X1, 16, f"fairfig {ff.__version__} · page {n}/2", size=7,
                  color=GREY, ha="right", va="baseline")
        self.line(X0, 20.5, X1, 20.5, lw=0.8)
        self.para(X0, 26, subtitle, size=7.5, color=GREY)

    def text(self, x, y, s, size=7, **kw):
        d = dict(va="center", ha="left", fontsize=size)
        d.update(kw)
        return self.bg.text(x, y, s, **d)

    def para(self, x, y, s, width=X1 - X0, size=7, lh=1.5, bullet=False, **kw):
        """Wrapped paragraph (monospace -> exact wrapping). Returns next y."""
        n = int(width // cw(size)) - (2 if bullet else 0)
        for k, line in enumerate(textwrap.wrap(s, n)):
            pre = ("• " if k == 0 else "  ") if bullet else ""
            self.text(x, y + k * size * lh * PT, pre + line, size=size, **kw)
        return y + (k + 1) * size * lh * PT

    def rect(self, x, y, w, h, color, **kw):
        d = dict(lw=0)
        d.update(kw)
        self.bg.add_patch(mpl.patches.Rectangle((x, y), w, h, facecolor=color, **d))

    def line(self, x0, y0, x1, y1, color="black", lw=0.6, **kw):
        self.bg.plot([x0, x1], [y0, y1], color=color, lw=lw, solid_capstyle="butt", **kw)

    def mark(self, x, y, **kw):
        self.bg.plot([x], [y], **kw)

    def gradient(self, x, y, w, h, colors):
        arr = np.asarray([mpl.colors.to_rgb(c) for c in colors])[None, :, :]
        self.bg.imshow(arr, extent=(x, x + w, y + h, y), aspect="auto", interpolation="bilinear")

    def heading(self, y, num, s):
        self.text(X0, y, f"{num}", size=9.5, weight="bold", color=ff.C.blue)
        self.text(X0 + 6, y, s, size=9.5, weight="bold")
        return y + 6

    def axes(self, x, y, w, h):
        """Real matplotlib axes at 1:1; (x, y) = top-left of the frame in mm."""
        return self.fig.add_axes([x / W, 1 - (y + h) / H, w / W, h / H])


KINDS = ["normal", "deutan", "protan", "tritan", "gray"]
KTXT = ["Normal", "Deutan", "Protan", "Tritan", "Grey"]

# =============================================================================
# PAGE 1 - colour
# =============================================================================
p = Page(1, "Colour-blind-safe identity for all papers: Okabe-Ito categorical colours, "
            "batlow/vik for ordered data, Liberation Mono, SVG + PDF export.")

# ---- 1. categorical ------------------------------------------------------------
y = p.heading(37, 1, "Categorical colours - fixed order, colour follows the entity")
cols = dict(slot=X0, mk=21, name=33, fill=62, ink=75, cr=88)
for k, lab in (("slot", "#"), ("mk", "Mark"), ("name", "Name"), ("fill", "Fill"),
               ("ink", "Edge"), ("cr", "White")):
    p.text(cols[k], y, lab, size=6.5, color=GREY)
sx, sw, sg = 100, 16, 2
for j, t in enumerate(KTXT):
    p.text(sx + j * (sw + sg) + sw / 2, y, t, size=6.5, color=GREY, ha="center")
long_names = {"green": "bluish green", "sky": "sky blue", "purple": "reddish purple"}
for i, (name, c, ik) in enumerate(zip(ff.NAMES, ff.COLORS, ff.INK)):
    yy = y + 6 + i * 7.5
    p.text(cols["slot"], yy, f"{i + 1}", size=8, weight="bold")
    p.mark(cols["mk"] + 1.5, yy, **ff.points(i, size=6))
    p.mark(cols["mk"] + 7, yy, **ff.points(i, size=6, hollow=True))
    p.text(cols["name"], yy, long_names.get(name, name), size=7.5, weight="bold")
    p.text(cols["fill"], yy, c.upper(), size=7)
    p.text(cols["ink"], yy, ik.upper(), size=7)
    cr = ff._contrast(c)
    p.text(cols["cr"], yy, f"{cr:.1f}", size=7, color="black" if cr >= 3 else ff.C.vermillion)
    for j, kind in enumerate(KINDS):
        p.rect(sx + j * (sw + sg), yy - 2.8, sw, 5.6, ff.simulate(c, kind))
y = y + 6 + 6 * 7.5
worst = {k: min(min(ff._dE(a, b, "deutan"), ff._dE(a, b, "protan"))
                for a, b in itertools.combinations(ff.COLORS[:k], 2)) for k in range(2, 7)}
w35 = (f"k = 3-5: {worst[3]:.1f}" if f"{worst[3]:.1f}" == f"{worst[5]:.1f}"
       else f"k = 3: {worst[3]:.1f}, 4: {worst[4]:.1f}, 5: {worst[5]:.1f}")
bright = [ff._contrast(a, b) for a, b in itertools.combinations(ff.COLORS[:3], 2)]
y = p.para(X0, y, "White = contrast against white (≥ 3 is the ACS rule for graphics; red "
                  "values rely on the dark edge + marker shape). Slots 1-3 also differ in "
                  f"brightness ({min(bright):.2f}-{max(bright):.2f}:1 between any two), so they "
                  "stay apart when hue is lost. Worst separation within the first k slots, "
                  "OKLab ΔE×100 under deutan/protan simulation (Machado 2009): "
                  f"k = 2: {worst[2]:.1f}, {w35}, k = 6: {worst[6]:.1f}. Six series need "
                  "distinct marker shapes; more than six: split the panel or use a ramp. "
                  "Alternatives: ff.use(palette='B' or 'C').",
           size=6.8)

# ---- 2. neutrals ------------------------------------------------------------------
y = p.heading(y + 5, 2, "Neutrals and reserved colours")
neutrals = [("black", ff.C.black, "text, axes, model"),
            ("grey_dk", ff.C.grey_dk, "2nd model, notes"),
            ("grey", ff.C.grey, "literature data"),
            ("grey_lt", ff.C.grey_lt, "guides: y=x, 0"),
            ("grid", ff.C.grid, "major grid, bands"),
            ("grid_minor", ff.C.grid_minor, "minor grid"),
            ("yellow", ff.C.yellow, "areas only")]
colw = (X1 - X0) / len(neutrals)
for j, (n, c, role) in enumerate(neutrals):
    x = X0 + j * colw
    p.rect(x, y - 1, colw - 2.5, 7, c, **({"edgecolor": "#CCCCCC", "lw": 0.4}
                                          if c in (ff.C.grid, ff.C.grid_minor) else {}))
    p.text(x, y + 9, n, size=6.5, weight="bold")
    p.text(x, y + 12.5, c.upper(), size=6.3)
    p.text(x, y + 16, role, size=6, color=GREY)
y += 22

# ---- 3. ordered -------------------------------------------------------------------
y = p.heading(y + 3, 3, "Ordered data - sequential and diverging (Crameri colour maps)")
bat = [mpl.colors.to_hex(ff.cmap("seq")(t)) for t in np.linspace(0, 1, 256)]
vik = [mpl.colors.to_hex(ff.cmap("div")(t)) for t in np.linspace(0, 1, 256)]
gx, gw = 55, X1 - 55


def cmap_block(y, title, sub, cols_):
    p.text(X0, y + 2.5, title, size=8, weight="bold")
    p.text(X0, y + 6.5, sub, size=6.3, color=GREY)
    p.gradient(gx, y, gw, 6.5, cols_)
    for j, (kind, t) in enumerate(zip(KINDS[1:], KTXT[1:])):
        yy = y + 8.2 + j * 3.4
        p.gradient(gx, yy, gw, 2.6, [ff.simulate(c, kind) for c in cols_])
        p.text(gx - 1.5, yy + 1.3, t, size=5.8, color=GREY, ha="right")
    return y + 8.2 + 4 * 3.4 + 2


y = cmap_block(y, "batlow", "ff.cmap('seq')", bat)
for n in (3, 5):
    r = ff.ramp(n)
    p.text(X0, y + 2, f"ff.ramp({n})", size=7)
    for k, c in enumerate(r):
        x = gx + k * 28
        p.line(x, y + 2, x + 10, y + 2, color=c, lw=1.0)
        p.mark(x + 5, y + 2, **ff.points(k, color=c, size=5))
        p.text(x + 11.5, y + 2, c.upper(), size=5.8, color=GREY)
    y += 6
p.text(X0, y + 1, "for isotherms, isobars, compositions: dark = low", size=6.3, color=GREY)
y = cmap_block(y + 6, "vik", "ff.cmap('div'), centre 0", vik)
y = p.para(X0, y + 2, "Never jet/rainbow: uneven lightness invents features and fails with "
                      "colour-vision deficiency and in greyscale.", size=6.8)

# ---- 4. why ------------------------------------------------------------------------
y = p.heading(y + 5, 4, "Why these choices")
why = [
    "Okabe-Ito (Okabe & Ito 2008; Wong, Nat. Methods 8, 441, 2011) is the accessible palette "
    "cited by the Nature figure guide; about 8% of men of N-European ancestry have red-green "
    "colour-vision deficiency.",
    "Slot order computed, not guessed: it maximises the worst-case CVD separation while "
    "slots 1-3 keep >= 3:1 contrast on white. Blue and vermillion are darker than published "
    "Okabe-Ito (#0072B2, #D55E00): a colour-blind reader found vermillion and green hard to "
    "tell apart at equal brightness (1.13:1; now 1.60:1, confirmed effortless).",
    "Liberation Mono (free, SIL OFL, bundled) keeps the BeautifulFigures monospace look with "
    "Courier's letter widths. Elsevier names Courier among its standard fonts; ACS recommends "
    "Arial/Helvetica but only sets a 4.5 pt minimum; Nature requires sans-serif "
    "(ff.use('nature', font='Arial')).",
    "Faint grid and outward ticks come from BeautifulFigures; grid lines are 0.5 pt (ACS "
    "minimum line weight) in very light grey so they stay under the data.",
    "batlow/vik (Crameri, Shephard & Heron, Nat. Commun. 11, 5444, 2020) are perceptually "
    "uniform and stay readable with CVD and in greyscale.",
    "Two-tone markers (fill + darker edge of the same hue) keep light hues visible on white.",
]
for s in why:
    y = p.para(X0 + 1, y, s, width=X1 - X0 - 1, size=6.8, bullet=True) + 1
p.text(X0, 289, "Set in Liberation Mono. Install the bundled TTFs (fairfig/fonts) on Windows "
                "to edit the SVGs with the same face.", size=6, color=GREY)
page1 = p.fig

# =============================================================================
# PAGE 2 - marks, type, layout, export
# =============================================================================
p = Page(2, "Colour never works alone: every series also has a marker shape or line "
            "style, so figures survive greyscale print and colour-vision deficiency.")

# ---- 5. marks ------------------------------------------------------------------------
y = p.heading(37, 5, "Marks")
rows = [("Experiment", "ff.points(i)", "filled: liquid x1, phase I"),
        ("2nd phase", "ff.points(i, hollow=True)", "open: vapour y1, phase II"),
        ("Literature", "ff.points(i, lit=True)", "grey, under your data")]
for r_, (t, code, note) in enumerate(rows):
    yy = y + 1 + r_ * 6.5
    p.text(X0, yy, t, size=7, weight="bold")
    p.text(38, yy, code, size=6.3, color=GREY)
    for i in range(6):
        kw = dict(size=6)
        if r_ == 1:
            kw["hollow"] = True
        if r_ == 2:
            kw["lit"] = True
        p.mark(100 + i * 8, yy, **ff.points(i, **kw))
    p.text(150, yy, note, size=6, color=GREY)
yy = y + 1 + 3 * 6.5
p.text(X0, yy, "Model", size=7, weight="bold")
p.text(38, yy, "ff.curve(i, style=s)", size=6.3, color=GREY)
for s_, lab in enumerate(["solid", "dashed", "dash-dot", "dotted"]):
    x = 100 + s_ * 12.5
    p.bg.plot([x, x + 9], [yy, yy], **ff.curve(None, style=s_))
p.text(150, yy, "1 model: series colour", size=6, color=GREY)
p.text(150, yy + 3.2, "several: black, styles", size=6, color=GREY)
yy += 8
p.text(X0, yy, "Guides", size=7, weight="bold")
p.text(38, yy, "ff.diagonal, ff.hline, ff.band", size=6.3, color=GREY)
p.line(100, yy + 2.2, 110, yy - 2.2, color=ff.C.grey_lt)
p.text(112, yy, "y=x", size=6, color=GREY)
p.line(121, yy, 131, yy, color=ff.C.grey_lt)
p.text(133, yy, "0", size=6, color=GREY)
p.rect(150, yy - 2.2, 12, 4.4, ff.C.grey_xlt)
p.text(163.5, yy, "±u", size=6, color=GREY)
p.rect(172, yy - 2.2, 12, 4.4, ff.tint(ff.C.blue, 0.10))
p.text(185.5, yy, "2-phase", size=6, color=GREY)
y = yy + 7

# ---- 6. type -----------------------------------------------------------------------------
y = p.heading(y + 2, 6, "Type and axis labels")
y = p.para(X0, y, "Liberation Mono, one size for all text (8 pt ACS/Elsevier, 7 pt Nature preset); "
                  "hierarchy by weight: panel labels bold, 1 pt larger. Quantities italic, "
                  "units upright, IUPAC T/K (units='paren' gives T (K)); unit factors joined "
                  "by a middle dot. Black text only.", size=6.8) + 1.5
examples = [(("T", "K"), 'label("T", "K")'),
            (("p", "kPa"), 'label("p", "kPa")'),
            (("x_1, y_1",), 'label("x_1, y_1")'),
            ((r"\rho", "kg m^-3"), 'label(r"\\rho", "kg m^-3")'),
            (("u", "m s^-1"), 'label("u", "m s^-1")'),
            ((r"\eta", "mPa s"), 'label(r"\\eta", "mPa s")')]
for k, (args, code) in enumerate(examples):
    col, row = divmod(k, 3)
    x, yy = X0 + col * 92, y + 1 + row * 6
    p.text(x, yy, ff.label(*args), size=8)
    p.text(x + 27, yy, "ff." + code, size=6.3, color=GREY)
y += 1 + 3 * 6
p.text(X0, y + 1, "a  b  c", size=9, weight="bold")
p.text(X0 + 17, y + 1, "ff.panel_labels(axes): above the frame, top-left "
                       "(Elsevier preset: (a), (b))", size=6.3, color=GREY)
y += 7

# ---- 7. layout & export --------------------------------------------------------------------
y = p.heading(y + 2, 7, "Layout and export - draw at final size, never rescale")
hdr = ["preset", "single", "1.5 col", "double", "text", "max h"]
xs = [X0, 45, 63, 80, 99, 111]
for x, t in zip(xs, hdr):
    p.text(x, y, t, size=6.3, color=GREY)
for r_, (j, d) in enumerate(ff.JOURNALS.items()):
    yy = y + 5 + r_ * 4.6
    vals = [f'use("{j}")', f"{d['single']:.1f}", f"{d['onehalf']:.0f}", f"{d['double']:.1f}",
            f"{d['font']:.0f} pt", f"{d['max_height']:.0f}" if d["max_height"] else "-"]
    for x, v in zip(xs, vals):
        p.text(x, yy, v, size=6.5)
p.text(X0, y + 5 + 3 * 4.6, "widths and heights in mm", size=6, color=GREY)
consts = ["closed box, ticks out (left/bottom)", "faint grid: major + minor, 0.5 pt",
          "legend on top: ff.legend(ax)", "lines 1.0 pt, axes 0.6 pt",
          "markers 4 pt, edge 0.6 pt", "export: SVG (editable) + PDF"]
for k, s in enumerate(consts):
    p.text(125, y + k * 4.1, s, size=6.3)
y = y + 6 * 4.1 + 2
y = p.para(X0, y, "Submit the PDF (ACS and Elsevier do not take SVG); keep the SVG for "
                  "editing in a vector editor.",
           size=6.3, color=GREY)

# ---- 8. example at 1:1 ------------------------------------------------------------------------
y = p.heading(y + 4, 8, "At 1:1 - two ACS single-column figures (84.6 x 67.7 mm)")
exec(open(os.path.join(HERE, "_example_data.py")).read())   # xm, Tm, ym, xe, Te, ye, ...


def draw_txy(ax):
    ax.plot(xm, Tm, **ff.curve(0), label="NRTL")
    ax.plot(ym, Tm, **ff.curve(0))
    ax.plot(xe, Te, **ff.points(0), label="$x_1$")
    ax.plot(ye, Te, **ff.points(0, hollow=True), label="$y_1$")
    ax.plot(xl, Tl + 0.5, **ff.points(1, lit=True), label="Lit.")
    ff.fraction_axis(ax, "x")
    ax.set(xlabel=ff.label("x_1, y_1"), ylabel=ff.label("T", "K"))
    h, l = ax.get_legend_handles_labels()
    ff.legend(ax, [h[k] for k in (1, 2, 0, 3)], [l[k] for k in (1, 2, 0, 3)])


def draw_xy(ax):
    ff.diagonal(ax)
    for name, i in S.items():
        ax.plot(xm, YM[name], **ff.curve(i))
        ax.plot(xe, YE[name], **ff.points(i), label=name)
    ff.fraction_axis(ax, "x")
    ff.fraction_axis(ax, "y")
    ax.set_aspect("equal")
    ax.set(xlabel=ff.label("x_1"), ylabel=ff.label("y_1"))
    ff.legend(ax)


def place_1to1(draw, x0, y0, letter):
    """Lay the figure out exactly as ff.figure('single') would, then redraw it
    on the sheet at the same position and size."""
    with mpl.rc_context({"figure.constrained_layout.use": True}):
        f, a = ff.figure("single")
        draw(a)
        ff.panel_labels([a], [letter])
        f.canvas.draw()
        pos = a.get_position()
        fw, fh = f.get_size_inches() / MM
        plt.close(f)
    p.rect(x0, y0, fw, fh, "none", edgecolor="#BBBBBB", lw=0.4, ls=(0, (2, 2)))
    ax = p.axes(x0 + pos.x0 * fw, y0 + (1 - pos.y1) * fh, pos.width * fw, pos.height * fh)
    ff.grid(ax)
    draw(ax)
    ff.panel_labels([ax], [letter])
    return fw, fh


fw, fh = place_1to1(draw_txy, X0, y, "a")
place_1to1(draw_xy, X1 - fw, y, "b")
y += fh + 4

# ---- 9. workflow ----------------------------------------------------------------------------------
y = p.heading(y + 2, 9, "Workflow")
code = ['import fairfig as ff; ff.use("acs")      # once per notebook',
        'fig, ax = ff.figure("single")           # or ff.subplots(1, 2)',
        'ax.plot(x, T, **ff.points(0)); ax.plot(xm, Tm, **ff.curve(0))',
        'ax.set(xlabel=ff.label("x_1"), ylabel=ff.label("T", "K")); ff.legend(ax)',
        'ff.save(fig, "figures/fig1")            # -> fig1.svg + fig1.pdf']
for k, s in enumerate(code):
    p.text(X0 + 2, y + k * 4.1, s.replace("  ", "  "), size=6.5)
page2 = p.fig

# ---- export ----------------------------------------------------------------------------------------
os.makedirs(os.path.join(ROOT, "docs"), exist_ok=True)
out = os.path.join(ROOT, "docs", "identity_sheet.pdf")
with PdfPages(out, metadata={"Title": "Figure identity (fairfig)",
                             "Creator": f"fairfig {ff.__version__}"}) as pdf:
    pdf.savefig(page1)
    pdf.savefig(page2)
print("wrote", out)
