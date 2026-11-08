"""Observable regressions for whole-line compression and its input sampler.

Expectations use canonical labels, literal witnesses, and a separately written
column-boundary oracle. The evidence probe compares these cases with Racket.
"""
from __future__ import annotations

import importlib.util
import itertools
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root

TASK = "4e081a15d785"
ROOT = find_root(__file__)
SOURCE = next(path for path in (
    ROOT / "generators" / TASK / "generator.py",
    ROOT / "puzzle_generators" / "per_puzzle" / TASK / "generator.py",
) if path.is_file())
SPEC = importlib.util.spec_from_file_location("compression_generator_under_test", SOURCE)
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)
CANONICAL = canonical_pairs(TASK, root=ROOT)


def whole_line_oracle(grid):
    """Retain every changed row and every column boundary visible in any row."""
    rows = [list(key) for key, _ in itertools.groupby(map(tuple, grid))]
    columns = [0] + [c for c in range(1, len(rows[0]))
                     if any(row[c] != row[c - 1] for row in rows)]
    return [[row[c] for c in columns] for row in rows]


@pytest.mark.parametrize("pair", CANONICAL, ids=lambda p: f"{p['split']}-{p['pair_index']}")
def test_all_canonical_inputs_belong_to_the_declared_domain(pair):
    assert GEN.self_check(pair["input"]) == []
    assert whole_line_oracle(pair["input"]) == pair["output"]


@pytest.mark.parametrize("grid", [
    [], [[]], [[1], [1, 2]], [[False]], [[10]], [[-1]], [[1.5]],
    "12", [None], [[0] * 31], [[0] for _ in range(31)],
])
def test_invalid_arc_grids_are_rejected_without_crashing(grid):
    assert GEN.self_check(grid)


@pytest.mark.parametrize("grid", [
    [[0, 1]], [[4, 4, 2, 2, 4]], [[3], [3], [1], [3]],
    [[1, 1, 2], [1, 2, 2]], [[1, 1, 1], [2, 3, 2]],
])
def test_lawful_identity_and_rowwise_ragged_cases_are_accepted(grid):
    assert GEN.self_check(grid) == []


@pytest.mark.parametrize("requested", [
    {"grid_h": 1, "grid_w": 2, "base_color_count": 2,
     "n_duplicates": 0, "n_column_duplicates": 0},
    {"grid_h": 1, "grid_w": 22, "base_color_count": 10,
     "n_duplicates": 0, "n_column_duplicates": 0},
    {"grid_h": 18, "grid_w": 1, "base_color_count": 10,
     "n_duplicates": 0, "n_column_duplicates": 0},
    {"grid_h": 18, "grid_w": 22, "base_color_count": 2,
     "n_duplicates": 17, "n_column_duplicates": 20},
    {"grid_h": 3, "grid_w": 4, "base_color_count": 2,
     "n_duplicates": 1, "n_column_duplicates": 1},
    {"grid_h": 2, "grid_w": 5, "base_color_count": 10,
     "n_duplicates": 0, "n_column_duplicates": 0},
    {"grid_h": 18}, {"grid_w": 1}, {"base_color_count": 10},
    {"n_duplicates": 17}, {"n_column_duplicates": 21},
])
@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_exact_controls_are_realized_from_pixels_in_every_band(requested, band):
    grid = GEN.generate(17, 11, difficulty=band, **requested)
    assert GEN.self_check(grid) == []
    rows = list(itertools.groupby(map(tuple, grid)))
    columns = list(itertools.groupby(zip(*grid)))
    observed = {
        "grid_h": len(grid), "grid_w": len(grid[0]),
        "base_color_count": len({v for row in grid for v in row}),
        "n_duplicates": len(grid) - len(rows),
        "n_column_duplicates": len(grid[0]) - len(columns),
    }
    assert all(observed[key] == value for key, value in requested.items())
    assert GEN.observe_overrides(grid) == observed


@pytest.mark.parametrize("requested", [
    {"grid_h": 2, "n_duplicates": 2},
    {"grid_w": 2, "n_column_duplicates": 2},
    {"grid_h": 1, "grid_w": 1, "base_color_count": 2},
    {"base_color_count": 3, "grid_h": 2, "grid_w": 2, "n_duplicates": 1},
    {"base_color_count": 3, "grid_h": 2, "grid_w": 2, "n_column_duplicates": 1},
])
def test_infeasible_joint_controls_raise_structured_errors(requested):
    with pytest.raises(ValueError) as caught:
        GEN.generate(5, 0, **requested)
    axes = getattr(caught.value, "incompatible_axes", ())
    assert len(axes) >= 2
    assert set(axes) <= set(requested)


@pytest.mark.parametrize("requested", [
    {"grid_h": 0}, {"grid_w": 23}, {"base_color_count": 11}, {"base_color_count": 1},
    {"n_duplicates": -1}, {"n_column_duplicates": 22},
    {"grid_h": True}, {"grid_w": 3.2}, {"base_color_count": "2"},
    {"unknown_axis": 2}, {"anchor_endpoints": True}, {"texture": "monochrome"},
])
def test_bad_or_retired_controls_cannot_be_silently_ignored(requested):
    with pytest.raises((ValueError, TypeError)):
        GEN.generate(5, 0, **requested)


def test_column_equality_is_global_and_nonconsecutive_lines_survive():
    witness = [[1, 1, 1, 2, 2, 1], [1, 1, 1, 2, 2, 1],
               [1, 1, 2, 2, 2, 1], [1, 1, 1, 2, 2, 1]]
    assert whole_line_oracle(witness) == [
        [1, 1, 2, 1], [1, 2, 2, 1], [1, 1, 2, 1]]
    assert GEN.self_check(witness) == []
    assert getattr(GEN, "CANONICAL_SHORTCUTS", {})
    for rival in GEN.CANONICAL_SHORTCUTS.values():
        assert rival(witness) != whole_line_oracle(witness)


def test_every_declared_canonical_shortcut_really_fits_every_canonical_pair():
    assert getattr(GEN, "CANONICAL_SHORTCUTS", {})
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        for pair in CANONICAL:
            assert rival(pair["input"]) == pair["output"], name


@pytest.mark.parametrize("grid", [[[0]], [[4, 4], [4, 4]], [[8], [8]]])
def test_training_domain_excludes_monochrome_degenerates(grid):
    assert GEN.self_check(grid)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_defaults_always_exercise_a_real_compression(band):
    for seed in range(32):
        grid = GEN.generate(seed, seed, difficulty=band)
        assert whole_line_oracle(grid) != grid, (seed, band)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_consecutive_four_pair_windows_teach_all_declared_rivals_under_rotation(band):
    rivals = getattr(GEN, "LESSON_COMPETITORS", {})
    assert rivals
    for seed in range(6):
        for start in range(8):
            grids = [GEN.generate(seed, start + i, difficulty=band) for i in range(4)]
            labels = [whole_line_oracle(grid) for grid in grids]
            for held_out in range(4):
                for name, rival in rivals.items():
                    fits = all(rival(grid) == label for i, (grid, label)
                               in enumerate(zip(grids, labels)) if i != held_out)
                    assert not fits or rival(grids[held_out]) == labels[held_out], (
                        seed, start, held_out, name)


def test_defaults_are_replayable_and_cover_canonical_stripes_and_varied_core_shapes():
    profiles, cores, stripe_count = set(), set(), 0
    for index in range(64):
        grid = GEN.generate(41, index, difficulty="hard")
        assert grid == GEN.generate(41, index, difficulty="hard")
        assert GEN.self_check(grid) == []
        profiles.add((len(grid), len(grid[0]), len({v for row in grid for v in row})))
        core = whole_line_oracle(grid)
        cores.add((len(core), len(core[0])))
        stripe_count += len({tuple(row) for row in grid}) == 1 or all(len(set(row)) == 1 for row in grid)
    canonical_profiles = {(len(p['input']), len(p['input'][0]),
                           len({v for row in p['input'] for v in row})) for p in CANONICAL}
    assert profiles & canonical_profiles
    assert stripe_count >= 8
    assert len(cores) >= 8
