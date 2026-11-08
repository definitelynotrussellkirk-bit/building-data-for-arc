from __future__ import annotations

import hashlib
import importlib
import json
import random
from collections import Counter
from pathlib import Path

import pytest


TASK = "a3c33cc348fb"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "data/canonical/puzzles.jsonl"
BASE_PATHS = (
    ROOT / "data/base/solutions/training/b548a754__a3c33cc348fb.json",
    ROOT / "data/base/solutions/augmented/b548a754__a2f39c96cab9.json",
)


def canonical_rows():
    rows = [
        json.loads(line)
        for line in CANONICAL.read_text().splitlines()
        if json.loads(line)["task_id"] == TASK
    ]
    assert len(rows) == 2
    return rows


def independent_oracle(grid):
    marker = next(
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 8
    )
    cells = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value not in (0, 8)
    ]
    rows = [row for row, _, _ in cells]
    cols = [col for _, col, _ in cells]
    row0, row1, col0, col1 = min(rows), max(rows), min(cols), max(cols)
    frame = grid[row0][col0]
    inner = next((value for _, _, value in cells if value != frame), frame)
    new_row0, new_row1 = min(row0, marker[0]), max(row1, marker[0])
    new_col0, new_col1 = min(col0, marker[1]), max(col1, marker[1])
    output = [[0] * len(grid[0]) for _ in grid]
    for row in range(new_row0, new_row1 + 1):
        for col in range(new_col0, new_col1 + 1):
            output[row][col] = (
                frame
                if row in (new_row0, new_row1) or col in (new_col0, new_col1)
                else inner
            )
    return output


def frozen(grid):
    return tuple(map(tuple, grid))


def test_all_eight_canonical_pair_appearances_are_exact():
    rows = canonical_rows()
    programs = {row["program_solution"] for row in rows}
    assert len(programs) == 1
    normalized = " ".join(programs.pop().split())
    assert hashlib.sha256(normalized.encode()).hexdigest()[:12] == MODULE.RULE_HASH
    pairs = [pair for row in rows for pair in row["train"] + row["test"]]
    assert len(pairs) == 8
    profiles = {}
    for pair in pairs:
        grid = pair["input"]
        assert MODULE.rule_mirror(grid) == independent_oracle(grid) == pair["output"]
        assert MODULE.self_check(grid) == []
        profile = MODULE.canonical_profile_signature(grid)
        assert profile in MODULE.PUBLIC_PROFILES
        assert MODULE.canonical_family_signature(grid) == profile
        profiles[profile] = frozen(grid)
    assert len({frozen(pair["input"]) for pair in pairs}) == 4
    assert set(profiles) == set(MODULE.PUBLIC_PROFILES)
    for profile in MODULE.PUBLIC_PROFILES:
        assert frozen(MODULE.generate(11, 17, scene_profile=profile)) == profiles[profile]


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("profile", MODULE.SCENE_PROFILES)
def test_every_profile_is_exact_observable_and_oracle_correct(profile, difficulty):
    for seed in range(3):
        grid = MODULE.generate(20_000 + seed, seed * 19, difficulty=difficulty, scene_profile=profile)
        analysis = MODULE._analysis(grid)
        assert analysis["errors"] == []
        assert analysis["scene_profile"] == profile
        assert MODULE.observe_overrides(grid) == {"scene_profile": profile}
        assert MODULE.rule_mirror(grid) == independent_oracle(grid) == analysis["output"]


def test_public_nuisances_preserve_complete_official_reach_families():
    literals = {
        frozen(pair["input"])
        for row in canonical_rows()
        for pair in row["train"] + row["test"]
    }
    for profile in MODULE.PUBLIC_PROFILES:
        scenes = [MODULE._random_scene(profile, "medium", random.Random(seed)) for seed in range(80)]
        assert all(MODULE.canonical_family_signature(grid) == profile for grid in scenes)
        assert all(MODULE.self_check(grid) == [] for grid in scenes)
        assert all(frozen(grid) not in literals for grid in scenes)
        assert len({frozen(grid) for grid in scenes}) == 80


def test_general_profiles_have_exact_distance_alignment_and_side_signatures():
    for profile in MODULE.GENERAL_PROFILES:
        for seed in range(60):
            grid = MODULE.generate(seed, seed * 7, scene_profile=profile)
            facts = MODULE._analysis(grid)["facts"]
            if profile == "near_reach":
                assert 1 <= facts["distance"] <= 3
            elif profile == "far_reach":
                assert 9 <= facts["distance"] <= 11
            elif profile == "corner_reach":
                assert 4 <= facts["distance"] <= 8
                assert facts["corner_aligned"]
            else:
                assert facts["side"] == "left"
                assert 4 <= facts["distance"] <= 8
                assert not facts["corner_aligned"]


def test_every_marker_side_and_edge_or_interior_alignment_is_witnessed():
    sides = set()
    alignments = set()
    for profile in MODULE.SCENE_PROFILES:
        for seed in range(200):
            grid = MODULE.generate(90_000 + seed, seed, scene_profile=profile)
            facts = MODULE._analysis(grid)["facts"]
            sides.add(facts["side"])
            alignments.add(facts["corner_aligned"])
    assert sides == {"top", "bottom", "left", "right"}
    assert alignments == {False, True}


def test_broad_rule_uses_first_marker_global_bbox_and_row_major_colors():
    grid = [[7] * 12 for _ in range(10)]
    grid[0][0] = 8
    grid[8][11] = 8
    grid[2][3] = 4
    grid[2][8] = 6
    grid[7][2] = 4
    before = frozen(grid)
    output = MODULE.rule_mirror(grid)
    assert output == independent_oracle(grid)
    assert frozen(grid) == before
    assert output[0][0] == 8
    assert output[2][2] == 7
    assert output[3][3] == 7
    assert output[8][11] == 8
    assert MODULE.self_check(grid)


def test_broad_rule_single_color_falls_back_to_same_interior_color():
    grid = [[0] * 9 for _ in range(8)]
    grid[1][7] = 8
    grid[4][2] = 5
    grid[5][3] = 5
    output = MODULE.rule_mirror(grid)
    assert output == independent_oracle(grid)
    assert {value for row in output for value in row} == {0, 5}
    assert MODULE.self_check(grid)


def test_default_distribution_is_complete_diverse_and_band_aware():
    expected_profiles = set(MODULE.SCENE_PROFILES)
    medians = {}
    for difficulty in ("easy", "medium", "hard"):
        grids = [MODULE.generate(40_000 + seed, seed * 23, difficulty=difficulty) for seed in range(1200)]
        analyses = [MODULE._analysis(grid) for grid in grids]
        profiles = Counter(item["scene_profile"] for item in analyses)
        assert set(profiles) == expected_profiles
        assert all(count >= 95 for count in profiles.values())
        assert len({frozen(grid) for grid in grids}) == len(grids)
        assert len({frozen(item["output"]) for item in analyses}) >= 1190
        assert all(item["errors"] == [] for item in analyses)
        assert {item["facts"]["side"] for item in analyses} == {"top", "bottom", "left", "right"}
        assert min(item["facts"]["distance"] for item in analyses) == 1
        expected_maximum = {"easy": 10, "medium": 11, "hard": 12}[difficulty]
        assert max(item["facts"]["distance"] for item in analyses) == expected_maximum
        areas = sorted(len(grid) * len(grid[0]) for grid in grids)
        medians[difficulty] = areas[len(areas) // 2]
    assert medians["easy"] < medians["medium"] < medians["hard"]


@pytest.mark.parametrize(
    "grid",
    [
        [],
        [[]],
        [[0] * 9 for _ in range(9)],
        [[False] * 10 for _ in range(10)],
        [[10] * 10 for _ in range(10)],
        [[0] * 10 for _ in range(9)] + [[0] * 9],
        [[8] * 10 for _ in range(10)],
        [[0 if (row, col) != (3, 3) else 8 for col in range(10)] for row in range(10)],
    ],
)
def test_malformed_and_minimal_impostors_fail_closed(grid):
    assert MODULE.self_check(grid)


def test_structural_mutations_fail_closed():
    grid = MODULE.generate(91, 7, scene_profile="public_1")
    facts = MODULE._analysis(grid)["facts"]
    row0, col0, row1, col1 = facts["bbox"]
    broken = [row[:] for row in grid]
    broken[row0][col0] = 0
    assert MODULE.self_check(broken)
    wrong_inside = [row[:] for row in grid]
    wrong_inside[row0 + 1][col0 + 1] = 7
    assert MODULE.self_check(wrong_inside)
    extra_color = [row[:] for row in grid]
    extra_color[row0 + 1][col0 + 1] = 9
    assert MODULE.self_check(extra_color)
    extra_marker = [row[:] for row in grid]
    extra_marker[-1][-1] = 8
    assert MODULE.self_check(extra_marker)
    diagonal = [row[:] for row in grid]
    marker_row, marker_col = facts["marker"]
    diagonal[marker_row][marker_col] = 0
    diagonal[max(0, row0 - 1)][max(0, col0 - 1)] = 8
    assert MODULE.self_check(diagonal)


def test_determinism_fresh_returns_and_global_rng_isolation():
    random.seed(123_456)
    state = random.getstate()
    first = MODULE.generate(731, 19, difficulty="hard")
    assert random.getstate() == state
    second = MODULE.generate(731, 19, difficulty="hard")
    assert first == second and first is not second and first[0] is not second[0]
    original = second[0][0]
    first[0][0] = 9
    assert second[0][0] == original
    assert MODULE.generate(731, 20, difficulty="hard") != second


@pytest.mark.parametrize(
    "kwargs",
    [
        {"scene_profile": "unknown"},
        {"texture": "left"},
        {"grid_h": 13},
        {"marker_side": "top"},
        {"frame_h": 5},
        {"palette_kind": "warm"},
        {"anchor_corner": True},
        {"difficulty": "expert"},
    ],
)
def test_unknown_controls_fail_closed(kwargs):
    with pytest.raises(ValueError):
        MODULE.generate(1, 0, **kwargs)


def test_axis_and_both_source_contracts_are_exact():
    assert MODULE.VERSION == "3.0.0"
    assert MODULE.RULE_HASH == "b3185fa9390c"
    assert set(MODULE.AXES) == {"scene_profile"}
    assert not MODULE.HELPFUL_TEXTURES and not MODULE.DEGENERATE_TEXTURES
    canonical_rules = {row["program_solution"] for row in canonical_rows()}
    assert len(canonical_rules) == 1
    canonical_rule = canonical_rules.pop()
    for path in BASE_PATHS:
        target = json.loads(path.read_text())["racket_target"]
        assert target["raw_code"] == target["target_code"] == canonical_rule
