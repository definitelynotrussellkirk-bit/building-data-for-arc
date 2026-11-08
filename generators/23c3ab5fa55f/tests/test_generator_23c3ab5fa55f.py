"""Focused semantic regression tests for ARC generator 23c3ab5fa55f."""

from __future__ import annotations

import copy
import json
import random
from pathlib import Path

import pytest

from puzzle_generators import base
from puzzle_generators.runner import _load_generator_module


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "23c3ab5fa55f"
GENERATOR = _load_generator_module(TASK_ID)
BANDS = ("easy", "medium", "hard")


def _canonical_pairs():
    with (ROOT / "data" / "canonical" / "puzzles.jsonl").open(
        encoding="utf-8"
    ) as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return list(row["train"]) + list(row["test"])
    raise KeyError(TASK_ID)


def _independent_rule(grid):
    width = len(grid[0])
    return [
        [value for value in row if value != 0]
        + [0] * (width - sum(value != 0 for value in row))
        for row in grid
    ]


def _tuple_grid(grid):
    return tuple(tuple(row) for row in grid)


def test_all_canonical_pairs_match_row_local_stable_compaction():
    pairs = _canonical_pairs()
    assert len(pairs) == 5
    seen_profiles = set()
    for pair in pairs:
        grid = copy.deepcopy(pair["input"])
        before = copy.deepcopy(grid)
        expected = pair["output"]
        assert GENERATOR.self_check(grid) == []
        assert _independent_rule(grid) == expected
        assert GENERATOR.rule_mirror(grid) == expected
        assert grid == before
        signature = GENERATOR.canonical_profile_signature(grid)
        assert signature is not None
        seen_profiles.add(signature)
    assert seen_profiles == GENERATOR._CANONICAL_PROFILES


def test_default_draws_are_replayable_fresh_and_provenance_exact():
    global_state = random.getstate()
    for band in BANDS:
        for seed in range(60):
            captured = []
            base.set_ctx_observer(captured.append)
            try:
                first = GENERATOR.generate(
                    seed,
                    seed * 101 + 7,
                    difficulty=band,
                )
            finally:
                base.set_ctx_observer(None)
            second = GENERATOR.generate(
                seed,
                seed * 101 + 7,
                difficulty=band,
            )
            assert first == second
            assert first is not second
            assert all(left is not right for left, right in zip(first, second))
            assert GENERATOR.self_check(first) == []
            assert GENERATOR.observe_overrides(first) == {
                name: captured[-1]._drawn[name]
                for name in GENERATOR.AXES
            }
            original = second[0][0]
            first[0][0] = (first[0][0] + 1) % 10
            replay = GENERATOR.generate(
                seed,
                seed * 101 + 7,
                difficulty=band,
            )
            assert replay[0][0] == original
    assert random.getstate() == global_state


def test_exact_axis_boundaries_and_incompatibilities():
    boundary_calls = (
        {"grid_h": 6},
        {"grid_h": 10},
        {"grid_w": 8},
        {"grid_w": 13},
        {"active_rows": 3},
        {"active_rows": 8},
        {"n_distinct_colors": 2},
        {"n_distinct_colors": 8},
        {
            "grid_h": 8,
            "grid_w": 9,
            "active_rows": 8,
            "n_distinct_colors": 8,
        },
    )
    for band in BANDS:
        for index, overrides in enumerate(boundary_calls):
            grid = GENERATOR.generate(
                10_000 + index,
                20_000 + index,
                difficulty=band,
                **overrides,
            )
            observed = GENERATOR.observe_overrides(grid)
            assert GENERATOR.self_check(grid) == []
            for key, value in overrides.items():
                assert observed[key] == value

    with pytest.raises(ValueError, match="active_rows cannot exceed grid_h"):
        GENERATOR.generate(1, 2, grid_h=6, active_rows=8)
    with pytest.raises(ValueError):
        GENERATOR.generate(1, 2, grid_h=5)
    with pytest.raises(ValueError):
        GENERATOR.generate(1, 2, grid_w=14)
    with pytest.raises(ValueError):
        GENERATOR.generate(1, 2, n_distinct_colors=9)


def test_self_check_rejects_targeted_semantic_impostors():
    control = GENERATOR.generate(998_877, 1, difficulty="hard")
    assert GENERATOR.self_check(control) == []

    height, width = len(control), len(control[0])
    all_background = [[0] * width for _ in range(height)]
    one_color_field = [[1] * width for _ in range(height)]

    no_singletons = copy.deepcopy(control)
    for row in no_singletons:
        nonzero = [index for index, value in enumerate(row) if value]
        if len(nonzero) == 1:
            target = next(index for index, value in enumerate(row) if value == 0)
            row[target] = row[nonzero[0]]

    compacted = _independent_rule(control)

    no_descending = copy.deepcopy(control)
    for row in no_descending:
        columns = [index for index, value in enumerate(row) if value]
        values = sorted(row[index] for index in columns)
        for index, value in zip(columns, values):
            row[index] = value

    impostors = {
        "all_background": all_background,
        "one_color_field": one_color_field,
        "no_singletons": no_singletons,
        "already_compacted": compacted,
        "no_descending_order_witness": no_descending,
    }
    for name, grid in impostors.items():
        assert GENERATOR.self_check(grid), name

    # The Racket operation is total on the compacted recombination, but the
    # teaching distribution must reject it because it hides the operation.
    assert GENERATOR.rule_mirror(compacted) == compacted


def test_linked_canonical_prior_is_present_but_not_a_fixed_template():
    expected_minimum = {"easy": 90, "medium": 65, "hard": 40}
    expected_maximum = {"easy": 175, "medium": 155, "hard": 135}
    for seed_offset in (100_000, 200_000):
        for band in BANDS:
            matches = 0
            profiles = set()
            inputs = set()
            outputs = set()
            shapes = set()
            for offset in range(200):
                seed = seed_offset + offset
                grid = GENERATOR.generate(seed, seed * 17 + 3, difficulty=band)
                output = _independent_rule(grid)
                inputs.add(_tuple_grid(grid))
                outputs.add(_tuple_grid(output))
                shapes.add((len(grid), len(grid[0])))
                signature = GENERATOR.canonical_profile_signature(grid)
                if signature is not None:
                    matches += 1
                    profiles.add(signature)
            assert expected_minimum[band] <= matches <= expected_maximum[band]
            assert profiles == GENERATOR._CANONICAL_PROFILES
            assert len(inputs) == 200
            assert len(outputs) == 200
            assert len(shapes) >= 4


def test_each_generated_lesson_refutes_common_shortcuts():
    for band in BANDS:
        for seed in range(120):
            grid = GENERATOR.generate(
                300_000 + seed,
                seed * 29 + 5,
                difficulty=band,
            )
            facts = GENERATOR._analysis(grid)["facts"]
            assert facts["singleton_rows"] >= 1
            assert facts["shifted_contiguous_rows"] >= 1
            assert facts["internally_gapped_rows"] >= 1
            assert facts["descending_rows"] >= 1
            assert len(set(facts["row_counts"])) >= 2
            assert _independent_rule(grid) != grid
