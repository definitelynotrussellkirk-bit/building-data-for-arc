from __future__ import annotations

import copy
import random

import pytest

from puzzle_generators.per_puzzle.ad0970c37953 import generator as gen
from scripts.canonical_profile_gate import canonical_inputs


def test_accepts_every_canonical_input() -> None:
    inputs = canonical_inputs(gen.TASK_ID)
    assert len(inputs) == 4
    assert [gen.self_check(grid) for grid in inputs] == [[], [], [], []]


def test_override_boundaries_are_exact_and_unknown_keys_reject() -> None:
    for difficulty in ("easy", "medium", "hard"):
        for height in (8, 16):
            for width in (8, 18):
                for n_blobs in (3, 6):
                    grid = gen.generate(
                        123,
                        17,
                        difficulty=difficulty,
                        grid_h=height,
                        grid_w=width,
                        n_blobs=n_blobs,
                    )
                    assert gen.observe_overrides(grid) == {
                        "grid_h": height,
                        "grid_w": width,
                        "n_blobs": n_blobs,
                    }
                    assert gen.self_check(grid) == []
    with pytest.raises(KeyError, match="unknown override"):
        gen.generate(1, 1, typo_axis=4)


def test_three_consecutive_samples_cover_decisive_profiles() -> None:
    grids = [gen.generate(9123, index, difficulty="medium") for index in range(3)]
    assert [gen.schedule_profile(9123, index, "medium") for index in range(3)] == list(
        gen.SCHEDULE_PROFILES
    )
    assert gen.SEMANTIC_WITNESSES["area_order_differs_from_spatial_order"](grids[0])
    assert gen.SEMANTIC_WITNESSES["row_before_column_equal_area_tie"](grids[1])
    assert gen.SEMANTIC_WITNESSES["same_colour_separate_objects"](grids[2])


def test_named_rivals_are_refuted_by_their_witness_profiles() -> None:
    size_grid = gen.generate(55, 0, difficulty="hard")
    tie_grid = gen.generate(55, 1, difficulty="hard")
    repeat_grid = gen.generate(55, 2, difficulty="hard")
    assert gen._rival_spatial_order(size_grid) != gen.rule_bar_gallery(size_grid)
    assert gen._rival_ties_left_to_right(tie_grid) != gen.rule_bar_gallery(tie_grid)
    assert gen._rival_aggregate_by_colour(repeat_grid) != gen.rule_bar_gallery(repeat_grid)
    for grid in (size_grid, tie_grid, repeat_grid):
        assert gen._rival_bbox_area(grid) != gen.rule_bar_gallery(grid)
        assert gen._rival_top_aligned(grid) != gen.rule_bar_gallery(grid)
        assert gen._rival_no_gaps(grid) != gen.rule_bar_gallery(grid)


def test_self_check_rejects_targeted_impostors() -> None:
    # 1. Empty lesson / no objects.
    blank = [[0] * 8 for _ in range(8)]
    assert gen.self_check(blank)

    # 2. Only one object.
    one = [[0] * 8 for _ in range(8)]
    one[1][1] = one[1][2] = one[2][1] = 3
    assert gen.self_check(one)

    # 3. Different-colour objects touch orthogonally.
    touching = gen.generate(100, 0, grid_h=8, grid_w=8, n_blobs=3)
    touching = copy.deepcopy(touching)
    touching[0][0], touching[0][1], touching[1][0] = 1, 2, 0
    assert any("touch" in reason for reason in gen.self_check(touching))

    # 4. Three rectangular singletons all have the same area and hide area mapping.
    tied_rectangles = [[0] * 8 for _ in range(8)]
    tied_rectangles[1][1] = 1
    tied_rectangles[1][4] = 2
    tied_rectangles[5][1] = 3
    reasons = gen.self_check(tied_rectangles)
    assert any("distinct object areas" in reason for reason in reasons)
    assert any("non-rectangular" in reason for reason in reasons)

    # 5. Too many objects.
    too_many = [[0] * 16 for _ in range(8)]
    for index in range(7):
        row, col = (index // 4) * 4 + 1, (index % 4) * 4 + 1
        too_many[row][col] = index + 1
    assert any("3-6 objects" in reason for reason in gen.self_check(too_many))


def test_replay_freshness_input_purity_and_global_rng() -> None:
    random.seed(424242)
    expected = [random.random() for _ in range(5)]
    random.seed(424242)
    first = gen.generate(77, 29, difficulty="medium")
    second = gen.generate(77, 29, difficulty="medium")
    observed = [random.random() for _ in range(5)]
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    assert observed == expected

    before = copy.deepcopy(first)
    answer = gen.rule_bar_gallery(first)
    assert first == before
    answer[0][0] = 9 if answer[0][0] != 9 else 8
    assert first == before
