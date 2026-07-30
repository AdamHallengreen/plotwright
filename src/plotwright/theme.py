"""Apply plotwright's preferred matplotlib theme.

Named palettes, linestyle sets, and marker sets each live as their own
small, checked-in .mplstyle file under _styles/{palettes,linestyles,markers}/
-- a static library of building blocks, not generated. `apply_theme()`
reads the ones it needs and combines them into the final color cycle at
runtime, since matplotlib style files can't merge multiple axes.prop_cycle
definitions on their own (a later `plt.style.use()` call replaces it
entirely rather than merging). Pass `colors=` to use your own colors
instead of a named palette.
"""

from __future__ import annotations

from collections.abc import Sequence
from importlib import resources
from pathlib import Path
from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
from cycler import Cycler, cycler
from matplotlib.colors import is_color_like

if TYPE_CHECKING:
    from importlib.abc import Traversable


def _styles_dir(*parts: str) -> Traversable:
    path = resources.files("plotwright") / "_styles"
    for part in parts:
        path = path / part
    return path


def _style_path(*parts: str) -> str:
    return str(_styles_dir(*parts))


def _list_names(*parts: str) -> tuple[str, ...]:
    names = (p.name.removesuffix(".mplstyle") for p in _styles_dir(*parts).iterdir() if p.name.endswith(".mplstyle"))
    return tuple(sorted(names))


def _read_cycle(*parts: str) -> Cycler:
    plt.style.use(_style_path(*parts))
    return plt.rcParams["axes.prop_cycle"]


def _require(name: str, kind: str, available: tuple[str, ...]) -> str:
    if name not in available:
        msg = f"Unknown {kind} {name!r}. Available: {available}"
        raise ValueError(msg)
    return name


def _require_colors(colors: Sequence[str]) -> None:
    invalid = [c for c in colors if not is_color_like(c)]
    if invalid:
        msg = f"Invalid color(s) in colors=: {invalid!r}. Must be valid matplotlib colors."
        raise ValueError(msg)


def _require_rc_path(path: str | Path) -> Path:
    resolved = Path(path)
    if not resolved.is_file():
        msg = f"extra_rc path does not exist: {str(resolved)!r}"
        raise ValueError(msg)
    return resolved


def _cycle_values(c: Cycler) -> tuple[str, list]:
    """The (key, values) of a single-key Cycler parsed from a .mplstyle file."""
    ((key, values),) = c.by_key().items()
    return key, list(values)


def _tile(values: Sequence, n: int) -> list:
    return [values[i % len(values)] for i in range(n)]


def _combine_cycles(color_cycle: Cycler, extras: Sequence[Cycler], *, sequential: bool) -> Cycler:
    """Combine a color cycle with extra single-key cycles (e.g. linestyle, marker).

    Lockstep (default, `sequential=False`): each extra cycle is tiled to the
    color cycle's length and zipped alongside it.
    `sequential=True`: the extras advance together only after the colors are
    exhausted (a Cartesian product).
    """
    if not extras:
        return color_cycle

    if not sequential:
        result = color_cycle
        n = len(color_cycle)
        for c in extras:
            key, values = _cycle_values(c)
            result = result + cycler(**{key: _tile(values, n)})
        return result

    m = min(len(c) for c in extras)
    parts = []
    for c in extras:
        key, values = _cycle_values(c)
        parts.append(cycler(**{key: values[:m]}))
    outer = parts[0]
    for p in parts[1:]:
        outer = outer + p
    return outer * color_cycle


def apply_theme(
    palette: str = "vibrant",
    *,
    base: str = "paper",
    colors: Sequence[str] | None = None,
    linestyle: str | None = None,
    marker: str | None = None,
    sequential: bool = False,
    latex: bool = False,
    extra_rc: dict | str | Path | None = None,
) -> None:
    """Apply plotwright's preferred style plus a color cycle to matplotlib.

    base        one of `list_bases()`, e.g. "paper" (default, for print/PDF)
                or "presentation" (larger scale, for on-screen slides).
    palette     one of `list_palettes()`, e.g. "vibrant" (default), "tab10".
                Ignored if `colors` is given.
    colors      use your own colors instead of a named palette -- a sequence
                of hex color strings, e.g. ["#EF476F", "#1082A8", ...].
    linestyle   name of a linestyle set to cycle alongside color, e.g.
                "basic" (see `list_linestyle_sets()`). None = no linestyle
                cycling.
    marker      name of a marker set to cycle alongside color, e.g. "basic"
                (see `list_marker_sets()`). None = no marker cycling.
    sequential  when `linestyle` and/or `marker` is given: advance them only
                after the colors are exhausted, instead of lockstep with
                colors (default).
    latex       layer the LaTeX-approximation text overlay on top (serif +
                Computer Modern mathtext, no usetex/pgf dependency).
    extra_rc    optional extra settings applied last, overwriting anything
                set above: either a dict of rcParams, or a path (str/Path)
                to an .mplstyle file.
    """
    _require(base, "base", list_bases())
    plt.style.use(_style_path("themes", f"{base}.mplstyle"))

    if colors is not None:
        _require_colors(colors)
        color_cycle = cycler(color=list(colors))
    else:
        color_cycle = _read_cycle("palettes", f"{_require(palette, 'palette', list_palettes())}.mplstyle")

    extras: list[Cycler] = []
    if linestyle is not None:
        extras.append(_read_cycle("linestyles", f"{_require(linestyle, 'linestyle', list_linestyle_sets())}.mplstyle"))
    if marker is not None:
        extras.append(_read_cycle("markers", f"{_require(marker, 'marker', list_marker_sets())}.mplstyle"))

    plt.rcParams["axes.prop_cycle"] = _combine_cycles(color_cycle, extras, sequential=sequential)

    if latex:
        plt.style.use(_style_path("overlays", "latex.mplstyle"))
    if isinstance(extra_rc, (str, Path)):
        plt.style.use(str(_require_rc_path(extra_rc)))
    elif extra_rc:
        plt.rcParams.update(extra_rc)


def list_bases() -> tuple[str, ...]:
    """Names of the available base themes for `apply_theme(base=...)`."""
    return _list_names("themes")


def list_palettes() -> tuple[str, ...]:
    """Names of the available color palettes for `apply_theme(palette=...)`."""
    return _list_names("palettes")


def list_linestyle_sets() -> tuple[str, ...]:
    """Names of the available linestyle sets for `apply_theme(linestyle=...)`."""
    return _list_names("linestyles")


def list_marker_sets() -> tuple[str, ...]:
    """Names of the available marker sets for `apply_theme(marker=...)`."""
    return _list_names("markers")


def palette_colors(palette: str) -> tuple[str, ...]:
    """The color values that make up a named palette, e.g.
    `palette_colors("vibrant")` -- hex strings with a leading '#', ready to
    pass straight to matplotlib (or back into `apply_theme(colors=...)`).
    Does not change the active theme. See `list_palettes()` for valid names.
    """
    with plt.rc_context():
        cycle = _read_cycle("palettes", f"{_require(palette, 'palette', list_palettes())}.mplstyle")
        _, values = _cycle_values(cycle)
    return tuple(values)
