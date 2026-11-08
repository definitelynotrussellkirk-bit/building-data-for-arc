from __future__ import annotations

import hashlib
import json
import random

import pytest
from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator


ROOT = find_root(__file__)
TASK = "2c30a4753f6b"
MODULE, SOURCE_PATH, SOURCE_SHA256 = load_selected_generator(TASK, root=ROOT)


def _canonical_row():
    with canonical_path(ROOT).open() as handle:
        return next(row for row in map(json.loads, handle) if row.get("task_id") == TASK)


def _frozen(grid):
    return tuple(map(tuple, grid))


def test_rule_hash_matches_canonical_program():
    rule = " ".join(_canonical_row()["program_solution"].split())
    assert MODULE.RULE_HASH == hashlib.sha256(rule.encode()).hexdigest()[:12]


def test_every_public_profile_replays_its_canonical_pair_exactly():
    pairs = canonical_pairs(TASK, root=ROOT)
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


def test_default_generation_reaches_every_profile():
    seen = {
        MODULE.observe_overrides(MODULE.generate(seed, seed * 37))["scene_profile"]
        for seed in range(5000)
    }
    assert seen == set(MODULE.SCENE_PROFILES)


def test_oracle_preserves_left_half_and_appends_reversed_rows():
    grid = [[0, 1, 2, 3], [4, 0, 5, 6]]
    output = MODULE.rule_mirror(grid)
    assert output == [[0, 1, 2, 3, 3, 2, 1, 0], [4, 0, 5, 6, 6, 5, 0, 4]]
    assert [row[:4] for row in output] == grid


def test_every_generated_output_is_symmetric_about_the_new_seam():
    for seed in range(100):
        grid = MODULE.generate(seed, seed * 17)
        output = MODULE.rule_mirror(grid)
        assert all(row == row[::-1] for row in output)
        assert all(row[: len(grid[0])] == source for row, source in zip(output, grid))


def test_single_marker_is_canonically_witnessed_and_observable():
    grid = MODULE.generate(123, 456, scene_profile="single_marker")
    facts = MODULE._analysis(grid)["facts"]
    assert facts["nonzero_count"] == 1
    assert not facts["lr_symmetric"]
    assert MODULE.rule_mirror(grid) != [row + row for row in grid]


def test_near_symmetric_has_exactly_one_opposing_pair_mismatch():
    grid = MODULE.generate(555, 777, scene_profile="near_symmetric")
    facts = MODULE._analysis(grid)["facts"]
    assert facts["mismatch_pairs"] == 1
    assert not facts["lr_symmetric"]


def test_aspect_profiles_have_declared_geometry():
    wide = MODULE.generate(1, 2, scene_profile="wide_asymmetric")
    tall = MODULE.generate(1, 2, scene_profile="tall_asymmetric")
    assert len(wide[0]) >= 2 * len(wide)
    assert len(tall) >= 2 * len(tall[0])
    assert len(MODULE.rule_mirror(wide)[0]) <= 30


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
        [[True, 0], [0, 1]],
        [[10, 0], [0, 1]],
        [[0] * 16 for _ in range(3)],
        [[0] * 5 for _ in range(5)],
        [[7] * 5 for _ in range(5)],
        [[0, 7, 0], [0, 0, 0], [0, 7, 0]],
        [[0] * 7 for _ in range(2)] + [[0, 0, 5, 5, 0, 0, 0], [0, 0, 5, 5, 0, 0, 0]] + [[0] * 7 for _ in range(2)],
    ],
)
def test_self_check_rejects_malformed_invisible_or_undeclared_scenes(grid):
    assert MODULE.self_check(grid)


def test_unknown_difficulty_profile_and_axis_fail_closed():
    with pytest.raises(ValueError):
        MODULE.generate(0, 0, difficulty="extreme")
    with pytest.raises(ValueError):
        MODULE.generate(0, 0, scene_profile="not_real")
    with pytest.raises(ValueError):
        MODULE.generate(0, 0, grid_w=10)


def test_public_returns_are_fresh():
    first = MODULE.generate(1, 2, scene_profile="public_1")
    frozen = _frozen(first)
    first[0][0] = 9
    assert _frozen(MODULE.generate(1, 2, scene_profile="public_1")) == frozen
