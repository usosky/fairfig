"""Palettes, colour maths, colour maps and the colour-vision checks."""
import itertools

import matplotlib as mpl
import numpy as np
import pytest
from matplotlib.colors import to_hex, to_rgb

import fairfig as ff
from fairfig import COLORS, INK, NAMES


def worst_dE(colors, kinds):
    return min(ff._dE(a, b, k) for a, b in itertools.combinations(colors, 2) for k in kinds)


# ---------------------------------------------------------------- palettes
def test_palettes_share_six_named_hues():
    names = {key: set(p["names"]) for key, p in ff.PALETTES.items()}
    assert set(ff.PALETTES) == {"fairfig", "okabe-ito"}
    for p in ff.PALETTES.values():
        assert len(p["colors"]) == len(p["names"]) == 6
    assert names["fairfig"] == names["okabe-ito"]      # so ff.C.<hue> always exists


def test_default_palette_is_active():
    assert COLORS == ["#005B90", "#BB4000", "#009E73", "#E69F00", "#56B4E9", "#CC79A7"]
    assert NAMES == ["blue", "vermillion", "green", "orange", "sky", "purple"]
    assert ff.C.blue == "#005B90" and ff.C.vermillion == "#BB4000"
    assert [to_hex(c) for c in mpl.rcParams["axes.prop_cycle"].by_key()["color"]] == \
        [c.lower() for c in COLORS]


def test_palette_switch_changes_lists_in_place():
    colors, names, ink = COLORS, NAMES, INK               # as after "from fairfig import ..."
    ff.use("acs", palette="okabe-ito")
    assert colors is ff.COLORS and names is ff.NAMES and ink is ff.INK
    assert colors == ff.PALETTES["okabe-ito"]["colors"]
    assert names[0] == "orange" and ff.C.blue == "#0072B2" and ff.C.vermillion == "#D55E00"
    assert ink == [ff.ink(c) for c in colors]
    assert mpl.rcParams["axes.prop_cycle"].by_key()["color"][0] in ("#E69F00", "#e69f00")
    ff.use("acs")
    assert colors == ff.PALETTES["fairfig"]["colors"] and ff.C.blue == "#005B90"


@pytest.mark.parametrize("spelling", ["okabe-ito", "Okabe-Ito", "okabe_ito", " OKABE ITO "])
def test_palette_names_are_forgiving(spelling):
    assert ff.use("acs", palette=spelling)["palette"] == "okabe-ito"


def test_unknown_palette_changes_nothing():
    mpl.rcParams["font.size"] = 11
    with pytest.raises(ValueError, match="palette must be one of"):
        ff.use("acs", palette="rainbow")
    assert mpl.rcParams["font.size"] == 11                # failed before touching settings


def test_reserved_colours_do_not_follow_the_palette():
    reserved = {k: getattr(ff.C, k) for k in ("yellow", "black", "grey", "grey_lt", "grid")}
    ff.use("acs", palette="okabe-ito")
    assert {k: getattr(ff.C, k) for k in reserved} == reserved


# ---------------------------------------------------------------- documented numbers
def test_brightness_levels_of_slots_1_to_3():
    """CHANGELOG 1.1.0: blue-vermillion 1.33:1, vermillion-green 1.60:1, blue-green 2.12:1."""
    blue, vermillion, green = COLORS[:3]
    assert round(ff._contrast(blue, vermillion), 2) == 1.33
    assert round(ff._contrast(vermillion, green), 2) == 1.60
    assert round(ff._contrast(blue, green), 2) == 2.12


def test_cvd_separation_matches_the_changelog():
    """CHANGELOG 1.1.0: worst deutan/protan separation 11.2 (slots 1-5), 7.5 (all six);
    tritanopia, slots 1-5: 11.3; normal vision, all six: 18.4 (OKLab dE x 100)."""
    assert round(worst_dE(COLORS[:5], ["deutan", "protan"]), 1) == 11.2
    assert round(worst_dE(COLORS, ["deutan", "protan"]), 1) == 7.5
    assert round(worst_dE(COLORS[:5], ["tritan"]), 1) == 11.3
    assert round(worst_dE(COLORS, ["normal"]), 1) == 18.4


def test_marker_edges_reach_3_to_1_on_white():
    for fill, edge in zip(COLORS, INK):
        assert ff._contrast(edge) >= 3.0
        assert ff._luminance(edge) < ff._luminance(fill)


def test_ink_known_values():
    assert INK == ["#013455", "#7c2800", "#066f50", "#ae7809", "#2288bb", "#9e4f7c"]


def test_contrast_matches_wcag():
    assert ff._contrast("#000000") == pytest.approx(21.0)
    assert ff._contrast("#FFFFFF") == pytest.approx(1.0)
    assert ff._contrast("#777777") == pytest.approx(4.48, abs=0.01)   # WCAG's own example
    assert ff._contrast("#FFFFFF", "#000000") == ff._contrast("#000000", "#FFFFFF")


def test_tint():
    assert ff.tint("#BB4000", 0) == "#ffffff"
    assert ff.tint("#BB4000", 1) == "#bb4000"
    assert ff.tint("#000000", 0.18) == to_hex((0.82, 0.82, 0.82))


def test_ink_stays_in_gamut_for_saturated_colours():
    for c in ["#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#F0E442"]:
        r, g, b = to_rgb(ff.ink(c))
        assert 0 <= min(r, g, b) and max(r, g, b) <= 1
        assert ff._luminance(ff.ink(c)) < ff._luminance(c)


# ---------------------------------------------------------------- slots, ramps, maps
def test_slots():
    S = ff.slots(["A + B", "A + C", "A + D"])
    assert S == {"A + B": 0, "A + C": 1, "A + D": 2}
    assert ff.slots({"x": 1, "y": 2}) == {"x": 0, "y": 1}       # dict keys, in order
    with pytest.raises(ValueError, match="identity colours"):
        ff.slots("ABCDEFG")


def test_ramp_is_dark_to_light_and_capped():
    r = ff.ramp(5)
    assert len(r) == 5 and r[0] == to_hex(ff.cmap("seq")(0.0))
    assert r[-1] == to_hex(ff.cmap("seq")(0.72))                # light end capped
    lum = [ff._luminance(c) for c in r]
    assert lum == sorted(lum)
    assert ff.ramp(5, reverse=True) == r[::-1]
    assert ff.ramp(3, cmap="vik", lo=0.1, hi=0.9)[1] == to_hex(mpl.colormaps["vik"](0.5))


def test_colour_maps():
    assert ff.cmap().name == "batlow" and ff.cmap("seq").N == 256
    assert ff.cmap("div").name == "vik"
    assert ff.cmap("viridis").name == "viridis"
    for name in ("batlow", "batlow_r", "vik", "vik_r"):
        assert name in mpl.colormaps
    assert mpl.rcParams["image.cmap"] == "batlow"


def test_colour_maps_register_once():
    ff._register_cmaps()                                           # no "already registered" error


# ---------------------------------------------------------------- simulation
@pytest.mark.parametrize("kind", ["normal", "deutan", "protan", "tritan", "gray", "grey"])
def test_simulate_keeps_black_and_white(kind):
    assert ff.simulate("#FFFFFF", kind) == "#ffffff"
    assert ff.simulate("#000000", kind) == "#000000"


def test_simulate_known_value():
    assert ff.simulate("#BB4000", "deutan") == "#837400"
    assert ff.simulate((187 / 255, 64 / 255, 0.0), "deutan") == ff.simulate("#BB4000", "deutan")


def test_simulate_images_keep_their_shape():
    rng = np.random.default_rng(0)
    img = rng.random((4, 5, 3))
    for kind in ("deutan", "protan", "tritan", "gray"):
        out = ff.simulate(img, kind)
        assert out.shape == (4, 5, 3) and out.min() >= 0 and out.max() <= 1
    np.testing.assert_allclose(ff.simulate(img, "normal"), img)
    rgba = np.concatenate([img, np.ones((4, 5, 1))], axis=-1)
    assert ff.simulate(rgba, "deutan").shape == (4, 5, 3)              # alpha dropped
    grey = ff.simulate(img, "gray")
    np.testing.assert_allclose(grey[..., 0], grey[..., 2])


def test_simulated_pixels_match_simulated_colours():
    img = np.array([[to_rgb("#BB4000"), to_rgb("#009E73")]])
    out = ff.simulate(img, "protan")
    assert [to_hex(p) for p in out[0]] == [ff.simulate("#BB4000", "protan"),
                                           ff.simulate("#009E73", "protan")]


# ---------------------------------------------------------------- reports
def test_check_palette_report(capsys):
    rep = ff.check_palette()
    out = capsys.readouterr().out
    assert len(rep["colors"]) == 6 and len(rep["pairs"]) == 15
    hexes = [row[0] for row in rep["colors"]]
    assert hexes == [c.upper() for c in COLORS]
    i, j, d = rep["pairs"][0]
    assert (i, j) == (0, 1) and set(d) == {"normal", "deutan", "protan", "tritan", "bright"}
    assert "needs distinct marker shapes" in out                        # pair 2-5, 7.5
    assert "<3:1 -> dark edge + marker shape" in out                    # orange, sky
    assert "TOO CLOSE" not in out


def test_check_palette_inputs(capsys):
    rep = ff.check_palette("okabe-ito", show=False)
    assert capsys.readouterr().out == ""
    assert rep["colors"][0][0] == "#E69F00"
    rep = ff.check_palette(["#FF0000", "#FE0000"], show=True)
    assert "TOO CLOSE under CVD" in capsys.readouterr().out
    assert rep["pairs"][0][2]["normal"] < 1


def test_swatches_card():
    fig = ff.swatches()
    ax = fig.axes[0]
    assert fig.get_figwidth() == pytest.approx(ff.width("double"))
    assert len(ax.patches) == 6 * 5                                     # 5 views per colour
    texts = [t.get_text() for t in ax.texts]
    assert "palette: fairfig" in texts and "1 blue" in texts and "#005B90" in texts
    card = [t.get_text() for t in ff.swatches(["#123456", "#abcdef"]).axes[0].texts]
    assert "1 0" in card and "2 1" in card and "#ABCDEF" in card     # numbered, no palette name
    assert not any(t.startswith("palette:") for t in card)
    assert ff.swatches("okabe-ito").axes[0].texts[0].get_text() == "palette: okabe-ito"
