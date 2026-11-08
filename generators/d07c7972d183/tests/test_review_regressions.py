"""Behavioral regressions for the periodic-row curriculum repair."""
from __future__ import annotations

import importlib
import importlib.util
import itertools
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root


TASK_ID = "d07c7972d183"
ROOT = find_root(__file__)
SOURCE = ROOT / "generators" / TASK_ID / "generator.py"
if SOURCE.is_file():
    spec = importlib.util.spec_from_file_location("periodic_review_generator", SOURCE)
    MODULE = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(MODULE)
else:
    MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")


def _row_period(grid):
    for p in range(1, len(grid) + 1):
        if all(a == b for a, b in zip(grid, grid[p:])):
            return p
    raise AssertionError("finite input always has a period")


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_generated_support_includes_canonical_top_left_foreground(band):
    grids = [MODULE.generate(8100 + i, i, difficulty=band) for i in range(80)]
    assert any(g[0][0] == 1 for g in grids), "forced black corner excludes canonical test"
    assert any(g[0][0] == 0 for g in grids), "repair must retain both corner values"


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_generated_support_requires_checking_the_entire_row_period(band):
    grids = [MODULE.generate(9200 + i, i, difficulty=band) for i in range(80)]
    assert any(any(g[j] == g[0] for j in range(1, _row_period(g))) for g in grids), (
        "first recurrence is not the true period in two canonical demonstrations"
    )


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_band_retains_canonical_shape_support(band):
    grids = [MODULE.generate(13000 + i, i, difficulty=band) for i in range(20)]
    assert any((len(g), len(g[0])) == (6, 3) for g in grids)


@pytest.mark.parametrize("overrides", [
    {"typo_period": 3}, {"_density_profile_roll": 0},
    {"grid_h": True}, {"grid_h": 6.5}, {"grid_h": "6"},
    {"grid_w": False}, {"grid_w": 3.1}, {"grid_w": "3"},
    {"period": True}, {"period": 2.9}, {"period": "2"},
])
def test_invalid_or_unknown_overrides_are_rejected(overrides):
    with pytest.raises((ValueError, TypeError)):
        MODULE.generate(41, 13, **overrides)


@pytest.mark.parametrize("bad_cell", [[], {}, [1], {"value": 1}, None, True, 1.0])
def test_validator_returns_reasons_for_malformed_cells(bad_cell):
    grid = [[0, 1, 0], [1, 0, 1]] * 3
    grid = [row[:] for row in grid]
    grid[0][0] = bad_cell
    assert MODULE.self_check(grid), "malformed input should be rejected without crashing"


def test_all_canonical_pairs_remain_in_the_declared_domain():
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert len(pairs) == 4
    for pair in pairs:
        assert MODULE.self_check(pair["input"]) == []


def test_full_joint_axis_boundaries_remain_exact_or_explain_incompatibility():
    for band, height, width, period in itertools.product(
        ("easy", "medium", "hard"), range(4, 19), (3, 12), range(2, 7)
    ):
        options = {"grid_h": height, "grid_w": width, "period": period}
        if period > height - 2:
            with pytest.raises(ValueError, match="requires grid_h"):
                MODULE.generate(72, 11, difficulty=band, **options)
            continue
        grid = MODULE.generate(72, 11, difficulty=band, **options)
        assert MODULE.self_check(grid) == []
        assert (len(grid), len(grid[0]), _row_period(grid)) == (height, width, period)


def test_constructed_counterexample_has_expected_authoring_output():
    # This expected grid is explicit; the generator's diagnostic solvers do not
    # supply its labels. Racket replay is retained separately with the return.
    a, b, c = [1, 0, 0], [0, 1, 0], [1, 1, 1]
    grid = [a, b, a, b, c, a, a, b, a]
    assert MODULE.self_check(grid) == []
    assert _row_period(grid) == 6
    expected = [
        [2, 0, 0], [0, 2, 0], [2, 0, 0], [0, 2, 0], [2, 2, 2],
        [2, 0, 0], [2, 0, 0], [0, 2, 0], [2, 0, 0], [0, 2, 0],
        [2, 2, 2], [2, 0, 0], [2, 0, 0],
    ]
    assert MODULE._diagnostic_output(grid) == expected
    assert all(rival(grid) != expected for rival in MODULE.LESSON_COMPETITORS.values())


def test_diagnostic_mirror_and_declared_shortcuts_match_canonical_labels():
    for pair in canonical_pairs(TASK_ID, root=ROOT):
        assert MODULE._diagnostic_output(pair["input"]) == pair["output"]
        for rival in MODULE.CANONICAL_SHORTCUTS.values():
            assert rival(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_schedule_start_and_query_position_keeps_a_distinguishing_demo(band):
    for seed, start in itertools.product((0, 17, 101), range(MODULE.LESSON_SCHEDULE_PERIOD)):
        grids = [MODULE.generate(seed, start + i, difficulty=band) for i in range(4)]
        outputs = [MODULE._diagnostic_output(grid) for grid in grids]
        for held_out in range(4):
            for name, rival in MODULE.LESSON_COMPETITORS.items():
                assert any(rival(grid) != out for i, (grid, out) in enumerate(zip(grids, outputs))
                           if i != held_out), (band, seed, start, held_out, name)


def test_connected_witness_family_is_lawful_and_refutes_rivals():
    import random
    for width, index, seed in itertools.product(range(5, 13), (1, 3), range(10)):
        rows = MODULE._draw_distinguishing_rows(width, index, random.Random(seed), connected=True)
        grid = [list(rows[i % 6]) for i in range(9)]
        assert MODULE.self_check(grid) == []
        assert _row_period(grid) == 6
        out = MODULE._diagnostic_output(grid)
        assert all(rival(grid) != out for rival in MODULE.LESSON_COMPETITORS.values())


def test_production_duplicate_rejection_preserves_rotation_evidence(monkeypatch):
    # Run through the real production sampler and Racket, replacing only a
    # generated broad input with an exact duplicate to exercise that branch.
    try:
        target = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
    except ModuleNotFoundError:
        pytest.skip("production runtime required; execute the public task_tests stage")
    from puzzle_generators.runner import run_one
    original = target.generate

    def duplicate_broad(seed, sample_index, **kwargs):
        return original(seed, 1 if sample_index == 2 else sample_index, **kwargs)

    monkeypatch.setattr(target, "generate", duplicate_broad)
    episode = run_one(TASK_ID, 17, 0, n_train=3, n_test=1, difficulty="medium")
    pairs = episode["train"] + episode["test"]
    assert len(pairs) == 4
    assert any(row["reason"] == "validate.duplicate_pair"
               for row in episode["sampling"]["rejections"])
    for held_out in range(4):
        for name, rival in target.LESSON_COMPETITORS.items():
            assert any(rival(pair["input"]) != pair["output"]
                       for i, pair in enumerate(pairs) if i != held_out), (held_out, name)
