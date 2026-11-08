from __future__ import annotations

from collections import Counter, deque
import hashlib
import importlib
import json
from pathlib import Path
import random

import pytest


TASK = "d4f2f542248a"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "data" / "canonical" / "puzzles.jsonl"
BASE_PATH = ROOT / "data" / "base" / "solutions" / "banks" / "0d41ded5f4cd" / "H85__d4f2f542248a.json"


def canonical_row():
    rows = [
        json.loads(line)
        for line in CANONICAL.read_text().splitlines()
        if json.loads(line).get("task_id") == TASK
    ]
    assert len(rows) == 1
    assert (rows[0]["source"], len(rows[0]["train"]), len(rows[0]["test"])) == (
        "bank:0d41ded5f4cd", 4, 1
    )
    return rows[0]


def canonical_pairs():
    row = canonical_row()
    return row["train"] + row["test"]


def frozen(grid):
    return tuple(map(tuple, grid))


def independent_bfs(grid, start):
    height, width = len(grid), len(grid[0])
    distance, count = {start: 0}, {start: 1}
    queue = deque([start])
    while queue:
        row, col = queue.popleft()
        for next_row, next_col in (
            (row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)
        ):
            if not (0 <= next_row < height and 0 <= next_col < width):
                continue
            if grid[next_row][next_col] == 5:
                continue
            neighbor = (next_row, next_col)
            candidate = distance[(row, col)] + 1
            if neighbor not in distance:
                distance[neighbor] = candidate
                count[neighbor] = count[(row, col)]
                queue.append(neighbor)
            elif distance[neighbor] == candidate:
                count[neighbor] += count[(row, col)]
    return distance, count


def independent_facts(grid):
    start = next((
        (row, col) for row, values in enumerate(grid)
        for col, value in enumerate(values) if value == 2
    ))
    goal = next((
        (row, col) for row, values in enumerate(grid)
        for col, value in enumerate(values) if value == 3
    ))
    from_start, start_count = independent_bfs(grid, start)
    from_goal, goal_count = independent_bfs(grid, goal)
    if goal not in from_start:
        return {"connected": False, "unavoidable": ()}
    distance = from_start[goal]
    total = start_count[goal]
    shortest = tuple(sorted(
        cell for cell in from_start
        if cell in from_goal and from_start[cell] + from_goal[cell] == distance
    ))
    unavoidable = tuple(sorted(
        cell for cell in shortest
        if grid[cell[0]][cell[1]] == 0 and start_count[cell] * goal_count[cell] == total
    ))
    return {
        "connected": True,
        "distance": distance,
        "paths": total,
        "shortest_blank_count": sum(grid[row][col] == 0 for row, col in shortest),
        "unavoidable": unavoidable,
    }


def independent_oracle(grid):
    output = [row[:] for row in grid]
    facts = independent_facts(grid)
    for row, col in facts["unavoidable"]:
        output[row][col] = 8
    return output


def test_metadata_hash_and_control_surface_are_exact():
    assert MODULE.VERSION == "2.0.0"
    assert MODULE.RULE_HASH == "de5e86ab7e23"
    assert tuple(MODULE.AXES) == ("scene_profile",)
    assert MODULE.SCENE_PROFILES == MODULE.PUBLIC_PROFILES + MODULE.GENERAL_PROFILES
    assert MODULE.HELPFUL_TEXTURES == MODULE.DEGENERATE_TEXTURES == ()
    normalized = " ".join(canonical_row()["program_solution"].split())
    assert hashlib.sha256(normalized.encode()).hexdigest()[:12] == MODULE.RULE_HASH


@pytest.mark.parametrize("index", range(5))
def test_every_canonical_pair_is_exact_anchored_and_independently_counted(index):
    pair = canonical_pairs()[index]
    profile = f"public_{index + 1}"
    expected = [
        (7, 10, 12, 2), (17, 6, 19, 13), (14, 39, 26, 3),
        (15, 3, 16, 12), (7, 10, 12, 2),
    ][index]
    facts = independent_facts(pair["input"])
    assert (facts["distance"], facts["paths"], facts["shortest_blank_count"], len(facts["unavoidable"])) == expected
    assert MODULE.canonical_profile_signature(pair["input"]) == profile
    assert MODULE.canonical_family_signature(pair["input"]) == profile
    assert MODULE.self_check(pair["input"]) == []
    assert MODULE.rule_mirror(pair["input"]) == independent_oracle(pair["input"])
    assert MODULE.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("profile", MODULE.PUBLIC_PROFILES)
@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_forced_public_profiles_are_exact_fresh_anchors(profile, band):
    first = MODULE.generate(19, 7, difficulty=band, scene_profile=profile)
    second = MODULE.generate(999, 333, difficulty=band, scene_profile=profile)
    expected = MODULE._PUBLIC_INPUTS[profile]
    assert first == second == expected
    assert first is not expected and first[0] is not expected[0]
    assert MODULE.canonical_profile_signature(first) == profile
    assert MODULE.observe_overrides(first) == {"scene_profile": profile}


@pytest.mark.parametrize("profile", MODULE.PUBLIC_PROFILES)
def test_public_variant_pool_is_distinct_and_preserves_the_complete_path_signature(profile):
    pool = MODULE._public_variant_pool(profile)
    assert len(pool) == len(set(pool)) == MODULE._PUBLIC_POOL_SIZE
    for index in range(0, MODULE._PUBLIC_VARIANTS_PER_BAND, 31):
        grid = MODULE._mutate_public(profile, index, 2)
        assert MODULE.canonical_family_signature(grid) == profile
        assert MODULE.self_check(grid) == []
        assert MODULE.rule_mirror(grid) == independent_oracle(grid)


@pytest.mark.parametrize("profile", MODULE.GENERAL_PROFILES)
@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_general_profile_and_band_is_valid_observable_and_independently_exact(profile, band):
    for seed in range(6):
        grid = MODULE.generate(20_000 + seed, seed * 31 + 7, difficulty=band, scene_profile=profile)
        analysis = MODULE._analysis(grid)
        facts = independent_facts(grid)
        assert analysis["errors"] == []
        assert analysis["scene_profile"] == profile
        assert MODULE.observe_overrides(grid) == {"scene_profile": profile}
        assert analysis["facts"]["shortest_distance"] == facts["distance"]
        assert analysis["facts"]["total_paths"] == facts["paths"]
        assert analysis["facts"]["unavoidable"] == facts["unavoidable"]
        assert analysis["output"] == MODULE.rule_mirror(grid) == independent_oracle(grid)


def test_default_census_is_balanced_complete_unique_and_oracle_exact():
    for band in (None, "easy", "medium", "hard"):
        inputs, outputs = set(), set()
        profiles = Counter()
        for sample_index in range(440):
            grid = MODULE.generate(810_000, sample_index, difficulty=band)
            analysis = MODULE._analysis(grid)
            assert analysis["errors"] == []
            assert analysis["output"] == independent_oracle(grid)
            inputs.add(frozen(grid))
            outputs.add(frozen(analysis["output"]))
            profiles[analysis["scene_profile"]] += 1
        assert len(inputs) == len(outputs) == 440
        assert set(profiles) == set(MODULE.SCENE_PROFILES)
        assert set(profiles.values()) == {40}


def test_profile_path_statistics_are_semantically_distinct():
    facts = {
        profile: MODULE._analysis(MODULE.generate(91, 9, scene_profile=profile))["facts"]
        for profile in MODULE.GENERAL_PROFILES
    }
    assert facts["unique_route"]["total_paths"] == 1
    assert facts["many_paths_few_gates"]["total_paths"] >= 8
    assert len(facts["many_paths_few_gates"]["unavoidable"]) <= 4
    assert 2 <= facts["few_paths_long_spine"]["total_paths"] <= 7
    assert len(facts["few_paths_long_spine"]["unavoidable"]) >= 8
    assert facts["many_paths_shared_spine"]["total_paths"] >= 8
    assert len(facts["many_paths_shared_spine"]["unavoidable"]) >= 5
    assert facts["dead_end_contrast"]["dead_ends"] >= 3
    assert facts["dead_end_contrast"]["unreachable_open"] == 0
    assert facts["disconnected_pockets"]["unreachable_open"] >= 1


def test_cross_profile_endpoint_recombination_is_not_an_official_family():
    grid = [row[:] for row in MODULE._PUBLIC_INPUTS["public_1"]]
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value in (2, 3):
                grid[row][col] = 0
    grid[1][1] = 2
    grid[7][10] = 3
    assert MODULE.canonical_profile_signature(grid) is None
    assert MODULE.canonical_family_signature(grid) is None


def test_two_equal_branches_mark_shared_bottlenecks_not_branch_cells():
    grid = [[5] * 11 for _ in range(9)]
    open_cells = {
        (4, 1), (4, 2), (4, 3),
        (3, 3), (2, 3), (2, 4), (2, 5), (2, 6), (2, 7), (3, 7),
        (5, 3), (6, 3), (6, 4), (6, 5), (6, 6), (6, 7), (5, 7),
        (4, 7), (4, 8), (4, 9),
    }
    for row, col in open_cells:
        grid[row][col] = 0
    grid[4][1], grid[4][9] = 2, 3
    facts = independent_facts(grid)
    output = MODULE.rule_mirror(grid)
    assert facts["paths"] == 2
    assert facts["unavoidable"] == ((4, 2), (4, 3), (4, 7), (4, 8))
    assert output == independent_oracle(grid)
    assert output[2][5] == output[6][5] == 0


def test_unique_shortest_route_ignores_a_longer_alternative():
    grid = [[5] * 12 for _ in range(10)]
    for col in range(1, 11):
        grid[3][col] = 0
    for row, col in (
        (4, 2), (5, 2), (6, 2), (7, 2), (7, 3), (7, 4), (7, 5),
        (7, 6), (7, 7), (7, 8), (7, 9), (6, 9), (5, 9), (4, 9),
    ):
        grid[row][col] = 0
    grid[3][1], grid[3][10] = 2, 3
    facts = independent_facts(grid)
    output = MODULE.rule_mirror(grid)
    assert facts["paths"] == 1
    assert len(facts["unavoidable"]) == 8
    assert all(output[3][col] == 8 for col in range(2, 10))
    assert all(output[7][col] == 0 for col in range(2, 10))


def test_disconnected_blank_pockets_are_preserved():
    grid = MODULE.generate(77, 11, scene_profile="disconnected_pockets")
    facts = MODULE._analysis(grid)["facts"]
    output = MODULE.rule_mirror(grid)
    unreachable = []
    start = facts["start"]
    reachable = set(independent_bfs(grid, start)[0])
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value == 0 and (row, col) not in reachable:
                unreachable.append((row, col))
    assert unreachable
    assert all(output[row][col] == 0 for row, col in unreachable)


def test_rule_mirror_is_input_pure_and_reentrant():
    grid = MODULE.generate(91, 9, difficulty="hard")
    before = frozen(grid)
    first = MODULE.rule_mirror(grid)
    second = MODULE.rule_mirror(grid)
    assert frozen(grid) == before
    assert first == second and first is not second and first[0] is not second[0]


@pytest.mark.parametrize(
    "grid",
    [
        [], [[]], [[False] * 11 for _ in range(10)], [[10] * 11 for _ in range(10)],
        [[5] * 11 for _ in range(9)] + [[5] * 10], [[5] * 10 for _ in range(9)],
        [[5] * 15 for _ in range(12)], [[5] * 11 for _ in range(15)],
        [[0] * 11 for _ in range(10)], [[5] * 11 for _ in range(10)],
    ],
)
def test_malformed_and_out_of_curriculum_inputs_fail_closed(grid):
    assert MODULE.self_check(grid)


def test_structural_mutations_fail_closed():
    grid = MODULE.generate(811, 7, difficulty="medium", scene_profile="many_paths_few_gates")

    input_cyan = [row[:] for row in grid]
    blank = next((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 0)
    input_cyan[blank[0]][blank[1]] = 8
    assert MODULE.self_check(input_cyan)

    broken_border = [row[:] for row in grid]
    broken_border[0][1] = 0
    assert MODULE.self_check(broken_border)

    missing_goal = [row[:] for row in grid]
    goal = next((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 3)
    missing_goal[goal[0]][goal[1]] = 0
    assert MODULE.self_check(missing_goal)

    duplicate_start = [row[:] for row in grid]
    duplicate_start[blank[0]][blank[1]] = 2
    assert MODULE.self_check(duplicate_start)


def test_determinism_fresh_returns_and_global_rng_isolation():
    random.seed(123_456)
    state = random.getstate()
    first = MODULE.generate(731, 19, difficulty="hard")
    assert random.getstate() == state
    second = MODULE.generate(731, 19, difficulty="hard")
    assert first == second and first is not second and first[0] is not second[0]
    original = second[0][0]
    first[0][0] = 0
    assert second[0][0] == original
    assert MODULE.generate(731, 20, difficulty="hard") != second


@pytest.mark.parametrize(
    "kwargs",
    [
        {"scene_profile": "unknown"}, {"texture": "no_corridor"}, {"grid_h": 10},
        {"grid_w": 12}, {"anchor_corner": True}, {"palette_kind": "warm"},
        {"difficulty": "expert"},
    ],
)
def test_unknown_and_retired_controls_fail_closed(kwargs):
    with pytest.raises(ValueError):
        MODULE.generate(1, 2, **kwargs)


def test_base_authority_and_reviewed_metadata_match_canonical_program():
    base = json.loads(BASE_PATH.read_text())
    source = canonical_row()["program_solution"]
    assert base["racket_target"]["raw_code"] == source
    assert base["racket_target"]["target_code"] == source
    description = base["description_target"]
    assert description["target_status"] == "reviewed_semantic_description"
    assert description["generator_parameters"] == ["scene_profile"]
    assert "every shortest" in description["target_text"]
    assert "at least one" in description["ambiguity_notes"]
