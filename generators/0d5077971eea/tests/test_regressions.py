"""Regression witnesses that fail against the retained v1.2.1 baseline."""
from pathlib import Path
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "workspace"))
from review_support import load_generator, observed

gen = load_generator()


def test_empty_row_is_diagnostic():
    assert gen.self_check([[]])


def test_unknown_override_is_rejected():
    with pytest.raises(ValueError):
        gen.generate(17, 1, typo_axis=2)


def test_advertised_density_changes_pixels():
    grid = gen.generate(17, 1, grid_h=5, grid_w=7,
                        n_distinct_colors=4, marker_density="high")
    assert observed(grid)["marker_density"] == "high"
    assert observed(grid)["n_distinct_colors"] == 4


def test_legal_boundary_overrides_work_in_easy():
    grid = gen.generate(17, 1, difficulty="easy", grid_h=12, grid_w=16,
                        n_distinct_colors=10, marker_density="high")
    assert observed(grid) == dict(grid_h=12, grid_w=16,
                                 n_distinct_colors=10, marker_density="high")


def test_minimum_canvas_high_density_full_palette_has_capacity():
    requested = dict(grid_h=5, grid_w=7, n_distinct_colors=10, marker_density="high")
    grid = gen.generate(6127, 1, **requested)
    assert gen.self_check(grid) == []
    assert observed(grid) == requested
