"""Save matplotlib figures and subplots to disk.

Ported from resources/latex_export.py's `LatexFigureSaver`, trimmed of the
LaTeX text-width/column-width sizing machinery (figdimens reading, figsize())
and the `\\includegraphics` snippet writer, which are out of scope for now.

Design carried over from the original:
  * Whole-figure saves use no tight bbox — whitespace is removed at draw time
    by constrained layout (see _styles/themes/paper.mplstyle and
    presentation.mplstyle), so figures save at their fixed designed size and
    widths are byte-exact across figures.
  * Single-subplot saves crop to the axes' true tight bbox (ticks, tick
    labels, offset/scientific text, axis labels and legend included; title
    excluded on demand) via an explicit inches Bbox.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable, Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import Literal

from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.transforms import Bbox

logger = logging.getLogger(__name__)

_LayoutEngineName = Literal["constrained", "compressed", "tight", "none"]

PS_PT_PER_INCH = 72.0
_VECTOR_META = {"pdf", "eps", "ps"}  # svg/png use different metadata schemas


def _resolve_path(filename: str | Path, output_dir: str | Path) -> Path:
    p = Path(filename)
    return p if p.is_absolute() else Path(output_dir) / p


def _metadata(fmt: str, reproducible: bool, extra: dict | None) -> dict | None:
    md: dict = {}
    if fmt in _VECTOR_META:
        md["Creator"] = "matplotlib / plotwright"
        if reproducible:
            # Omit the timestamp so identical inputs give byte-identical files.
            md["CreationDate"] = None
    if extra:
        md.update(extra)
    return md or None


def _engine_name(engine) -> _LayoutEngineName:
    """Map a layout-engine instance back to a name we can safely re-apply."""
    if engine is None:
        return "none"
    from matplotlib.layout_engine import ConstrainedLayoutEngine, TightLayoutEngine

    if isinstance(engine, ConstrainedLayoutEngine):
        return "constrained"
    if isinstance(engine, TightLayoutEngine):
        return "tight"
    return "none"


def mark_rasterized(*artists: Artist) -> tuple[Artist, ...]:
    """Rasterize heavy artists (dense scatter, pcolormesh) so a vector file
    stays small while text and axes remain vector. Pair with a save dpi."""
    for a in artists:
        a.set_rasterized(True)
    return artists


class FigureSaver:
    """Save figures and subplots at a fixed size and dpi."""

    def __init__(self, output_dir: str | Path = "figures", *, dpi: int = 300) -> None:
        self.output_dir = Path(output_dir)
        self._dpi = dpi

    # ---- whole-figure save ------------------------------------------------ #
    def save_figure(
        self,
        fig: Figure,
        filename: str | Path,
        *,
        transparent: bool = False,
        reproducible: bool = True,
        metadata: dict | None = None,
    ) -> Path:
        """Save the whole figure at its fixed designed size (no tight bbox),
        so widths match exactly across figures."""
        path = _resolve_path(filename, self.output_dir)
        path.parent.mkdir(parents=True, exist_ok=True)
        fmt = path.suffix.lstrip(".") or "pdf"
        fig.savefig(
            path,
            dpi=self._dpi,
            format=fmt,
            transparent=transparent,
            bbox_inches=None,  # fixed figure bbox -> byte-exact width
            pad_inches=0.0,
            metadata=_metadata(fmt, reproducible, metadata),
        )
        logger.info(f"Saved figure to {path}")
        return path

    # ---- single-panel save, cropped, optional title ----------------------- #
    @contextmanager
    def _isolated(self, fig: Figure, ax: Axes, include_title: bool) -> Iterator[None]:
        """Temporarily show only `ax` (optionally without its title) with the
        layout engine frozen, so measuring/saving one panel can't reflow it.
        Everything is restored on exit, even if the body raises."""
        fig.canvas.draw()  # resolve constrained layout
        prev_engine = fig.get_layout_engine()
        fig.set_layout_engine("none")  # freeze positions
        other_axes = [a for a in fig.axes if a is not ax]
        prev_visible = [a.get_visible() for a in other_axes]
        prev_title = ax.get_title()
        try:
            for a in other_axes:
                a.set_visible(False)
            if not include_title:
                ax.set_title("")
            fig.canvas.draw()  # apply changes; no reflow
            yield
        finally:
            if not include_title:
                ax.set_title(prev_title)
            for a, v in zip(other_axes, prev_visible, strict=True):
                a.set_visible(v)
            fig.set_layout_engine(_engine_name(prev_engine))
            fig.canvas.draw_idle()

    def subplot_width_in(
        self,
        fig: Figure,
        ax: Axes,
        *,
        pad_pt: float = 3.0,
        relative_pad: float | None = None,
        include_title: bool = False,
        extra_artists: Iterable[Artist] | None = None,
    ) -> float:
        """The padded crop width (inches) a single panel would occupy. Use the
        max over several panels as `target_width_in` to align them."""
        with self._isolated(fig, ax, include_title):
            bbox = self._ax_extent(
                fig,
                ax,
                extra_artists,
                pad_pt=pad_pt,
                relative_pad=relative_pad,
                target_width_in=None,
            )
        return bbox.width

    def save_subplot(
        self,
        fig: Figure,
        ax: Axes,
        filename: str | Path,
        *,
        pad_pt: float = 3.0,
        relative_pad: float | None = None,
        include_title: bool = False,
        extra_artists: Iterable[Artist] | None = None,
        target_width_in: float | None = None,
        transparent: bool = False,
        reproducible: bool = True,
        metadata: dict | None = None,
    ) -> Path:
        """Save a single subplot cropped to its true tight bbox.

        pad_pt          absolute margin per side, in points (default). Uniform
                        across panels, so they align.
        relative_pad    opt-in: fractional padding (old .expanded behaviour).
        include_title   render crops out the title; set True to keep it.
        extra_artists   extra artists to keep inside the crop. The axes legend
                        is included automatically.
        target_width_in pad the crop symmetrically out to this width so
                        side-by-side panels line up (see subplot_width_in or
                        save_subplots_aligned).
        """
        path = _resolve_path(filename, self.output_dir)
        path.parent.mkdir(parents=True, exist_ok=True)
        fmt = path.suffix.lstrip(".") or "pdf"

        with self._isolated(fig, ax, include_title):
            bbox = self._ax_extent(
                fig,
                ax,
                extra_artists,
                pad_pt=pad_pt,
                relative_pad=relative_pad,
                target_width_in=target_width_in,
            )
            fig.savefig(
                path,
                dpi=self._dpi,
                format=fmt,
                transparent=transparent,
                bbox_inches=bbox,  # inches Bbox
                pad_inches=0.0,  # padding already baked into bbox
                metadata=_metadata(fmt, reproducible, metadata),
            )

        logger.info(f"Saved subplot to {path}")
        return path

    def save_subplots_aligned(
        self,
        fig: Figure,
        axes: Sequence[Axes],
        filenames: Sequence[str | Path],
        *,
        pad_pt: float = 3.0,
        relative_pad: float | None = None,
        include_title: bool = False,
        extra_artists: Iterable[Artist] | None = None,
        transparent: bool = False,
        reproducible: bool = True,
        metadata: dict | None = None,
    ) -> list[Path]:
        """Save several panels cropped to a common width (their max), so they
        line up column-to-column when placed at natural size."""
        axes, filenames = list(axes), list(filenames)
        if len(axes) != len(filenames):
            msg = "axes and filenames must have the same length."
            raise ValueError(msg)
        target = max(
            self.subplot_width_in(
                fig,
                a,
                pad_pt=pad_pt,
                relative_pad=relative_pad,
                include_title=include_title,
                extra_artists=extra_artists,
            )
            for a in axes
        )
        return [
            self.save_subplot(
                fig,
                a,
                fn,
                pad_pt=pad_pt,
                relative_pad=relative_pad,
                include_title=include_title,
                extra_artists=extra_artists,
                target_width_in=target,
                transparent=transparent,
                reproducible=reproducible,
                metadata=metadata,
            )
            for a, fn in zip(axes, filenames, strict=True)
        ]

    # ---- internals ---------------------------------------------------------#
    def _ax_extent(
        self,
        fig: Figure,
        ax: Axes,
        extra_artists: Iterable[Artist] | None,
        *,
        pad_pt: float,
        relative_pad: float | None,
        target_width_in: float | None,
    ) -> Bbox:
        renderer = getattr(fig.canvas, "get_renderer", lambda: None)()
        extras: list[Artist] = list(extra_artists) if extra_artists else []
        legend = ax.get_legend()
        if legend is not None and legend not in extras:
            extras.append(legend)

        # get_tightbbox already covers ticks, tick labels, offset/scientific
        # text, axis labels and the (visible) title; a blanked title drops out.
        bbox_disp = ax.get_tightbbox(renderer, bbox_extra_artists=extras or None)
        if bbox_disp is None:
            bbox_disp = ax.get_window_extent(renderer)
        bbox_in = bbox_disp.transformed(fig.dpi_scale_trans.inverted())

        if relative_pad is not None:
            bbox_in = bbox_in.expanded(1.0 + relative_pad, 1.0 + relative_pad)
        else:
            bbox_in = bbox_in.padded(pad_pt / PS_PT_PER_INCH)

        if target_width_in is not None:
            if target_width_in > bbox_in.width:
                extra = (target_width_in - bbox_in.width) / 2.0
                x0, y0, x1, y1 = bbox_in.extents
                bbox_in = Bbox.from_extents(x0 - extra, y0, x1 + extra, y1)
            elif target_width_in < bbox_in.width - 1e-9:
                logger.warning(
                    f"target_width_in {target_width_in:.3f}in is smaller than "
                    f"the panel's own width {bbox_in.width:.3f}in; not shrinking "
                    f"(panels may not align)."
                )
        return bbox_in
