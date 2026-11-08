"""Focused regressions for generator 93d3caa82997."""
from __future__ import annotations

import copy
import importlib
import itertools
import json
import random
from pathlib import Path

import pytest


TASK_ID = "93d3caa82997"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
ROOT = Path(__file__).resolve().parents[1]


def _canonical_row() -> dict:
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError("canonical task row missing")


def test_rule_hash_and_all_canonical_pairs_are_pinned() -> None:
    assert GEN.RULE_HASH == "f3ff69e38bd8"
    row = _canonical_row()
    pairs = row["train"] + row["test"]
    assert len(pairs) == 5
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN._solve_grid(pair["input"]) == pair["output"]
        assert pair["input"] == original


@pytest.mark.parametrize(
    "grid_h,grid_w,shape_pair,selector_layout,distractor_count",
    itertools.product((10, 12), (12, 15), range(8), range(3), (1, 2)),
)
def test_every_boundary_override_tuple_is_exact_and_observable(
    grid_h: int,
    grid_w: int,
    shape_pair: int,
    selector_layout: int,
    distractor_count: int,
) -> None:
    requested = {
        "grid_h": grid_h,
        "grid_w": grid_w,
        "shape_pair": shape_pair,
        "selector_layout": selector_layout,
        "distractor_count": distractor_count,
    }
    grid = GEN.generate(7301, shape_pair * 10 + selector_layout, difficulty="hard", **requested)
    assert GEN.observe_overrides(grid) == requested
    assert GEN.self_check(grid) == []


def test_unknown_override_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 2, mystery_axis=7)


def test_deterministic_fresh_and_global_rng_pure() -> None:
    random.seed(99173)
    before = random.getstate()
    first = GEN.generate(19, 7, difficulty="medium")
    after = random.getstate()
    second = GEN.generate(19, 7, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    assert before == after
    first[0][0] = 9
    assert GEN.generate(19, 7, difficulty="medium") == second


def test_every_generated_draw_refutes_all_declared_rivals() -> None:
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for sample_index in range(40):
            grid = GEN.generate(8800 + band_index, sample_index, difficulty=band)
            expected = GEN._solve_grid(grid)
            for name, rival in GEN.SEMANTIC_RIVALS.items():
                assert rival(grid) != expected, (band, sample_index, name)


def test_self_check_rejects_targeted_impostors() -> None:
    grid = GEN.generate(
        123,
        5,
        difficulty="medium",
        grid_h=12,
        grid_w=15,
        shape_pair=0,
        selector_layout=0,
        distractor_count=2,
    )

    missing_selector = copy.deepcopy(grid)
    missing_selector[0][3] = 0
    assert GEN.self_check(missing_selector)

    dirty_separator = copy.deepcopy(grid)
    dirty_separator[1][0] = 6
    assert GEN.self_check(dirty_separator)

    no_distractor = copy.deepcopy(grid)
    _a, _b, _first, _second, distractors = GEN._scene(no_distractor)
    for obj in distractors:
        for row, col in obj.cells:
            no_distractor[row + 1][col] = 0
    assert GEN.self_check(no_distractor)

    duplicate_selected_component = copy.deepcopy(grid)
    a, _b, first, _second, _distractors = GEN._scene(duplicate_selected_component)
    occupied = {(r + 1, c) for obj in GEN._components(duplicate_selected_component[1:]) for r, c in obj.cells}
    new_cell = next(
        (r, c)
        for r in range(2, len(grid))
        for c in range(len(grid[0]))
        if (r, c) not in occupied
        and all((r + dr, c + dc) not in occupied for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        and not (first.top <= r - 1 <= first.bottom and first.left <= c <= first.right)
    )
    duplicate_selected_component[new_cell[0]][new_cell[1]] = a
    assert GEN.self_check(duplicate_selected_component)

    illegal_selected_shape = copy.deepcopy(grid)
    _a, _b, _first, second, _distractors = GEN._scene(illegal_selected_shape)
    illegal_selected_shape[second.top + 1][second.left] = 0
    assert GEN.self_check(illegal_selected_shape)


def test_lesson_identifiability_and_negative_recombination_probe() -> None:
    pairs = []
    for sample_index in range(4):
        grid = GEN.generate(456, sample_index, difficulty="hard")
        pairs.append({"input": grid, "output": GEN._solve_grid(grid)})
    assert GEN.lesson_identifiable(pairs[:3], pairs[3]) == []

    for name, rival in GEN.LESSON_COMPETITORS.items():
        malformed = copy.deepcopy(pairs)
        malformed[0]["output"] = rival(malformed[0]["input"])
        reasons = GEN.lesson_identifiable(malformed[:3], malformed[3])
        assert reasons, name
        assert any("disagrees" in reason or "competitor" in reason for reason in reasons), (name, reasons)
