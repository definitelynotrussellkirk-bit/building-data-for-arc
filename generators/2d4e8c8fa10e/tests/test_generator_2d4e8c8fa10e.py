"""Focused regression tests for generator 2d4e8c8fa10e."""
from __future__ import annotations

import random

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "2d4e8c8fa10e"
ROOT = find_root(__file__)
gen, SOURCE_PATH, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def _blank(h: int = 8, w: int = 9) -> list[list[int]]:
    return [[0 for _ in range(w)] for _ in range(h)]


def _paint(grid: list[list[int]], cells) -> None:
    for row, col in cells:
        grid[row][col] = 6


def test_rule_hash_and_all_canonical_pairs_are_owned_exactly():
    assert gen.RULE_HASH == "dbcfc990f307"
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert len(pairs) == 3
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_three_example_schedule_covers_every_semantic_control(difficulty):
    for start in range(12):
        grids = [
            gen.generate(7001 + start, start + offset, difficulty=difficulty)
            for offset in range(gen.EXAMPLES_NEEDED)
        ]
        observed = [gen.observe_overrides(grid) for grid in grids]
        assert {row["distractor_profile"] for row in observed} == {
            "triomino",
            "tetromino",
            "square_tail",
        }
        assert max(row["square_count"] for row in observed) >= 2
        assert all(gen.self_check(grid) == [] for grid in grids)
        assert all(gen.strict_canonical_like(grid) == [] for grid in grids)

        demos = [
            {"input": grid, "output": gen.rule_mirror(grid)}
            for grid in grids
        ]
        query_grid = gen.generate(
            7001 + start,
            start + gen.EXAMPLES_NEEDED,
            difficulty=difficulty,
        )
        query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
        assert gen.lesson_identifiable(demos, query) == []
        for competitor in gen.LESSON_COMPETITORS.values():
            assert any(
                competitor(pair["input"]) != pair["output"] for pair in demos
            )


@pytest.mark.parametrize(
    "overrides",
    [
        {
            "grid_h": 8,
            "grid_w": 9,
            "square_count": 1,
            "distractor_count": 1,
            "distractor_profile": "triomino",
        },
        {
            "grid_h": 10,
            "grid_w": 11,
            "square_count": 3,
            "distractor_count": 3,
            "distractor_profile": "square_tail",
        },
        {
            "grid_h": 8,
            "grid_w": 11,
            "square_count": 3,
            "distractor_count": 3,
            "distractor_profile": "tetromino",
        },
        {
            "grid_h": 10,
            "grid_w": 9,
            "square_count": 1,
            "distractor_count": 3,
            "distractor_profile": "square_tail",
        },
    ],
)
def test_override_boundaries_are_exact_and_observable(overrides):
    grid = gen.generate(9917, 13, difficulty="hard", **overrides)
    assert gen.observe_overrides(grid) == overrides
    assert gen.self_check(grid, meta={"overrides": overrides}) == []


def test_unknown_and_invalid_overrides_reject_loudly():
    with pytest.raises(TypeError, match="unknown override"):
        gen.generate(1, 0, typo_axis=3)
    with pytest.raises(ValueError, match="grid_h"):
        gen.generate(1, 0, grid_h=7)
    with pytest.raises(ValueError, match="square_count"):
        gen.generate(1, 0, square_count=True)
    with pytest.raises(ValueError, match="distractor_profile"):
        gen.generate(1, 0, distractor_profile="blob")
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(1, 0, difficulty="extreme")


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(721991)
    before = random.getstate()
    first = gen.generate(44, 9, difficulty="medium")
    after = random.getstate()
    assert before == after

    second = gen.generate(44, 9, difficulty="medium")
    assert first == second
    first[0][0] = 9
    third = gen.generate(44, 9, difficulty="medium")
    assert third == second
    assert first is not second and second is not third
    assert all(a is not b for a, b in zip(second, third))


def test_self_check_rejects_targeted_impostors():
    wrong_color = gen.generate(91, 0)
    wrong_color[0][0] = 5
    assert any("colors" in reason for reason in gen.self_check(wrong_color))

    no_distractor = _blank()
    _paint(no_distractor, ((1, 1), (1, 2), (2, 1), (2, 2)))
    assert any("distractor" in reason for reason in gen.self_check(no_distractor))

    no_square = _blank()
    _paint(no_square, ((1, 1), (1, 2), (1, 3)))
    assert any("2x2" in reason for reason in gen.self_check(no_square))

    square_tail_only = _blank()
    _paint(square_tail_only, ((1, 1), (1, 2), (2, 1), (2, 2), (3, 1)))
    assert any("2x2" in reason for reason in gen.self_check(square_tail_only))

    mixed_profiles = _blank()
    _paint(mixed_profiles, ((0, 0), (0, 1), (1, 0), (1, 1)))
    _paint(mixed_profiles, ((0, 4), (1, 4), (2, 4)))
    _paint(mixed_profiles, ((4, 0), (5, 0), (6, 0), (6, 1)))
    assert any("share one profile" in reason for reason in gen.self_check(mixed_profiles))

    merged_objects = _blank()
    _paint(merged_objects, ((1, 1), (1, 2), (2, 1), (2, 2)))
    _paint(merged_objects, ((2, 3), (3, 3), (4, 3)))
    assert gen.self_check(merged_objects)


def test_semantic_controls_refute_the_named_canonical_shortcuts():
    tetromino = gen.generate(
        808,
        0,
        square_count=2,
        distractor_count=2,
        distractor_profile="tetromino",
    )
    square_tail = gen.generate(
        809,
        0,
        square_count=2,
        distractor_count=2,
        distractor_profile="square_tail",
    )
    expected_tetromino = gen.rule_mirror(tetromino)
    expected_tail = gen.rule_mirror(square_tail)

    assert gen.SEMANTIC_RIVALS["keep_all_size4"](tetromino) != expected_tetromino
    assert (
        gen.SEMANTIC_RIVALS["keep_largest_components"](tetromino)
        != expected_tetromino
    )
    assert (
        gen.SEMANTIC_RIVALS["keep_any_local_2x2"](square_tail)
        != expected_tail
    )
    assert (
        gen.SEMANTIC_RIVALS["keep_largest_components"](square_tail)
        != expected_tail
    )
    assert gen.SEMANTIC_RIVALS["keep_first_square_only"](tetromino) != expected_tetromino
    assert gen.SEMANTIC_RIVALS["keep_everything"](tetromino) != expected_tetromino


def _bbox_dims(cells) -> tuple[int, int]:
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return max(rows) - min(rows) + 1, max(cols) - min(cols) + 1


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_tetromino_schedule_contains_both_orientations_and_refutes_height2_rival(difficulty):
    for sample_index in range(12):
        if "tetromino" not in gen.schedule_profile(0, sample_index, difficulty):
            continue
        grid = gen.generate(3119, sample_index, difficulty=difficulty)
        analysis = gen._analysis_or_raise(grid)
        assert analysis["distractor_profile"] == "tetromino"
        dimensions = {_bbox_dims(cells) for cells in analysis["distractors"]}
        assert (3, 2) in dimensions
        assert (2, 3) in dimensions
        assert (
            gen.SEMANTIC_RIVALS["keep_size4_height2"](grid)
            != gen.rule_mirror(grid)
        )


def test_horizontal_tetromino_is_lawful_and_refutes_height2_rival():
    grid = _blank()
    _paint(grid, ((0, 0), (0, 1), (1, 0), (1, 1)))
    _paint(grid, ((4, 4), (4, 5), (4, 6), (5, 4)))

    assert gen.self_check(grid) == []
    assert gen.rule_mirror(grid) != gen.SEMANTIC_RIVALS["keep_size4_height2"](grid)


@pytest.mark.parametrize("bad_seed", [True, False, 1.5, "1"])
def test_generate_rejects_noninteger_or_boolean_seed(bad_seed):
    with pytest.raises(TypeError, match="seed"):
        gen.generate(bad_seed, 0)


@pytest.mark.parametrize("bad_index", [True, False, 1.5, "1"])
def test_generate_rejects_noninteger_or_boolean_sample_index(bad_index):
    with pytest.raises(TypeError, match="sample_index"):
        gen.generate(1, bad_index)


def test_generate_rejects_negative_sample_index():
    with pytest.raises(ValueError, match="sample_index"):
        gen.generate(1, -1)
