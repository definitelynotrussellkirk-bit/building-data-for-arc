from __future__ import annotations

import hashlib
import importlib
import json
import random
from collections import Counter
from pathlib import Path

import pytest


TASK = "9c5bdbcdcd50"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "data/canonical/puzzles.jsonl"
BASE_PATHS = (
    ROOT / "data/base/solutions/training/e9c9d9a1__9c5bdbcdcd50.json",
    ROOT / "data/base/solutions/augmented/e9c9d9a1__f469a6c6f63b.json",
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
    pairs, seen = [], set()
    for row in canonical_rows():
        for pair in row["train"] + row["test"]:
            key = tuple(map(tuple, pair["input"]))
            if key not in seen:
                seen.add(key)
                pairs.append(pair)
    return pairs


def full_dividers(grid):
    height, width = len(grid), len(grid[0])
    rows = [row for row in range(height) if all(grid[row][col] == 3 for col in range(width))]
    cols = [col for col in range(width) if all(grid[row][col] == 3 for row in range(height))]
    return rows, cols


def ranges(dividers, length):
    bounds = [-1] + dividers + [length]
    return [
        (left + 1, right - 1)
        for left, right in zip(bounds, bounds[1:])
        if left + 1 <= right - 1
    ]


def independent_oracle(grid):
    height, width = len(grid), len(grid[0])
    divider_rows, divider_cols = full_dividers(grid)
    row_ranges = ranges(divider_rows, height)
    col_ranges = ranges(divider_cols, width)
    result = [row[:] for row in grid]
    for row_index, (row0, row1) in enumerate(row_ranges):
        for col_index, (col0, col1) in enumerate(col_ranges):
            if row_index == 0 and col_index == 0:
                color = 2
            elif row_index == 0 and col_index == len(col_ranges) - 1:
                color = 4
            elif row_index == len(row_ranges) - 1 and col_index == 0:
                color = 1
            elif row_index == len(row_ranges) - 1 and col_index == len(col_ranges) - 1:
                color = 8
            elif 0 < row_index < len(row_ranges) - 1 and 0 < col_index < len(col_ranges) - 1:
                color = 7
            else:
                color = 0
            for row in range(row0, row1 + 1):
                for col in range(col0, col1 + 1):
                    result[row][col] = color
    return result


def frozen(grid):
    return tuple(map(tuple, grid))


def test_all_eight_canonical_pair_appearances_are_exact():
    appearances = 0
    profiles = {}
    for row in canonical_rows():
        assert hashlib.sha256(row["program_solution"].encode()).hexdigest()[:12] == MODULE.RULE_HASH
        for pair in row["train"] + row["test"]:
            appearances += 1
            grid = pair["input"]
            assert MODULE.rule_mirror(grid) == independent_oracle(grid) == pair["output"]
            assert MODULE.self_check(grid) == []
            profile = MODULE.canonical_profile_signature(grid)
            assert profile in MODULE.PUBLIC_PROFILES
            assert MODULE.canonical_family_signature(grid) == profile
            profiles[profile] = frozen(grid)
    assert appearances == 8
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


def test_public_nuisances_preserve_complete_official_topologies_without_literals():
    literals = {frozen(pair["input"]) for pair in unique_canonical_pairs()}
    for profile in MODULE.PUBLIC_PROFILES:
        expected_shape = MODULE._PROFILE_SHAPES[profile]
        scenes = [MODULE._random_scene(profile, "medium", random.Random(seed)) for seed in range(100)]
        assert all(MODULE._analysis(grid)["facts"]["region_shape"] == expected_shape for grid in scenes)
        assert all(MODULE.canonical_family_signature(grid) == profile for grid in scenes)
        assert all(frozen(grid) not in literals for grid in scenes)
        assert len({frozen(grid) for grid in scenes}) >= 96


def test_general_profiles_have_exact_distinct_region_topologies():
    expected = {
        "wide_3x6": (3, 6),
        "tall_6x3": (6, 3),
        "mixed_5x4": (5, 4),
        "dense_6x6": (6, 6),
    }
    for profile, shape in expected.items():
        for seed in range(40):
            grid = MODULE.generate(seed, seed * 7, scene_profile=profile)
            assert MODULE._analysis(grid)["facts"]["region_shape"] == shape


def test_corner_edge_interior_and_divider_branches_are_spatially_exact():
    grid = MODULE.generate(501, 23, scene_profile="dense_6x6")
    facts = MODULE._analysis(grid)["facts"]
    output = MODULE.rule_mirror(grid)
    row_ranges, col_ranges = facts["row_ranges"], facts["col_ranges"]
    expected = {
        (0, 0): 2,
        (0, len(col_ranges) - 1): 4,
        (len(row_ranges) - 1, 0): 1,
        (len(row_ranges) - 1, len(col_ranges) - 1): 8,
    }
    for row_index, (row0, row1) in enumerate(row_ranges):
        for col_index, (col0, col1) in enumerate(col_ranges):
            color = expected.get((row_index, col_index))
            if color is None:
                color = 7 if 0 < row_index < len(row_ranges) - 1 and 0 < col_index < len(col_ranges) - 1 else 0
            assert all(output[row][col] == color for row in range(row0, row1 + 1) for col in range(col0, col1 + 1))
    assert all(all(value == 3 for value in output[row]) for row in facts["divider_rows"])
    assert all(all(output[row][col] == 3 for row in range(len(grid))) for col in facts["divider_cols"])


def test_broad_rule_accepts_other_contents_and_partial_divider_families():
    controls = []
    grid = [[9] * 11 for _ in range(10)]
    grid[3] = [3] * 11
    grid[7] = [3] * 11
    for row in range(10):
        grid[row][2] = 3
        grid[row][8] = 3
    controls.append(grid)
    controls.append([[5] * 7 for _ in range(6)])
    horizontal = [[6] * 8 for _ in range(9)]
    horizontal[2] = [3] * 8
    horizontal[6] = [3] * 8
    controls.append(horizontal)
    for control in controls:
        before = frozen(control)
        assert MODULE.rule_mirror(control) == independent_oracle(control)
        assert frozen(control) == before
        assert MODULE.self_check(control)


def test_default_distribution_is_complete_diverse_and_band_aware():
    expected_profiles = set(MODULE.SCENE_PROFILES)
    areas = {}
    for difficulty in ("easy", "medium", "hard"):
        grids = [MODULE.generate(40_000 + seed, seed * 23, difficulty=difficulty) for seed in range(1200)]
        analyses = [MODULE._analysis(grid) for grid in grids]
        profiles = Counter(item["scene_profile"] for item in analyses)
        assert set(profiles) == expected_profiles
        assert all(count >= 70 for count in profiles.values())
        assert len({frozen(grid) for grid in grids}) >= 1140
        assert len({frozen(item["output"]) for item in analyses}) >= 1140
        assert all(item["errors"] == [] for item in analyses)
        all_bands = [
            size
            for item in analyses
            for size in item["facts"]["row_bands"] + item["facts"]["col_bands"]
        ]
        if difficulty == "easy":
            assert min(all_bands) == 1 and max(all_bands) == 4
        elif difficulty == "medium":
            assert min(all_bands) == 1 and max(all_bands) == 5
        else:
            assert min(all_bands) == 2 and max(all_bands) == 6
        areas[difficulty] = sorted(len(grid) * len(grid[0]) for grid in grids)[len(grids) // 2]
    assert areas["easy"] < areas["medium"] < areas["hard"]


@pytest.mark.parametrize(
    "grid",
    [
        [],
        [[]],
        [[0] * 4 for _ in range(4)],
        [[False] * 8 for _ in range(8)],
        [[10] * 8 for _ in range(8)],
        [[0] * 8 for _ in range(7)] + [[0] * 7],
        [[0] * 10 for _ in range(10)],
        [[3] * 10 for _ in range(10)],
        [[0 if (row, col) != (5, 5) else 3 for col in range(10)] for row in range(10)],
        [[3 if row == 4 or col in (2, 6) else 0 for col in range(9)] for row in range(9)],
    ],
)
def test_malformed_and_minimal_impostors_fail_closed(grid):
    assert MODULE.self_check(grid)


def test_structural_mutations_fail_closed():
    grid = MODULE.generate(91, 7, scene_profile="public_4x4")
    facts = MODULE._analysis(grid)["facts"]
    stray = [row[:] for row in grid]
    stray[facts["row_ranges"][0][0]][facts["col_ranges"][0][0]] = 3
    assert MODULE.self_check(stray)
    broken = [row[:] for row in grid]
    broken[facts["divider_rows"][0]][0] = 0
    assert MODULE.self_check(broken)
    third_color = [row[:] for row in grid]
    third_color[facts["row_ranges"][1][0]][facts["col_ranges"][1][0]] = 5
    assert MODULE.self_check(third_color)
    missing_line = [row[:] for row in grid]
    for col in range(len(grid[0])):
        missing_line[facts["divider_rows"][0]][col] = 0
    assert MODULE.self_check(missing_line)
    border_line = [row[:] for row in grid]
    border_line[0] = [3] * len(grid[0])
    assert MODULE.self_check(border_line)


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
        {"texture": "full_grid"},
        {"grid_h": 19},
        {"band_count": 4},
        {"divider_color": 3},
        {"difficulty": "expert"},
    ],
)
def test_unknown_controls_fail_closed(kwargs):
    with pytest.raises(ValueError):
        MODULE.generate(1, 0, **kwargs)


def test_axis_and_source_contract_are_exact():
    assert MODULE.VERSION == "3.0.0"
    assert MODULE.RULE_HASH == "c2cf9830b316"
    assert set(MODULE.AXES) == {"scene_profile"}
    assert not MODULE.HELPFUL_TEXTURES and not MODULE.DEGENERATE_TEXTURES
    canonical_rule = canonical_rows()[0]["program_solution"]
    for row in canonical_rows():
        assert row["program_solution"] == canonical_rule
    for path in BASE_PATHS:
        target = json.loads(path.read_text())["racket_target"]
        assert target["raw_code"] == target["target_code"] == canonical_rule
