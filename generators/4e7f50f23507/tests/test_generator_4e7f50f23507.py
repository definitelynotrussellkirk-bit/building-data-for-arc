from __future__ import annotations

from collections import Counter, deque
import hashlib
import importlib
import json
from pathlib import Path
import random

import pytest


TASK = "4e7f50f23507"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "data" / "canonical" / "puzzles.jsonl"
BASE_PATH = ROOT / "data" / "base" / "solutions" / "banks" / "7f8a290afe75" / "H82__4e7f50f23507.json"


def canonical_row():
    rows = [
        json.loads(line)
        for line in CANONICAL.read_text().splitlines()
        if json.loads(line).get("task_id") == TASK
    ]
    assert len(rows) == 1
    assert (rows[0]["source"], len(rows[0]["train"]), len(rows[0]["test"])) == (
        "bank:7f8a290afe75", 4, 1
    )
    return rows[0]


def canonical_pairs():
    row = canonical_row()
    return row["train"] + row["test"]


def frozen(grid):
    return tuple(map(tuple, grid))


def independent_bfs(grid, start):
    height, width = len(grid), len(grid[0])
    distances = {start: 0}
    queue = deque([start])
    while queue:
        row, col = queue.popleft()
        for next_row, next_col in (
            (row - 1, col), (row + 1, col),
            (row, col - 1), (row, col + 1),
        ):
            neighbor = (next_row, next_col)
            if not (0 <= next_row < height and 0 <= next_col < width):
                continue
            if grid[next_row][next_col] == 5 or neighbor in distances:
                continue
            distances[neighbor] = distances[(row, col)] + 1
            queue.append(neighbor)
    return distances


def independent_components(cells):
    remaining = set(cells)
    sizes = []
    while remaining:
        stack = [remaining.pop()]
        size = 0
        while stack:
            row, col = stack.pop()
            size += 1
            for neighbor in (
                (row - 1, col), (row + 1, col),
                (row, col - 1), (row, col + 1),
            ):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
        sizes.append(size)
    return tuple(sorted(sizes, reverse=True))


def independent_facts(grid):
    seed_2 = next(
        (row, col) for row, values in enumerate(grid)
        for col, value in enumerate(values) if value == 2
    )
    seed_3 = next(
        (row, col) for row, values in enumerate(grid)
        for col, value in enumerate(values) if value == 3
    )
    distance_2 = independent_bfs(grid, seed_2)
    distance_3 = independent_bfs(grid, seed_3)
    equal = tuple(sorted(
        cell for cell in set(distance_2) & set(distance_3)
        if grid[cell[0]][cell[1]] == 0 and distance_2[cell] == distance_3[cell]
    ))
    all_open = {
        (row, col) for row, values in enumerate(grid)
        for col, value in enumerate(values) if value != 5
    }
    return {
        "seed_2": seed_2,
        "seed_3": seed_3,
        "connected": seed_3 in distance_2,
        "shortest": distance_2.get(seed_3),
        "manhattan": abs(seed_2[0] - seed_3[0]) + abs(seed_2[1] - seed_3[1]),
        "equal": equal,
        "components": independent_components(equal),
        "reachable": set(distance_2),
        "unreachable_open": all_open - set(distance_2),
    }


def independent_oracle(grid):
    output = [row[:] for row in grid]
    for row, col in independent_facts(grid)["equal"]:
        output[row][col] = 8
    return output


def test_metadata_hash_and_control_surface_are_exact():
    assert MODULE.VERSION == "3.0.0"
    assert MODULE.RULE_HASH == "c06350648cb4"
    assert MODULE.EXAMPLES_NEEDED == 4
    assert tuple(MODULE.AXES) == ("scene_profile",)
    assert MODULE.SCENE_PROFILES == MODULE.PUBLIC_PROFILES + MODULE.GENERAL_PROFILES
    assert MODULE.HELPFUL_TEXTURES == MODULE.DEGENERATE_TEXTURES == ()
    normalized = " ".join(canonical_row()["program_solution"].split())
    assert hashlib.sha256(normalized.encode()).hexdigest()[:12] == MODULE.RULE_HASH


@pytest.mark.parametrize("index", range(5))
def test_every_canonical_pair_is_exact_anchored_and_independently_solved(index):
    pair = canonical_pairs()[index]
    profile = f"public_{index + 1}"
    expected = [
        (14, 8, 4, (2, 2), 0),
        (12, 12, 10, (3, 3, 1, 1, 1, 1), 0),
        (12, 12, 23, (9, 9, 1, 1, 1, 1, 1), 0),
        (14, 14, 6, (2, 2, 1, 1), 0),
        (8, 8, 9, (9,), 0),
    ][index]
    facts = independent_facts(pair["input"])
    assert (
        facts["shortest"], facts["manhattan"], len(facts["equal"]),
        facts["components"], len(facts["unreachable_open"]),
    ) == expected
    assert MODULE._PUBLIC_INPUTS[profile] == pair["input"]
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
    assert MODULE.canonical_family_signature(first) == profile
    assert MODULE.observe_overrides(first) == {"scene_profile": profile}


@pytest.mark.parametrize("profile", MODULE.PUBLIC_PROFILES)
def test_embedded_public_streams_are_unique_disjoint_and_retain_exact_sealed_core(profile):
    streams = []
    for band_index in range(4):
        grids = [MODULE._embed_public(profile, index, band_index) for index in range(40)]
        signatures = {frozen(grid) for grid in grids}
        assert len(signatures) == 40
        streams.append(signatures)
        for grid in grids[::7]:
            assert MODULE.canonical_profile_signature(grid) is None
            assert MODULE.canonical_family_signature(grid) == profile
            assert MODULE.self_check(grid) == []
            assert MODULE.rule_mirror(grid) == independent_oracle(grid)
    for first in range(4):
        for second in range(first + 1, 4):
            assert streams[first].isdisjoint(streams[second])


@pytest.mark.parametrize("profile", MODULE.GENERAL_PROFILES)
@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_general_profile_and_band_is_observable_valid_and_independently_exact(profile, band):
    for seed in range(1):
        grid = MODULE.generate(20_000 + seed, seed * 31 + 7, difficulty=band, scene_profile=profile)
        analysis = MODULE._analysis(grid)
        facts = independent_facts(grid)
        assert analysis["errors"] == []
        assert analysis["scene_profile"] == profile
        assert MODULE.observe_overrides(grid) == {"scene_profile": profile}
        assert analysis["facts"]["shortest_distance"] == facts["shortest"]
        assert analysis["facts"]["manhattan"] == facts["manhattan"]
        assert analysis["facts"]["equal"] == facts["equal"]
        assert analysis["facts"]["equal_components"] == facts["components"]
        assert analysis["output"] == MODULE.rule_mirror(grid) == independent_oracle(grid)


def test_default_lesson_schedule_is_identifying_complete_unique_and_oracle_exact():
    orientation_profiles = {"same_row_tie", "same_column_tie", "diagonal_tie"}
    topology_profiles = {
        "single_tie", "fragmented_ties", "long_connected_tie",
        "disconnected_pockets",
    }
    public_profiles = set(MODULE.PUBLIC_PROFILES)
    band_sets = []
    for band in (None, "easy", "medium", "hard"):
        inputs, outputs = set(), set()
        profiles = Counter()
        exact_count = 0
        for lesson_index in range(13):
            lesson_profiles = []
            for phase in range(MODULE.EXAMPLES_NEEDED):
                sample_index = lesson_index * MODULE.EXAMPLES_NEEDED + phase
                grid = MODULE.generate(810_000, sample_index, difficulty=band)
                analysis = MODULE._analysis(grid)
                assert analysis["errors"] == []
                assert analysis["output"] == independent_oracle(grid)
                inputs.add(frozen(grid))
                outputs.add(frozen(analysis["output"]))
                profiles[analysis["scene_profile"]] += 1
                lesson_profiles.append(analysis["scene_profile"])
                exact_count += MODULE.canonical_profile_signature(grid) is not None

            assert lesson_profiles[0] == "wall_detour"
            assert lesson_profiles[1] in orientation_profiles
            assert lesson_profiles[2] in topology_profiles
            assert lesson_profiles[3] in public_profiles
            detour = independent_facts(
                MODULE.generate(
                    810_000,
                    lesson_index * MODULE.EXAMPLES_NEEDED,
                    difficulty=band,
                )
            )
            assert detour["shortest"] > detour["manhattan"]

        assert len(inputs) == len(outputs) == 52
        assert set(profiles) == set(MODULE.SCENE_PROFILES)
        assert profiles["wall_detour"] == 13
        assert sum(profiles[p] for p in orientation_profiles) == 13
        assert min(profiles[p] for p in orientation_profiles) >= 4
        assert sum(profiles[p] for p in topology_profiles) == 13
        assert min(profiles[p] for p in topology_profiles) >= 3
        assert sum(profiles[p] for p in public_profiles) == 13
        assert min(profiles[p] for p in public_profiles) >= 2
        assert exact_count == 4
        assert exact_count / 52 >= 0.05
        band_sets.append(inputs)
    exact_public = {frozen(grid) for grid in MODULE._PUBLIC_INPUTS.values()}
    for first in range(4):
        for second in range(first + 1, 4):
            # Exact official anchors intentionally recur across bands; all
            # generalized nuisance witnesses remain band-disjoint.
            assert band_sets[first] & band_sets[second] <= exact_public


def test_general_profiles_have_the_declared_semantic_contrasts():
    facts = {
        profile: independent_facts(MODULE.generate(91, 9, scene_profile=profile))
        for profile in MODULE.GENERAL_PROFILES
    }
    assert len(facts["single_tie"]["equal"]) == 1
    assert len(facts["fragmented_ties"]["components"]) >= 2
    assert facts["long_connected_tie"]["components"] == (len(facts["long_connected_tie"]["equal"]),)
    assert len(facts["long_connected_tie"]["equal"]) >= 8
    assert facts["wall_detour"]["shortest"] > facts["wall_detour"]["manhattan"]
    assert facts["same_row_tie"]["seed_2"][0] == facts["same_row_tie"]["seed_3"][0]
    assert facts["same_column_tie"]["seed_2"][1] == facts["same_column_tie"]["seed_3"][1]
    assert facts["diagonal_tie"]["seed_2"][0] != facts["diagonal_tie"]["seed_3"][0]
    assert facts["diagonal_tie"]["seed_2"][1] != facts["diagonal_tie"]["seed_3"][1]
    assert facts["disconnected_pockets"]["unreachable_open"]


def test_endpoint_recombination_does_not_receive_a_public_family_label():
    grid = [row[:] for row in MODULE._PUBLIC_INPUTS["public_1"]]
    old_goal = next(
        (row, col) for row, values in enumerate(grid)
        for col, value in enumerate(values) if value == 3
    )
    grid[old_goal[0]][old_goal[1]] = 0
    grid[6][6] = 3
    assert MODULE.canonical_profile_signature(grid) is None
    assert MODULE.canonical_family_signature(grid) is None
    assert MODULE.self_check(grid)


def test_open_room_uses_graph_bisector_and_not_seed_row_only():
    grid = [[5] * 11 for _ in range(9)]
    for row in range(1, 8):
        for col in range(1, 10):
            grid[row][col] = 0
    grid[4][2], grid[4][8] = 2, 3
    output = MODULE.rule_mirror(grid)
    assert output == independent_oracle(grid)
    assert all(output[row][5] == 8 for row in range(1, 8))
    assert all(output[row][4] == 0 for row in range(1, 8))


def test_odd_seed_distance_has_no_graph_vertex_bisector_and_is_rejected_from_curriculum():
    grid = [[5] * 11 for _ in range(9)]
    for row in range(1, 8):
        for col in range(1, 10):
            grid[row][col] = 0
    grid[4][2], grid[4][7] = 2, 3
    assert independent_facts(grid)["shortest"] == 5
    assert independent_facts(grid)["equal"] == ()
    assert MODULE.rule_mirror(grid) == grid
    assert MODULE.self_check(grid)


def test_disconnected_blanks_are_never_marked():
    grid = MODULE.generate(77, 11, scene_profile="disconnected_pockets")
    facts = independent_facts(grid)
    output = MODULE.rule_mirror(grid)
    assert facts["unreachable_open"]
    assert all(output[row][col] == 0 for row, col in facts["unreachable_open"] if grid[row][col] == 0)


def test_wall_detour_uses_bfs_distance_not_manhattan_distance():
    grid = MODULE.generate(811, 7, scene_profile="wall_detour")
    facts = independent_facts(grid)
    assert facts["shortest"] > facts["manhattan"]
    assert MODULE.rule_mirror(grid) == independent_oracle(grid)


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
        [], [[]], [[False] * 11 for _ in range(9)], [[10] * 11 for _ in range(9)],
        [[5] * 11 for _ in range(8)] + [[5] * 10], [[5] * 8 for _ in range(9)],
        [[5] * 23 for _ in range(12)], [[5] * 11 for _ in range(23)],
        [[0] * 11 for _ in range(9)], [[5] * 11 for _ in range(9)],
    ],
)
def test_malformed_and_out_of_curriculum_inputs_fail_closed(grid):
    assert MODULE.self_check(grid)


def test_structural_mutations_fail_closed():
    grid = MODULE.generate(811, 7, difficulty="medium", scene_profile="diagonal_tie")
    blank = next(
        (row, col) for row, values in enumerate(grid)
        for col, value in enumerate(values) if value == 0
    )

    input_cyan = [row[:] for row in grid]
    input_cyan[blank[0]][blank[1]] = 8
    assert MODULE.self_check(input_cyan)

    broken_border = [row[:] for row in grid]
    broken_border[0][1] = 0
    assert MODULE.self_check(broken_border)

    missing_goal = [row[:] for row in grid]
    goal = next(
        (row, col) for row, values in enumerate(grid)
        for col, value in enumerate(values) if value == 3
    )
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
        {"scene_profile": "unknown"}, {"texture": "no_seeds"}, {"grid_h": 10},
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
    assert "both distances must be finite" in description["ambiguity_notes"]
    assert "shortest-path distance" in description["target_text"]
