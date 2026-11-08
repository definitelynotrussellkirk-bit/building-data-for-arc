"""Focused regression tests for the largest-per-fixed-color generator repair."""
from __future__ import annotations

import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest
from reviewer_support import canonical_path, find_root

ROOT = find_root(__file__)
TASK = "6afe10b621e4"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")


def _canonical_row():
    with canonical_path(ROOT).open() as handle:
        return next(row for row in map(json.loads, handle) if row.get("task_id") == TASK)


def _base_row():
    path = canonical_path(ROOT).parent.parent / "base" / "solutions" / "custom" / "5f3e1b4e__6afe10b621e4.json"
    return json.loads(path.read_text())


def test_rule_hash_and_task_local_target_match_canonical_authority():
    canonical = _canonical_row()["program_solution"]
    normalized = " ".join(canonical.split())
    assert MODULE.RULE_HASH == hashlib.sha256(normalized.encode()).hexdigest()[:12]
    racket_target = _base_row()["racket_target"]
    assert racket_target["raw_code"] == canonical
    assert racket_target["target_code"] == canonical


def test_self_check_accepts_every_canonical_input_and_mirror_matches_train_outputs():
    row = _canonical_row()
    pairs = [*row["train"], *row["test"]]
    assert len(pairs) == 5
    for pair in pairs:
        assert MODULE.self_check(pair["input"]) == []
        if "output" in pair:
            assert MODULE.rule_mirror(pair["input"]) == pair["output"]


def test_regression_easy_seed_22_no_longer_silently_drops_green():
    grid = MODULE.generate(22, 22, difficulty="easy")
    observed = MODULE.observe_overrides(grid)
    assert observed["n_red_objs"] >= 2
    assert observed["n_green_objs"] >= 2
    assert MODULE.self_check(grid, difficulty="easy") == []
    assert {1, 4} <= {value for row in MODULE.rule_mirror(grid) for value in row}


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_lessons_are_valid_and_defeat_global_two_largest_shortcut(band):
    for seed in range(80):
        grid = MODULE.generate(seed, seed * 17 + 3, difficulty=band)
        analysis = MODULE._analysis(grid, generated=True)
        assert analysis["errors"] == []
        assert analysis["facts"]["global_rank_trap"] is True
        assert MODULE.self_check(grid, difficulty=band) == []


@pytest.mark.parametrize(
    "axis,value",
    [
        ("grid_h", 7), ("grid_h", 18),
        ("grid_w", 7), ("grid_w", 18),
        ("n_red_objs", 2), ("n_red_objs", 4),
        ("n_green_objs", 2), ("n_green_objs", 4),
        ("winner_size_small", 3), ("winner_size_small", 6),
        ("winner_size_gap", 2), ("winner_size_gap", 3),
        ("larger_color", "red"), ("larger_color", "green"),
        ("include_distractor", False), ("include_distractor", True),
    ],
)
def test_every_declared_boundary_override_is_observable(axis, value):
    grid = MODULE.generate(1234, 5678, difficulty="medium", **{axis: value})
    assert MODULE.observe_overrides(grid)[axis] == value
    assert MODULE.self_check(
        grid,
        difficulty="medium",
        meta={"overrides": {axis: value}},
    ) == []


def test_self_check_rejects_targeted_structural_impostors():
    all_background = [[0] * 10 for _ in range(10)]
    missing_green = [[0] * 10 for _ in range(10)]
    missing_green[1][1:4] = [2, 2, 2]
    missing_green[5][5] = 2

    tied_red = [[0] * 10 for _ in range(10)]
    for r, c in [(1, 1), (1, 2), (2, 1), (6, 1), (6, 2), (7, 1)]:
        tied_red[r][c] = 2
    for r, c in [(1, 7), (1, 8), (2, 7), (7, 7)]:
        tied_red[r][c] = 3

    single_component_each = [[0] * 10 for _ in range(10)]
    for r, c in [(1, 1), (1, 2), (2, 1)]:
        single_component_each[r][c] = 2
    for r, c in [(7, 7), (7, 8), (8, 7)]:
        single_component_each[r][c] = 3

    bad_distractor = MODULE.generate(9, 9, difficulty="medium", include_distractor=False)
    bad_distractor = [row[:] for row in bad_distractor]
    zeros = [(r, c) for r, row in enumerate(bad_distractor) for c, value in enumerate(row) if value == 0]
    (r1, c1), (r2, c2) = zeros[0], zeros[-1]
    bad_distractor[r1][c1] = 7
    bad_distractor[r2][c2] = 7

    for grid in (all_background, missing_green, tied_red, single_component_each, bad_distractor):
        assert MODULE.self_check(grid)


def test_negative_recombination_without_any_green_is_rejected():
    grid = MODULE.generate(333, 444, difficulty="hard", include_distractor=False)
    recombined = [[6 if value == 3 else value for value in row] for row in grid]
    errors = MODULE.self_check(recombined, difficulty="hard")
    assert errors
    assert any("green" in error or "allowed" in error for error in errors)


def test_generation_is_deterministic_fresh_and_global_rng_independent():
    random.seed(987654321)
    before = random.getstate()
    first = MODULE.generate(111, 222, difficulty="hard")
    assert random.getstate() == before
    second = MODULE.generate(111, 222, difficulty="hard")
    assert first == second
    assert first is not second and first[0] is not second[0]
    frozen = [row[:] for row in second]
    first[0][0] = 9 if first[0][0] != 9 else 7
    assert MODULE.generate(111, 222, difficulty="hard") == frozen


def test_unknown_controls_fail_loudly():
    with pytest.raises(ValueError, match="unknown difficulty"):
        MODULE.generate(1, 2, difficulty="extreme")
    with pytest.raises(ValueError, match="unknown override"):
        MODULE.generate(1, 2, not_an_axis=3)

@pytest.mark.parametrize("seed", [12, 29])
def test_large_winner_override_expands_unrequested_canvas_without_rejection(seed):
    grid = MODULE.generate(seed, seed, difficulty="easy", winner_size_small=6)
    observed = MODULE.observe_overrides(grid)
    assert observed["winner_size_small"] == 6
    assert not MODULE.self_check(grid, difficulty="easy")
