from __future__ import annotations

import hashlib
import importlib
import json
import random
from collections import Counter
from pathlib import Path

import pytest


TASK = "9d52c9d09009"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "data/canonical/puzzles.jsonl"
BASE_PATH = ROOT / "data/base/solutions/training/37d3e8b2__9d52c9d09009.json"


def canonical_row():
    rows = []
    with CANONICAL.open() as handle:
        for line in handle:
            row = json.loads(line)
            if row["task_id"] == TASK:
                rows.append(row)
    assert len(rows) == 1
    return rows[0]


def components4(grid, color=8):
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
            for other in ((row + 1, col), (row - 1, col), (row, col + 1), (row, col - 1)):
                if other in cells:
                    cells.remove(other)
                    queue.append(other)
        result.append(component)
    return sorted(result, key=lambda component: min(component))


def hole_count(grid, component):
    rows = [row for row, _ in component]
    cols = [col for _, col in component]
    row0, row1, col0, col1 = min(rows), max(rows), min(cols), max(cols)
    zeros = {
        (row, col)
        for row in range(row0, row1 + 1)
        for col in range(col0, col1 + 1)
        if grid[row][col] == 0
    }
    count = 0
    while zeros:
        queue = [zeros.pop()]
        for row, col in queue:
            for other in ((row + 1, col), (row - 1, col), (row, col + 1), (row, col - 1)):
                if other in zeros:
                    zeros.remove(other)
                    queue.append(other)
        count += 1
    return count


def independent_oracle(grid):
    output = [row[:] for row in grid]
    for component in components4(grid):
        holes = hole_count(grid, component)
        color = 7 if holes == 4 else holes
        for row, col in component:
            output[row][col] = color
    return output


def frozen(grid):
    return tuple(map(tuple, grid))


def test_all_four_canonical_pair_appearances_are_exact():
    row = canonical_row()
    assert hashlib.sha256(row["program_solution"].encode()).hexdigest()[:12] == MODULE.RULE_HASH
    pairs = row["train"] + row["test"]
    assert len(pairs) == 4
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


def test_public_nuisances_preserve_complete_object_morphology_without_literals():
    literals = {frozen(pair["input"]) for pair in canonical_row()["train"] + canonical_row()["test"]}
    for profile in MODULE.PUBLIC_PROFILES:
        expected = tuple(sorted(MODULE._family_key(shape) for shape in MODULE._PUBLIC_OBJECTS[profile]))
        scenes = [MODULE._public_scene(profile, "medium", random.Random(seed)) for seed in range(60)]
        assert all(MODULE._analysis(grid)["facts"]["family_signature"] == expected for grid in scenes)
        assert all(MODULE.canonical_family_signature(grid) == profile for grid in scenes)
        assert all(frozen(grid) not in literals for grid in scenes)
        assert len({frozen(grid) for grid in scenes}) == 60


def test_general_profiles_have_exact_hole_signatures():
    for profile, signature in MODULE._GENERAL_HOLES.items():
        for seed in range(30):
            grid = MODULE.generate(seed, seed * 7, scene_profile=profile)
            assert MODULE._analysis(grid)["facts"]["hole_signature"] == tuple(sorted(signature))


def test_each_hole_count_maps_to_the_intended_output_color():
    grid = MODULE.generate(501, 23, scene_profile="all_counts")
    analysis = MODULE._analysis(grid)
    output = MODULE.rule_mirror(grid)
    seen = {}
    for obj in analysis["facts"]["objects"]:
        color = 7 if obj["holes"] == 4 else obj["holes"]
        assert all(output[row][col] == color for row, col in obj["cells"])
        seen[obj["holes"]] = color
    assert seen == {1: 1, 2: 2, 3: 3, 4: 7}
    assert 4 not in {value for row in output for value in row}


def test_broad_rule_handles_zero_five_and_other_color_branches():
    grid = [[6] * 27 for _ in range(15)]
    # A solid 3x4 color-8 block has zero bounding-box zero regions and is erased.
    for row in range(1, 4):
        for col in range(1, 5):
            grid[row][col] = 8
    # A 3x11 outer frame with four internal walls has five zero regions and maps to 5.
    for row in range(6, 9):
        for col in range(10, 21):
            if row in (6, 8) or col in (10, 12, 14, 16, 18, 20):
                grid[row][col] = 8
            else:
                grid[row][col] = 0
    before = frozen(grid)
    output = MODULE.rule_mirror(grid)
    assert output == independent_oracle(grid)
    assert frozen(grid) == before
    assert all(output[row][col] == 0 for row in range(1, 4) for col in range(1, 5))
    assert all(output[row][col] == 5 for row, col in components4(grid)[1])
    assert MODULE.self_check(grid)


def test_default_distribution_is_complete_diverse_and_band_aware():
    expected_profiles = set(MODULE.SCENE_PROFILES)
    medians = {}
    for difficulty in ("easy", "medium", "hard"):
        grids = [MODULE.generate(40_000 + seed, seed * 23, difficulty=difficulty) for seed in range(1200)]
        analyses = [MODULE._analysis(grid) for grid in grids]
        profiles = Counter(item["scene_profile"] for item in analyses)
        assert set(profiles) == expected_profiles
        assert all(count >= 70 for count in profiles.values())
        assert len({frozen(grid) for grid in grids}) == len(grids)
        assert len({frozen(item["output"]) for item in analyses}) == len(grids)
        assert all(item["errors"] == [] for item in analyses)
        assert {obj["holes"] for item in analyses for obj in item["facts"]["objects"]} == {1, 2, 3, 4}
        areas = sorted(len(grid) * len(grid[0]) for grid in grids)
        medians[difficulty] = areas[len(areas) // 2]
    assert medians["easy"] < medians["medium"] < medians["hard"]


@pytest.mark.parametrize(
    "grid",
    [
        [],
        [[]],
        [[0] * 10 for _ in range(10)],
        [[False] * 12 for _ in range(12)],
        [[10] * 12 for _ in range(12)],
        [[0] * 12 for _ in range(11)] + [[0] * 11],
        [[8] * 12 for _ in range(12)],
        [[0 if (row, col) != (5, 5) else 8 for col in range(12)] for row in range(12)],
        [[8 if 2 <= row <= 5 and 2 <= col <= 6 else 0 for col in range(12)] for row in range(12)],
    ],
)
def test_malformed_and_minimal_impostors_fail_closed(grid):
    assert MODULE.self_check(grid)


def test_structural_mutations_fail_closed():
    grid = MODULE.generate(91, 7, scene_profile="all_counts")
    facts = MODULE._analysis(grid)["facts"]
    isolated = [row[:] for row in grid]
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            if grid[row][col] == 0 and all(
                not (0 <= row + dr < len(grid) and 0 <= col + dc < len(grid[0]))
                or grid[row + dr][col + dc] == 0
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
            ):
                isolated[row][col] = 8
                break
        else:
            continue
        break
    assert MODULE.self_check(isolated)
    opened = [row[:] for row in grid]
    first = facts["objects"][0]
    border_cell = min(first["cells"])
    opened[border_cell[0]][border_cell[1]] = 0
    assert MODULE.self_check(opened)
    third_color = [row[:] for row in grid]
    row, col = facts["objects"][1]["cells"][0]
    third_color[row][col] = 5
    assert MODULE.self_check(third_color)
    deleted = [row[:] for row in grid]
    for row, col in facts["objects"][2]["cells"]:
        deleted[row][col] = 0
    assert MODULE.self_check(deleted)


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
        {"texture": "solid_block"},
        {"grid_h": 19},
        {"frame1_h": 5},
        {"anchor_corner": True},
        {"difficulty": "expert"},
    ],
)
def test_unknown_controls_fail_closed(kwargs):
    with pytest.raises(ValueError):
        MODULE.generate(1, 0, **kwargs)


def test_axis_and_source_contract_are_exact():
    assert MODULE.VERSION == "3.0.0"
    assert MODULE.RULE_HASH == "3d808db30609"
    assert set(MODULE.AXES) == {"scene_profile"}
    assert not MODULE.HELPFUL_TEXTURES and not MODULE.DEGENERATE_TEXTURES
    canonical_rule = canonical_row()["program_solution"]
    target = json.loads(BASE_PATH.read_text())["racket_target"]
    assert target["raw_code"] == target["target_code"] == canonical_rule
