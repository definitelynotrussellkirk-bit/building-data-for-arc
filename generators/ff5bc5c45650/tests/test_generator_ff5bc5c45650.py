from __future__ import annotations

import copy
import json
import random
from pathlib import Path

import pytest

from puzzle_generators import base
from puzzle_generators.per_puzzle.ff5bc5c45650 import generator as gen


ROOT = Path(__file__).resolve().parents[1]


def _canonical_inputs():
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == gen.TASK_ID:
            return [pair["input"] for pair in row["train"]] + [row["test"]["input"]]
    raise AssertionError("canonical task missing")


def test_canonical_inputs_are_accepted_and_strict():
    for grid in _canonical_inputs():
        assert gen.self_check(copy.deepcopy(grid)) == []
        assert gen.strict_canonical_like(copy.deepcopy(grid)) == []


def test_boundary_overrides_are_exact_and_observable():
    grid = gen.generate(
        17,
        29,
        difficulty="easy",
        grid_h=24,
        grid_w=24,
        n_shapes=5,
        max_size=16,
        palette_size=5,
        position_bias="right",
        vertical_bias="bottom",
    )
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == {
        "grid_h": 24,
        "grid_w": 24,
        "n_shapes": 5,
        "max_size": 16,
        "palette_size": 5,
        "position_bias": "right",
        "vertical_bias": "bottom",
    }


def test_incompatible_and_unknown_overrides_fail_loudly():
    with pytest.raises(ValueError, match="palette_size"):
        gen.generate(0, 0, n_shapes=1, palette_size=5)
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(0, 0, misspelled_axis=1)


def test_mutation_fixtures_are_rejected():
    fixtures = gen.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert gen.self_check(grid), name


def test_rivals_are_refuted_and_lesson_schedule_is_identifiable():
    pairs = []
    for index in range(4):
        grid = gen.generate(123, index, difficulty="medium")
        _, output = gen._target_and_output(grid)
        pairs.append({"input": grid, "output": output})
    assert gen.lesson_identifiable(pairs[:3], pairs[3]) == []
    assert any(gen._first_component_is_not_target(pair["input"]) for pair in pairs[:3])
    for name, rival in gen.SEMANTIC_RIVALS.items():
        assert any(rival(pair["input"]) != pair["output"] for pair in pairs[:3]), name


def test_replay_fresh_returns_and_global_rng_purity():
    random.seed(991)
    before = random.getstate()
    first = gen.generate(42, 7, difficulty="hard")
    after = random.getstate()
    second = gen.generate(42, 7, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert first != second

def test_every_four_consecutive_examples_refute_first_component_shortcut():
    for difficulty in ("easy", "medium", "hard"):
        for start in (0, 11, 22, 33):
            grids = [gen.generate(12345, start + offset, difficulty=difficulty) for offset in range(4)]
            assert any(gen._first_component_is_not_target(grid) for grid in grids)

def test_default_draw_provenance_matches_returned_grid():
    for difficulty in ("easy", "medium", "hard"):
        for offset in range(24):
            captured = []
            base.set_ctx_observer(captured.append)
            try:
                grid = gen.generate(80_000 + offset, 300 + offset, difficulty=difficulty)
            finally:
                base.set_ctx_observer(None)
            assert len(captured) == 1
            assert captured[0].recorded_draws() == gen.observe_overrides(grid)
            assert captured[0].overrides_used() == {}

def test_every_selected_shape_refutes_crop_and_one_profile_shortcuts():
    for shapes in gen._SHAPES_BY_SIZE.values():
        for mask in shapes:
            grid = [[0] * (max(c for _, c in mask) + 1) for _ in range(max(r for r, _ in mask) + 1)]
            for row, col in mask:
                grid[row][col] = 4
            expected = gen._intersection_for_cells(mask)
            assert expected != gen._rival_crop_largest(grid)
            assert expected != gen._rival_row_histogram(grid)
            assert expected != gen._rival_col_histogram(grid)

