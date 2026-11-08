from __future__ import annotations

import copy
import json
import random
from pathlib import Path

import pytest

from puzzle_generators.per_puzzle.f67822970902 import generator as gen


ROOT = Path(__file__).resolve().parents[1]


def _canonical_row() -> dict:
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                return row
    raise AssertionError("canonical task row not found")


def _first_zero_far_from_template(grid: list[list[int]]) -> tuple[int, int]:
    template = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 2
    }
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value != 0:
                continue
            if all(abs(row - rr) + abs(col - cc) > 1 for rr, cc in template):
                return row, col
    raise AssertionError("no distant zero cell")


def test_canonical_inputs_are_owned_and_python_mirror_matches_all_pairs() -> None:
    row = _canonical_row()
    pairs = row["train"] + [row["test"]]
    assert len(pairs) == 3
    for pair in pairs:
        grid = copy.deepcopy(pair["input"])
        assert gen.self_check(grid) == []
        assert gen.rule_mirror(grid) == pair["output"]
        assert grid == pair["input"], "analysis/mirror must not mutate canonical input"


def test_ordinary_draws_expose_boundary_rotation_and_clipping_branches() -> None:
    for band in ("easy", "medium", "hard"):
        rotations: set[int] = set()
        for sample_index in range(12):
            grid = gen.generate(1701, sample_index, difficulty=band)
            analysis = gen._analyze(grid)
            assert analysis["errors"] == []
            assert analysis["interior_count"] >= 1
            assert analysis["full_stamps"] >= 1
            assert analysis["clipped_stamps"] >= 1
            rotations.update(analysis["rotation_support"])
        assert rotations == {1, 3, 4, 6}


def test_exact_override_boundaries_are_observable() -> None:
    cases = (
        {"grid_h": 6},
        {"grid_h": 24},
        {"grid_w": 8},
        {"grid_w": 26},
        {"tpl_k": 5},
        {"tpl_k": 16},
        {"n_codes": 1},
        {"n_codes": 8},
    )
    for band in ("easy", "medium", "hard"):
        for overrides in cases:
            grid = gen.generate(91, 37, difficulty=band, **overrides)
            observed = gen.observe_overrides(grid)
            assert gen.self_check(grid) == []
            for key, expected in overrides.items():
                assert observed[key] == expected


def test_deterministic_replay_returns_fresh_objects_and_preserves_global_rng() -> None:
    random.seed(123456)
    state = random.getstate()
    first = gen.generate(55, 89, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(55, 89, difficulty="hard")
    assert random.getstate() == state
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert second[0][0] != 9


def test_self_check_rejects_targeted_structural_impostors() -> None:
    base = gen.generate(808, 17, difficulty="medium")

    no_codes = copy.deepcopy(base)
    for row, values in enumerate(no_codes):
        for col, value in enumerate(values):
            if value in gen._CODES:
                no_codes[row][col] = 0
    assert any("1..8 code" in error for error in gen.self_check(no_codes))

    second_template = copy.deepcopy(base)
    row, col = _first_zero_far_from_template(second_template)
    second_template[row][col] = 2
    assert any("exactly one red template" in error for error in gen.self_check(second_template))

    bad_palette = copy.deepcopy(base)
    row, col = _first_zero_far_from_template(bad_palette)
    bad_palette[row][col] = 5
    assert any("palette" in error for error in gen.self_check(bad_palette))

    touching_code = copy.deepcopy(base)
    code = next(
        (row, col, value)
        for row, values in enumerate(touching_code)
        for col, value in enumerate(values)
        if value in gen._CODES
    )
    touching_code[code[0]][code[1]] = 0
    template = {
        (row, col)
        for row, values in enumerate(touching_code)
        for col, value in enumerate(values)
        if value == 2
    }
    destination = next(
        (row + dr, col + dc)
        for row, col in sorted(template)
        for dr in (-1, 0, 1)
        for dc in (-1, 0, 1)
        if 0 <= row + dr < len(touching_code)
        and 0 <= col + dc < len(touching_code[0])
        and touching_code[row + dr][col + dc] == 0
    )
    touching_code[destination[0]][destination[1]] = code[2]
    assert any("halo" in error for error in gen.self_check(touching_code))


def test_self_check_rejects_rotation_symmetric_template() -> None:
    grid = [[0 for _ in range(12)] for _ in range(10)]
    for row, col in ((1, 2), (2, 1), (2, 2), (2, 3), (3, 2)):
        grid[row][col] = 2
    grid[0][8] = 1
    grid[9][10] = 4
    errors = gen.self_check(grid)
    assert any("four distinct rotations" in error for error in errors)


def test_invalid_calls_reject_loudly() -> None:
    with pytest.raises(TypeError, match="unknown override"):
        gen.generate(0, 0, difficulty="easy", texture="warm")
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(0, 0, difficulty="expert")
    with pytest.raises(ValueError, match="grid_h"):
        gen.generate(0, 0, difficulty="easy", grid_h=5)
