from __future__ import annotations

import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
TASK = "3a4b67ab16ff"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")


def _canonical_row():
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        return next(row for row in map(json.loads, handle) if row.get("task_id") == TASK)


def _pairs():
    row = _canonical_row()
    test = row["test"]
    return row["train"] + ([test] if isinstance(test, dict) else test)


def _frozen(grid):
    return tuple(map(tuple, grid))


def test_rule_hash_matches_canonical_program():
    rule = " ".join(_canonical_row()["program_solution"].split())
    assert MODULE.RULE_HASH == hashlib.sha256(rule.encode()).hexdigest()[:12]


def test_every_public_profile_replays_its_canonical_pair_exactly():
    pairs = _pairs()
    assert len(pairs) == len(MODULE.PUBLIC_PROFILES) == 4
    for profile, pair in zip(MODULE.PUBLIC_PROFILES, pairs):
        grid = MODULE.generate(0, 0, scene_profile=profile)
        assert grid == pair["input"]
        assert MODULE.rule_mirror(grid) == pair["output"]
        assert MODULE.canonical_profile_signature(grid) == profile
        assert MODULE.observe_overrides(grid) == {"scene_profile": profile}


def test_every_general_profile_is_valid_and_recoverable_in_every_band():
    for band_index, band in enumerate((None, "easy", "medium", "hard")):
        for profile_index, profile in enumerate(MODULE.GENERAL_PROFILES):
            for seed in range(30):
                grid = MODULE.generate(
                    100_000 * band_index + 1_000 * profile_index + seed,
                    seed * 31,
                    difficulty=band,
                    scene_profile=profile,
                )
                analysis = MODULE._analysis(grid)
                assert not analysis["errors"]
                assert analysis["scene_profile"] == profile
                assert MODULE.observe_overrides(grid) == {"scene_profile": profile}


def test_default_generation_reaches_every_declared_profile():
    seen = {
        MODULE.observe_overrides(MODULE.generate(seed, seed * 37))["scene_profile"]
        for seed in range(6000)
    }
    assert seen == set(MODULE.SCENE_PROFILES)


def test_oracle_restores_gray_bbox_clears_outside_and_fills_intersection():
    grid = [[0] * 8 for _ in range(8)]
    for row in range(2, 7):
        for col in range(1, 7):
            grid[row][col] = 5
    grid[0][0] = 3
    grid[4][4] = 3
    output = MODULE.rule_mirror(grid)
    assert output[0][0] == 0
    assert all(output[row][col] == 3 for row in range(2, 5) for col in range(1, 5))
    assert output[6][6] == 5


def test_higher_numeric_color_wins_overlapping_intersections():
    grid = [[0] * 7 for _ in range(7)]
    for row in range(1, 6):
        for col in range(1, 6):
            grid[row][col] = 5
    grid[1][1] = grid[4][4] = 2
    grid[3][3] = grid[5][5] = 7
    output = MODULE.rule_mirror(grid)
    assert output[2][2] == 2
    assert output[3][3] == output[4][4] == 7
    assert output[5][5] == 7
    assert output[1][5] == 5


def test_inactive_color_is_erased_without_affecting_active_fill():
    grid = MODULE.generate(123, 456, scene_profile="inactive_companion")
    facts = MODULE._analysis(grid)["facts"]
    assert len(facts["active_colors"]) == len(facts["inactive_colors"]) == 1
    output = MODULE.rule_mirror(grid)
    inactive = facts["inactive_colors"][0]
    assert all(value != inactive for row in output for value in row)


def test_profile_touch_contracts_are_geometrically_real():
    expected = {
        "top_left_projection": {"top", "left"},
        "top_right_projection": {"top", "right"},
        "bottom_left_projection": {"bottom", "left"},
        "bottom_right_projection": {"bottom", "right"},
        "horizontal_band": {"left", "right"},
        "vertical_band": {"top", "bottom"},
        "interior_box": set(),
        "full_bbox_projection": {"top", "left", "bottom", "right"},
    }
    for profile, touches in expected.items():
        grid = MODULE.generate(77, 88, scene_profile=profile)
        facts = MODULE._analysis(grid)["facts"]
        color = facts["active_colors"][0]
        assert set(MODULE._touches(facts["colors"][color]["intersection"], facts["gray_bbox"])) == touches


def test_nonoverlap_and_overlap_profiles_have_declared_relations():
    separate = MODULE._analysis(MODULE.generate(1, 2, scene_profile="three_color_nonoverlap"))["facts"]
    overlap = MODULE._analysis(MODULE.generate(1, 2, scene_profile="overlap_priority"))["facts"]
    assert len(separate["active_colors"]) == 3 and not separate["overlaps"]
    assert len(overlap["active_colors"]) == 2 and overlap["overlaps"]


def test_every_output_change_is_explained_by_base_restore_or_color_intersection():
    for seed in range(300):
        grid = MODULE.generate(seed, seed * 19)
        facts = MODULE._analysis(grid)["facts"]
        output = MODULE.rule_mirror(grid)
        expected = [[0 for _ in row] for row in grid]
        for row, col in facts["gray_area"]:
            expected[row][col] = 5
        for color in sorted(facts["colors"]):
            for row, col in MODULE._rect_cells(facts["colors"][color]["intersection"]):
                expected[row][col] = color
        assert output == expected


def test_generation_is_deterministic_fresh_and_global_rng_independent():
    random.seed(987654)
    before = random.getstate()
    first = MODULE.generate(111, 222, difficulty="hard")
    assert random.getstate() == before
    second = MODULE.generate(111, 222, difficulty="hard")
    assert first == second and first is not second and first[0] is not second[0]
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert MODULE.generate(111, 222, difficulty="hard") == second


@pytest.mark.parametrize(
    "grid",
    [
        [],
        [[]],
        [[0, 1], [0]],
        [[True] + [0] * 4 for _ in range(5)],
        [[10] + [0] * 4 for _ in range(5)],
        [[0] * 31 for _ in range(5)],
        [[0] * 7 for _ in range(7)],
        [[5] * 7 for _ in range(7)],
        [[0] * 7 for _ in range(2)] + [[0, 5, 5, 5, 5, 5, 0] for _ in range(3)] + [[0] * 7 for _ in range(2)],
        [[0] * 7 for _ in range(2)] + [[0, 5, 5, 5, 5, 5, 0], [0, 5, 0, 0, 0, 5, 0], [0, 5, 5, 5, 5, 5, 0]] + [[0] * 7 for _ in range(2)],
        [[0] * 7 for _ in range(2)] + [[0, 5, 5, 5, 5, 5, 0] for _ in range(5)],
    ],
)
def test_self_check_rejects_malformed_or_undeclared_impostors(grid):
    assert MODULE.self_check(grid)


def test_unknown_difficulty_profile_and_axis_fail_closed():
    with pytest.raises(ValueError):
        MODULE.generate(0, 0, difficulty="extreme")
    with pytest.raises(ValueError):
        MODULE.generate(0, 0, scene_profile="not_real")
    with pytest.raises(ValueError):
        MODULE.generate(0, 0, rect_h=5)


def test_public_returns_are_fresh():
    first = MODULE.generate(1, 2, scene_profile="public_1")
    frozen = _frozen(first)
    first[0][0] = 9
    assert _frozen(MODULE.generate(1, 2, scene_profile="public_1")) == frozen
