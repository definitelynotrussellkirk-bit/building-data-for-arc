from __future__ import annotations

import copy
import json
import random
from pathlib import Path

import pytest

from puzzle_generators.per_puzzle.a6b5a6d9b5ef import generator as gen

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "data/canonical/puzzles.jsonl"


def _canonical_row():
    with CANONICAL.open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                return row
    raise AssertionError("canonical task row missing")


def test_canonical_inputs_and_outputs_match_rule():
    row = _canonical_row()
    pairs = row["train"] + [row["test"]]
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_exact_override_axes_are_observable_at_boundaries():
    cases = [
        dict(
            grid_h=8,
            grid_w=11,
            divider_col=4,
            n_blue=3,
            n_distractors=4,
            n_distractor_colors=1,
            n_target_collisions=1,
        ),
        dict(
            grid_h=18,
            grid_w=20,
            divider_col=8,
            n_blue=10,
            n_distractors=12,
            n_distractor_colors=3,
            n_target_collisions=2,
        ),
    ]
    for index, overrides in enumerate(cases):
        grid = gen.generate(3100 + index, index, difficulty="hard", **overrides)
        assert gen.observe_overrides(grid) == overrides
        assert gen.self_check(grid, meta={"overrides": overrides}) == []


def test_unknown_override_rejected():
    with pytest.raises(TypeError, match="unknown override"):
        gen.generate(1, 0, imaginary_axis=4)


def test_regression_degenerate_and_structure_destroying_impostors_rejected():
    valid = gen.generate(44, 3, difficulty="medium")
    h, w = len(valid), len(valid[0])
    divider = gen.observe_overrides(valid)["divider_col"]

    impostors = []
    impostors.append([[0 for _ in range(w)] for _ in range(h)])

    no_divider = copy.deepcopy(valid)
    for row in range(h):
        no_divider[row][divider] = 0
    impostors.append(no_divider)

    no_blue = copy.deepcopy(valid)
    for row in range(h):
        for col in range(w):
            if no_blue[row][col] == 1:
                no_blue[row][col] = 0
    impostors.append(no_blue)

    blue_right = copy.deepcopy(valid)
    source = next(
        (row, col)
        for row in range(h)
        for col in range(w)
        if blue_right[row][col] == 1
    )
    blue_right[source[0]][source[1]] = 0
    blue_right[source[0]][divider + 1] = 1
    impostors.append(blue_right)

    disconnected = copy.deepcopy(valid)
    blue_cells = [
        (row, col)
        for row in range(h)
        for col in range(w)
        if disconnected[row][col] == 1
    ]
    for row, col in blue_cells:
        disconnected[row][col] = 0
    disconnected[0][0] = 1
    disconnected[h - 1][min(divider - 1, w - 1)] = 1
    impostors.append(disconnected)

    for grid in impostors:
        assert gen.self_check(grid), "malformed scene unexpectedly accepted"


def test_collision_is_overwritten_and_other_distractors_are_preserved():
    grid = gen.generate(
        91,
        2,
        grid_h=10,
        grid_w=13,
        divider_col=6,
        n_blue=6,
        n_distractors=8,
        n_distractor_colors=2,
        n_target_collisions=2,
    )
    before = gen._analysis(grid)
    output = gen.rule_mirror(grid)
    collision_cells = {(row, col) for row, col, _ in before["target_collisions"]}
    assert len(collision_cells) == 2
    assert all(output[row][col] == 8 for row, col in collision_cells)
    for row, col, value in before["distractors"]:
        if (row, col) not in before["mirror_cells"]:
            assert output[row][col] == value


def test_generated_lesson_refutes_named_competitors():
    demos = []
    seed = 20260725
    for sample_index in range(gen.EXAMPLES_NEEDED):
        grid = gen.generate(seed, sample_index, difficulty="medium")
        demos.append({"input": grid, "output": gen.rule_mirror(grid)})
    query_grid = gen.generate(seed, gen.EXAMPLES_NEEDED, difficulty="medium")
    query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
    assert gen.lesson_identifiable(demos, query) == []
    for name, competitor in gen.LESSON_COMPETITORS.items():
        assert any(
            competitor(pair["input"]) != pair["output"] for pair in demos
        ), name


def test_replay_fresh_objects_and_global_rng_purity():
    random.seed(9981)
    state = random.getstate()
    first = gen.generate(12345, 7, difficulty="easy")
    assert random.getstate() == state
    second = gen.generate(12345, 7, difficulty="easy")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 99
    assert second[0][0] != 99
