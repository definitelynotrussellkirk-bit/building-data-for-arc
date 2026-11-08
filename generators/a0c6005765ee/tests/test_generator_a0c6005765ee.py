from __future__ import annotations

import hashlib
import importlib
import json
import random
from collections import Counter
from pathlib import Path

import pytest


TASK = "a0c6005765ee"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "data/canonical/puzzles.jsonl"
BASE_PATH = ROOT / "data/base/solutions/banks/e352836528da/M4__a0c6005765ee.json"


def canonical_row():
    rows = [
        json.loads(line)
        for line in CANONICAL.read_text().splitlines()
        if json.loads(line)["task_id"] == TASK
    ]
    assert len(rows) == 1
    return rows[0]


def components4(grid, color):
    cells = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    }
    result = []
    while cells:
        queue = [cells.pop()]
        component = []
        for row, col in queue:
            component.append((row, col))
            for other in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if other in cells:
                    cells.remove(other)
                    queue.append(other)
        result.append(component)
    return sorted(result, key=lambda component: min(component))


def independent_frames(grid):
    frames = []
    for component in components4(grid, 5):
        rows = [row for row, _ in component]
        cols = [col for _, col in component]
        row0, col0, row1, col1 = min(rows), min(cols), max(rows), max(cols)
        border = {
            (row, col)
            for row in range(row0, row1 + 1)
            for col in range(col0, col1 + 1)
            if row in (row0, row1) or col in (col0, col1)
        }
        if border <= set(component):
            frames.append((row0, col0, row1, col1))
    return frames


def independent_oracle(grid):
    output = [row[:] for row in grid]
    height, width = len(grid), len(grid[0])
    for row in range(height):
        for col in range(width):
            for row0, col0, row1, col1 in independent_frames(grid):
                if not (row0 < row < row1 and col0 < col < col1):
                    continue
                if (
                    (row0 > 0 and grid[row0 - 1][col] == 7)
                    or (row1 < height - 1 and grid[row1 + 1][col] == 7)
                    or (col0 > 0 and grid[row][col0 - 1] == 7)
                    or (col1 < width - 1 and grid[row][col1 + 1] == 7)
                ):
                    output[row][col] = 3
                    break
    return output


def frozen(grid):
    return tuple(map(tuple, grid))


def draw_frame(grid, row0, col0, row1, col1):
    for row in range(row0, row1 + 1):
        for col in range(col0, col1 + 1):
            if row in (row0, row1) or col in (col0, col1):
                grid[row][col] = 5


def test_all_three_canonical_pair_appearances_are_exact():
    row = canonical_row()
    normalized = " ".join(row["program_solution"].split())
    assert hashlib.sha256(normalized.encode()).hexdigest()[:12] == MODULE.RULE_HASH
    pairs = row["train"] + row["test"]
    assert len(pairs) == 3
    profiles = {}
    for pair in pairs:
        grid = pair["input"]
        assert MODULE.rule_mirror(grid) == independent_oracle(grid) == pair["output"]
        assert MODULE.self_check(grid) == []
        profile = MODULE.canonical_profile_signature(grid)
        assert profile in MODULE.PUBLIC_PROFILES
        assert MODULE.canonical_family_signature(grid) == profile
        profiles[profile] = frozen(grid)
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


def test_public_nuisances_preserve_complete_official_frame_families():
    literals = {frozen(pair["input"]) for pair in canonical_row()["train"] + canonical_row()["test"]}
    for profile in MODULE.PUBLIC_PROFILES:
        scenes = [MODULE._random_scene(profile, "medium", random.Random(seed)) for seed in range(80)]
        assert all(MODULE.canonical_family_signature(grid) == profile for grid in scenes)
        assert all(MODULE.self_check(grid) == [] for grid in scenes)
        assert all(frozen(grid) not in literals for grid in scenes)
        assert len({frozen(grid) for grid in scenes}) == 80


def test_general_profiles_have_exact_frame_and_marker_signatures():
    expected = {
        "single_large": (1, (1,)),
        "double_varied": (2, (1, 1)),
        "two_stripes": (1, (2,)),
        "cross_stripes": (1, (4,)),
    }
    for profile, signature in expected.items():
        for seed in range(40):
            grid = MODULE.generate(seed, seed * 7, scene_profile=profile)
            facts = MODULE._analysis(grid)["facts"]
            assert (facts["frame_count"], facts["marker_counts"]) == signature
            if profile == "cross_stripes":
                assert {marker[0] for marker in facts["frames"][0]["markers"]} == {
                    "top", "bottom", "left", "right"
                }


def test_all_four_marker_directions_project_correctly():
    for side in ("top", "bottom", "left", "right"):
        grid = [[0] * 11 for _ in range(11)]
        draw_frame(grid, 3, 3, 7, 7)
        if side == "top":
            grid[2][5] = 7
            expected = {(row, 5) for row in range(4, 7)}
        elif side == "bottom":
            grid[8][5] = 7
            expected = {(row, 5) for row in range(4, 7)}
        elif side == "left":
            grid[5][2] = 7
            expected = {(5, col) for col in range(4, 7)}
        else:
            grid[5][8] = 7
            expected = {(5, col) for col in range(4, 7)}
        output = MODULE.rule_mirror(grid)
        assert output == independent_oracle(grid)
        assert {(row, col) for row in range(11) for col in range(11) if output[row][col] == 3} == expected


def test_broad_rule_handles_union_distractor_border_and_arbitrary_colors():
    grid = [[8] * 18 for _ in range(14)]
    draw_frame(grid, 0, 2, 6, 9)
    grid[3][10] = 7
    grid[7][5] = 7
    draw_frame(grid, 4, 12, 10, 17)
    grid[3][14] = 7
    grid[8][11] = 7
    grid[12][2] = 5
    grid[12][3] = 5
    grid[13][2] = 5
    before = frozen(grid)
    output = MODULE.rule_mirror(grid)
    assert output == independent_oracle(grid)
    assert frozen(grid) == before
    assert output[3][5] == 3
    assert output[5][6] == 8
    assert output[6][5] == 5
    assert output[5][14] == 3
    assert output[8][14] == 3
    assert output[12][2] == 5
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
        assert len({frozen(grid) for grid in grids}) >= 1150
        assert len({frozen(item["output"]) for item in analyses}) >= 1150
        assert all(item["errors"] == [] for item in analyses)
        assert {side for item in analyses for frame in item["facts"]["frames"] for side, *_ in frame["markers"]} == {
            "top", "bottom", "left", "right"
        }
        areas = sorted(len(grid) * len(grid[0]) for grid in grids)
        medians[difficulty] = areas[len(areas) // 2]
    assert medians["easy"] < medians["medium"] < medians["hard"]


@pytest.mark.parametrize(
    "grid",
    [
        [],
        [[]],
        [[0] * 7 for _ in range(7)],
        [[False] * 8 for _ in range(8)],
        [[10] * 8 for _ in range(8)],
        [[0] * 8 for _ in range(7)] + [[0] * 7],
        [[0] * 8 for _ in range(8)],
        [[5] * 8 for _ in range(8)],
        [[0 if (row, col) != (3, 3) else 7 for col in range(8)] for row in range(8)],
    ],
)
def test_malformed_and_minimal_impostors_fail_closed(grid):
    assert MODULE.self_check(grid)


def test_structural_mutations_fail_closed():
    grid = MODULE.generate(91, 7, scene_profile="public_1")
    facts = MODULE._analysis(grid)["facts"]
    frame = facts["frames"][0]
    row0, col0, row1, col1 = frame["bbox"]
    opened = [row[:] for row in grid]
    opened[row0][col0] = 0
    assert MODULE.self_check(opened)
    filled = [row[:] for row in grid]
    filled[row0 + 1][col0 + 1] = 5
    assert MODULE.self_check(filled)
    corner_marker = [row[:] for row in grid]
    marker = next(iter(facts["markers"]))
    corner_marker[marker[0]][marker[1]] = 0
    if row0 > 0:
        corner_marker[row0 - 1][col0] = 7
    else:
        corner_marker[row1 + 1][col0] = 7
    assert MODULE.self_check(corner_marker)
    extra_marker = [row[:] for row in grid]
    extra_marker[-1][-1] = 7
    assert MODULE.self_check(extra_marker)
    third_color = [row[:] for row in grid]
    third_color[-1][-1] = 2
    assert MODULE.self_check(third_color)


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
        {"texture": "marker_at_corner"},
        {"grid_h": 12},
        {"side": "top"},
        {"palette_kind": "warm"},
        {"density": "sparse"},
        {"difficulty": "expert"},
    ],
)
def test_unknown_controls_fail_closed(kwargs):
    with pytest.raises(ValueError):
        MODULE.generate(1, 0, **kwargs)


def test_axis_and_source_contract_are_exact():
    assert MODULE.VERSION == "3.0.0"
    assert MODULE.RULE_HASH == "dd8e67797905"
    assert set(MODULE.AXES) == {"scene_profile"}
    assert not MODULE.HELPFUL_TEXTURES and not MODULE.DEGENERATE_TEXTURES
    canonical_rule = canonical_row()["program_solution"]
    target = json.loads(BASE_PATH.read_text())["racket_target"]
    assert target["raw_code"] == target["target_code"] == canonical_rule
