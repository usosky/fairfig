"""Figure snapshots: pytest-mpl compares each figure with a baseline image.

    pytest --mpl              compare (as CI does)
    pytest                    draw the figures without comparing

Baselines are per FreeType version, see tests/baseline/README.md. A test that
fails writes the baseline, the new image and their difference to the folder
given by --mpl-results-path (CI uploads it as an artifact).
"""
import pytest

import fairfig as ff
import figures
from helpers import BASELINE_DIR, MPL


def snapshot(tolerance=1.0):
    """Compare with this FreeType's baseline (RMS tolerance on 0-255 pixels).
    Matplotlib 3.8-3.10 render pixel-identically; 3.7 differs by < 0.7 except
    in contour maps. A colour change of one slot gives about 1.2-2.8, a 10 %
    bigger marker 6-13, a moved legend about 30."""
    return pytest.mark.mpl_image_compare(baseline_dir=BASELINE_DIR, style="default",
                                         tolerance=tolerance, savefig_kwargs={"dpi": 100})


# ---------------------------------------------------------------- cookbook recipes
@snapshot()
def test_txy():
    ff.use("acs")
    return figures.txy()


@snapshot()
def test_pxy_and_xy():
    ff.use("acs")
    return figures.pxy_and_xy()


@snapshot()
def test_lle():
    ff.use("acs")
    return figures.lle()


@snapshot()
def test_density_and_excess_volume():
    ff.use("acs")
    return figures.density_and_excess_volume()


@snapshot()
def test_deviations():
    ff.use("acs")
    return figures.deviations()


# matplotlib 3.8 changed how contour sets are drawn (RMS 5.3 against 3.7)
@snapshot(tolerance=6.0 if MPL < (3, 8) else 1.0)
def test_maps():
    ff.use("acs")
    return figures.maps()


# ---------------------------------------------------------------- options
@snapshot()
def test_all_slots():
    ff.use("acs")
    return figures.all_slots()


@snapshot()
def test_all_slots_okabe_ito():
    ff.use("acs", palette="okabe-ito")
    return figures.all_slots()


@snapshot()
def test_errorbars_open_frame_legend_right():
    ff.use("acs", frame="open")
    return figures.errorbars()


@snapshot()
def test_nature_preset():
    ff.use("nature")
    return figures.txy()


@snapshot()
def test_elsevier_inward_ticks_paren_units():
    ff.use("elsevier", ticks="in", units="paren")
    return figures.pxy_and_xy()


# ---------------------------------------------------------------- checks
@snapshot()
def test_swatches():
    ff.use("acs")
    return ff.swatches()


@snapshot()
def test_swatches_okabe_ito():
    ff.use("acs")
    return ff.swatches("okabe-ito")


@snapshot()
def test_cvd_preview():
    ff.use("acs")
    return ff.cvd_preview(figures.cvd_source(), dpi=100, ncols=5)
