from __future__ import annotations

import hashlib
import importlib
import json
import random
from collections import Counter
from pathlib import Path

import pytest


TASK = "997c17fd6870"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "data/canonical/puzzles.jsonl"
BASE_PATHS = (
    ROOT / "data/base/solutions/training/8ee62060__997c17fd6870.json",
    ROOT / "data/base/solutions/augmented/8ee62060__68aa988b8901.json",
)


def canonical_rows():
    rows = []
    with CANONICAL.open() as handle:
        for line in handle:
            row = json.loads(line)
            if row["task_id"] == TASK:
                rows.append(row)
    assert len(rows) == 2
    return rows


def unique_canonical_pairs():
    pairs = []
    seen = set()
    for row in canonical_rows():
        for pair in row["train"] + row["test"]:
            key = tuple(map(tuple, pair["input"]))
            if key not in seen:
                seen.add(key)
                pairs.append(pair)
    return pairs


def independent_oracle(grid):
    width = len(grid[0])
    return [
        [value for col in range(width - 2, -1, -2) for value in row[col:col + 2]]
        for row in grid
    ]


def frozen(grid):
    return tuple(map(tuple, grid))


def test_all_canonical_pair_appearances_are_exact():
    expected = {frozen(pair["input"]): pair["output"] for pair in unique_canonical_pairs()}
    assert len(expected) == len(MODULE.PUBLIC_PROFILES) == 4
    for row in canonical_rows():
        for pair in row["train"] + row["test"]:
            grid = pair["input"]
            assert MODULE.rule_mirror(grid) == independent_oracle(grid) == pair["output"]
            assert MODULE.self_check(grid) == []
            assert MODULE.canonical_profile_signature(grid) in MODULE.PUBLIC_PROFILES
            assert MODULE.canonical_family_signature(grid) in MODULE.PUBLIC_PROFILES
    for profile, pair in zip(MODULE.PUBLIC_PROFILES, unique_canonical_pairs()):
        grid = MODULE.generate(11, 17, scene_profile=profile)
        assert grid == pair["input"]
        assert MODULE.rule_mirror(grid) == pair["output"]
        assert MODULE.observe_overrides(grid) == {"scene_profile": profile}


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("profile", MODULE.SCENE_PROFILES)
def test_every_profile_is_exact_and_observable(profile, difficulty):
    for seed in range(3):
        grid = MODULE.generate(20_000 + seed, seed * 19, difficulty=difficulty, scene_profile=profile)
        analysis = MODULE._analysis(grid)
        assert analysis["errors"] == []
        assert analysis["scene_profile"] == profile
        assert MODULE.observe_overrides(grid) == {"scene_profile": profile}
        assert MODULE.rule_mirror(grid) == independent_oracle(grid) == analysis["output"]
        assert grid != analysis["output"]


def test_official_family_nuisances_are_nonliteral_and_band_aware():
    literals = {frozen(pair["input"]) for pair in unique_canonical_pairs()}
    bands = (("easy", 3, 6), ("medium", 5, 8), ("hard", 7, 10))
    for profile in MODULE.PUBLIC_PROFILES:
        for difficulty, low, high in bands:
            scenes = [MODULE._public_nuisance(profile, difficulty, random.Random(seed)) for seed in range(80)]
            assert all(MODULE.canonical_family_signature(grid) == profile for grid in scenes)
            assert all(frozen(grid) not in literals for grid in scenes)
            assert all(low <= len(grid) // 2 <= high for grid in scenes)
            assert len({frozen(grid) for grid in scenes}) >= 70


def test_public_families_preserve_complete_macro_morphology():
    expected_kind = {
        "public_1": "hook",
        "public_2": "corner",
        "public_3": "gap",
        "public_4": "checker",
    }
    for profile in MODULE.PUBLIC_PROFILES:
        for seed in range(30):
            grid = MODULE._public_nuisance(profile, "medium", random.Random(seed))
            facts = MODULE._analysis(grid)["facts"]
            assert MODULE._diagonal_run(sorted(facts["occupied"]))
            assert set(facts["kinds"].values()) == {expected_kind[profile]}
            assert len({frozen(tile) for tile in facts["occupied"].values()}) == 1


def test_general_profiles_refute_diagonal_and_fixed_motif_shortcuts():
    for seed in range(50):
        varied = MODULE._analysis(MODULE.generate(seed, seed, scene_profile="diagonal_varied"))["facts"]
        assert len(set(varied["kinds"].values())) >= 2
        permuted = MODULE._analysis(MODULE.generate(seed, seed, scene_profile="permuted_tiles"))["facts"]
        positions = sorted(permuted["occupied"])
        n_pairs = permuted["n_pairs"]
        assert positions != [(index, index) for index in range(n_pairs)]
        assert {row for row, _ in positions} == set(range(n_pairs))
        assert {col for _, col in positions} == set(range(n_pairs))
        multi = MODULE._analysis(MODULE.generate(seed, seed, scene_profile="multi_tiles"))["facts"]
        assert multi["occupied_count"] > multi["n_pairs"]
        assert any(sum(row == target for row, _ in multi["occupied"]) >= 2 for target in range(multi["n_pairs"]))


def test_pair_order_reversal_is_not_a_whole_grid_reflection():
    for profile in MODULE.SCENE_PROFILES:
        grid = MODULE.generate(71, len(profile), scene_profile=profile)
        output = MODULE.rule_mirror(grid)
        whole_reflection = [list(reversed(row)) for row in grid]
        assert output != whole_reflection
        width = len(grid[0])
        for row, expected in zip(grid, output):
            input_pairs = [row[col:col + 2] for col in range(0, width, 2)]
            output_pairs = [expected[col:col + 2] for col in range(0, width, 2)]
            assert output_pairs == list(reversed(input_pairs))


def test_broad_rule_accepts_noncanonical_rectangles_but_training_rejects_them():
    grids = [
        [[1, 2, 3, 4], [5, 6, 7, 8], [9, 0, 1, 2]],
        [[1, 0, 2, 3, 4, 5]],
        [[(row * 8 + col) % 10 for col in range(8)] for row in range(5)],
    ]
    for grid in grids:
        assert MODULE.rule_mirror(grid) == independent_oracle(grid)
        assert MODULE.self_check(grid)


def test_default_distribution_is_complete_diverse_and_nontrivial():
    expected = set(MODULE.SCENE_PROFILES)
    for difficulty in ("easy", "medium", "hard"):
        grids = [MODULE.generate(40_000 + seed, seed * 23, difficulty=difficulty) for seed in range(1400)]
        analyses = [MODULE._analysis(grid) for grid in grids]
        profiles = Counter(item["scene_profile"] for item in analyses)
        outputs = [item["output"] for item in analyses]
        assert set(profiles) == expected
        assert all(count >= 120 for count in profiles.values())
        assert len({frozen(grid) for grid in grids}) >= 1350
        assert len({frozen(grid) for grid in outputs}) >= 1350
        assert all(grid != output for grid, output in zip(grids, outputs))
        assert {value for grid in grids for row in grid for value in row if value} == set(range(1, 10))


@pytest.mark.parametrize(
    "grid",
    [
        [],
        [[]],
        [[0, 0], [0, 0]],
        [[False] * 6 for _ in range(6)],
        [[10] * 6 for _ in range(6)],
        [[0] * 5 for _ in range(6)],
        [[0] * 6 for _ in range(5)],
        [[0] * 6 for _ in range(6)],
        [[1] * 6 for _ in range(6)],
        [[1, 2] + [0] * 4 for _ in range(6)],
    ],
)
def test_malformed_and_minimal_impostors_fail_closed(grid):
    assert MODULE.self_check(grid)


def test_structural_mutations_fail_closed():
    grid = MODULE.generate(91, 7, scene_profile="public_1")
    facts = MODULE._analysis(grid)["facts"]
    macro_row, macro_col = next(iter(facts["occupied"]))
    hole = [row[:] for row in grid]
    cell = next(
        (2 * macro_row + dr, 2 * macro_col + dc)
        for dr in range(2) for dc in range(2)
        if hole[2 * macro_row + dr][2 * macro_col + dc]
    )
    hole[cell[0]][cell[1]] = 0
    assert MODULE.self_check(hole)
    third_color = [row[:] for row in grid]
    third_color[0][0] = 9
    assert MODULE.self_check(third_color)
    missing_tile = [row[:] for row in grid]
    missing_row, missing_col = sorted(facts["occupied"])[len(facts["occupied"]) // 2]
    for row in range(2 * missing_row, 2 * missing_row + 2):
        for col in range(2 * missing_col, 2 * missing_col + 2):
            missing_tile[row][col] = 0
    assert MODULE.self_check(missing_tile)
    malformed_tile = [row[:] for row in grid]
    tile_colors = sorted(facts["colors"])
    malformed_tile[cell[0]][cell[1]] = (
        tile_colors[1] if malformed_tile[cell[0]][cell[1]] == tile_colors[0] else tile_colors[0]
    )
    assert MODULE.self_check(malformed_tile)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"scene_profile": "unknown"},
        {"texture": "noise"},
        {"grid_h": 12},
        {"n_pairs": 6},
        {"palette_size": 3},
        {"difficulty": "expert"},
    ],
)
def test_unknown_controls_fail_closed(kwargs):
    with pytest.raises(ValueError):
        MODULE.generate(1, 0, **kwargs)


def test_determinism_fresh_returns_and_global_rng_isolation():
    random.seed(9157)
    state = random.getstate()
    first = MODULE.generate(101, 13, difficulty="hard", scene_profile="multi_tiles")
    assert random.getstate() == state
    second = MODULE.generate(101, 13, difficulty="hard", scene_profile="multi_tiles")
    assert first == second and first is not second and first[0] is not second[0]
    first[0][0] = 9
    assert MODULE.generate(101, 13, difficulty="hard", scene_profile="multi_tiles") == second


def test_axis_contract_is_literal_minimal_and_fully_observable():
    assert set(MODULE.AXES) == {"scene_profile"}
    assert tuple(MODULE.AXES["scene_profile"]["valid"].split("|")) == MODULE.SCENE_PROFILES
    assert MODULE.HELPFUL_TEXTURES == MODULE.DEGENERATE_TEXTURES == ()


def test_rule_hash_and_both_base_sources_match_canonical():
    source = canonical_rows()[0]["program_solution"]
    assert all(row["program_solution"] == source for row in canonical_rows())
    digest = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
    assert MODULE.RULE_HASH == digest == "7ac779229e5e"
    for path in BASE_PATHS:
        base = json.loads(path.read_text())
        assert base["racket_target"]["raw_code"] == source
        assert base["racket_target"]["target_code"] == source
