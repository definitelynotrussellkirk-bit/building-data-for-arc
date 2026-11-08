from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from itertools import product
from pathlib import Path

import pytest

from puzzle_generators import base as generator_base

TASK_ID = "c9b2eae14052"
ROOT = Path(__file__).resolve().parents[1]
gen = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")


def _canonical_row() -> dict:
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        return next(json.loads(line) for line in handle if TASK_ID in line)


def _canonical_pairs() -> list[dict]:
    row = _canonical_row()
    return [*row["train"], *row["test"]]


def test_rule_hash_and_all_canonical_pairs_are_pinned_and_accepted():
    row = _canonical_row()
    normalized = " ".join(row["program_solution"].split())
    assert gen.RULE_HASH == hashlib.sha256(normalized.encode()).hexdigest()[:12]
    assert len(_canonical_pairs()) == 3
    for pair in _canonical_pairs():
        source = copy.deepcopy(pair["input"])
        assert gen.self_check(source) == []
        assert gen.strict_canonical_like(source) == []
        assert gen.rule_mirror(source) == pair["output"]
        assert source == pair["input"]


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_every_joint_override_boundary_is_exact_and_observable(difficulty):
    for sample_index, (height, width, count) in enumerate(
        product((8, 14), (7, 14), (3, 6))
    ):
        overrides = {"grid_h": height, "grid_w": width, "n_objects": count}
        grid = gen.generate(81_000, sample_index, difficulty=difficulty, **overrides)
        assert gen.self_check(grid) == []
        assert gen.observe_overrides(grid) == overrides
        assert gen.rule_mirror(grid) != grid


def test_default_keyed_axis_requests_equal_returned_grid_values():
    captured = []
    generator_base.set_ctx_observer(captured.append)
    try:
        for band in ("easy", "medium", "hard"):
            for index in range(40):
                grid = gen.generate(91_000 + index, index * 19 + 7, difficulty=band)
                draws = captured[-1].recorded_draws()
                assert gen.observe_overrides(grid) == {
                    axis: draws[axis] for axis in gen.AXES
                }
    finally:
        generator_base.set_ctx_observer(None)


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(20260725)
    state = random.getstate()
    first = gen.generate(117, 23, difficulty="hard", n_objects=6)
    assert random.getstate() == state
    second = gen.generate(117, 23, difficulty="hard", n_objects=6)
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert gen.generate(117, 23, difficulty="hard", n_objects=6) == second


def test_sequential_schedule_covers_every_side_and_both_size_rivals():
    for band in ("easy", "medium", "hard"):
        grids = [gen.generate(731, index, difficulty=band) for index in range(12)]
        for witness_name in (
            "top_target",
            "right_target",
            "bottom_target",
            "left_target",
            "interior_drop_present",
            "multi_border_drop_present",
            "target_strictly_smaller_than_a_drop",
            "target_strictly_larger_than_a_drop",
        ):
            assert any(gen.SEMANTIC_WITNESSES[witness_name](grid) for grid in grids)


def test_three_demo_lesson_refutes_named_shortcuts():
    for band in ("easy", "medium", "hard"):
        for start in range(12):
            pairs = []
            for offset in range(4):
                inp = gen.generate(44_000 + start, start + offset, difficulty=band)
                pairs.append({"input": inp, "output": gen.rule_mirror(inp)})
            assert gen.lesson_identifiable(pairs[:3], pairs[3]) == []
            for rival in gen.LESSON_COMPETITORS.values():
                assert not all(rival(pair["input"]) == pair["output"] for pair in pairs[:3])


def test_self_check_rejects_targeted_structural_impostors():
    valid = gen.generate(99, 0, grid_h=9, grid_w=9, n_objects=6)
    assert gen.self_check(valid) == []

    ragged = copy.deepcopy(valid)
    ragged[-1].pop()
    assert any("ragged" in error for error in gen.self_check(ragged))

    no_target = [[0] * 9 for _ in range(9)]
    no_target[2][2:4] = [1, 1]
    no_target[4][4:6] = [2, 2]
    no_target[6][2:4] = [3, 3]
    assert any("exactly-one-border" in error for error in gen.self_check(no_target))

    no_interior = [[0] * 9 for _ in range(9)]
    no_interior[0][2:4] = [1, 1]
    no_interior[3][0] = no_interior[4][0] = 2
    no_interior[-1][4:6] = [3, 3]
    assert any("interior object" in error for error in gen.self_check(no_interior))

    touching_colors = copy.deepcopy(valid)
    records = gen._analysis(touching_colors)["records"]
    r, c = next(
        (nr, nc)
        for cell in records[0]["cells"]
        for nr, nc in gen._orthogonal_neighbors(cell)
        if 0 <= nr < len(touching_colors)
        and 0 <= nc < len(touching_colors[0])
        and touching_colors[nr][nc] == 0
    )
    touching_colors[r][c] = records[1]["color"]
    assert any("touch orthogonally" in error for error in gen.self_check(touching_colors))

    repeated_color = copy.deepcopy(valid)
    records = gen._analysis(repeated_color)["records"]
    for r, c in records[-1]["cells"]:
        repeated_color[r][c] = records[0]["color"]
    assert any("reused" in error for error in gen.self_check(repeated_color))

    singleton = copy.deepcopy(valid)
    records = gen._analysis(singleton)["records"]
    for r, c in records[0]["cells"][1:]:
        singleton[r][c] = 0
    assert any("expected 2..4" in error for error in gen.self_check(singleton))


def test_unknown_and_removed_legacy_axes_fail_closed():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, palette_kind="warm")
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, texture="all_corner")
