"""Focused regression tests for generator 6d06c5b96c19."""
from __future__ import annotations

import copy
import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs


gen = importlib.import_module("puzzle_generators.per_puzzle.6d06c5b96c19.generator")


def _canonical_inputs():
    return [pair["input"] for pair in canonical_pairs(gen.TASK_ID)]


def test_rule_hash_and_canonical_inputs_are_pinned():
    assert gen.RULE_HASH == "9b7b9cf11c40"
    inputs = _canonical_inputs()
    assert len(inputs) == 4
    for grid in inputs:
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []


def test_true_rule_is_downward_rotation_not_marker_to_bottom():
    grid = [
        [7, 1, 1],
        [7, 3, 3],
        [2, 4, 4],
        [7, 5, 5],
        [7, 6, 6],
        [7, 8, 8],
    ]
    assert gen.rule_mirror(grid) == [
        [6, 6],
        [8, 8],
        [1, 1],
        [3, 3],
        [4, 4],
        [5, 5],
    ]
    assert gen.rule_mirror(grid) != gen._rival_move_marker_row_to_bottom(grid)
    assert gen.rule_mirror(grid) != gen._rival_rotate_up_by_marker(grid)


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_declared_axes_are_exact_and_observable(difficulty):
    for h, w, red, palette_size in ((5, 6, 0, 3), (14, 15, 13, 6), (8, 10, 4, 5)):
        grid = gen.generate(
            101,
            3,
            difficulty=difficulty,
            grid_h=h,
            grid_w=w,
            red_row_index=red,
            payload_palette_size=palette_size,
        )
        assert gen.observe_overrides(grid) == {
            "grid_h": h,
            "grid_w": w,
            "red_row_index": red,
            "payload_palette_size": palette_size,
        }
        assert gen.self_check(grid) == []


def test_unknown_and_incompatible_overrides_are_rejected():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, typo_axis=4)
    with pytest.raises(ValueError, match="does not fit") as exc_info:
        gen.generate(1, 0, grid_h=5, red_row_index=13)
    assert set(exc_info.value.incompatible_axes) == {"grid_h", "red_row_index"}


def test_schedule_covers_canonical_and_decisive_marker_branches():
    grids = [gen.generate(202, i, difficulty="hard") for i in range(8)]
    assert {gen.schedule_profile(202, i, "hard") for i in range(8)} == set(gen.SCHEDULE_PROFILES)
    assert sum(gen.strict_canonical_like(grid) == [] for grid in grids) == 4
    assert any(gen.SEMANTIC_WITNESSES["top_marker_means_zero_shift"](g) for g in grids)
    assert any(gen.SEMANTIC_WITNESSES["downward_direction_is_distinguishable"](g) for g in grids)
    assert any(gen.SEMANTIC_WITNESSES["bottom_marker_wraps_cyclically"](g) for g in grids)


def test_self_check_rejects_decisive_mutations():
    grid = gen.generate(303, 5, difficulty="medium")
    assert gen.self_check(grid) == []

    missing_red = copy.deepcopy(grid)
    red_row = gen.observe_overrides(missing_red)["red_row_index"]
    missing_red[red_row][0] = missing_red[(red_row + 1) % len(grid)][0]
    assert any("exactly one red" in err for err in gen.self_check(missing_red))

    two_reds = copy.deepcopy(grid)
    two_reds[(red_row + 1) % len(grid)][0] = 2
    assert any("exactly one red" in err for err in gen.self_check(two_reds))

    mixed_instruction = copy.deepcopy(grid)
    row = (red_row + 1) % len(grid)
    replacement = next(c for c in range(10) if c not in {2, mixed_instruction[row][0]})
    mixed_instruction[row][0] = replacement
    assert any("share one" in err for err in gen.self_check(mixed_instruction))

    leaked_instruction = copy.deepcopy(grid)
    marker = next(row[0] for row in leaked_instruction if row[0] != 2)
    leaked_instruction[0][1] = marker
    assert any("must not appear" in err for err in gen.self_check(leaked_instruction))


def test_consecutive_lessons_refute_named_rivals():
    for start in range(24):
        demos = []
        for sample_index in range(start, start + gen.EXAMPLES_NEEDED):
            grid = gen.generate(404, sample_index, difficulty="hard")
            demos.append({"input": grid, "output": gen.rule_mirror(grid)})
        query_grid = gen.generate(404, start + gen.EXAMPLES_NEEDED, difficulty="hard")
        query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
        assert gen.lesson_identifiable(demos, query) == []


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(8675309)
    before = random.getstate()
    first = gen.generate(505, 7, difficulty="medium")
    second = gen.generate(505, 7, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert gen.generate(505, 7, difficulty="medium") == second
    assert random.getstate() == before
