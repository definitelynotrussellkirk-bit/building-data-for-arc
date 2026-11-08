from __future__ import annotations

import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
TASK = "4512012999bb"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")


def _canonical_rows():
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        return [row for row in map(json.loads, handle) if row.get("task_id") == TASK]


def _pairs(row):
    test = row["test"]
    return row["train"] + ([test] if isinstance(test, dict) else test)


def _frozen(grid):
    return tuple(map(tuple, grid))


def test_both_canonical_rows_share_one_rule_hash():
    rows = _canonical_rows()
    assert {row["source"] for row in rows} == {"training", "augmented"}
    hashes = {
        hashlib.sha256(" ".join(row["program_solution"].split()).encode()).hexdigest()[:12]
        for row in rows
    }
    assert hashes == {MODULE.RULE_HASH} == {"dea780b8cf83"}


def test_public_profiles_replay_all_unique_canonical_pairs_exactly():
    rows = _canonical_rows()
    training = next(row for row in rows if row["source"] == "training")
    pairs = _pairs(training)
    assert len(pairs) == len(MODULE.PUBLIC_PROFILES) == 5
    for profile, pair in zip(MODULE.PUBLIC_PROFILES, pairs):
        grid = MODULE.generate(0, 0, scene_profile=profile)
        assert grid == pair["input"]
        assert MODULE.rule_mirror(grid) == pair["output"]
        assert MODULE.canonical_profile_signature(grid) == profile
        assert MODULE.observe_overrides(grid) == {"scene_profile": profile}
    augmented = next(row for row in rows if row["source"] == "augmented")
    assert {_frozen(pair["input"]) for pair in _pairs(augmented)} == {_frozen(pair["input"]) for pair in pairs}
    assert {_frozen(pair["output"]) for pair in _pairs(augmented)} == {_frozen(pair["output"]) for pair in pairs}


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
                assert len(analysis["facts"]["candidates"]) == 1
                assert MODULE.observe_overrides(grid) == {"scene_profile": profile}


def test_default_generation_reaches_every_declared_profile():
    seen = {
        MODULE.observe_overrides(MODULE.generate(seed, seed * 37))["scene_profile"]
        for seed in range(4000)
    }
    assert seen == set(MODULE.SCENE_PROFILES)


@pytest.mark.parametrize("profile", ["direct_above", "direct_below", "direct_right"])
def test_direct_profiles_have_strictly_better_direct_score(profile):
    facts = MODULE._analysis(MODULE.generate(41, 73, scene_profile=profile))["facts"]
    assert facts["direct_score"] > facts["flip_score"]
    assert not facts["flipped"]


@pytest.mark.parametrize("profile", ["flip_above", "flip_below", "flip_right"])
def test_flip_profiles_have_strictly_better_mirrored_score(profile):
    facts = MODULE._analysis(MODULE.generate(41, 73, scene_profile=profile))["facts"]
    assert facts["flip_score"] > facts["direct_score"]
    assert facts["flipped"]


def test_tie_falls_back_to_direct_orientation():
    facts = MODULE._analysis(MODULE.generate(77, 88, scene_profile="tie_direct"))["facts"]
    assert facts["direct_score"] == facts["flip_score"]
    assert not facts["flipped"]
    output = MODULE.rule_mirror(MODULE.generate(77, 88, scene_profile="tie_direct"))
    assert tuple(tuple(row[1:-1]) for row in output[1:-1]) == facts["crop"]


def test_odd_center_column_is_excluded_from_both_scores():
    facts = MODULE._analysis(MODULE.generate(17, 29, scene_profile="odd_center_ignored"))["facts"]
    assert facts["inner_width"] % 2 == 1
    center = facts["inner_width"] // 2
    assert any(row[center] in (facts["left_color"], facts["right_color"]) for row in facts["crop"])
    direct_without_center = sum(
        (col < facts["inner_width"] // 2 and value == facts["left_color"])
        or (col >= (facts["inner_width"] + 1) // 2 and value == facts["right_color"])
        for row in facts["crop"]
        for col, value in enumerate(row)
        if col != center
    )
    assert facts["direct_score"] == direct_without_center


def test_variegated_guide_columns_are_copied_row_by_row():
    grid = MODULE.generate(9, 10, scene_profile="variegated_walls")
    facts = MODULE._analysis(grid)["facts"]
    output = MODULE.rule_mirror(grid)
    assert len(set(facts["left_wall"][1:-1])) > 1
    assert len(set(facts["right_wall"][1:-1])) > 1
    assert tuple(row[0] for row in output) == facts["left_wall"]
    assert tuple(row[-1] for row in output) == facts["right_wall"]


def test_multicolor_crop_keeps_accents_but_scores_only_side_colors():
    grid = MODULE.generate(101, 202, scene_profile="multicolor_crop")
    facts = MODULE._analysis(grid)["facts"]
    accents = {value for row in facts["crop"] for value in row} - {0, facts["left_color"], facts["right_color"]}
    assert len(accents) >= 1
    assert not facts["flipped"]
    assert accents <= {value for row in MODULE.rule_mirror(grid) for value in row}


def test_output_is_exact_frame_walls_plus_oriented_crop():
    for seed in range(400):
        grid = MODULE.generate(seed, seed * 19)
        analysis = MODULE._analysis(grid)
        assert not analysis["errors"]
        facts = analysis["facts"]
        expected = [[0] * facts["outer_width"] for _ in range(facts["outer_height"])]
        for row in range(facts["outer_height"]):
            expected[row][0] = facts["left_wall"][row]
            expected[row][-1] = facts["right_wall"][row]
            if 0 < row < facts["outer_height"] - 1:
                source = facts["crop"][row - 1]
                expected[row][1:-1] = list(reversed(source)) if facts["flipped"] else list(source)
        assert MODULE.rule_mirror(grid) == expected


def test_crop_placement_profiles_are_geometrically_real():
    for place in ("above", "below", "right"):
        for prefix in ("direct", "flip"):
            profile = f"{prefix}_{place}"
            facts = MODULE._analysis(MODULE.generate(5, 7, scene_profile=profile))["facts"]
            assert MODULE._placement(facts) == place


def test_generation_is_deterministic_fresh_and_global_rng_independent():
    random.seed(987654)
    before = random.getstate()
    first = MODULE.generate(111, 222, difficulty="hard")
    assert random.getstate() == before
    second = MODULE.generate(111, 222, difficulty="hard")
    assert first == second and first is not second and first[0] is not second[0]
    first[0][0] = 9
    assert MODULE.generate(111, 222, difficulty="hard") == second


@pytest.mark.parametrize(
    "grid",
    [
        [],
        [[]],
        [[0, 1], [0]],
        [[True] + [0] * 6 for _ in range(7)],
        [[10] + [0] * 6 for _ in range(7)],
        [[0] * 31 for _ in range(7)],
        [[0] * 7 for _ in range(6)],
        [[0] * 7 for _ in range(7)],
        [[1] * 7 for _ in range(7)],
    ],
)
def test_self_check_rejects_malformed_or_ruleless_impostors(grid):
    assert MODULE.self_check(grid)


def test_self_check_rejects_same_side_colors_and_unknown_crop_relation():
    same = MODULE.generate(1, 2, scene_profile="direct_right")
    facts = MODULE._analysis(same)["facts"]
    row0, col0, row1, col1 = facts["frame_bbox"]
    for row in range(row0 + 1, row1):
        same[row][col1] = same[row][col0]
    assert MODULE.self_check(same)


def test_unknown_difficulty_profile_and_axis_fail_closed():
    with pytest.raises(ValueError):
        MODULE.generate(0, 0, difficulty="extreme")
    with pytest.raises(ValueError):
        MODULE.generate(0, 0, scene_profile="not_real")
    with pytest.raises(ValueError):
        MODULE.generate(0, 0, frame_h=7)


def test_public_returns_are_fresh():
    first = MODULE.generate(1, 2, scene_profile="public_1")
    frozen = _frozen(first)
    first[0][0] = 9
    assert _frozen(MODULE.generate(1, 2, scene_profile="public_1")) == frozen


def test_axis_contract_is_literal_minimal_and_complete():
    assert set(MODULE.AXES) == {"scene_profile"}
    valid = set(MODULE.AXES["scene_profile"]["valid"].split("|"))
    assert valid == set(MODULE.SCENE_PROFILES)
    assert not MODULE.HELPFUL_TEXTURES and not MODULE.DEGENERATE_TEXTURES
