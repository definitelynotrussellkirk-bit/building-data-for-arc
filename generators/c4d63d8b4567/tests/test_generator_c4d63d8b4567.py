from __future__ import annotations

import copy
from collections import Counter
import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash


TASK_ID = "c4d63d8b4567"
gen = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")


def _pair(grid):
    return {"input": copy.deepcopy(grid), "output": gen.rule_mirror(grid)}


def _global_exactly_two_rival(grid):
    """Plausible shortcut: suppress any color not occurring twice globally."""
    source = [list(row) for row in grid]
    output = [row[:] for row in source]
    height, width = len(source), len(source[0])
    counts = Counter(value for row in source for value in row if value)
    eligible = [color for color, count in counts.items() if count == 2]

    for row in range(height):
        for color in eligible:
            columns = [col for col in range(width) if source[row][col] == color]
            if len(columns) == 2:
                start, end = min(columns), max(columns)
                if all(source[row][col] == 0 for col in range(start + 1, end)):
                    for col in range(start, end + 1):
                        output[row][col] = color

    for col in range(width):
        for color in eligible:
            rows = [row for row in range(height) if source[row][col] == color]
            if len(rows) == 2:
                start, end = min(rows), max(rows)
                if all(source[row][col] == 0 for row in range(start + 1, end)):
                    for row in range(start, end + 1):
                        output[row][col] = color
    return output


def test_rule_hash_and_all_canonical_pairs_match_authority():
    assert gen.RULE_HASH == canonical_rule_hash(TASK_ID)
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 5
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert gen.self_check(original) == []
        assert gen.strict_canonical_like(original) == []
        assert gen.rule_mirror(original) == pair["output"]
        assert original == pair["input"]


def test_scene_profile_override_is_exact_and_unknown_axes_reject():
    for profile in gen.SCENE_PROFILES:
        for band in ("easy", "medium", "hard"):
            grid = gen.generate(19, 7, difficulty=band, scene_profile=profile)
            assert gen.observe_overrides(grid) == {"scene_profile": profile}
            assert gen.self_check(grid) == []
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, typo_axis="p7x8_2")


def test_four_sample_schedule_refutes_every_named_lesson_competitor():
    for start in range(8):
        demos = [
            _pair(gen.generate(200 + start, index, difficulty="medium"))
            for index in range(start, start + gen.EXAMPLES_NEEDED)
        ]
        query = _pair(
            gen.generate(
                200 + start,
                start + gen.EXAMPLES_NEEDED,
                difficulty="medium",
            )
        )
        scheduled = {
            gen.schedule_profile(0, index) for index in range(start, start + 4)
        }
        assert scheduled == {0, 1, 2, 3}
        assert gen.lesson_identifiable(demos, query) == []


def test_four_sample_schedule_refutes_global_exactly_two_shortcut():
    for start in range(8):
        grids = [
            gen.generate(700 + start, index, difficulty="medium")
            for index in range(start, start + gen.EXAMPLES_NEEDED)
        ]
        assert any(
            any(
                count > 2
                for count in Counter(
                    value for row in grid for value in row if value
                ).values()
            )
            for grid in grids
        )
        assert any(
            _global_exactly_two_rival(grid) != gen.rule_mirror(grid)
            for grid in grids
        )


def test_schedule_exposes_blocked_off_axis_and_both_orientations():
    grids = [gen.generate(321, index, difficulty="hard") for index in range(4)]
    assert any(gen.SEMANTIC_WITNESSES["blocked_pair"](grid) for grid in grids)
    assert any(gen.SEMANTIC_WITNESSES["off_axis_pair"](grid) for grid in grids)
    assert any(gen.SEMANTIC_WITNESSES["horizontal_active"](grid) for grid in grids)
    assert any(gen.SEMANTIC_WITNESSES["vertical_active"](grid) for grid in grids)
    assert any(gen.SEMANTIC_WITNESSES["multiple_active_pairs"](grid) for grid in grids)
    assert any(gen.SEMANTIC_WITNESSES["repeated_color"](grid) for grid in grids)


def test_named_mutation_fixtures_are_rejected():
    fixtures = gen.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert gen.self_check(grid), name


def test_deterministic_fresh_returns_and_global_rng_purity():
    random.seed(991827)
    before = random.getstate()
    first = gen.generate(88, 3, difficulty="easy")
    middle = random.getstate()
    second = gen.generate(88, 3, difficulty="easy")
    after = random.getstate()
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert before == middle == after


def test_difficulty_changes_layout_without_changing_validity():
    outputs = [
        gen.generate(404, 6, difficulty=band)
        for band in ("easy", "medium", "hard")
    ]
    assert len({repr(grid) for grid in outputs}) >= 2
    assert all(gen.self_check(grid) == [] for grid in outputs)
