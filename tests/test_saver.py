import logging

import matplotlib.pyplot as plt
import pytest

from plotwright import FigureSaver, mark_rasterized


def _make_figure(label):
    fig, ax = plt.subplots(label=label)
    ax.plot([0, 1, 2], [0, 1, 4])
    return fig, ax


def test_save_figure_writes_a_file(tmp_path):
    plt.close("all")
    fig, _ax = _make_figure("alpha")

    path = FigureSaver(tmp_path).save_figure(fig, "alpha.png")

    assert path.exists()
    assert path.stat().st_size > 0

    plt.close("all")


def test_save_subplot_crops_smaller_than_save_figure(tmp_path):
    plt.close("all")
    fig, ax = _make_figure("gamma")

    saver = FigureSaver(tmp_path)
    sub_path = saver.save_subplot(fig, ax, "sub.png")

    assert sub_path.exists()
    assert saver.subplot_width_in(fig, ax) < fig.get_size_inches()[0]

    plt.close("all")


def test_save_subplots_aligned_writes_all_files(tmp_path):
    plt.close("all")
    fig, (ax1, ax2) = plt.subplots(1, 2, label="aligned")
    ax1.plot([0, 1], [0, 1], label="short")
    ax1.legend()
    ax2.plot([0, 1], [1, 0])

    saver = FigureSaver(tmp_path)
    paths = saver.save_subplots_aligned(fig, [ax1, ax2], ["left.png", "right.png"])

    assert len(paths) == 2
    assert all(p.exists() and p.stat().st_size > 0 for p in paths)

    plt.close("all")


def test_save_subplots_aligned_raises_on_length_mismatch(tmp_path):
    plt.close("all")
    fig, (ax1, ax2) = plt.subplots(1, 2, label="mismatch")

    saver = FigureSaver(tmp_path)
    with pytest.raises(ValueError, match="same length"):
        saver.save_subplots_aligned(fig, [ax1, ax2], ["only_one.png"])

    plt.close("all")


def test_mark_rasterized_sets_flag_and_returns_artists():
    plt.close("all")
    _fig, ax = plt.subplots()
    (line,) = ax.plot([0, 1], [0, 1])
    scatter = ax.scatter([0, 1], [1, 0])

    result = mark_rasterized(line, scatter)

    assert result == (line, scatter)
    assert line.get_rasterized() is True
    assert scatter.get_rasterized() is True

    plt.close("all")


def test_save_figure_custom_metadata_is_embedded(tmp_path):
    plt.close("all")
    fig, _ax = _make_figure("meta")

    saver = FigureSaver(tmp_path)
    path = saver.save_figure(fig, "meta.pdf", transparent=True, metadata={"Subject": "plotwright-test-marker"})

    assert path.exists()
    assert b"plotwright-test-marker" in path.read_bytes()

    plt.close("all")


def test_save_figure_reproducible_is_byte_identical_across_saves(tmp_path):
    plt.close("all")
    fig, _ax = _make_figure("repro")

    saver = FigureSaver(tmp_path)
    path_a = saver.save_figure(fig, "repro_a.pdf")
    path_b = saver.save_figure(fig, "repro_b.pdf")

    assert path_a.read_bytes() == path_b.read_bytes()

    plt.close("all")


def test_target_width_in_smaller_than_panel_warns(tmp_path, caplog):
    plt.close("all")
    fig, ax = _make_figure("warn")

    saver = FigureSaver(tmp_path)
    with caplog.at_level(logging.WARNING):
        saver.save_subplot(fig, ax, "warn.png", target_width_in=0.01)

    assert "smaller than" in caplog.text

    plt.close("all")
