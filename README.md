# plotwright

[![Release](https://img.shields.io/github/v/release/AdamHallengreen/plotwright)](https://github.com/AdamHallengreen/plotwright/releases)
[![Build status](https://img.shields.io/github/actions/workflow/status/AdamHallengreen/plotwright/main.yml?branch=main)](https://github.com/AdamHallengreen/plotwright/actions/workflows/main.yml?query=branch%3Amain)
[![Commit activity](https://img.shields.io/github/commit-activity/m/AdamHallengreen/plotwright)](https://github.com/AdamHallengreen/plotwright/commits/main)
[![License](https://img.shields.io/github/license/AdamHallengreen/plotwright)](LICENSE)

A small matplotlib companion for consistent, presentable figures: a composable color/linestyle/
marker theme system, and a `FigureSaver` for exporting whole figures or single cropped subplots at
a fixed, reproducible size.

- **Github repository**: <https://github.com/AdamHallengreen/plotwright/>

## Installation

```bash
pip install plotwright
```

or, with [uv](https://docs.astral.sh/uv/):

```bash
uv add plotwright
```

## Quickstart

```python
import matplotlib.pyplot as plt
from plotwright import FigureSaver, apply_theme

apply_theme("vibrant", base="paper")  # both are defaults; shown here for clarity

fig, ax = plt.subplots()
ax.plot([0, 1, 2], [0, 1, 4], label="series 1")
ax.legend()

FigureSaver("figures").save_figure(fig, "example.png")
```

`apply_theme` sets matplotlib `rcParams` for the rest of the session -- scope it to one figure with
`plt.rc_context()` if you need more than one theme active side by side. `FigureSaver` handles
writing figures to disk at a consistent size.

## Palettes, bases, linestyles & markers

`apply_theme(palette=, *, base=, linestyle=, marker=, ...)` layers a base theme with a color cycle,
and optionally a linestyle/marker cycle alongside it. Every name below is also available
programmatically, so you're never guessing:

```python
from plotwright import list_bases, list_palettes, list_linestyle_sets, list_marker_sets

list_bases()            # ('paper', 'presentation')
list_palettes()         # ('fishy', 'ggplot2', 'ibm', 'okabe_ito', 'petroff10', ...)
list_linestyle_sets()   # ('basic',)
list_marker_sets()      # ('basic',)
```

| `base=`               | Use case                                     |
| --------------------- | --------------------------------------------- |
| `paper` (default)     | Print/PDF figures -- compact, serif           |
| `presentation`        | On-screen slides -- larger scale, sans-serif  |

Palettes (`palette=`): `vibrant` (default), `fishy`, `ggplot2`, `ibm`, `okabe_ito`, `petroff10`,
`seaborn_deep`, `tab10`, `tol_bright`, `tol_muted`. Linestyle sets and marker sets
(`linestyle=`/`marker=`): `basic`. Preview a palette's actual colors without applying it via
`palette_colors("vibrant")`.

Pass your own colors instead of a named palette with `colors=[...]` (a list of hex strings), and
layer extra `rcParams` on top with `extra_rc=` (a dict, or a path to another `.mplstyle` file). See
[`notebooks/demo.ipynb`](notebooks/demo.ipynb) for a runnable tour of every option, including a
side-by-side swatch of all palettes, `sequential=`, and `latex=True`.

## Saving figures

```python
saver = FigureSaver("figures", dpi=300)

saver.save_figure(fig, "whole_figure.png")                        # fixed size, no tight bbox
saver.save_subplot(fig, ax, "one_panel.png")                       # cropped to that axes' tight bbox
saver.save_subplots_aligned(fig, [ax1, ax2], ["a.png", "b.png"])   # cropped to a common width
```

Use `mark_rasterized(*artists)` to rasterize dense scatter/heatmap artists before saving to a
vector format (pdf/eps/ps) -- keeps text and axes vector while the heavy artist becomes a bitmap.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT -- see [LICENSE](LICENSE).
