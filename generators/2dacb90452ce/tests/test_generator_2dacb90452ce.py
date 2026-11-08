"""Regression and curriculum-contract tests for 2dacb90452ce."""
from __future__ import annotations

import copy
import importlib.util
import os
import random
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "2dacb90452ce"
HOME = Path(__file__).resolve().parents[1]
CANONICAL_PALETTE_BY_SIZE = {2: 3, 3: 4, 4: 5, 5: 8}
ALLOWED_PALETTES_BY_SIZE = {
    2: {2, 3, 4},
    3: {3, 4, 5},
    4: {4, 5, 6},
    5: {7, 8, 9},
}


def _load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py")).resolve()
    spec = importlib.util.spec_from_file_location(f"reviewed_{TASK_ID}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()
PAIRS = canonical_pairs(TASK_ID, root=find_root(__file__))


def test_rule_hash_and_every_canonical_pair_are_pinned_and_accepted():
    assert gen.RULE_HASH == "511f58f5d471"
    assert len(PAIRS) == 4
    for pair in PAIRS:
        original = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_axis_surface_is_small_exact_and_observable_in_every_band():
    assert gen.AXES == {
        "grid_size": {
            "type": "int",
            "default": "difficulty-skewed 2..5",
            "valid": "2..5",
            "doc": "Square input side length; palette profile follows the canonical task.",
        }
    }
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []

    for band in (None, "easy", "medium", "hard"):
        for size in (2, 3, 4, 5):
            grid = gen.generate(91 + size, size, difficulty=band, grid_size=size)
            assert len(grid) == len(grid[0]) == size
            assert gen.observe_overrides(grid) == {"grid_size": size}
            palette_count = len({value for row in grid for value in row})
            assert palette_count in ALLOWED_PALETTES_BY_SIZE[size]
            assert gen.self_check(grid) == []


def test_unknown_override_is_rejected_instead_of_silently_ignored():
    with pytest.raises((TypeError, ValueError), match="unknown override"):
        gen.generate(7, 1, difficulty="medium", typo_axis=4)


def test_distribution_mixes_canonical_and_neighboring_profiles_and_refutes_rivals():
    seen_profiles = set()
    exact = off_profile = 0
    assert "canonical_profile_only_else_grid_tile" in gen.CANONICAL_SHORTCUTS
    assert set(gen.CANONICAL_SHORTCUTS) <= set(gen.SEMANTIC_RIVALS)

    for band_index, band in enumerate(("easy", "medium", "hard")):
        for index in range(60):
            grid = gen.generate(20_000 + 100 * band_index + index, index, difficulty=band)
            size = len(grid)
            palette_count = len({value for row in grid for value in row})
            profile = (size, len(grid[0]), palette_count)
            seen_profiles.add(profile)
            assert profile[:2] == (size, size)
            assert palette_count in ALLOWED_PALETTES_BY_SIZE[size]
            expected = gen.rule_mirror(grid)
            assert gen.self_check(grid) == []
            if palette_count == CANONICAL_PALETTE_BY_SIZE[size]:
                exact += 1
                assert gen.strict_canonical_like(grid) == []
            else:
                off_profile += 1
                assert gen.strict_canonical_like(grid)
                assert gen.CANONICAL_SHORTCUTS[
                    "canonical_profile_only_else_grid_tile"
                ](grid) != expected
            for name, rival in gen.SEMANTIC_RIVALS.items():
                if (
                    name == "canonical_profile_only_else_grid_tile"
                    and palette_count == CANONICAL_PALETTE_BY_SIZE[size]
                ):
                    assert rival(grid) == expected
                else:
                    assert rival(grid) != expected

    assert exact > 0
    assert off_profile > 0
    assert {profile[:2] for profile in seen_profiles} == {
        (2, 2), (3, 3), (4, 4), (5, 5)
    }
    assert all(
        any(profile[0] == size and profile[2] != CANONICAL_PALETTE_BY_SIZE[size]
            for profile in seen_profiles)
        for size in CANONICAL_PALETTE_BY_SIZE
    )


def test_two_demo_lessons_are_identifiable_against_every_declared_competitor():
    assert gen.EXAMPLES_NEEDED == 2
    assert set(gen.LESSON_COMPETITORS) == set(gen.SEMANTIC_RIVALS)
    for band in ("easy", "medium", "hard"):
        for start in range(12):
            demos = []
            for offset in range(gen.EXAMPLES_NEEDED):
                grid = gen.generate(30_000 + start, start + offset, difficulty=band)
                demos.append({"input": grid, "output": gen.rule_mirror(grid)})
            query_grid = gen.generate(
                31_000 + start, start + gen.EXAMPLES_NEEDED, difficulty=band
            )
            query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
            assert gen.lesson_identifiable(demos, query) == []


def test_self_check_rejects_declared_structural_impostors():
    fixtures = list(gen.mutation_fixtures())
    assert len(fixtures) >= 5
    for name, grid in fixtures:
        errors = gen.self_check(grid)
        assert errors, f"declared impostor {name!r} unexpectedly passed"


@pytest.mark.parametrize(
    "grid",
    [None, [], [[]], [[0], [0, 1]], [[True, 1], [2, 3]]],
)
def test_malformed_grid_is_diagnostic_not_exception(grid):
    assert gen.self_check(grid)


def test_generation_is_repeatable_fresh_and_global_rng_pure():
    random.seed(20261004)
    state = random.getstate()
    first = gen.generate(99, 17, difficulty="hard")
    second = gen.generate(99, 17, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(row_a is not row_b for row_a, row_b in zip(first, second))
    assert random.getstate() == state
    first[0][0] = (first[0][0] + 1) % 10
    assert first != second
