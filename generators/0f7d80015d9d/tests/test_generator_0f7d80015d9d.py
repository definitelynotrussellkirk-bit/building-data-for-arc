from __future__ import annotations

import copy
import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs


TASK_ID = "0f7d80015d9d"
gen = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)


def _analysis(grid):
    result = gen._analyze(grid)
    assert not result["errors"], result["errors"]
    return result


def test_canonical_pairs_are_accepted_and_mirrored_exactly():
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 4
    for pair in pairs:
        assert gen.self_check(copy.deepcopy(pair["input"])) == []
        assert gen.rule_mirror(copy.deepcopy(pair["input"])) == pair["output"]


def test_all_exact_axes_are_observable_at_full_boundaries():
    case = 0
    for height in (7, 19):
        for width in (7, 19):
            for aspect in gen.RECT_ASPECTS:
                for profile in gen.SCHEDULE_PROFILES:
                    grid = gen.generate(
                        9000 + case,
                        case,
                        difficulty="medium",
                        grid_h=height,
                        grid_w=width,
                        rect_aspect=aspect,
                        scene_profile=profile,
                    )
                    assert gen.self_check(
                        grid,
                        meta={
                            "overrides": {
                                "grid_h": height,
                                "grid_w": width,
                                "rect_aspect": aspect,
                                "scene_profile": profile,
                            }
                        },
                    ) == []
                    assert gen.observe_overrides(grid) == {
                        "grid_h": height,
                        "grid_w": width,
                        "rect_aspect": aspect,
                        "scene_profile": profile,
                    }
                    case += 1
    assert case == 48


def test_unknown_and_out_of_domain_overrides_reject_loudly():
    with pytest.raises(KeyError):
        gen.generate(1, 0, typo_axis="left")
    with pytest.raises(ValueError):
        gen.generate(1, 0, grid_h=6)
    with pytest.raises(ValueError):
        gen.generate(1, 0, scene_profile="not-a-profile")


def test_every_sliding_four_example_window_covers_the_decisive_profiles():
    for start in range(16):
        profiles = {
            gen.observe_overrides(gen.generate(12345, start + offset))["scene_profile"]
            for offset in range(gen.EXAMPLES_NEEDED)
        }
        assert profiles == set(gen.SCHEDULE_PROFILES)


def test_midpoint_marker_counts_as_right_and_refutes_center_left_rival():
    grid = gen.generate(222, 2, scene_profile="center_opposite")
    facts = _analysis(grid)
    assert facts["red"][1] == facts["midpoint"]
    assert facts["red_left"] is False
    true_output = gen.rule_mirror(grid)
    rival_output = gen._rival_center_is_left(grid)
    assert true_output != rival_output
    assert true_output[facts["rect"][1]][facts["rect"][2] - 1] == 8


def test_self_check_rejects_targeted_structural_impostors():
    grid = gen.generate(777, 0, grid_h=11, grid_w=11, rect_aspect="wide")
    facts = _analysis(grid)
    red = facts["red"]
    cyan = facts["cyan"]
    top, bottom, left, right = facts["rect"]

    missing_red = copy.deepcopy(grid)
    missing_red[red[0]][red[1]] = 7
    assert any("exactly one color-2" in error for error in gen.self_check(missing_red))

    rectangle_hole = copy.deepcopy(grid)
    rectangle_hole[top][left] = 7
    assert any("solid rectangle" in error for error in gen.self_check(rectangle_hole))

    rectangle_not_bottom = copy.deepcopy(grid)
    for col in range(left, right + 1):
        rectangle_not_bottom[bottom][col] = 7
    assert any("bottom row" in error for error in gen.self_check(rectangle_not_bottom))

    marker_outside_span = copy.deepcopy(grid)
    marker_outside_span[cyan[0]][cyan[1]] = 7
    outside_col = 0 if left > 0 else len(grid[0]) - 1
    marker_outside_span[0][outside_col] = 8
    assert any("within its column span" in error for error in gen.self_check(marker_outside_span))

    texture_leak = copy.deepcopy(grid)
    texture_leak[0][0] = 1
    assert any("palette must be exactly" in error for error in gen.self_check(texture_leak))


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    random.seed(314159)
    state_before = random.getstate()
    first = gen.generate(42, 9, difficulty="hard")
    state_after = random.getstate()
    second = gen.generate(42, 9, difficulty="hard")
    assert state_before == state_after
    assert first == second
    assert first is not second
    assert all(row_a is not row_b for row_a, row_b in zip(first, second))
    first[0][0] = 99
    assert second[0][0] != 99
