# Saving

```python
ff.save(fig, "figures/fig1")              # figures/fig1.svg + figures/fig1.pdf
ff.save(fig, "figures/fig1.png")          # one format, from the extension
ff.save(fig, "figures/fig1", formats=("pdf", "tif"))
ff.save(fig, "figures/fig1", cvd=True)    # also fig1_cvd.svg: the colour-blind check
```

`ff.save` keeps the designed size (no tight bounding box, which would change the
width), creates missing folders and returns the paths it wrote.

| Format | What you get | Use it for |
|---|---|---|
| PDF | vector, TrueType fonts embedded (Type 42): text stays text | submission (ACS and Elsevier do not take SVG) |
| SVG | vector, live text | editing in Inkscape, Illustrator, Affinity |
| PNG | raster at 600 dpi (`dpi=` to change) | slides, web |
| TIFF | raster, RGB, LZW-compressed, 600 dpi | journals that ask for TIFF |
| EPS | vector | journals that ask for EPS |

The files carry `fairfig <version>` as their creator.

## Fonts in SVG files

An SVG names its fonts instead of embedding them. fairfig adds a fallback with the
same letter widths to every font declaration
(`'Liberation Mono', 'Courier New', monospace`), so the layout holds in an editor that
does not have Liberation Mono. To edit with the same face, install the four TTF files
from the `fonts` folder of the package:

```python
import fairfig as ff, os
print(os.path.join(os.path.dirname(ff.__file__), "fonts"))
```

## Draw at the final size

Never scale a figure after saving it: the text would no longer be 7 or 8 pt, and thin
lines could drop below the 0.5 pt that ACS asks for. Change the size with
`ff.figure(width=..., aspect=...)` instead, and let the layout engine fit the labels.
