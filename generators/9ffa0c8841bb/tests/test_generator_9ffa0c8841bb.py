from __future__ import annotations

import hashlib
import importlib
import json
import random
from collections import Counter
from pathlib import Path

import pytest


TASK = "9ffa0c8841bb"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "data/canonical/puzzles.jsonl"
BASE_PATH = ROOT / "data/base/solutions/banks/0d41ded5f4cd/H91__9ffa0c8841bb.json"


def canonical_row():
    rows = [
        json.loads(line)
        for line in CANONICAL.read_text().splitlines()
        if json.loads(line)["task_id"] == TASK
    ]
    assert len(rows) == 1
    return rows[0]


def zero_components(grid):
    cells = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 0
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


def boundary_votes(grid, component):
    height, width = len(grid), len(grid[0])
    votes = []
    for row, col in component:
        for other_row, other_col in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
            if 0 <= other_row < height and 0 <= other_col < width:
                value = grid[other_row][other_col]
                if 1 <= value <= 4:
                    votes.append(value)
    return votes


def independent_winner(votes):
    counts = Counter(votes)
    if not counts:
        return 0
    maximum = max(counts.values())
    winners = [color for color, count in counts.items() if count == maximum]
    return winners[0] if len(winners) == 1 else 0


def independent_oracle(grid):
    output = [row[:] for row in grid]
    for component in zero_components(grid):
        winner = independent_winner(boundary_votes(grid, component))
        if winner:
            for row, col in component:
                output[row][col] = winner
    return output


def frozen(grid):
    return tuple(map(tuple, grid))


def test_all_five_canonical_pair_appearances_are_exact():
    row = canonical_row()
    normalized = " ".join(row["program_solution"].split())
    assert hashlib.sha256(normalized.encode()).hexdigest()[:12] == MODULE.RULE_HASH
    pairs = row["train"] + row["test"]
    assert len(pairs) == 5
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


def test_public_nuisances_preserve_complete_vote_families():
    literals = {frozen(pair["input"]) for pair in canonical_row()["train"] + canonical_row()["test"]}
    for profile in MODULE.PUBLIC_PROFILES:
        scenes = [MODULE._public_scene(profile, random.Random(seed)) for seed in range(60)]
        assert all(MODULE.canonical_family_signature(grid) == profile for grid in scenes)
        assert all(MODULE.self_check(grid) == [] for grid in scenes)
        assert any(frozen(grid) not in literals for grid in scenes)
        assert len({frozen(grid) for grid in scenes}) == 60


def test_general_profiles_have_exact_plurality_signatures():
    expected = {
        "all_colors": (0, 4),
        "one_tie": (1, 3),
        "two_ties": (2, 2),
        "shared_focus": (0, 1),
    }
    for profile, signature in expected.items():
        for seed in range(30):
            grid = MODULE.generate(seed, seed * 7, scene_profile=profile)
            facts = MODULE._analysis(grid)["facts"]
            winners = [item["winner"] for item in facts["chambers"]]
            observed = (winners.count(0), len(set(winners) - {0}))
            assert observed == signature
            if profile == "shared_focus":
                assert facts["internal_markers"] == 4


def test_unique_plurality_tie_and_preservation_branches():
    grid = [[9] * 12 for _ in range(10)]
    for row in range(1, 4):
        for col in range(1, 4):
            grid[row][col] = 0
        for col in range(7, 10):
            grid[row][col] = 0
    grid[0][1:4] = [1, 1, 2]
    grid[2][0] = 1
    grid[0][7:10] = [2, 3, 9]
    grid[4][7:10] = [2, 3, 9]
    for row in range(6, 8):
        for col in range(1, 3):
            grid[row][col] = 0
        for col in range(6, 8):
            grid[row][col] = 0
    grid[5][6] = 4
    before = frozen(grid)
    output = MODULE.rule_mirror(grid)
    assert output == independent_oracle(grid)
    assert frozen(grid) == before
    assert all(output[row][col] == 1 for row in range(1, 4) for col in range(1, 4))
    assert all(output[row][col] == 0 for row in range(1, 4) for col in range(7, 10))
    assert all(output[row][col] == 0 for row in range(6, 8) for col in range(1, 3))
    assert all(output[row][col] == 4 for row in range(6, 8) for col in range(6, 8))
    assert output[9][11] == 9
    assert MODULE.self_check(grid)


def test_shared_wall_markers_vote_into_both_adjacent_chambers():
    grid = MODULE.generate(701, 13, scene_profile="shared_focus")
    facts = MODULE._analysis(grid)["facts"]
    common = {item["winner"] for item in facts["chambers"]}
    assert len(common) == 1 and 0 not in common
    assert facts["internal_markers"] == 4
    output = MODULE.rule_mirror(grid)
    winner = common.pop()
    assert all(
        output[row][col] == winner
        for component in zero_components(grid)
        for row, col in component
    )


def test_default_distribution_is_complete_diverse_and_band_aware():
    expected_profiles = set(MODULE.SCENE_PROFILES)
    for difficulty in ("easy", "medium", "hard"):
        grids = [MODULE.generate(40_000 + seed, seed * 23, difficulty=difficulty) for seed in range(1200)]
        analyses = [MODULE._analysis(grid) for grid in grids]
        profiles = Counter(item["scene_profile"] for item in analyses)
        assert set(profiles) == expected_profiles
        assert all(count >= 65 for count in profiles.values())
        assert len({frozen(grid) for grid in grids}) >= 1150
        assert len({frozen(item["output"]) for item in analyses}) >= 1150
        assert all(item["errors"] == [] for item in analyses)
        assert {item["winner"] for analysis in analyses for item in analysis["facts"]["chambers"]} == {0, 1, 2, 3, 4}
    general_medians = {}
    for difficulty in ("easy", "medium", "hard"):
        areas = sorted(
            len(grid) * len(grid[0])
            for profile in MODULE.GENERAL_PROFILES
            for seed in range(100)
            for grid in [MODULE.generate(80_000 + seed, seed, difficulty=difficulty, scene_profile=profile)]
        )
        general_medians[difficulty] = areas[len(areas) // 2]
    assert general_medians["easy"] < general_medians["medium"] < general_medians["hard"]


@pytest.mark.parametrize(
    "grid",
    [
        [],
        [[]],
        [[0] * 12 for _ in range(12)],
        [[False] * 12 for _ in range(12)],
        [[10] * 12 for _ in range(12)],
        [[0] * 12 for _ in range(11)] + [[0] * 11],
        [[5] * 12 for _ in range(12)],
        [[0 if (row, col) != (5, 5) else 5 for col in range(12)] for row in range(12)],
    ],
)
def test_malformed_and_minimal_impostors_fail_closed(grid):
    assert MODULE.self_check(grid)


def test_structural_mutations_fail_closed():
    grid = MODULE.generate(91, 7, scene_profile="all_colors")
    facts = MODULE._analysis(grid)["facts"]
    opened = [row[:] for row in grid]
    opened[facts["wall_rows"][1]][2] = 0
    assert MODULE.self_check(opened)
    bad_intersection = [row[:] for row in grid]
    bad_intersection[facts["wall_rows"][1]][facts["wall_cols"][1]] = 1
    assert MODULE.self_check(bad_intersection)
    chamber_marker = [row[:] for row in grid]
    first = facts["chambers"][0]["bbox"]
    chamber_marker[first[0]][first[1]] = 1
    assert MODULE.self_check(chamber_marker)
    wrong_palette = [row[:] for row in grid]
    wrong_palette[0][1] = 6
    assert MODULE.self_check(wrong_palette)
    missing_color = [[5 if value == 4 else value for value in row] for row in grid]
    assert MODULE.self_check(missing_color)


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
        {"texture": "no_majority"},
        {"grid_h": 15},
        {"n_rooms": 4},
        {"marker_mix": "winner"},
        {"difficulty": "expert"},
    ],
)
def test_unknown_controls_fail_closed(kwargs):
    with pytest.raises(ValueError):
        MODULE.generate(1, 0, **kwargs)


def test_axis_and_source_contract_are_exact():
    assert MODULE.VERSION == "3.0.0"
    assert MODULE.RULE_HASH == "e1d60c5dd3e1"
    assert set(MODULE.AXES) == {"scene_profile"}
    assert not MODULE.HELPFUL_TEXTURES and not MODULE.DEGENERATE_TEXTURES
    canonical_rule = canonical_row()["program_solution"]
    target = json.loads(BASE_PATH.read_text())["racket_target"]
    assert target["raw_code"] == target["target_code"] == canonical_rule
