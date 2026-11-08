from __future__ import annotations

import copy
import json
import random
from pathlib import Path

import pytest

from puzzle_generators.per_puzzle.cfe428d096c3 import generator as gen


ROOT = Path(__file__).resolve().parents[1]


def _canonical_inputs():
    for line in (ROOT / "data/canonical/puzzles.jsonl").open():
        row = json.loads(line)
        if row.get("task_id") == gen.TASK_ID:
            return [pair["input"] for split in ("train", "test") for pair in row[split]]
    raise AssertionError("canonical task row not found")


def _erase_component(grid, cells):
    result = copy.deepcopy(grid)
    for row, col in cells:
        result[row][col] = 0
    return result


def _extend_component(grid, cells):
    result = copy.deepcopy(grid)
    height, width = len(result), len(result[0])
    occupied = {(r, c) for r in range(height) for c in range(width) if result[r][c]}
    for row, col in cells:
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            candidate = (row + dr, col + dc)
            if not (0 <= candidate[0] < height and 0 <= candidate[1] < width):
                continue
            if candidate in occupied:
                continue
            result[candidate[0]][candidate[1]] = 1
            return result
    raise AssertionError("no empty extension cell found")


def test_rule_hash_and_exact_override_boundaries():
    assert gen.RULE_HASH == "aba2f01fcba9"
    assert set(gen.AXES) == {"grid_size", "n_extra_rects"}
    for difficulty in ("easy", "medium", "hard"):
        for grid_size in (12, 14):
            for n_extra_rects in (0, 2):
                grid = gen.generate(
                    7001,
                    7,
                    difficulty=difficulty,
                    grid_size=grid_size,
                    n_extra_rects=n_extra_rects,
                )
                assert gen.self_check(grid) == []
                assert gen.observe_overrides(grid) == {
                    "grid_size": grid_size,
                    "n_extra_rects": n_extra_rects,
                }

    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(7001, 7, palette_kind="warm")
    with pytest.raises(ValueError, match="must be an integer"):
        gen.generate(7001, 7, grid_size=True)


def test_canonical_inputs_and_rule_mirror():
    inputs = _canonical_inputs()
    assert len(inputs) == 5
    for grid in inputs:
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        output = gen.rule_mirror(grid)
        assert output != grid


def test_self_check_rejects_four_targeted_impostors():
    ordinary = gen.generate(8100, 2, difficulty="hard", n_extra_rects=2)
    analysis = gen._analyze(ordinary)
    assert analysis["errors"] == []
    assert len(analysis["blue_nonrectangles"]) == 1

    blank = [[0] * 12 for _ in range(12)]
    assert gen.self_check(blank)

    tall = next(
        component
        for component in analysis["solid_rectangles"]
        if component["aspect"] == "tall"
    )
    missing_tall = _erase_component(ordinary, tall["cells"])
    assert any("tall" in error or "3..5" in error for error in gen.self_check(missing_tall))

    wrong_marker = copy.deepcopy(ordinary)
    for row, col in analysis["decorations"][0]["cells"]:
        wrong_marker[row][col] = 7
    assert any("palette" in error or "color-6" in error for error in gen.self_check(wrong_marker))

    solidified = copy.deepcopy(ordinary)
    nonrect = analysis["blue_nonrectangles"][0]
    rows = [row for row, _ in nonrect["cells"]]
    cols = [col for _, col in nonrect["cells"]]
    for row in range(min(rows), max(rows) + 1):
        for col in range(min(cols), max(cols) + 1):
            solidified[row][col] = 1
    assert gen.self_check(solidified)

    malformed_blue = _extend_component(ordinary, tall["cells"])
    assert gen.self_check(malformed_blue)


def test_determinism_fresh_returns_and_global_rng_purity():
    state = random.getstate()
    first = gen.generate(9101, 11, difficulty="medium")
    assert random.getstate() == state
    second = gen.generate(9101, 11, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))


def test_three_demo_schedule_identifies_the_query():
    pairs = []
    for sample_index in range(4):
        grid = gen.generate(1234567, sample_index, difficulty="medium")
        pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
    assert gen.lesson_identifiable(pairs[:3], pairs[3]) == []
