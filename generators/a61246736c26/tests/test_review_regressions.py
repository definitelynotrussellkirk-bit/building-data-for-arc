"""Source-bound regressions for the a61246736c26 teaching and validator repairs."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

PROBE_PATH = Path(__file__).resolve().parents[1] / "workspace/coverage_probe.py"
SPEC = importlib.util.spec_from_file_location("a612_review_coverage", PROBE_PATH)
assert SPEC and SPEC.loader
PROBE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROBE)
GEN, SOURCE, SOURCE_SHA256 = PROBE.selected_generator()


def test_every_frame_permutation_and_solid_row_assignment_is_lawful():
    """A profile classifier must not narrow the structural semantic domain."""
    failures = []
    cases = list(PROBE.recombination_cases())
    assert len(cases) == 648
    for case in cases:
        errors = GEN.self_check(case["input"])
        if errors:
            failures.append((case["frames"], case["solid_rows"], errors))
        else:
            assert GEN.observe_overrides(case["input"])["scene_profile"]
        assert GEN.rule_mirror(case["input"]) == case["expected"]
    assert not failures, f"{len(failures)}/648 rejected; first failures: {failures[:3]}"


@pytest.mark.parametrize("frames", [(5, 9, 0), (9, 0, 5)])
def test_all_top_solids_use_the_actual_nonzero_row_swatch(frames):
    grid, expected = PROBE.lattice_case(frames, (0, 0, 0))
    assert GEN.self_check(grid) == []
    assert GEN.rule_mirror(grid) == expected
    assert expected[0] == [frames[0]] * 4 + [8] + [frames[0]] * 4 + [8] + [frames[0]] * 4


def malformed_rectangles():
    grid, _ = PROBE.lattice_case((9, 0, 5), (0, 1, 2))
    deleted_row_separator = [row[:] for row in grid]
    deleted_row_separator[5][0] = 9
    deleted_column_separator = [row[:] for row in grid]
    deleted_column_separator[0][5] = 9
    bad_swatch = [row[:] for row in grid]
    bad_swatch[2][0] = 3
    return [deleted_row_separator, deleted_column_separator, grid[1:], grid[:-1],
            [row[1:] for row in grid], [row[:-1] for row in grid], bad_swatch,
            [[8] * 16 for _ in range(16)], [[0]]]


@pytest.mark.parametrize("grid", malformed_rectangles(), ids=[
    "deleted-row-separator-cell", "deleted-column-separator-cell", "missing-top-row",
    "missing-bottom-row", "missing-swatch-column", "missing-right-column",
    "nonuniform-swatch", "all-separator", "one-cell"])
def test_malformed_rectangular_inputs_return_error_lists(grid):
    errors = GEN.self_check(grid)
    assert isinstance(errors, list)
    assert errors and all(isinstance(error, str) and error for error in errors)
    with pytest.raises(ValueError):
        GEN.observe_overrides(grid)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("seed", [True, False, 1.0, 1.75, "1"])
def test_seed_requires_a_python_integer_excluding_boolean(seed, band):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(seed, 0, difficulty=band, scene_profile="row_cycle_012")


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("index", [True, False, 1.0, 1.75, "1", -1])
def test_sample_index_requires_a_nonnegative_python_integer(index, band):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, index, difficulty=band, scene_profile="row_cycle_012")


def test_default_support_has_nonzero_same_row_frames_and_both_column_counts():
    same_row_frames, column_counts, frame_permutations = set(), set(), set()
    for draw in range(600):
        seed, band_index = divmod(draw, 3)
        grid = GEN.generate(seed, seed * 29, difficulty=("easy", "medium", "hard")[band_index])
        assert GEN.self_check(grid) == [], seed
        features = PROBE.lattice_features(grid)
        column_counts.add(features["columns"])
        frame_permutations.add(features["frames"])
        if len(set(features["solid_rows"])) == 1:
            same_row_frames.add(features["frames"][features["solid_rows"][0]])
    assert same_row_frames == {0, 5, 9}
    assert column_counts == {3, 4}
    assert len(frame_permutations) == 6


def test_six_consecutive_default_draws_supply_two_witnesses_of_each_kind():
    failures = []
    for band in ("easy", "medium", "hard"):
        for seed in (0, 3, 19):
            for start in (0, 1, 10, 11):
                grids = [GEN.generate(seed, index, difficulty=band) for index in range(start, start + 6)]
                assert all(GEN.self_check(grid) == [] for grid in grids)
                same_row = sum(PROBE.crossed_same_row_witness(grid) for grid in grids)
                mixed_row = sum(PROBE.mixed_row_swatch_witness(grid) for grid in grids)
                if same_row < 2 or mixed_row < 2:
                    failures.append((band, seed, start, same_row, mixed_row))
    assert not failures, f"Insufficient witnesses in {len(failures)} windows; first: {failures[:3]}"


@pytest.mark.parametrize("size", [7, 8])
def test_four_column_lattices_above_arc_size_limit_are_rejected(size):
    grid, _ = PROBE.lattice_case((9, 0, 5), (0, 1, 2, 0), tile_size=size)
    assert len(grid[0]) > 30
    errors = GEN.self_check(grid)
    assert isinstance(errors, list) and errors
    with pytest.raises(ValueError):
        GEN.observe_overrides(grid)
