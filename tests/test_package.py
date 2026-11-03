"""Release metadata agree with each other, and the package ships its files."""
import json
import os
import re

import fairfig as ff
from helpers import ROOT


def read(name):
    with open(os.path.join(ROOT, name), encoding="utf-8") as fh:
        return fh.read()


def test_citation_has_this_version():
    m = re.search(r"^version: *([\w.]+) *$", read("CITATION.cff"), re.M)
    assert m and m.group(1) == ff.__version__, "update version (and date-released) in CITATION.cff"


def test_changelog_has_this_version():
    assert re.search(rf"^## {re.escape(ff.__version__)}\b", read("CHANGELOG.md"), re.M)


def test_zenodo_creators_match_citation_authors():
    creators = [c["name"] for c in json.loads(read(".zenodo.json"))["creators"]]
    cff = read("CITATION.cff").split("\ncontact:")[0]
    authors = [f"{f.strip()}, {g.strip()}" for f, g in
               re.findall(r"family-names: (.+)\n\s+given-names: (.+)", cff)]
    assert creators == authors


def test_public_functions_are_documented():
    for name in ff.__all__:
        obj = getattr(ff, name)
        if callable(obj):
            assert (obj.__doc__ or "").strip(), name


def test_package_files():
    """Fonts, style sheet, licences and the typing marker are installed with the package."""
    pkg = os.path.dirname(ff.__file__)
    fonts = sorted(f for f in os.listdir(os.path.join(pkg, "fonts")) if f.endswith(".ttf"))
    assert fonts == ["LiberationMono-Bold.ttf", "LiberationMono-BoldItalic.ttf",
                     "LiberationMono-Italic.ttf", "LiberationMono-Regular.ttf"]
    for f in ("fairfig.mplstyle", "py.typed", "LICENSE_crameri_colormaps.txt",
              os.path.join("fonts", "LICENSE_LiberationMono_OFL.txt")):
        assert os.path.isfile(os.path.join(pkg, f)), f
    assert ff.STYLE == os.path.join(pkg, "fairfig.mplstyle")
