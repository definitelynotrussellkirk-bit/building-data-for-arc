"""Portable regressions for generator 0be8ff9b4144."""
from __future__ import annotations

import importlib

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "0be8ff9b4144"
MOD = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
ROOT = find_root(__file__)


def test_canonical_pairs_match_the_independent_python_mirror():
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert len(pairs) == 5
    for pair in pairs:
        assert MOD.self_check(pair["input"]) == []
        assert MOD._mirror(pair["input"]) == pair["output"]


def test_rule_hash_is_pinned_to_the_verified_authority():
    assert MOD.RULE_HASH == "138495330232"


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    ("axis", "value", "observed"),
    [
        ("grid_h", 5, 5),
        ("grid_h", 16, 16),
        ("grid_w", 6, 6),
        ("grid_w", 18, 18),
        ("n_top", 1, 1),
        ("n_top", 6, 6),
        ("n_left", 1, 1),
        ("n_left", 6, 6),
        ("background", 0, 0),
        ("background", 9, 9),
    ],
)
def test_every_single_axis_endpoint_is_exact_in_every_band(
    difficulty, axis, value, observed
):
    grid = MOD.generate(17, 5, difficulty=difficulty, **{axis: value})
    assert MOD.self_check(grid) == []
    assert MOD.observe_overrides(grid)[axis] == observed


@pytest.mark.parametrize(
    "kwargs",
    [
        {"grid_h": 5, "n_left": 3},
        {"grid_h": 8, "n_left": 6},
        {"grid_w": 6, "n_top": 4},
        {"grid_w": 8, "n_top": 6},
    ],
)
def test_compatible_joint_overrides_are_exact(kwargs):
    grid = MOD.generate(31, 2, difficulty="hard", **kwargs)
    observed = MOD.observe_overrides(grid)
    assert {key: observed[key] for key in kwargs} == kwargs


@pytest.mark.parametrize(
    "kwargs",
    [
        {"grid_h": 5, "n_left": 4},
        {"grid_h": 6, "n_left": 5},
        {"grid_w": 6, "n_top": 5},
        {"grid_w": 7, "n_top": 6},
    ],
)
def test_declared_geometry_conflicts_fail_loudly(kwargs):
    with pytest.raises(ValueError, match="incompatible"):
        MOD.generate(31, 2, **kwargs)


@pytest.mark.parametrize(
    "args, kwargs",
    [
        ((0, True), {}),
        ((0, 1.0), {}),
        ((0, "1"), {}),
        ((0, -1), {}),
        ((0, 0), {"unknown_probe": 1}),
        ((0, 0), {"grid_h": True}),
        ((0, 0), {"background": False}),
        ((0, 0), {"texture": "NOT_AN_ALLOWED_TEXTURE"}),
    ],
)
def test_invalid_call_controls_are_rejected(args, kwargs):
    with pytest.raises((TypeError, ValueError)):
        MOD.generate(*args, **kwargs)


def test_only_lawful_helpful_textures_are_advertised():
    valid = set(MOD.AXES["texture"]["valid"].split("|"))
    assert valid == set(MOD.HELPFUL_TEXTURES)
    assert not (valid & set(getattr(MOD, "DEGENERATE_TEXTURES", ())))


def _pair(grid):
    return {"input": grid, "output": MOD._mirror(grid)}


def test_declared_shortcuts_fit_every_labeled_canonical_pair():
    expected = {
        "any_nonbackground_header_activates",
        "preserve_occupied_intersections",
        "corner_8_required",
    }
    assert set(MOD.CANONICAL_SHORTCUTS) == expected
    for name, shortcut in MOD.CANONICAL_SHORTCUTS.items():
        for pair in canonical_pairs(TASK_ID, root=ROOT):
            assert shortcut(pair["input"]) == pair["output"], name


def test_exact_wrong_header_witness_refutes_the_strongest_shortcut():
    grid = [
        [8, 2, 4, 0, 0, 0],
        [3, 0, 0, 0, 0, 0],
        [6, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
    ]
    expected = [row[:] for row in grid]
    expected[1][1] = 5
    assert MOD.self_check(grid) == []
    assert MOD._mirror(grid) == expected
    assert MOD.SEMANTIC_WITNESSES["wrong_header_colors_are_inactive"](grid)
    rival = MOD.SEMANTIC_RIVALS["any_nonbackground_header_activates"]
    assert rival(grid) != expected
    assert rival(grid)[1][2] == 5
    assert rival(grid)[2][1] == 5
    assert rival(grid)[2][2] == 5


@pytest.mark.parametrize("texture", ["wrong_marker", "body_content", "corner_var"])
def test_each_rich_texture_carries_all_three_semantic_contrasts(texture):
    grid = MOD.generate(871, 5, difficulty="hard", texture=texture)
    assert MOD.observe_overrides(grid)["texture"] == texture
    official = MOD._mirror(grid)
    for witness_name, witness in MOD.SEMANTIC_WITNESSES.items():
        assert witness(grid), (texture, witness_name)
    for rival_name, rival in MOD.SEMANTIC_RIVALS.items():
        assert rival(grid) != official, (texture, rival_name)


def test_four_profile_schedule_survives_every_start_and_query_rotation():
    assert MOD.LESSON_SCHEDULE_PERIOD == 4
    assert tuple(MOD.SCHEDULE_PROFILES) == tuple(MOD.HELPFUL_TEXTURES)
    for start in range(8):
        pairs = []
        observed = []
        for sample_index in range(start, start + MOD.EXAMPLES_NEEDED + 1):
            grid = MOD.generate(941, sample_index, difficulty="medium")
            pairs.append(_pair(grid))
            observed.append(MOD.observe_overrides(grid)["texture"])
        assert observed == [
            MOD.schedule_profile(941, index, "medium")
            for index in range(start, start + MOD.EXAMPLES_NEEDED + 1)
        ]
        for query_index in range(len(pairs)):
            query = pairs[query_index]
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert MOD.lesson_identifiable(demos, query) == []
            for name, rival in MOD.LESSON_COMPETITORS.items():
                assert any(
                    rival(demo["input"]) != demo["output"] for demo in demos
                ), (start, query_index, name)


def test_distribution_is_deterministic_fresh_and_has_strict_support():
    import copy
    import random

    random.seed(20261011)
    before = random.getstate()
    first = MOD.generate(314159, 7, difficulty="hard")
    after = random.getstate()
    second = MOD.generate(314159, 7, difficulty="hard")
    pristine = copy.deepcopy(second)
    assert before == after
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = (first[0][0] + 1) % 10
    assert second == pristine

    for band_index, band in enumerate(("easy", "medium", "hard")):
        profiles = set()
        strict_hits = 0
        signatures = set()
        for sample_index in range(48):
            grid = MOD.generate(7000 + band_index, sample_index, difficulty=band)
            assert MOD.self_check(grid) == []
            profiles.add(MOD.observe_overrides(grid)["texture"])
            strict_hits += MOD.strict_canonical_like(grid) == []
            signatures.add(tuple(tuple(row) for row in grid))
        assert profiles == set(MOD.SCHEDULE_PROFILES)
        assert strict_hits >= 12
        assert len(signatures) >= 44


def test_strict_hook_accepts_all_canonical_inputs_and_only_plain_defaults():
    for pair in canonical_pairs(TASK_ID, root=ROOT):
        assert MOD.strict_canonical_like(pair["input"]) == []
    plain = MOD.generate(99, 0, texture="plain")
    assert MOD.strict_canonical_like(plain) == []
    for texture in ("wrong_marker", "body_content", "corner_var"):
        assert MOD.strict_canonical_like(MOD.generate(99, 0, texture=texture))


def test_self_check_rejects_distribution_impostors():
    valid = MOD.generate(151, 1, texture="wrong_marker", grid_h=8, grid_w=9)
    assert MOD.self_check(valid) == []

    no_inactive_top = [row[:] for row in valid]
    for col in range(1, len(no_inactive_top[0])):
        no_inactive_top[0][col] = 2
    assert MOD.self_check(no_inactive_top)

    no_inactive_left = [row[:] for row in valid]
    for row in range(1, len(no_inactive_left)):
        no_inactive_left[row][0] = 3
    assert MOD.self_check(no_inactive_left)

    painted_input = [row[:] for row in valid]
    painted_input[-1][-1] = 5
    assert MOD.self_check(painted_input)


def test_pinned_profile_floor_has_exact_canonical_support_in_every_band():
    import hashlib

    canonical_profiles = {
        (
            len(pair["input"]),
            len(pair["input"][0]),
            len({value for row in pair["input"] for value in row}),
        )
        for pair in canonical_pairs(TASK_ID, root=ROOT)
    }
    for band in ("easy", "medium", "hard"):
        hits = 0
        for index in range(20):
            digest = hashlib.sha256(
                f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
            ).hexdigest()
            seed = int(digest[:12], 16)
            grid = MOD.generate(seed, seed % 7919 + index, difficulty=band)
            profile = (
                len(grid),
                len(grid[0]),
                len({value for row in grid for value in row}),
            )
            hits += profile in canonical_profiles
        assert hits >= 1, band


def test_pinned_profile_floor_meets_the_blocking_twenty_five_percent_floor():
    import hashlib

    canonical_profiles = {
        (
            len(pair["input"]),
            len(pair["input"][0]),
            len({value for row in pair["input"] for value in row}),
        )
        for pair in canonical_pairs(TASK_ID, root=ROOT)
    }
    hits = 0
    for band in ("easy", "medium", "hard"):
        for index in range(20):
            digest = hashlib.sha256(
                f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
            ).hexdigest()
            seed = int(digest[:12], 16)
            grid = MOD.generate(seed, seed % 7919 + index, difficulty=band)
            profile = (
                len(grid),
                len(grid[0]),
                len({value for row in grid for value in row}),
            )
            hits += profile in canonical_profiles
    assert hits >= 15
