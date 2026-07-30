"""plotwright: preferred matplotlib theme + figure saving."""

from importlib.metadata import version

from plotwright.saver import FigureSaver, mark_rasterized
from plotwright.theme import (
    apply_theme,
    list_bases,
    list_linestyle_sets,
    list_marker_sets,
    list_palettes,
    palette_colors,
)

__version__ = version("plotwright")

__all__ = [
    "FigureSaver",
    "__version__",
    "apply_theme",
    "list_bases",
    "list_linestyle_sets",
    "list_marker_sets",
    "list_palettes",
    "mark_rasterized",
    "palette_colors",
]
