"""Focused regression tests for the border-equality-matrix generator."""
from __future__ import annotations

import importlib
import random

import pytest

gen = importlib.import_module("puzzle_generators.per_puzzle.95f82d34a755.generator")


CANONICAL = [
    (
        [
            [0, 7, 2, 4, 5, 2],
            [2, 0, 0, 0, 0, 0],
            [5, 0, 0, 0, 0, 0],
            [7, 0, 0, 0, 0, 0],
            [2, 0, 0, 0, 0, 0],
        ],
        [
            [0, 2, 0, 0, 2],
            [0, 0, 0, 5, 0],
            [7, 0, 0, 0, 0],
            [0, 2, 0, 0, 2],
        ],
    ),
    (
        [
            [0, 1, 3, 8, 8],
            [3, 0, 0, 0, 0],
            [8, 0, 0, 0, 0],
            [3, 0, 0, 0, 0],
        ],
        [
            [0, 3, 0, 0],
            [0, 0, 8, 8],
            [0, 3, 0, 0],
        ],
    ),
    (
        [
            [0, 6, 2, 1, 4, 6],
            [6, 0, 0, 0, 0, 0],
            [4, 0, 0, 0, 0, 0],
            [6, 0, 0, 0, 0, 0],
            [1, 0, 0, 0, 0, 0],
        ],
        [
            [6, 0, 0, 0, 6],
            [0, 0, 0, 4, 0],
            [6, 0, 0, 0, 6],
            [0, 0, 1, 0, 0],
        ],
    ),
    (
        [
            [0, 2, 9, 5, 5, 9],
            [9, 0, 0, 0, 0, 0],
            [5, 0, 0, 0, 0, 0],
            [2, 0, 0, 0, 0, 0],
            [9, 0, 0, 0, 0, 0],
        ],
        [
            [0, 9, 0, 0, 9],
            [0, 0, 5, 5, 0],
            [2, 0, 0, 0, 0],
            [0, 9, 0, 0, 9],
        ],
    ),
    (
        [
            [0, 7, 4, 1, 2, 4],
            [4, 0, 0, 0, 0, 0],
            [7, 0, 0, 0, 0, 0],
            [4, 0, 0, 0, 0, 0],
            [2, 0, 0, 0, 0, 0],
        ],
        [
            [0, 4, 0, 0, 4],
            [7, 0, 0, 0, 0],
            [0, 4, 0, 0, 4],
            [0, 0, 0, 2, 0],
        ],
    ),
]


def test_rule_mirror_and_self_check_accept_all_canonical_pairs():
    for source, expected in CANONICAL:
        assert gen.self_check(source) == []
        assert gen.rule_mirror(source) == expected


def test_every_exact_override_is_observable_at_boundaries():
    for difficulty in ("easy", "medium", "hard"):
        for grid_h in (4, 9):
            for grid_w in (5, 9):
                for profile in gen.SCENE_PROFILES:
                    for palette_band in gen.PALETTE_BANDS:
                        requested = {
                            "grid_h": grid_h,
                            "grid_w": grid_w,
                            "scene_profile": profile,
                            "palette_band": palette_band,
                        }
                        grid = gen.generate(
                            1234,
                            17,
                            difficulty=difficulty,
                            **requested,
                        )
                        assert gen.self_check(grid) == []
                        assert gen.observe_overrides(grid) == requested


def test_five_consecutive_demonstrations_cover_the_full_profile_schedule():
    for start in range(15):
        observed = {
            gen.observe_overrides(gen.generate(77, start + offset))["scene_profile"]
            for offset in range(gen.EXAMPLES_NEEDED)
        }
        assert observed == set(gen.SCENE_PROFILES)


def test_every_lesson_contains_both_official_input_shapes():
    for difficulty in ("easy", "medium", "hard"):
        for start in range(0, 15, gen.EXAMPLES_NEEDED):
            shapes = {
                (len(grid), len(grid[0]))
                for grid in (
                    gen.generate(20260725, start + offset, difficulty=difficulty)
                    for offset in range(gen.EXAMPLES_NEEDED)
                )
            }
            assert (4, 5) in shapes
            assert (5, 6) in shapes


def test_self_check_rejects_targeted_structural_impostors():
    grid = gen.generate(20260725, 4, difficulty="hard")
    impostors = gen.mutation_impostors(grid)
    assert len(impostors) >= 4
    for name, impostor in impostors:
        assert gen.self_check(impostor), name


def test_negative_recombination_is_rejected_but_oracle_mirror_executes():
    top_source = gen.generate(
        8,
        0,
        grid_h=5,
        grid_w=6,
        scene_profile="single_shared",
        palette_band="low",
    )
    left_source = gen.generate(
        9,
        0,
        grid_h=5,
        grid_w=6,
        scene_profile="single_shared",
        palette_band="high",
    )
    recombined = [row[:] for row in top_source]
    for r in range(1, len(recombined)):
        recombined[r][0] = left_source[r][0]
    assert "no shared label" in " ".join(gen.self_check(recombined))
    assert all(value == 0 for row in gen.rule_mirror(recombined) for value in row)


def test_lesson_identifiability_refutes_named_shortcuts():
    seed = 314159
    demos = []
    for sample_index in range(gen.EXAMPLES_NEEDED):
        source = gen.generate(seed, sample_index, difficulty="medium")
        demos.append({"input": source, "output": gen.rule_mirror(source)})
    query_source = gen.generate(seed, gen.EXAMPLES_NEEDED, difficulty="medium")
    query = {"input": query_source, "output": gen.rule_mirror(query_source)}
    assert gen.lesson_identifiable(demos, query) == []
    for name, competitor in gen.LESSON_COMPETITORS.items():
        assert any(competitor(demo["input"]) != demo["output"] for demo in demos), name


def test_generation_is_deterministic_fresh_and_rng_pure():
    state = random.getstate()
    first = gen.generate(4242, 3, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(4242, 3, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9
    assert gen.generate(4242, 3, difficulty="hard") == second


def test_unknown_override_and_invalid_difficulty_reject_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, typo_axis=3)
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(1, 0, difficulty="expert")
