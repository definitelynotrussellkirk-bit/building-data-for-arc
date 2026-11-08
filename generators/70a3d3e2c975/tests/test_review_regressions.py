"""Black-box regressions for the reflection generator's reviewed contract.

Run from a library with ``PYTHONPATH=shared/runtime python -m pytest -q
generators/70a3d3e2c975/tests/test_review_regressions.py``.  The same file also
runs in a prepared runtime under ``tests/70a3d3e2c975``.  Canonical examples
are authoring evidence and must not be imported during a blind solve.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import os
from pathlib import Path
import sys

import pytest


# Bind imports and canonical data to this test's own tree, not the shell cwd.
for ancestor in Path(__file__).resolve().parents:
    runtime = ancestor / "shared" / "runtime"
    if (runtime / "reviewer_support.py").is_file():
        sys.path.insert(0, str(runtime))
        break
    if (ancestor / "reviewer_support.py").is_file():
        sys.path.insert(0, str(ancestor))
        break

from reviewer_support import canonical_pairs, find_root  # noqa: E402


TASK_ID = "70a3d3e2c975"
ROOT = find_root(__file__)
DEFAULT_GENERATOR = ROOT / "generators" / TASK_ID / "generator.py"
if not DEFAULT_GENERATOR.is_file():
    DEFAULT_GENERATOR = (
        ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"
    )
GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", DEFAULT_GENERATOR))
SPEC = importlib.util.spec_from_file_location("reflection_review_generator", GENERATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
gen = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = gen
SPEC.loader.exec_module(gen)


def source_cells(grid):
    axis = len(grid[0]) // 2
    return [value for row in grid for value in row[:axis] if value not in (0, 9)]


def valid_scene():
    grid = [[0, 0, 0, 9, 0, 0, 0] for _ in range(5)]
    grid[1][1] = 2
    return grid


def corrupt_scene(kind):
    grid = valid_scene()
    if kind == "right_side_mark":
        grid[1][4] = 2
    elif kind == "stray_axis_color":
        grid[2][0] = 9
    elif kind == "multiple_full_axes":
        for row in grid:
            row[2] = 9
    elif kind == "off_center_axis":
        for row in grid:
            row[3], row[2] = 0, 9
    elif kind == "no_source":
        grid[1][1] = 0
    elif kind == "even_width":
        for row in grid:
            row.append(0)
    elif kind == "missing_axis":
        for row in grid:
            row[3] = 0
    elif kind == "ragged":
        grid[-1].pop()
    else:
        raise AssertionError(kind)
    return grid


def assert_diagnostics(grid, **kwargs):
    errors = gen.self_check(grid, **kwargs)
    assert isinstance(errors, list) and errors
    assert all(isinstance(error, str) and error for error in errors)


@pytest.mark.parametrize("pair", canonical_pairs(TASK_ID, root=ROOT))
def test_canonical_inputs_are_accepted_without_mutation(pair):
    grid = deepcopy(pair["input"])
    assert gen.self_check(grid) == []
    assert grid == pair["input"]


@pytest.mark.parametrize("kind", [
    "right_side_mark", "stray_axis_color", "multiple_full_axes",
    "off_center_axis", "no_source", "even_width", "missing_axis", "ragged",
])
def test_validator_rejects_invalid_reflection_domains(kind):
    assert_diagnostics(corrupt_scene(kind))


@pytest.mark.parametrize("texture", ["empty_left", "full_left", "no_axis"])
@pytest.mark.parametrize("kind", ["right_side_mark", "stray_axis_color", "missing_axis"])
def test_metadata_cannot_bypass_actual_grid_validation(texture, kind):
    assert_diagnostics(corrupt_scene(kind), meta={"texture": texture})


@pytest.mark.parametrize("value", [None, True, 2.0, "2", [], {}, -1, 10])
def test_nonliteral_or_out_of_range_cell_has_diagnostics(value):
    grid = valid_scene()
    grid[1][1] = value
    assert_diagnostics(grid)


@pytest.mark.parametrize("grid", [None, [], [[]], [None], [0], 7, "0009000"])
def test_malformed_grid_has_diagnostics_instead_of_raising(grid):
    assert_diagnostics(grid)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("height,half_width,marks", [(5, 2, 1), (14, 8, 20), (7, 3, 6)])
def test_advertised_geometry_and_mark_counts_are_exact_in_every_band(
    band, height, half_width, marks
):
    grid = gen.generate(
        73, 0, difficulty=band, grid_h=height, half_w=half_width,
        marks=marks, palette_kind="varied", palette_size=1,
    )
    assert (len(grid), len(grid[0])) == (height, 2 * half_width + 1)
    assert len(source_cells(grid)) == marks
    assert gen.self_check(grid) == []


@pytest.mark.parametrize("key", ["palette_size", "n_distinct_colors"])
@pytest.mark.parametrize("count", [1, 2, 4, 6])
def test_palette_cardinality_overrides_count_colors_actually_present(key, count):
    for seed in (0, 7, 31):
        grid = gen.generate(
            seed, 1, grid_h=8, half_w=4, marks=6, palette_kind="varied",
            **{key: count},
        )
        assert len(set(source_cells(grid))) == count, (seed, key, count)


@pytest.mark.parametrize("key", ["palette_size", "n_distinct_colors"])
def test_eight_foreground_colors_are_supported_when_feasible(key):
    grid = gen.generate(
        7, 1, difficulty="hard", grid_h=8, half_w=4, marks=8,
        palette_kind="varied", **{key: 8},
    )
    assert set(source_cells(grid)) == set(range(1, 9))


@pytest.mark.parametrize("kind,pool", [
    ("warm", {2, 4, 6, 7}), ("cool", {1, 3, 8}),
])
@pytest.mark.parametrize("key", ["palette_kind", "texture"])
def test_palette_family_controls_constrain_actual_source_colors(key, kind, pool):
    for seed in (0, 7, 31):
        grid = gen.generate(
            seed, 1, grid_h=8, half_w=4, marks=6, palette_size=2,
            **{key: kind},
        )
        assert set(source_cells(grid)) <= pool, (seed, key, kind)
        assert len(set(source_cells(grid))) == 2


@pytest.mark.parametrize("kind", ["default", "warm", "cool", "varied"])
def test_helpful_texture_is_an_exact_alias_for_palette_kind(kind):
    kwargs = {"grid_h": 8, "half_w": 4, "marks": 6, "palette_size": 2}
    expected = gen.generate(91, 3, palette_kind=kind, **kwargs)
    assert gen.generate(91, 3, texture=kind, **kwargs) == expected
    assert gen.generate(91, 3, texture=kind, palette_kind=kind, **kwargs) == expected


def test_matching_palette_cardinality_aliases_agree():
    kwargs = {"grid_h": 8, "half_w": 4, "marks": 6, "palette_kind": "varied"}
    expected = gen.generate(15, 1, palette_size=3, **kwargs)
    assert gen.generate(15, 1, n_distinct_colors=3, **kwargs) == expected
    assert gen.generate(15, 1, palette_size=3, n_distinct_colors=3, **kwargs) == expected
    assert len(set(source_cells(expected))) == 3


@pytest.mark.parametrize("overrides", [
    {"palette_size": 2, "n_distinct_colors": 3},
    {"palette_kind": "warm", "texture": "cool"},
    {"grid_h": 5, "half_w": 2, "marks": 11},
    {"marks": 4, "palette_size": 5},
    {"marks": 4, "n_distinct_colors": 5},
    {"marks": 6, "palette_kind": "warm", "palette_size": 5},
    {"marks": 6, "palette_kind": "cool", "n_distinct_colors": 4},
])
def test_infeasible_or_conflicting_controls_fail_explicitly(overrides):
    with pytest.raises(ValueError):
        gen.generate(1, 0, **overrides)


@pytest.mark.parametrize("key,value", [
    ("grid_h", 4), ("grid_h", 15), ("half_w", 1), ("half_w", 9),
    ("marks", 0), ("marks", 21), ("palette_size", 0), ("palette_size", 9),
    ("n_distinct_colors", 0), ("n_distinct_colors", 9),
])
def test_controls_outside_the_honest_domain_are_rejected(key, value):
    with pytest.raises(ValueError):
        gen.generate(1, 0, **{key: value})


@pytest.mark.parametrize("key,value", [
    ("grid_h", "8"), ("grid_h", 8.0), ("grid_h", None),
    ("half_w", 4.0), ("marks", 6.9), ("marks", "6"),
    ("palette_size", True), ("palette_size", 2.0), ("palette_size", "2"),
    ("palette_size", None), ("n_distinct_colors", True),
    ("n_distinct_colors", None), ("palette_kind", "unknown"),
    ("texture", "unknown"), ("position_bias", "right_half"),
    ("density", "sparse"), ("pallete_size", 2),
])
def test_unknown_and_malformed_controls_are_rejected_without_coercion(key, value):
    with pytest.raises(ValueError):
        gen.generate(1, 0, **{key: value})


@pytest.mark.parametrize("texture", ["empty_left", "no_axis"])
def test_intentionally_invalid_diagnostic_scenes_still_fail_selfcheck(texture):
    grid = gen.generate(7, 0, texture=texture)
    assert_diagnostics(grid)
    assert_diagnostics(grid, meta={"texture": texture})


def test_full_left_diagnostic_scene_honors_geometry_and_palette():
    grid = gen.generate(
        17, 0, texture="full_left", grid_h=6, half_w=2,
        palette_kind="warm", n_distinct_colors=2,
    )
    assert (len(grid), len(grid[0])) == (6, 5)
    assert len(source_cells(grid)) == 12
    assert len(set(source_cells(grid))) == 2
    assert set(source_cells(grid)) <= {2, 4, 6, 7}
    assert gen.self_check(grid, meta={"texture": "full_left"}) == []


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_draws_remain_deterministic_valid_and_unmodified_by_checks(band):
    for seed in (11, 97):
        for index in range(8):
            grid = gen.generate(seed, index, difficulty=band)
            original = deepcopy(grid)
            assert gen.self_check(grid) == []
            assert grid == original
            assert grid == gen.generate(seed, index, difficulty=band)


def observed_components(grid):
    """Measure actual foreground topology without generator placement helpers."""
    axis = len(grid[0]) // 2
    remaining = {
        (r, c) for r, row in enumerate(grid) for c, value in enumerate(row[:axis])
        if value not in (0, 9)
    }
    result = []
    while remaining:
        component = {remaining.pop()}
        frontier = set(component)
        while frontier:
            neighbors = {
                point
                for r, c in frontier
                for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
            } & remaining
            remaining.difference_update(neighbors)
            component.update(neighbors)
            frontier = neighbors
        result.append(component)
    return result


def has_canonical_motif_layout(grid):
    components = observed_components(grid)
    return (
        (len(grid), len(grid[0])) in {(7, 7), (7, 9), (8, 9)}
        and len(set(source_cells(grid))) == 2
        and len(components) == 2
        and all(
            2 <= len(component) <= 4
            and len({grid[r][c] for r, c in component}) == 1
            for component in components
        )
    )


def reflected_rows(grid):
    """Independent domain oracle: preserve each row's source and reverse it."""
    axis = len(grid[0]) // 2
    return [list(row[:axis + 1]) + list(reversed(row[:axis])) for row in grid]


def test_defaults_cover_canonical_motifs_and_difficulty_changes_visible_counts():
    totals = {}
    for band in (None, "easy", "medium", "hard"):
        grids = [gen.generate(seed, index, difficulty=band)
                 for seed in range(16) for index in range(2)]
        # Half the ordinary curriculum should retain the canonical motif family.
        assert sum(has_canonical_motif_layout(grid) for grid in grids) >= 16, band
        totals[band] = sum(len(source_cells(grid)) for grid in grids)
    assert totals["hard"] > totals["easy"], totals


def test_fixed_three_demo_lessons_query_both_observed_families_across_seeds():
    for band in (None, "easy", "medium", "hard"):
        queries = [gen.generate(seed, 3, difficulty=band) for seed in range(16)]
        motif_flags = [has_canonical_motif_layout(grid) for grid in queries]
        assert set(motif_flags) == {False, True}, band
        for grid, motif_family in zip(queries, motif_flags):
            assert gen.self_check(grid) == []
            if not motif_family:
                assert any(len(component) == 1 for component in observed_components(grid))


def test_every_cyclic_three_demo_window_teaches_each_declared_rival():
    canonical = canonical_pairs(TASK_ID, root=ROOT)
    assert all(reflected_rows(pair["input"]) == pair["output"] for pair in canonical)
    rivals = gen.LESSON_COMPETITORS
    assert {"drop_singletons", "ignore_outer_edge", "canonical_colors_only"} <= set(rivals)
    for name, rival in rivals.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in canonical), name

    for band in (None, "easy", "medium", "hard"):
        for seed in range(8):
            pairs = []
            for index in range(8):
                grid = gen.generate(seed, index, difficulty=band)
                pairs.append({"input": grid, "output": reflected_rows(grid)})
            for start in range(8):
                demos = [pairs[(start + offset) % len(pairs)] for offset in range(3)]
                query = pairs[(start + 3) % len(pairs)]
                for name, rival in rivals.items():
                    assert any(rival(pair["input"]) != pair["output"] for pair in demos), (
                        band, seed, start, name
                    )
                assert gen.lesson_identifiable(demos, query) == []
