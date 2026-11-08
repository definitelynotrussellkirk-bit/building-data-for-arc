from __future__ import annotations

import random
from pathlib import Path

import pytest

from arcpuzzles.catalog import Catalog
from arcpuzzles.parametric_worker import _real_evaluator
from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "d4be41674012"
ROOT = find_root(__file__)
generator, _SOURCE, _SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def test_canonical_pairs_are_accepted_and_match_left_to_right_transpose_stack():
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) == 4
    for pair in pairs:
        before = [row[:] for row in pair["input"]]
        assert generator.self_check(pair["input"]) == []
        assert generator.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


def test_generated_scenes_match_protected_racket_at_boundaries():
    program = Catalog(ROOT)._variants()[TASK_ID][0]["program_solution"]
    calls = [
        (0, 0, "easy", {"grid_h": 7, "grid_w": 9, "color_count": 1}),
        (1, 7, "medium", {"grid_h": 14, "grid_w": 18, "color_count": 2}),
        (2, 11, "hard", {"grid_h": 30, "grid_w": 30, "color_count": 3}),
    ]
    apply, identity, bridge = _real_evaluator(ROOT / "shared/runtime")
    try:
        assert identity["backend"] == "racket" and identity["protected"] is True
        for seed, sample_index, difficulty, overrides in calls:
            grid = generator.generate(seed, sample_index, difficulty=difficulty, **overrides)
            assert generator.self_check(grid) == []
            assert generator.observe_overrides(grid) == overrides
            expected = generator.rule_mirror(grid)
            assert len(expected) <= 30 and len(expected[0]) <= 30
            assert apply(program, grid) == expected
    finally:
        bridge.close()


def test_generated_components_have_unique_left_edges_and_nontrivial_asymmetry():
    for seed in range(40):
        grid = generator.generate(seed, seed * 13 + 5, difficulty="hard")
        scene = generator._analyze_scene(grid)
        assert len(scene["objects"]) == 3
        lefts = [obj["c1"] for obj in scene["objects"]]
        assert lefts == sorted(lefts) and len(set(lefts)) == 3
        assert all(obj["crop"] != generator._rotate_clockwise(obj["crop"]) for obj in scene["objects"])
        assert generator.rule_mirror(grid) != generator.rule_rotate_clockwise(grid)


def test_strict_controls_and_exact_override_observation():
    for grid_h in (7, 30):
        for grid_w in (9, 30):
            for color_count in (1, 3):
                grid = generator.generate(
                    17, 31, difficulty="medium",
                    grid_h=grid_h, grid_w=grid_w, color_count=color_count,
                )
                assert generator.observe_overrides(grid) == {
                    "grid_h": grid_h,
                    "grid_w": grid_w,
                    "color_count": color_count,
                }

    bad = [
        {"difficulty": "expert"}, {"bogus": 1},
        {"grid_h": 6}, {"grid_h": 31}, {"grid_h": True},
        {"grid_w": 8}, {"grid_w": 31}, {"grid_w": 12.0},
        {"color_count": 0}, {"color_count": 4}, {"color_count": False},
    ]
    for kwargs in bad:
        with pytest.raises((TypeError, ValueError)):
            generator.generate(0, 0, **kwargs)


def test_self_check_rejects_ambiguous_or_malformed_scenes():
    canonical = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)[0]["input"]
    ragged = [row[:] for row in canonical]
    ragged[-1] = ragged[-1][:-1]
    assert generator.self_check(ragged)

    missing_object = [row[:] for row in canonical]
    for row in missing_object:
        for index, value in enumerate(row):
            if value == 4:
                row[index] = 0
    assert any("components" in error for error in generator.self_check(missing_object))

    same_left = [[0] * 9 for _ in range(9)]
    for r, c in ((1, 1), (1, 2), (2, 2), (4, 1), (4, 2), (5, 1), (7, 5), (7, 6), (8, 6)):
        same_left[r][c] = 3 if r < 4 else 5 if r < 7 else 7
    assert any("left" in error for error in generator.self_check(same_left))


def test_self_check_requires_a_transpose_visible_object():
    grid = [[0] * 15 for _ in range(10)]
    symmetric_under_transpose = ((0, 1), (1, 1))
    for row0, col0, color in ((1, 1, 2), (4, 6, 4), (7, 11, 7)):
        for dr, row in enumerate(symmetric_under_transpose):
            for dc, occupied in enumerate(row):
                if occupied:
                    grid[row0 + dr][col0 + dc] = color

    errors = generator.self_check(grid)
    assert any("transpose" in error for error in errors)


def test_deterministic_fresh_returns_and_global_rng_isolation():
    random.seed(9981)
    state = random.getstate()
    first = generator.generate(19, 31, difficulty="hard")
    assert random.getstate() == state
    second = generator.generate(19, 31, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second, strict=True))
