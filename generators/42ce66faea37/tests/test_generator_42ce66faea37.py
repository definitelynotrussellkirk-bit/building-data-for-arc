"""Focused regression tests for the 42ce66faea37 generator repair."""
from __future__ import annotations

import copy
import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash


GENERATOR = importlib.import_module(
    "puzzle_generators.per_puzzle.42ce66faea37.generator"
)


def _grid(*rows: str) -> list[list[int]]:
    return [[int(cell) for cell in row] for row in rows]


def _pair(grid: list[list[int]]) -> dict[str, list[list[int]]]:
    return {"input": grid, "output": GENERATOR.rule_mirror(grid)}


def test_rule_hash_and_all_canonical_pairs_are_pinned() -> None:
    assert GENERATOR.RULE_HASH == canonical_rule_hash(GENERATOR.TASK_ID)
    pairs = canonical_pairs(GENERATOR.TASK_ID)
    assert len(pairs) == 5
    profiles = []
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert GENERATOR.self_check(pair["input"]) == []
        assert GENERATOR.strict_canonical_like(pair["input"]) == []
        assert GENERATOR.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original
        profiles.append(GENERATOR.observe_overrides(pair["input"])["scene_profile"])
    assert profiles.count("endpoint_owner_lower") == 1
    assert profiles.count("endpoint_owner_higher") == 1


def test_unknown_and_invalid_overrides_are_rejected() -> None:
    with pytest.raises(ValueError, match="unknown override"):
        GENERATOR.generate(1, 0, typo_axis="interior_cross")
    for overrides in (
        {"grid_h": 7},
        {"grid_w": 15},
        {"pair_count": 1},
        {"pair_count": True},
        {"scene_profile": "cross"},
    ):
        with pytest.raises(ValueError):
            GENERATOR.generate(1, 0, **overrides)


def test_every_axis_is_exact_and_observable_at_boundaries() -> None:
    cases = [
        {
            "grid_h": 8,
            "grid_w": 8,
            "pair_count": 2,
            "scene_profile": "disjoint",
        },
        {
            "grid_h": 8,
            "grid_w": 14,
            "pair_count": 4,
            "scene_profile": "interior_cross",
        },
        {
            "grid_h": 14,
            "grid_w": 8,
            "pair_count": 3,
            "scene_profile": "endpoint_owner_lower",
        },
        {
            "grid_h": 14,
            "grid_w": 14,
            "pair_count": 4,
            "scene_profile": "endpoint_owner_higher",
        },
    ]
    for index, overrides in enumerate(cases):
        grid = GENERATOR.generate(97, index, difficulty="hard", **overrides)
        assert GENERATOR.observe_overrides(grid) == overrides
        assert GENERATOR.self_check(grid, meta={"overrides": overrides}) == []


def test_four_sample_schedule_kills_all_named_rivals_in_every_sliding_window() -> None:
    for band in ("easy", "medium", "hard"):
        for seed in range(8):
            # Check every residue-class start, not just the aligned 0..3 window.
            for start in range(4):
                demos = [
                    _pair(GENERATOR.generate(seed, start + offset, difficulty=band))
                    for offset in range(GENERATOR.EXAMPLES_NEEDED)
                ]
                query = _pair(
                    GENERATOR.generate(
                        seed,
                        start + GENERATOR.EXAMPLES_NEEDED,
                        difficulty=band,
                    )
                )
                profiles = {
                    GENERATOR.observe_overrides(pair["input"])["scene_profile"]
                    for pair in demos
                }
                assert profiles == set(GENERATOR.SCHEDULE_PROFILES)
                assert GENERATOR.lesson_identifiable(demos, query) == []
                for name, competitor in GENERATOR.LESSON_COMPETITORS.items():
                    assert any(
                        competitor(pair["input"]) != pair["output"] for pair in demos
                    ), name


def test_overlap_color_priority_is_explicit_for_all_collision_profiles() -> None:
    for profile in (
        "interior_cross",
        "endpoint_owner_lower",
        "endpoint_owner_higher",
    ):
        grid = GENERATOR.generate(
            811,
            19,
            grid_h=10,
            grid_w=10,
            pair_count=2,
            scene_profile=profile,
        )
        analysis = GENERATOR._analyze(grid)
        output = GENERATOR.rule_mirror(grid)
        assert analysis["scene_profile"] == profile
        intersections = analysis["interior_crossings"] or analysis["endpoint_crossings"]
        assert intersections
        for (row, col), left_color, right_color in intersections:
            assert output[row][col] == max(left_color, right_color)


def test_self_check_rejects_four_rule_hiding_structural_impostors() -> None:
    one_color_only = _grid(
        "10000000",
        "01000000",
        "00100000",
        "00010000",
        "00000000",
        "00000000",
        "00000000",
        "00000000",
    )
    singleton_color = _grid(
        "10000002",
        "00000000",
        "00100000",
        "00000000",
        "00000000",
        "00000000",
        "00000000",
        "00000000",
    )
    axis_aligned_pair = _grid(
        "10000002",
        "00000000",
        "10000000",
        "00000000",
        "00000000",
        "00000000",
        "00000002",
        "00000000",
    )
    adjacent_diagonal_pairs = _grid(
        "12000000",
        "21000000",
        "00000000",
        "00000000",
        "00000000",
        "00000000",
        "00000000",
        "00000000",
    )
    duplicate_endpoint_count = _grid(
        "10000002",
        "01000020",
        "00100200",
        "00010000",
        "00000000",
        "00000000",
        "00000000",
        "00000000",
    )
    for impostor in (
        one_color_only,
        singleton_color,
        axis_aligned_pair,
        adjacent_diagonal_pairs,
        duplicate_endpoint_count,
    ):
        assert GENERATOR.self_check(impostor)


def test_replay_is_deterministic_fresh_and_global_rng_pure() -> None:
    random.seed(6421)
    expected_global = [random.random() for _ in range(8)]
    random.seed(6421)

    first = GENERATOR.generate(31337, 17, difficulty="medium")
    second = GENERATOR.generate(31337, 17, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))

    first[0][0] = 9 if first[0][0] != 9 else 8
    third = GENERATOR.generate(31337, 17, difficulty="medium")
    assert third == second
    assert [random.random() for _ in range(8)] == expected_global


def test_rule_mirror_does_not_mutate_its_input() -> None:
    grid = GENERATOR.generate(51, 6, difficulty="hard")
    original = copy.deepcopy(grid)
    output = GENERATOR.rule_mirror(grid)
    assert grid == original
    assert output != grid
