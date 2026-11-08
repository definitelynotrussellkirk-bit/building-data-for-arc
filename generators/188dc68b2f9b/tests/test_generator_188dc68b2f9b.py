from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

import pytest

gen = importlib.import_module("puzzle_generators.per_puzzle.188dc68b2f9b.generator")


ROOT = Path(__file__).resolve().parents[1]


def _canonical_row() -> dict:
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                return row
    raise AssertionError("canonical task row not found")


def _fold_out_impostor() -> list[list[int]]:
    # Legal-looking three-role cross, but the NE singleton folds to local col=2
    # while the NW output width is only 2, so a generated lesson would hide it.
    grid = [[4] * 7 for _ in range(7)]
    for c in range(7):
        grid[2][c] = 2
    for r in range(7):
        grid[r][2] = 2
    grid[0][5] = 1
    return grid


def test_rule_hash_and_canonical_pairs_match_exactly() -> None:
    row = _canonical_row()
    assert gen.RULE_HASH == "63b928f87f96"
    pairs = list(row["train"]) + list(row["test"])
    assert len(pairs) == 4
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_exact_override_boundaries_are_observable_in_every_band() -> None:
    cases = [
        {"grid_h": 7, "grid_w": 7, "quadrant": "nw", "sep_position": "centered"},
        {"grid_h": 13, "grid_w": 13, "quadrant": "se", "sep_position": "offset"},
        {"grid_h": 7, "grid_w": 13, "quadrant": "ne", "sep_position": "offset"},
        {"grid_h": 13, "grid_w": 7, "quadrant": "sw", "sep_position": "centered"},
    ]
    for difficulty in ("easy", "medium", "hard"):
        for index, overrides in enumerate(cases):
            grid = gen.generate(1000 + index, 200 + index, difficulty=difficulty, **overrides)
            assert gen.observe_overrides(grid) == overrides
            assert gen.self_check(grid, difficulty=difficulty, meta={"overrides": overrides}) == []


def test_unknown_and_invalid_overrides_reject_loudly() -> None:
    with pytest.raises(TypeError, match="unknown override"):
        gen.generate(1, 0, not_an_axis=True)
    with pytest.raises(ValueError, match="grid_h"):
        gen.generate(1, 0, grid_h=6)
    with pytest.raises(ValueError, match="quadrant"):
        gen.generate(1, 0, quadrant="middle")


def test_structural_impostors_are_rejected() -> None:
    valid = gen.generate(77, 4, difficulty="medium")
    facts = gen.semantic_observables(valid)
    sr, sc = facts["singleton_pos"]
    sep_r, sep_c = facts["separator_row"], facts["separator_col"]
    singleton = facts["singleton_color"]
    dom = facts["dominant"]

    no_singleton = copy.deepcopy(valid)
    no_singleton[sr][sc] = dom

    broken_separator = copy.deepcopy(valid)
    col = 0 if sc != 0 else 1
    broken_separator[sep_r][col] = dom

    duplicate_singleton = copy.deepcopy(valid)
    for r, row in enumerate(duplicate_singleton):
        for c, value in enumerate(row):
            if value == dom and (r, c) != (sr, sc):
                duplicate_singleton[r][c] = singleton
                break
        else:
            continue
        break

    fourth_role = copy.deepcopy(valid)
    replacement = next(color for color in range(10) if color not in facts["palette"])
    replaced = 0
    for r, row in enumerate(fourth_role):
        for c, value in enumerate(row):
            if value == dom and (r, c) != (sr, sc):
                fourth_role[r][c] = replacement
                replaced += 1
                if replaced == 2:
                    break
        if replaced == 2:
            break

    fold_out = _fold_out_impostor()

    for name, grid in {
        "no_singleton": no_singleton,
        "broken_separator": broken_separator,
        "duplicate_singleton": duplicate_singleton,
        "fourth_role_absent_elsewhere": fourth_role,
        "fold_out": fold_out,
    }.items():
        assert gen.self_check(grid), name

    assert any("folds outside" in reason for reason in gen.self_check(fold_out))


def test_replay_fresh_returns_and_global_rng_purity() -> None:
    state = random.getstate()
    first = gen.generate(31337, 17, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(31337, 17, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = (first[0][0] + 1) % 10
    assert gen.generate(31337, 17, difficulty="hard") == second


def test_every_three_demo_window_is_identifiable() -> None:
    for difficulty in ("easy", "medium", "hard"):
        for start in range(24):
            seed = 9000 + start
            demos = []
            for offset in range(gen.EXAMPLES_NEEDED):
                grid = gen.generate(seed, start + offset, difficulty=difficulty)
                demos.append({"input": grid, "output": gen.rule_mirror(grid)})
            query_grid = gen.generate(seed, start + gen.EXAMPLES_NEEDED, difficulty=difficulty)
            assert gen.lesson_identifiable(
                demos, {"input": query_grid, "output": gen.rule_mirror(query_grid)}
            ) == [], (difficulty, start)


def test_centered_shortcut_fits_canonical_but_offset_witness_kills_it() -> None:
    shortcut = gen.CANONICAL_SHORTCUTS["assume_centered_divider"]
    row = _canonical_row()
    for pair in list(row["train"]) + list(row["test"]):
        assert shortcut(pair["input"]) == pair["output"]

    grid = gen.generate(4242, 1, difficulty="hard", sep_position="offset")
    assert gen.rule_mirror(grid) != shortcut(grid)
