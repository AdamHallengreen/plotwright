import matplotlib.pyplot as plt
import pytest

from plotwright import apply_theme, list_bases, list_linestyle_sets, list_marker_sets, list_palettes, palette_colors


def test_list_palettes_includes_known_names():
    palettes = list_palettes()
    assert "vibrant" in palettes
    assert "tab10" in palettes
    assert len(palettes) == len(set(palettes))


def test_list_linestyle_and_marker_sets():
    assert "basic" in list_linestyle_sets()
    assert "basic" in list_marker_sets()


def test_list_bases_includes_paper_and_presentation():
    bases = list_bases()
    assert "paper" in bases
    assert "presentation" in bases


def test_palette_colors_matches_applied_cycle():
    colors = [c.lstrip("#").lower() for c in palette_colors("tab10")]

    apply_theme("tab10")
    applied = [c["color"].lstrip("#").lower() for c in plt.rcParams["axes.prop_cycle"]]

    assert colors == applied


def test_palette_colors_does_not_change_active_theme():
    apply_theme("vibrant")
    before = plt.rcParams["axes.prop_cycle"]

    palette_colors("tab10")

    assert plt.rcParams["axes.prop_cycle"] == before


def test_palette_colors_unknown_palette_raises():
    with pytest.raises(ValueError, match="Unknown palette"):
        palette_colors("not-a-real-palette")


def test_apply_theme_sets_base_rcparams():
    apply_theme("tab10")
    assert plt.rcParams["axes.grid"] is True
    assert plt.rcParams["axes.grid.axis"] == "y"
    assert tuple(plt.rcParams["figure.figsize"]) == (7.27, 4.5)


def test_apply_theme_presentation_base_has_larger_fonts():
    apply_theme("tab10", base="presentation")
    assert plt.rcParams["font.size"] == 16
    assert plt.rcParams["font.family"] == ["sans-serif"]
    assert tuple(plt.rcParams["figure.figsize"]) == (10, 5.625)


def test_apply_theme_unknown_base_raises():
    with pytest.raises(ValueError, match="Unknown base"):
        apply_theme("vibrant", base="not-a-real-base")


def test_apply_theme_sets_color_cycle():
    expected = [c.lstrip("#").lower() for c in palette_colors("tab10")]

    apply_theme("tab10")
    colors = [c["color"].lstrip("#").lower() for c in plt.rcParams["axes.prop_cycle"]]

    assert colors == expected


def test_apply_theme_unknown_palette_raises():
    with pytest.raises(ValueError, match="Unknown palette"):
        apply_theme("not-a-real-palette")


def test_apply_theme_unknown_linestyle_raises():
    with pytest.raises(ValueError, match="Unknown linestyle"):
        apply_theme("vibrant", linestyle="not-a-real-set")


def test_apply_theme_unknown_marker_raises():
    with pytest.raises(ValueError, match="Unknown marker"):
        apply_theme("vibrant", marker="not-a-real-set")


def test_apply_theme_latex_overlay():
    apply_theme("vibrant", latex=True)
    assert plt.rcParams["mathtext.fontset"] == "cm"
    assert plt.rcParams["axes.formatter.use_mathtext"] is True


def test_apply_theme_extra_rc_dict_overwrites():
    apply_theme("vibrant", extra_rc={"axes.grid": False})
    assert plt.rcParams["axes.grid"] is False


def test_apply_theme_extra_rc_mplstyle_path_overwrites(tmp_path):
    style = tmp_path / "extra.mplstyle"
    style.write_text("axes.grid: False\nfigure.dpi: 150\n")

    apply_theme("vibrant", extra_rc=style)

    assert plt.rcParams["axes.grid"] is False
    assert plt.rcParams["figure.dpi"] == 150


def test_apply_theme_extra_rc_mplstyle_path_as_string(tmp_path):
    style = tmp_path / "extra.mplstyle"
    style.write_text("axes.grid: False\n")

    apply_theme("vibrant", extra_rc=str(style))

    assert plt.rcParams["axes.grid"] is False


def test_apply_theme_extra_rc_missing_path_raises():
    with pytest.raises(ValueError, match="extra_rc path does not exist"):
        apply_theme("vibrant", extra_rc="not-a-real-file.mplstyle")


def test_apply_theme_custom_colors_overrides_palette():
    apply_theme("tab10", colors=["#000000", "#ffffff", "#ff00ff"])
    colors = [c["color"] for c in plt.rcParams["axes.prop_cycle"]]
    assert [c.lstrip("#").lower() for c in colors] == ["000000", "ffffff", "ff00ff"]


def test_apply_theme_invalid_colors_raises():
    with pytest.raises(ValueError, match="Invalid color"):
        apply_theme(colors=["#000000", "not-a-color"])


def test_apply_theme_custom_colors_with_linestyle():
    apply_theme(colors=["#000000", "#ffffff"], linestyle="basic")
    entries = list(plt.rcParams["axes.prop_cycle"])
    colors = [e["color"].lstrip("#").lower() for e in entries]
    assert colors == ["000000", "ffffff"]
    assert [e["linestyle"] for e in entries] == ["-", "-"]


def test_apply_theme_palette_with_linestyle_uses_static_cycle_files():
    expected = [c.lstrip("#").lower() for c in palette_colors("tab10")]

    apply_theme("tab10", linestyle="basic")
    entries = list(plt.rcParams["axes.prop_cycle"])
    colors = [e["color"].lstrip("#").lower() for e in entries]

    assert colors == expected
    assert all("linestyle" in e for e in entries)


def test_apply_theme_palette_sequential_markers_is_product():
    n_colors = len(palette_colors("okabe_ito"))

    apply_theme("okabe_ito", marker="basic", sequential=True)
    entries = list(plt.rcParams["axes.prop_cycle"])

    # sequential/product mode repeats each marker across a full pass of colors
    assert len(entries) > n_colors
    first_marker = entries[0]["marker"]
    assert all(e["marker"] == first_marker for e in entries[:n_colors])


def test_apply_theme_palette_with_linestyle_and_marker_lockstep():
    apply_theme("vibrant", linestyle="basic", marker="basic")
    entries = list(plt.rcParams["axes.prop_cycle"])
    assert all("linestyle" in e and "marker" in e for e in entries)
