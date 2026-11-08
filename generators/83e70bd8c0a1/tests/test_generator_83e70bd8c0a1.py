"""Regression tests for the 83e70bd8c0a1 anti-diagonal reflection sampler."""
from __future__ import annotations

import copy
import importlib
import itertools
import random

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "83e70bd8c0a1"
GEN = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)


def _pairs() -> list[dict]:
    return canonical_pairs(TASK_ID, root=find_root(__file__))


def test_rule_pin_and_canonical_pairs_match_independent_geometry_oracle():
    assert GEN.RULE_HASH == "ea62a41435bf"
    pairs = _pairs()
    assert len(pairs) == 3
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        n = len(source)
        expected = [
            [source[n - 1 - c][n - 1 - r] for c in range(n)]
            for r in range(n)
        ]
        assert GEN.self_check(source) == []
        assert GEN.rule_mirror(source) == expected == pair["output"]
        assert source == pair["input"]


def test_default_draws_stay_on_profile_and_refute_every_declared_rival():
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(24):
            grid = GEN.generate(711, sample_index, difficulty=difficulty)
            assert GEN.self_check(grid, difficulty=difficulty) == []
            assert GEN.strict_canonical_like(grid) == []
            assert len(grid) == len(grid[0])
            assert 5 <= len(grid) <= 7
            assert len({value for row in grid for value in row}) == 7

            intended = GEN.rule_mirror(grid)
            for name, witness in GEN.SEMANTIC_WITNESSES.items():
                assert witness(grid), (difficulty, sample_index, name)
            for name, rival in GEN.SEMANTIC_RIVALS.items():
                assert rival(grid) != intended, (difficulty, sample_index, name)


def test_generation_is_deterministic_fresh_and_global_random_pure():
    random.seed(314159)
    state = random.getstate()
    first = GEN.generate(12345, 7, difficulty="medium")
    assert random.getstate() == state
    second = GEN.generate(12345, 7, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))


def test_exact_override_boundaries_are_observable_in_every_band():
    domains = {
        "grid_size": (5, 7),
        "diagonal_marks": (1, 3),
        "mirror_pairs": (1, 2),
        "singletons": (4, 5),
    }
    names = tuple(domains)
    case = 0
    for difficulty in ("easy", "medium", "hard"):
        for values in itertools.product(*(domains[name] for name in names)):
            requested = dict(zip(names, values))
            grid = GEN.generate(
                9200 + case,
                case,
                difficulty=difficulty,
                **requested,
            )
            assert GEN.observe_overrides(grid) == requested
            assert GEN.self_check(
                grid,
                difficulty=difficulty,
                meta={"overrides": requested},
            ) == []
            case += 1


@pytest.mark.parametrize(
    "kwargs,match",
    [
        ({"unknown_axis": 1}, "unknown override"),
        ({"grid_size": 4}, "grid_size"),
        ({"grid_size": 8}, "grid_size"),
        ({"diagonal_marks": 0}, "diagonal_marks"),
        ({"diagonal_marks": 4}, "diagonal_marks"),
        ({"mirror_pairs": 0}, "mirror_pairs"),
        ({"mirror_pairs": 3}, "mirror_pairs"),
        ({"singletons": 3}, "singletons"),
        ({"singletons": 6}, "singletons"),
        ({"grid_size": True}, "integer"),
        ({"grid_size": "6"}, "integer"),
        ({"difficulty": "extreme"}, "difficulty"),
    ],
)
def test_invalid_generation_requests_fail_loudly(kwargs, match):
    with pytest.raises((TypeError, ValueError), match=match):
        GEN.generate(1, 0, **kwargs)


def test_every_cyclic_query_rotation_remains_identifiable():
    for difficulty in ("easy", "medium", "hard"):
        for lesson_index in range(12):
            items = []
            for offset in range(GEN.EXAMPLES_NEEDED + 1):
                sample_index = lesson_index * 17 + offset
                grid = GEN.generate(404, sample_index, difficulty=difficulty)
                items.append({"input": grid, "output": GEN.rule_mirror(grid)})

            for query_index in range(len(items)):
                query = items[query_index]
                demos = [
                    item for index, item in enumerate(items)
                    if index != query_index
                ]
                assert GEN.lesson_identifiable(demos, query) == []
                for name, rival in GEN.LESSON_COMPETITORS.items():
                    assert any(
                        rival(demo["input"]) != demo["output"]
                        for demo in demos
                    ), (difficulty, lesson_index, query_index, name)


def test_declared_canonical_shortcut_is_real_and_has_generated_counterexamples():
    assert set(GEN.CANONICAL_SHORTCUTS) == {"reflect_only_unique_colors"}
    for name, shortcut in GEN.CANONICAL_SHORTCUTS.items():
        for pair in _pairs():
            assert shortcut(pair["input"]) == pair["output"], name
        for difficulty in ("easy", "medium", "hard"):
            for sample_index in range(12):
                grid = GEN.generate(808, sample_index, difficulty=difficulty)
                assert shortcut(grid) != GEN.rule_mirror(grid), (
                    name,
                    difficulty,
                    sample_index,
                )


def test_self_check_rejects_structural_impostors():
    valid = GEN.generate(99, 3)
    bad_cases = {
        "empty": [],
        "blank": [[0 for _ in range(6)] for _ in range(6)],
        "ragged": [[0, 0], [0]],
        "rectangle": [[0 for _ in range(6)] for _ in range(5)],
        "out_of_range": copy.deepcopy(valid),
        "too_few_colors": copy.deepcopy(valid),
        "no_fixed_points": copy.deepcopy(valid),
    }
    bad_cases["out_of_range"][0][0] = 10
    for row in bad_cases["too_few_colors"]:
        for column, value in enumerate(row):
            if value:
                row[column] = 1
    n = len(bad_cases["no_fixed_points"])
    for r in range(n):
        bad_cases["no_fixed_points"][r][n - 1 - r] = 0

    for name, grid in bad_cases.items():
        assert GEN.self_check(grid), name
