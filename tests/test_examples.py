"""Every script in examples/ runs and writes its files. The scripts run in a
temporary copy, so the repository's examples/output/ and docs/ stay untouched."""
import os
import runpy
import shutil
import sys

import matplotlib.pyplot as plt
import pytest

from helpers import ROOT

EXAMPLES = os.path.join(ROOT, "examples")
SCRIPTS = sorted(f for f in os.listdir(EXAMPLES) if f.endswith(".py") and not f.startswith("_"))
COOKBOOK = ["fig1_Txy", "fig2_Pxy_xy", "fig3_LLE", "fig4_density_VE", "fig5_deviations",
            "fig6_maps", "palette_card", "palette_card_okabe-ito"]
WRITES = {
    "quickstart.py": ["examples/output/quickstart.svg", "examples/output/quickstart.pdf"],
    "journals.py": [f"examples/output/journal_{j}.pdf" for j in ("acs", "elsevier", "nature")],
    "check_colours.py": ["examples/output/check_colours.svg", "examples/output/check_colours_cvd.png"],
    "demo_phase_equilibria.py": [f"examples/output/{n}.{e}" for n in COOKBOOK for e in ("svg", "pdf")],
    "make_readme_images.py": [f"docs/{n}.png" for n in ("preview", "gallery", "palettes", "cvd_check")]
                             + ["docs/img/quickstart.png", "docs/img/fig6_maps.png"],
    "make_identity_sheet.py": ["docs/identity_sheet.pdf"],
}


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    """A copy of examples/ with room for docs/ next to it, as in the repository."""
    shutil.copytree(EXAMPLES, tmp_path / "examples",
                    ignore=shutil.ignore_patterns("output", "__pycache__"))
    monkeypatch.setattr(plt, "show", lambda *args, **kwargs: None)
    monkeypatch.setattr(sys, "path", list(sys.path))     # the scripts insert their parent folder
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_every_example_is_checked():
    assert sorted(WRITES) == SCRIPTS


@pytest.mark.parametrize("script", SCRIPTS)
def test_example_runs(sandbox, script):
    runpy.run_path(str(sandbox / "examples" / script), run_name="__main__")
    for rel in WRITES[script]:
        assert (sandbox / rel).stat().st_size > 1000, rel
