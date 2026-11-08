"""Behavioral regression contract for sparse global-bounding-box inputs."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root, load_selected_generator


ROOT = find_root(__file__)
GENERATOR, SOURCE, SOURCE_SHA256 = load_selected_generator("a5bda33d14a0", root=ROOT)
_spec = spec_from_file_location("bbox_distribution_probe", Path(__file__).parents[1] / "workspace/probe_distribution.py")
PROBE = module_from_spec(_spec)
_spec.loader.exec_module(PROBE)


def draw(**overrides):
    return GENERATOR.generate(1729, 0, **overrides)


@pytest.mark.parametrize("h,w", [(4, 4), (4, 18), (18, 4), (18, 18)])
def test_declared_dimensions_are_lawful(h, w):
    grid = draw(grid_h=h, grid_w=w)
    assert (len(grid), len(grid[0])) == (h, w)
    assert GENERATOR.self_check(grid) == []
    observation = PROBE.describe(grid)
    assert min(observation["bbox_shape"]) >= 3
    assert 8 not in observation["input_colors"]
    assert PROBE.border_rule(grid) != grid


@pytest.mark.parametrize("axis,value", [("grid_h", 8.0), ("grid_w", "9"),
    ("grid_h", True), ("n_cells", 3.0), ("n_cells", "3"), ("n_cells", True),
    ("n_distinct_colors", 4.0), ("n_distinct_colors", "4"), ("n_distinct_colors", True)])
def test_integer_axes_reject_coercion(axis, value):
    with pytest.raises((TypeError, ValueError)):
        draw(**{axis: value})


@pytest.mark.parametrize("n_cells", [3, 4, 8, 12])
def test_cell_count_override_is_observable(n_cells):
    grid = draw(grid_h=8, grid_w=10, n_cells=n_cells)
    assert PROBE.describe(grid)["n_cells"] == n_cells


@pytest.mark.parametrize("n_colors", range(2, 10))
def test_distinct_colors_include_background(n_colors):
    grid = draw(n_distinct_colors=n_colors)
    row = PROBE.describe(grid)
    assert row["n_distinct_colors"] == n_colors
    assert row["source_palette_count"] == n_colors - 1
    assert row["n_cells"] >= n_colors - 1


@pytest.mark.parametrize("key,value", [("an_unknown_axis", 1), ("palette_kind", "warm"),
    ("texture", "single_cell"), ("palette_size", 3), ("position_bias", "spread"),
    ("density", "sparse")])
def test_unknown_and_removed_keys_rejected(key, value):
    with pytest.raises((TypeError, ValueError)):
        draw(**{key: value})


@pytest.mark.parametrize("axis,value", [("grid_h", 3), ("grid_h", 19), ("grid_w", 3),
    ("grid_w", 19), ("n_cells", 2), ("n_cells", 13),
    ("n_distinct_colors", 1), ("n_distinct_colors", 10)])
def test_axes_reject_out_of_range(axis, value):
    with pytest.raises((TypeError, ValueError)):
        draw(**{axis: value})


def test_explicit_counts_must_be_jointly_feasible():
    with pytest.raises((TypeError, ValueError)):
        draw(n_cells=3, n_distinct_colors=9)
    for n_cells in range(3, 13):
        for n_colors in range(2, min(9, n_cells + 1) + 1):
            grid = draw(grid_h=4, grid_w=4, n_cells=n_cells, n_distinct_colors=n_colors)
            row = PROBE.describe(grid)
            assert row["n_cells"] == n_cells
            assert row["n_distinct_colors"] == n_colors
            assert GENERATOR.self_check(grid) == []


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_deterministic_calls_and_general_invariants(difficulty):
    for index in range(8):
        grid = GENERATOR.generate(23, index, difficulty=difficulty)
        assert grid == GENERATOR.generate(23, index, difficulty=difficulty)
        assert GENERATOR.self_check(grid) == []
        row = PROBE.describe(grid)
        assert 4 <= row["grid_h"] <= 18 and 4 <= row["grid_w"] <= 18
        assert 3 <= row["n_cells"] <= 12
        assert 1 <= row["source_palette_count"] <= 8
        assert row["n_distinct_colors"] == row["source_palette_count"] + 1
        assert min(row["bbox_shape"]) >= 3 and 8 not in row["input_colors"]
        assert PROBE.border_rule(grid) != grid


def test_default_layout_and_cell_count_diversity():
    observations = [PROBE.describe(GENERATOR.generate(1729, i)) for i in range(96)]
    assert len({row["n_cells"] for row in observations}) >= 3
    assert len({tuple(row["corners"]) for row in observations}) >= 3
    assert sum(row["nw_se_pair"] for row in observations) < 80
    assert sum(row["row_first_last_bbox_exact"] for row in observations) < 80


def test_canonical_inputs_validate_and_independent_rule_matches():
    pairs = canonical_pairs("a5bda33d14a0", root=ROOT)
    assert pairs
    for pair in pairs:
        assert GENERATOR.self_check(pair["input"]) == []
        assert PROBE.border_rule(pair["input"]) == pair["output"]


@pytest.mark.parametrize("bad", [[], [[0]], [[True, 0], [0, 1]], [[0, 1], [0]],
    [[0, 0, 0], [0, 8, 0], [0, 0, 0]],
    [[1, 0, 2], [0, 0, 0], [0, 0, 0]]])
def test_self_check_returns_errors_for_malformed_or_degenerate_inputs(bad):
    assert GENERATOR.self_check(bad)
