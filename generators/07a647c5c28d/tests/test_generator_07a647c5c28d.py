"""Focused regressions for generator 07a647c5c28d."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
MOD = importlib.import_module(
    "puzzle_generators.per_puzzle.07a647c5c28d.generator"
)


def _canonical_row() -> dict:
    with (REPO / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == MOD.TASK_ID:
                return row
    raise AssertionError("canonical task row missing")


def _base_solution() -> dict:
    path = (
        REPO
        / "data/base/solutions/banks/f4facb1306bd/"
        "E116__07a647c5c28d.json"
    )
    return json.loads(path.read_text(encoding="utf-8"))


def _bbox(grid):
    cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 6
    ]
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _inside_non_six(grid) -> int:
    r1, c1, r2, c2 = _bbox(grid)
    return sum(
        grid[r][c] not in (0, 6)
        for r in range(r1, r2 + 1)
        for c in range(c1, c2 + 1)
    )


def _outside_nonzero(grid) -> int:
    r1, c1, r2, c2 = _bbox(grid)
    return sum(
        grid[r][c] != 0
        for r in range(len(grid))
        for c in range(len(grid[0]))
        if not (r1 <= r <= r2 and c1 <= c <= c2)
    )


def test_rule_hash_authority_sync_and_all_canonical_pairs():
    row = _canonical_row()
    source = row["program_solution"]
    normalized = " ".join(source.split())
    expected = hashlib.sha256(normalized.encode()).hexdigest()[:12]
    assert MOD.RULE_HASH == expected == "fa0093f9ce0e"

    racket_target = _base_solution()["racket_target"]
    assert racket_target["raw_code"] == source
    assert racket_target["target_code"] == source
    assert racket_target["rule_hash"] == expected

    pairs = list(row["train"]) + list(row["test"])
    assert len(pairs) == 5
    for pair in pairs:
        grid = copy.deepcopy(pair["input"])
        before = copy.deepcopy(grid)
        assert MOD.self_check(grid) == []
        assert MOD.rule_mirror(grid) == pair["output"]
        assert grid == before


def test_exact_axis_boundaries_are_honored_in_every_band():
    for band in ("easy", "medium", "hard"):
        for index, (grid_h, grid_w, box_h, box_w, texture) in enumerate(
            (
                (7, 7, 2, 2, "two_sixes"),
                (16, 16, 8, 8, "plain"),
                (7, 16, 5, 8, "interior_six"),
                (16, 7, 8, 5, "interior_six"),
            )
        ):
            grid = MOD.generate(
                1000 + index,
                19,
                difficulty=band,
                grid_h=grid_h,
                grid_w=grid_w,
                box_h=box_h,
                box_w=box_w,
                texture=texture,
            )
            assert MOD.self_check(grid) == []
            assert len(grid) == grid_h
            assert len(grid[0]) == grid_w
            assert MOD.observe_overrides(grid) == {
                "box_h": box_h,
                "box_w": box_w,
                "texture": texture,
            }


def test_three_demo_windows_cover_all_marker_grammars_and_payload_rule():
    for band in ("easy", "medium", "hard"):
        for start in range(12):
            grids = [
                MOD.generate(7331, start + offset, difficulty=band)
                for offset in range(3)
            ]
            profiles = [MOD.observe_overrides(grid)["texture"] for grid in grids]
            assert set(profiles) == set(MOD.HELPFUL_TEXTURES)
            assert sum(_inside_non_six(grid) > 0 for grid in grids) >= 2
            assert all(_outside_nonzero(grid) > 0 for grid in grids)


def test_determinism_fresh_returns_input_purity_and_global_rng_purity():
    random.seed(76475)
    before = random.getstate()
    first = MOD.generate(17, 29, difficulty="hard")
    after = random.getstate()
    second = MOD.generate(17, 29, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert first[0] is not second[0]

    original = copy.deepcopy(first)
    output = MOD.rule_mirror(first)
    assert first == original
    output[0][0] = 9 if output[0][0] != 9 else 8
    assert first == original

    first[0][0] = 9 if first[0][0] != 9 else 8
    assert first != second
    assert second != MOD.generate(18, 29, difficulty="hard")
    assert second != MOD.generate(17, 30, difficulty="hard")


def test_self_check_rejects_rule_hiding_mutations():
    valid = MOD.generate(88, 14, difficulty="medium")
    assert MOD.self_check(valid) == []

    no_six = copy.deepcopy(valid)
    for row in no_six:
        for c, value in enumerate(row):
            if value == 6:
                row[c] = 0
    assert MOD.self_check(no_six)

    one_six = copy.deepcopy(no_six)
    one_six[2][2] = 6
    assert MOD.self_check(one_six)

    identity = [[0] * 8 for _ in range(8)]
    for r, c in ((0, 0), (0, 7), (7, 0), (7, 7)):
        identity[r][c] = 6
    identity[3][3] = 4
    assert MOD.self_check(identity)

    no_outside = copy.deepcopy(valid)
    r1, c1, r2, c2 = _bbox(no_outside)
    for r in range(len(no_outside)):
        for c in range(len(no_outside[0])):
            if not (r1 <= r <= r2 and c1 <= c <= c2):
                no_outside[r][c] = 0
    assert MOD.self_check(no_outside)


def test_invalid_calls_and_incompatible_override_combinations_reject_loudly():
    with pytest.raises(TypeError):
        MOD.generate(1, 1, unknown_axis=3)
    with pytest.raises(ValueError):
        MOD.generate(1, 1, difficulty="extreme")
    with pytest.raises(ValueError):
        MOD.generate(1, 1, grid_h=7, box_h=8)
    with pytest.raises(ValueError):
        MOD.generate(1, 1, texture="interior_six", box_h=2)
    with pytest.raises(ValueError):
        MOD.generate(1, 1, texture="interior_six", box_w=2)


def test_absent_feature_recombination_is_rejected_but_oracle_defined():
    grid = MOD.generate(
        991,
        0,
        difficulty="easy",
        texture="two_sixes",
        box_h=2,
        box_w=2,
    )
    replacement = next(color for color in range(1, 10) if color not in {v for row in grid for v in row})
    mutation = copy.deepcopy(grid)
    marker = next((r, c) for r, row in enumerate(mutation) for c, value in enumerate(row) if value == 6)
    mutation[marker[0]][marker[1]] = replacement
    assert replacement not in {
        value
        for r, row in enumerate(mutation)
        for c, value in enumerate(row)
        if (r, c) != marker
    }
    assert MOD.self_check(mutation)
    assert MOD.rule_mirror(mutation) == [[6]]
