# fairfig

<p>
  <img src="assets/auspire-logo.png" alt="AuSpire" height="44">
  &nbsp;&nbsp;&nbsp;
  <img src="assets/eu-cofunded.png" alt="Co-funded by the European Union" height="44">
</p>

Colour-blind-safe, journal-ready matplotlib figures with one consistent visual identity.

![Two example panels drawn with fairfig: isothermal p–x–y data with an ordered colour ramp, and an x–y diagram for three systems](docs/preview.png)

- **Colour that works for everyone.** Okabe–Ito hues in an order computed for
  colour-vision deficiency, with the first three at distinct brightness levels, tested
  with a colour-blind reader; two alternative palettes one argument away; batlow/vik
  colour maps for ordered data; every series also carries a marker shape or line style.
- **Drawn at final size.** Exact column widths for ACS, Elsevier and Nature, one text
  size per figure, so nothing gets rescaled.
- **Conventions built in.** Experiment = markers, model = lines, filled/open markers for
  two phases or branches, grey open markers for literature data.
- **Export ready.** SVG with editable text plus PDF with embedded fonts; a built-in
  colour-blind and greyscale preview.
- **Nothing else to install.** The font (Liberation Mono) and colour maps are bundled;
  fairfig needs only numpy and matplotlib.

The full visual reference is [`docs/identity_sheet.pdf`](docs/identity_sheet.pdf).

## Install

```bash
pip install git+https://github.com/usosky/fairfig
```

or clone the repository and run `pip install -e .` in it. Requires Python ≥ 3.9,
numpy and matplotlib ≥ 3.7.

## Quick start

```python
import fairfig as ff
ff.use("acs")                     # or "elsevier", "nature"; palette="B" or "C"

fig, ax = ff.figure("single")     # exact column width; ff.subplots(1, 2) -> double
ax.plot(xm, Tm, **ff.curve(0), label="NRTL")                 # model = line
ax.plot(x,  T,  **ff.points(0), label="$x_1$")               # liquid = filled
ax.plot(y,  T,  **ff.points(0, hollow=True), label="$y_1$")  # vapour = open
ax.plot(xl, Tl, **ff.points(1, lit=True), label="Lit.")      # literature = grey
ff.fraction_axis(ax, "x")
ax.set(xlabel=ff.label("x_1, y_1"), ylabel=ff.label("T", "K"))
ff.legend(ax)                     # key above the plot; wraps to a 2nd row if needed
ff.save(fig, "figures/fig1")      # -> figures/fig1.svg + figures/fig1.pdf
```

Ordered series (isotherms, isobars, compositions) take a colour ramp instead of the
categorical colours:

```python
r = ff.ramp(len(T_list))                          # batlow, dark = low
ax.plot(x, p, **ff.points(k, color=r[k]))         # marker shape still follows k
```

[`examples/demo_phase_equilibria.py`](examples/demo_phase_equilibria.py) is a cookbook
with T–x–y, p–x–y, x–y, LLE, density, excess volume, deviation plots and colour maps;
its output is in [`examples/output/`](examples/output/).

## Identity rules

| | Rule |
|---|---|
| Colour | Okabe–Ito hues, fixed order: blue `#005B90`, vermillion `#BB4000`, bluish green `#009E73`, orange `#E69F00`, sky blue `#56B4E9`, reddish purple `#CC79A7` ([other palettes](#palettes)). Colour follows the entity through a whole paper (`ff.slots`). At most 6 per panel. |
| Ordered data | `batlow` (sequential), `vik` (diverging, centred at 0). Never jet/rainbow. |
| Marks | Experiment = two-tone markers, model = lines, filled/open = phase or branch, grey open = literature. Colour is never the only cue. |
| Neutrals | Black text, axes and reference model; `#808080` literature; `#B3B3B3` guides; grid `#E6E6E6` (major) / `#F2F2F2` (minor); yellow only for areas. |
| Type | Liberation Mono, one size (8 pt; 7 pt for Nature); quantities italic, units upright: `T/K`, `ρ/(kg·m⁻³)`. Bold panel labels a, b (Elsevier: (a)). No coloured text. |
| Layout | Draw at final width. Closed box, outward ticks, faint 0.5 pt grid, frameless legend on top. |
| Export | SVG (editable text) + PDF (fonts embedded as TrueType). |

Why these colours: slots 1–3 sit at three brightness levels (dark blue, mid
vermillion, lighter green; 1.3–2.1:1 between any two) and keep ≥ 3:1 contrast on
white, so they stay apart where hue is lost: colour-vision deficiency, small markers,
greyscale print. Under simulated deuteranopia/protanopia the worst separation stays
≥ 11 (OKLab ΔE×100) for up to five series; with six it drops to 7.5, so marker shapes
become mandatory. Blue and vermillion are darker than the published Okabe–Ito values
(`#0072B2`, `#D55E00`): a colour-blind reader found vermillion and green hard to tell
apart because they had the same brightness (1.13:1; now 1.60:1), and confirmed that
the new set takes no effort. Check any palette with `ff.check_palette()` (it also
prints the brightness ratio that online contrast checkers report) and any figure with
`ff.cvd_preview(fig)`.

Switches: `ff.use(palette="B")`, `ticks="in"`, `frame="open"`, `grid=False`,
`units="paren"` (`T (K)`), `font="Arial"`, `fontsize=…`. Per axes: `ff.grid(ax, False)`
(e.g. on colour maps), `ff.legend(ax, loc="upper right")`. Other formats:
`ff.save(fig, "fig1.tif")` (600 dpi, RGB).

### Palettes

Choose one per paper with `ff.use("acs", palette="B")`; marker shapes, line styles and
everything else stay the same.

| `palette=` | Slots 1–6 | Use it for |
|---|---|---|
| `"A"` (default) | `#005B90` `#BB4000` `#009E73` `#E69F00` `#56B4E9` `#CC79A7` | everything new: the fairfig colours above |
| `"B"` | `#0072B2` `#D55E00` `#009E73` `#E69F00` `#56B4E9` `#CC79A7` | fairfig 1.0: published Okabe–Ito values in fairfig's order; finishing figures started with 1.0 |
| `"C"` | `#E69F00` `#56B4E9` `#009E73` `#0072B2` `#D55E00` `#CC79A7` | Okabe–Ito in its published order, the most widely recommended colour-blind-safe palette |

C leaves out Okabe–Ito's black (fairfig keeps black for text and models) and yellow
(1.3:1 on white, too faint for lines; `ff.C.yellow` is for areas). Its first two colours
are light (2.3:1 on white) and equally bright, so A and B hold up better in greyscale.
Long names work too: `"fairfig"`, `"fairfig-1.0"`, `"okabe-ito"`. `ff.C.vermillion` and
the other hue names return that hue in the active palette; `ff.check_palette("C")` and
`ff.swatches("C")` describe any palette, and
[`examples/output/`](examples/output/) has a card for each (`palette_card*.svg`).

## Journal presets

| preset | single | 1.5 column | double | text | notes |
|---|---|---|---|---|---|
| `acs` | 84.6 mm | 127 mm | 177.8 mm | 8 pt | ≤ 240 pt / 504 pt wide, text ≥ 4.5 pt, lines ≥ 0.5 pt |
| `elsevier` | 90 mm | 140 mm | 190 mm | 8 pt | 7 pt text, sub/superscripts ≥ 6 pt |
| `nature` | 89 mm | 120 mm | 183 mm | 7 pt | 5–7 pt, max height 170 mm, sans-serif only: use `font="Arial"` |

Submit the PDF: ACS and Elsevier accept PDF but do not list SVG. Keep the SVG for
editing. Sub/superscripts are drawn at 0.75× (matplotlib uses 0.7×) so they stay
≥ 6 pt with 8 pt text.

To edit the SVGs in CorelDRAW, Inkscape or Illustrator with the same face, install
the four `.ttf` files in `fairfig/fonts` on your system. Without them, viewers fall
back to Courier New, which has the same letter widths.

## API

`use` · `figure` · `subplots` · `points` · `curve` · `ramp` · `cmap` · `slots` ·
`label` · `legend` · `panel_labels` · `end_label` · `fraction_axis` · `grid` ·
`diagonal` · `hline` · `vline` · `band` · `ticks_out` · `colorbar` · `save` ·
`cvd_preview` · `check_palette` · `swatches` · `simulate` · `tint` · `ink`

Constants: `C`, `COLORS`, `INK`, `NAMES`, `PALETTES`, `MARKERS`, `LINESTYLES`, `JOURNALS`,
`ERRORBAR`.
Style file only: `plt.style.use(ff.STYLE)`.

## Cite

GitHub's "Cite this repository" button gives APA and BibTeX from
[`CITATION.cff`](CITATION.cff). Archived on Zenodo (DOI added at the first release).

> Usosky, D., Latasa López, J. C., Novoa Colas, V., Belbasis, A., Martín Martín, J. A.,
> García Algaba, A., & Rahim, A. (2026). *fairfig: colour-blind-safe, journal-ready
> matplotlib figures* (Version 1.2.0) [Computer software].
> https://github.com/usosky/fairfig

## Authors

**Denis Usosky**¹\*, **Juan Carlos Latasa López**¹, **Valery Novoa Colas**¹,
**Aaron Belbasis**², **Juan Alberto Martín Martín**¹, **Ana García Algaba**¹ and
**Abdul Rahim**¹

¹ IDOM Consulting, Engineering, Architecture S.A.U., Bilbao, Spain<br>
² Aurecon Australasia Pty Ltd, Melbourne, VIC, Australia<br>
\* Corresponding author

ORCID iDs: [Denis Usosky](https://orcid.org/0000-0002-6245-5110),
[Juan Carlos Latasa López](https://orcid.org/0009-0004-9312-544X),
[Valery Novoa Colas](https://orcid.org/0009-0009-7567-8012),
[Juan Alberto Martín Martín](https://orcid.org/0000-0002-5158-0709).

Developed within the AuSpire project (Marie Skłodowska-Curie Actions, Grant Agreement
No 101177949).

## Licence

MIT © 2026 Denis Usosky — see [`LICENSE`](LICENSE). Bundled third-party material keeps
its own licence: Liberation Mono (SIL Open Font License 1.1) and the batlow/vik colour
maps by Fabio Crameri (MIT). Details in [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).
Logos in `assets/` are not covered by these licences. Release notes are in
[`CHANGELOG.md`](CHANGELOG.md).

## Acknowledgements

Co-funded by the European Union under the Marie Skłodowska-Curie Grant Agreement
No 101177949 (AuSpire). Views and opinions expressed are however those of the author(s)
only and do not necessarily reflect those of the European Union or the Research Executive
Agency. Neither the European Union nor the granting authority can be held responsible
for them.

We thank IDOM Consulting, Engineering, Architecture S.A.U. for supporting this work, and
our colleagues at IDOM and Aurecon for their collaboration within AuSpire. Thanks also
to [Lander Laparra](https://gravatar.com/nightagile2dc1fd9bba) for testing the colours,
which shaped the default palette, and to Petro Pavliuchenko for his support. The
monospace look, faint grid, legend on top and two-tone markers follow the first author's
earlier style based on [BeautifulFigures](https://github.com/AndreyChurkin/BeautifulFigures)
by A. Churkin.

## References

- Okabe, M. & Ito, K. (2008) *Color Universal Design*; Wong, B. (2011) Points of view: Color blindness, *Nat. Methods* 8, 441.
- Crameri, F., Shephard, G. E. & Heron, P. J. (2020) The misuse of colour in science communication, *Nat. Commun.* 11, 5444.
- Machado, G. M., Oliveira, M. M. & Fernandes, L. A. F. (2009) A physiologically-based model for simulation of color vision deficiency, *IEEE TVCG* 15, 1291.
- Nature research figure guide; ACS and Elsevier author and artwork guidelines.
