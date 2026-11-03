"""Shared constants for the tests."""
import os

import matplotlib as mpl
from matplotlib import ft2font

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MPL = tuple(int(v) for v in mpl.__version__.split(".")[:2])

# Text rendering depends on the FreeType that matplotlib is built with
# (2.6 up to matplotlib 3.10, 2.14 from 3.11), so baselines are kept per
# FreeType major.minor version.
FREETYPE = ".".join(ft2font.__freetype_version__.split(".")[:2])
BASELINE_DIR = os.path.join(HERE, "baseline", f"freetype-{FREETYPE}")
