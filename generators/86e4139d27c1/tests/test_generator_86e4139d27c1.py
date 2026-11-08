from __future__ import annotations

import hashlib
import json
import random
from collections import Counter
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root, load_selected_generator


TASK = "86e4139d27c1"
ROOT = find_root(__file__)
MODULE, _, _ = load_selected_generator(TASK, root=ROOT)
CANONICAL = canonical_path(ROOT)
BASE = CANONICAL.parent.parent / "base/solutions/training/e9614598__86e4139d27c1.json"


def canonical_row():
    with CANONICAL.open() as handle:
        for line in handle:
            row = json.loads(line)
            if row["task_id"] == TASK:
                return row
    raise AssertionError("canonical row missing")


def canonical_pairs():
    row = canonical_row()
    return row["train"] + row["test"]


def independent_oracle(grid):
    blues = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1]
    if len(blues) < 2:
        raise ValueError("need two blues")
    midpoint = ((blues[0][0] + blues[1][0]) // 2, (blues[0][1] + blues[1][1]) // 2)
    output = [row[:] for row in grid]
    for dr, dc in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
        row, col = midpoint[0] + dr, midpoint[1] + dc
        if 0 <= row < len(grid) and 0 <= col < len(grid[0]):
            output[row][col] = 3
    return output


def frozen(grid):
    return tuple(map(tuple, grid))


def test_all_canonical_pairs_are_exact_and_strict():
    for profile, pair in zip(MODULE.PUBLIC_PROFILES, canonical_pairs()):
        grid = MODULE.generate(11, 17, scene_profile=profile)
        assert grid == pair["input"]
        assert MODULE.rule_mirror(grid) == independent_oracle(grid) == pair["output"]
        assert MODULE.canonical_profile_signature(grid) == profile
        assert MODULE.canonical_family_signature(grid) == profile
        assert MODULE.observe_overrides(grid) == {"scene_profile": profile}
        assert MODULE.self_check(grid) == []


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("profile", MODULE.GENERAL_PROFILES)
def test_every_general_profile_in_every_band(profile, difficulty):
    for seed in range(4):
        grid = MODULE.generate(20_000 + seed, seed * 19, difficulty=difficulty, scene_profile=profile)
        analysis = MODULE._analysis(grid)
        assert analysis["errors"] == []
        assert analysis["scene_profile"] == profile
        assert MODULE.observe_overrides(grid) == {"scene_profile": profile}
        assert MODULE.rule_mirror(grid) == independent_oracle(grid) == analysis["output"]


def test_profiles_witness_order_floor_overwrite_clipping_and_preservation():
    for seed in range(20):
        three = MODULE._analysis(MODULE.generate(seed, 1, scene_profile="first_two_of_three"))["facts"]
        assert three["blue_count"] == 3
        assert three["blues"][:2] == tuple(sorted(three["blues"]))[:2]
        assert three["blues"][2] not in three["in_bounds_footprint"]

        odd = MODULE._analysis(MODULE.generate(seed, 2, scene_profile="odd_floor"))["facts"]
        assert odd["row_delta"] % 2 or odd["col_delta"] % 2
        expected_midpoint = (
            (odd["first_blue"][0] + odd["second_blue"][0]) // 2,
            (odd["first_blue"][1] + odd["second_blue"][1]) // 2,
        )
        assert odd["midpoint"] == expected_midpoint

        overwritten_grid = MODULE.generate(seed, 3, scene_profile="endpoint_overwrite")
        overwritten = MODULE._analysis(overwritten_grid)["facts"]
        assert overwritten["endpoint_overlap_count"] == 2
        assert sum(value == 1 for row in MODULE.rule_mirror(overwritten_grid) for value in row) == 0

        clipped = MODULE._analysis(MODULE.generate(seed, 4, scene_profile="clipped_plus"))["facts"]
        assert clipped["clipped_count"] == 1
        assert len(clipped["in_bounds_footprint"]) == 4

        decor_grid = MODULE.generate(seed, 5, scene_profile="decor_preserved")
        decor = MODULE._analysis(decor_grid)["facts"]
        output = MODULE.rule_mirror(decor_grid)
        assert decor["decor_count"] >= 6
        assert decor["preserved_decor_count"] == decor["decor_count"]
        assert all(output[row][col] == value for row, col, value in decor["decor"])


def test_public_nuisances_preserve_family_without_replaying_literals():
    literal_inputs = {frozen(pair["input"]) for pair in canonical_pairs()}
    for profile in MODULE.PUBLIC_PROFILES:
        scenes = [MODULE._public_nuisance(profile, random.Random(seed)) for seed in range(80)]
        assert all(MODULE.canonical_profile_signature(grid) is None for grid in scenes)
        assert all(MODULE.canonical_family_signature(grid) == profile for grid in scenes)
        assert all(frozen(grid) not in literal_inputs for grid in scenes)
        assert len({frozen(grid) for grid in scenes}) >= 76
        assert all(MODULE.rule_mirror(grid) == independent_oracle(grid) for grid in scenes)


def test_default_public_nuisances_respect_difficulty_bands():
    for profile in MODULE.PUBLIC_PROFILES:
        easy = MODULE._public_nuisance(profile, random.Random(101), "easy")
        medium = MODULE._public_nuisance(profile, random.Random(101), "medium")
        hard = MODULE._public_nuisance(profile, random.Random(101), "hard")
        assert max(len(easy), len(easy[0])) <= 12
        assert 10 <= len(medium) <= 16 and 10 <= len(medium[0]) <= 16
        assert 16 <= len(hard) <= 24 and 16 <= len(hard[0]) <= 24
        assert MODULE.canonical_family_signature(easy) == profile
        assert MODULE.canonical_family_signature(medium) == profile
        assert MODULE.canonical_family_signature(hard) == profile


def test_first_two_row_major_cells_control_the_rule():
    grid = [[0] * 9 for _ in range(8)]
    for row, col in ((1, 7), (3, 1), (7, 8)):
        grid[row][col] = 1
    output = MODULE.rule_mirror(grid)
    assert output == independent_oracle(grid)
    assert output[2][4] == 3
    assert output[7][8] == 1


def test_rule_mirror_accepts_broad_racket_domain_but_training_gate_is_calibrated():
    grid = [[0] * 7 for _ in range(7)]
    grid[0][0] = grid[4][4] = grid[6][6] = grid[6][5] = 1
    grid[2][6] = 3
    grid[5][0] = 9
    original = [row[:] for row in grid]
    assert MODULE.rule_mirror(grid) == independent_oracle(grid)
    assert grid == original
    assert MODULE.self_check(grid)


def test_default_distribution_is_complete_diverse_and_stable():
    for difficulty in ("easy", "medium", "hard"):
        grids = [MODULE.generate(40_000 + seed, seed * 23, difficulty=difficulty) for seed in range(1200)]
        profiles = Counter(MODULE._analysis(grid)["scene_profile"] for grid in grids)
        outputs = [MODULE.rule_mirror(grid) for grid in grids]
        assert set(profiles) == set(MODULE.SCENE_PROFILES)
        assert all(count >= 24 for count in profiles.values())
        assert len({frozen(grid) for grid in grids}) >= 1180
        assert len({frozen(grid) for grid in outputs}) >= 1180
        assert all(MODULE.self_check(grid) == [] for grid in grids)


@pytest.mark.parametrize(
    "grid",
    [
        [],
        [[]],
        [[0] * 3 for _ in range(2)],
        [[False] * 3 for _ in range(3)],
        [[10] * 3 for _ in range(3)],
        [[0] * 3 for _ in range(3)],
        [[0, 1, 0], [0, 0], [0, 1, 0]],
    ],
)
def test_malformed_or_crashing_inputs_fail_closed(grid):
    assert MODULE.self_check(grid)


def test_semantic_mutations_fail_closed():
    grid = MODULE.generate(7, 9, scene_profile="axis_even")
    facts = MODULE._analysis(grid)["facts"]
    one_blue = [row[:] for row in grid]
    row, col = facts["second_blue"]
    one_blue[row][col] = 0
    assert MODULE.self_check(one_blue)

    four_blues = [row[:] for row in MODULE.generate(8, 10, scene_profile="first_two_of_three")]
    occupied = {(r, c) for r, row in enumerate(four_blues) for c, value in enumerate(row) if value}
    extra = next((r, c) for r in range(len(four_blues)) for c in range(len(four_blues[0])) if (r, c) not in occupied)
    four_blues[extra[0]][extra[1]] = 1
    assert MODULE.self_check(four_blues)

    input_green = [row[:] for row in grid]
    extra = next((r, c) for r in range(len(grid)) for c in range(len(grid[0])) if grid[r][c] == 0)
    input_green[extra[0]][extra[1]] = 3
    assert MODULE.self_check(input_green)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"scene_profile": "unknown"},
        {"texture": "no_blues"},
        {"grid_h": 10},
        {"endpoint_orientation": "diag"},
        {"difficulty": "expert"},
    ],
)
def test_unknown_controls_fail_closed(kwargs):
    with pytest.raises(ValueError):
        MODULE.generate(1, 0, **kwargs)


def test_determinism_fresh_returns_and_global_rng_isolation():
    random.seed(9157)
    state = random.getstate()
    first = MODULE.generate(91, 13, difficulty="hard", scene_profile="decor_preserved")
    assert random.getstate() == state
    second = MODULE.generate(91, 13, difficulty="hard", scene_profile="decor_preserved")
    assert first == second and first is not second and first[0] is not second[0]
    first[0][0] = 9
    assert MODULE.generate(91, 13, difficulty="hard", scene_profile="decor_preserved") == second


def test_axis_contract_is_literal_minimal_and_fully_observable():
    assert set(MODULE.AXES) == {"scene_profile"}
    assert tuple(MODULE.AXES["scene_profile"]["valid"].split("|")) == MODULE.SCENE_PROFILES
    assert MODULE.HELPFUL_TEXTURES == MODULE.DEGENERATE_TEXTURES == ()


def test_rule_hash_and_base_sources_are_semantically_synchronized():
    source = canonical_row()["program_solution"]
    normalized = " ".join(source.split())
    digest = hashlib.sha256(normalized.encode()).hexdigest()[:12]
    assert MODULE.RULE_HASH == digest == "23ba8d9ddb01"
    base = json.loads(BASE.read_text())
    raw_code = base["racket_target"]["raw_code"]
    target_code = base["racket_target"]["target_code"]
    assert " ".join(raw_code.split()) == normalized
    assert " ".join(target_code.split()) == normalized
    assert raw_code == target_code
