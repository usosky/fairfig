# Third-party components

fairfig's own code is released under the MIT licence (see `LICENSE`). The repository
also contains the following third-party material, each under its own terms.

| Component | Location | Licence | Copyright |
|---|---|---|---|
| Liberation Mono 2.1.5 (Regular, Bold, Italic, Bold Italic), unmodified | `fairfig/fonts/` | SIL Open Font License 1.1 — `fairfig/fonts/LICENSE_LiberationMono_OFL.txt` | © 2010 Google Corporation; © 2012 Red Hat, Inc. (Reserved Font Name "Liberation") |
| batlow and vik colour maps (Scientific colour maps v8, as distributed in cmcrameri) | `fairfig/_cmapdata.py` | MIT — `fairfig/LICENSE_crameri_colormaps.txt` | © 2020 Fabio Crameri |
| AuSpire logo and EU emblem "Co-funded by the European Union" | `assets/` | Not licensed for reuse; shown as required for EU-funded projects (see `assets/README.md`) | AuSpire project; European Union |

Please cite the colour maps when you use them: Crameri, F. (2018) Scientific colour maps,
Zenodo, doi:10.5281/zenodo.1243862; Crameri, F., Shephard, G. E. & Heron, P. J. (2020)
The misuse of colour in science communication, *Nat. Commun.* 11, 5444.

The categorical colours are based on the Okabe–Ito palette (Okabe, M. & Ito, K. (2008)
*Color Universal Design*; Wong, B. (2011) *Nat. Methods* 8, 441): the `okabe-ito`
palette uses its published values, and the default `fairfig` palette darkens its blue
and vermillion. The colour-vision-deficiency simulation uses the matrices of Machado,
Oliveira & Fernandes (2009) *IEEE TVCG* 15, 1291.
