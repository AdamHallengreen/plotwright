# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- `apply_theme()` for composing a base theme (`paper`, `presentation`) with a color palette and
  optional linestyle/marker cycling.
- Ten built-in color palettes, two base themes, and a `basic` linestyle set and marker set.
- `palette_colors()` to preview a palette's colors without applying it.
- `FigureSaver` for saving whole figures at a fixed size, and single subplots cropped to their
  tight bounding box, with `save_subplots_aligned()` to align panel widths across a figure.
- `mark_rasterized()` helper for mixing rasterized artists into otherwise-vector output.
