"""Test setup: a non-interactive backend, the default identity before every
test, and no settings or figures left behind."""
import os

import matplotlib

matplotlib.use("Agg")

import matplotlib as mpl  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import pytest  # noqa: E402

import fairfig as ff  # noqa: E402
from helpers import BASELINE_DIR, FREETYPE  # noqa: E402


@pytest.fixture(autouse=True)
def identity():
    """Every test starts from ff.use("acs"); matplotlib settings are restored
    afterwards. (Snapshot tests call ff.use themselves: pytest-mpl resets the
    style before it runs them.)"""
    with mpl.rc_context():
        ff.use("acs")
        yield
    plt.close("all")


def pytest_collection_modifyitems(config, items):
    """Skip image comparison where no baselines exist for this FreeType version
    (e.g. a matplotlib built against the system FreeType), unless the run must
    compare (FAIRFIG_REQUIRE_BASELINES=1, as in CI)."""
    comparing = config.getoption("--mpl", False) and not config.getoption("--mpl-generate-path", None)
    if not comparing or os.path.isdir(BASELINE_DIR):
        return
    msg = (f"no baseline images for FreeType {FREETYPE} (matplotlib {mpl.__version__}) in "
           f"{BASELINE_DIR}; see tests/baseline/README.md")
    if os.environ.get("FAIRFIG_REQUIRE_BASELINES"):
        raise pytest.UsageError(msg)
    skip = pytest.mark.skip(reason=msg)
    for item in items:
        if item.get_closest_marker("mpl_image_compare"):
            item.add_marker(skip)
