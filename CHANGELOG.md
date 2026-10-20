# Changelog

## 1.2.0 — 2026-10-20

First release on GitHub.

- Palettes: the 1.1 colours stay the default (`"fairfig"`); the colour-blind reader
  confirmed that they take no effort to tell apart. `ff.use(palette="okabe-ito")`
  switches to Okabe–Ito in its published order, without black and yellow.
- `ff.PALETTES` lists both; `check_palette()` and `swatches()` take a palette name;
  `ff.C.<hue>` returns that hue in the active palette. The cookbook also writes
  `palette_card_okabe-ito`.
- `band()` is transparent, so the grid shows through two-phase regions and uncertainty
  bands; `along="y"` shades between two x limits (liquid-liquid regions).
- `cvd_preview(fig, ncols=...)` lays the views out in one row if asked.
- Shorter README with pictures: `examples/make_readme_images.py` makes
  `docs/preview.png`, `gallery.png`, `palettes.png` and `cvd_check.png`.
- Authors, citation and funding: seven authors from IDOM and Aurecon with ORCID iDs and
  affiliations in `CITATION.cff` and `.zenodo.json`; the README acknowledges them, the
  AuSpire project (Marie Skłodowska-Curie Grant Agreement No 101177949, with the AuSpire
  logo and the EU emblem in `assets/`), IDOM's support, Lander Laparra and
  Petro Pavliuchenko.

## 1.1.0 — 2026-10-02

**Colours changed.** Figures made with 1.0 will look different; to keep one paper
consistent, finish it with 1.0.0.

- Blue `#0072B2` → `#005B90` and vermillion `#D55E00` → `#BB4000` (both darker).
  A colour-blind reader could tell vermillion and bluish green apart only with
  effort: the two had the same brightness (ratio 1.13:1). Slots 1–3 now sit at
  three brightness levels: blue–vermillion 1.33:1, vermillion–green 1.60:1,
  blue–green 2.12:1. Green, orange, sky blue and reddish purple are unchanged.
- No worst case got worse. Worst separation under simulated deuteranopia/protanopia
  (OKLab ΔE×100): slots 1–5 11.0 → 11.2, all six 7.5 (unchanged). Tritanopia,
  slots 1–5: 8.4 → 11.3. Normal vision, all six: 15.6 → 18.4. The only pair that
  moved closer is blue–vermillion, which stays far apart (≥ 18.7).
- A lighter green, the reader's suggestion, was tested and not used: it fixes
  vermillion–green but then green matches sky blue (tritanopia), orange
  (protanopia) and reddish purple (deuteranopia) in brightness and hue.
- `check_palette()` also prints each pair's brightness ratio (the WCAG luminance
  ratio that online contrast checkers report) and flags pairs that are close under
  colour-vision deficiency and have the same brightness.

## 1.0.0 — 2026-09-23

First release.
