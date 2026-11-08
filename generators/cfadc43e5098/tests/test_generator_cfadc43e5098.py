from __future__ import annotations

from collections import Counter
import hashlib
import importlib
import json
from pathlib import Path
import random

import pytest


TASK = "cfadc43e5098"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "data" / "canonical" / "puzzles.jsonl"
BASE_PATHS = (
    ROOT / "data" / "base" / "solutions" / "training" / "f3b10344__cfadc43e5098.json",
    ROOT / "data" / "base" / "solutions" / "augmented" / "f3b10344__2849735f278d.json",
)


def canonical_rows():
    rows = [
        json.loads(line)
        for line in CANONICAL.read_text().splitlines()
        if json.loads(line).get("task_id") == TASK
    ]
    assert [(row["source"], len(row["train"]), len(row["test"])) for row in rows] == [
        ("training", 3, 1), ("augmented", 4, 0)
    ]
    return rows


def frozen(grid):
    return tuple(map(tuple, grid))


def independent_components(grid):
    height, width = len(grid), len(grid[0])
    remaining = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != 0
    }
    components = []
    while remaining:
        start = min(remaining)
        color = grid[start[0]][start[1]]
        remaining.remove(start)
        stack, cells = [start], {start}
        while stack:
            row, col = stack.pop()
            for neighbor in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if neighbor in remaining and grid[neighbor[0]][neighbor[1]] == color:
                    remaining.remove(neighbor)
                    cells.add(neighbor)
                    stack.append(neighbor)
        rows = [row for row, _ in cells]
        cols = [col for _, col in cells]
        components.append((color, (min(rows), min(cols), max(rows), max(cols))))
    return tuple(components)


def rectangles_intersect(first, second):
    return (
        max(first[0], second[0]) <= min(first[2], second[2])
        and max(first[1], second[1]) <= min(first[3], second[3])
    )


def independent_bridge(first, second):
    ar1, ac1, ar2, ac2 = first
    br1, bc1, br2, bc2 = second
    row_start, row_end = max(ar1, br1), min(ar2, br2)
    col_start, col_end = max(ac1, bc1), min(ac2, bc2)
    if row_start <= row_end and col_start > col_end and ar1 + ar2 == br1 + br2:
        left, right = sorted((first, second), key=lambda box: box[1])
        bridge = (row_start + 1, left[3] + 1, row_end - 1, right[1] - 1)
    elif col_start <= col_end and row_start > row_end and ac1 + ac2 == bc1 + bc2:
        top, bottom = sorted((first, second), key=lambda box: box[0])
        bridge = (top[2] + 1, col_start + 1, bottom[0] - 1, col_end - 1)
    else:
        return None
    return bridge if bridge[0] <= bridge[2] and bridge[1] <= bridge[3] else None


def independent_oracle(grid):
    components = independent_components(grid)
    bridges = []
    for first_index, (color, first_box) in enumerate(components):
        for second_index in range(first_index + 1, len(components)):
            second_color, second_box = components[second_index]
            if color != second_color:
                continue
            bridge = independent_bridge(first_box, second_box)
            if bridge is None:
                continue
            blocked = any(
                index not in (first_index, second_index)
                and blocker_color == color
                and rectangles_intersect(blocker_box, bridge)
                for index, (blocker_color, blocker_box) in enumerate(components)
            )
            if not blocked:
                bridges.append(bridge)
    output = [row[:] for row in grid]
    for row1, col1, row2, col2 in bridges:
        for row in range(row1, row2 + 1):
            for col in range(col1, col2 + 1):
                output[row][col] = 8
    return output


def test_metadata_hash_and_control_surface_are_exact():
    rows = canonical_rows()
    assert MODULE.VERSION == "3.0.0"
    assert MODULE.RULE_HASH == "b67b77ea3d2d"
    assert tuple(MODULE.AXES) == ("scene_profile",)
    assert MODULE.SCENE_PROFILES == MODULE.PUBLIC_PROFILES + MODULE.GENERAL_PROFILES
    assert MODULE.HELPFUL_TEXTURES == MODULE.DEGENERATE_TEXTURES == ()
    for row in rows:
        normalized = " ".join(row["program_solution"].split())
        assert hashlib.sha256(normalized.encode()).hexdigest()[:12] == MODULE.RULE_HASH


@pytest.mark.parametrize("index", range(4))
def test_every_training_pair_is_exact_and_anchored(index):
    row = canonical_rows()[0]
    pair = (row["train"] + row["test"])[index]
    profile = f"public_{index + 1}"
    assert MODULE.canonical_profile_signature(pair["input"]) == profile
    assert MODULE.canonical_family_signature(pair["input"]) == profile
    assert MODULE.self_check(pair["input"]) == []
    assert MODULE.rule_mirror(pair["input"]) == independent_oracle(pair["input"])
    assert MODULE.rule_mirror(pair["input"]) == pair["output"]


def test_augmented_row_is_the_same_four_authoritative_lessons_in_declared_order():
    row = canonical_rows()[1]
    expected_profiles = ("public_1", "public_2", "public_4", "public_3")
    for pair, profile in zip(row["train"], expected_profiles):
        assert MODULE.canonical_profile_signature(pair["input"]) == profile
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


@pytest.mark.parametrize("profile", MODULE.GENERAL_PROFILES)
@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_general_profile_and_band_is_valid_observable_and_independently_exact(profile, band):
    for seed in range(8):
        grid = MODULE.generate(20_000 + seed, seed * 31 + 7, difficulty=band, scene_profile=profile)
        analysis = MODULE._analysis(grid)
        assert analysis["errors"] == []
        assert analysis["scene_profile"] == profile
        assert all(9 <= len(component["cells"]) <= 49 for component in analysis["facts"]["components"])
        assert MODULE.observe_overrides(grid) == {"scene_profile": profile}
        assert analysis["output"] == MODULE.rule_mirror(grid) == independent_oracle(grid)


def test_default_census_is_balanced_complete_unique_and_oracle_exact():
    for band in (None, "easy", "medium", "hard"):
        inputs, outputs = set(), set()
        profiles = Counter()
        for sample_index in range(1200):
            grid = MODULE.generate(810_000, sample_index, difficulty=band)
            analysis = MODULE._analysis(grid)
            assert analysis["errors"] == []
            assert analysis["output"] == independent_oracle(grid)
            inputs.add(frozen(grid))
            outputs.add(frozen(analysis["output"]))
            profiles[analysis["scene_profile"]] += 1
        assert len(inputs) == len(outputs) == 1200
        assert set(profiles) == set(MODULE.SCENE_PROFILES)
        assert set(profiles.values()) == {100}


def test_profile_contrasts_cover_both_axes_blocking_mismatch_and_unequal_boxes():
    facts_by_profile = {
        profile: MODULE._analysis(MODULE.generate(91, 9, scene_profile=profile))["facts"]
        for profile in MODULE.GENERAL_PROFILES
    }
    horizontal = facts_by_profile["horizontal_pair"]
    vertical = facts_by_profile["vertical_pair"]
    blocker = facts_by_profile["blocker_cross"]
    mismatch = facts_by_profile["midpoint_decoy"]
    unequal = facts_by_profile["unequal_overlap"]
    assert {item["orientation"] for item in horizontal["unblocked"]} == {"horizontal"}
    assert {item["orientation"] for item in vertical["unblocked"]} == {"vertical"}
    assert blocker["blocked_count"] >= 1
    assert any(item["large"] for item in mismatch["mismatches"])
    assert any(item["unequal_boxes"] for item in unequal["unblocked"])


def test_cross_profile_recombination_is_not_mistaken_for_an_official_family():
    # Put public_2's first-endpoint dimensions into public_1's otherwise linked
    # geometry.  The individual size and surrounding arrangement are public,
    # but their cross-profile combination is not an official returned-grid profile.
    grid = [row[:] for row in MODULE._PUBLIC_INPUTS["public_1"]]
    for row in range(1, 8):
        for col in range(4, 10):
            grid[row][col] = 0
    for row in range(4, 11):
        for col in range(3, 10):
            grid[row][col] = 2
    assert MODULE.canonical_profile_signature(grid) is None
    assert MODULE.canonical_family_signature(grid) is None
    assert MODULE.self_check(grid)


def test_broad_rule_uses_component_bounding_boxes_not_filled_shapes():
    grid = [[0] * 20 for _ in range(14)]
    for row, col in ((2, 2), (2, 3), (3, 2), (4, 2), (4, 3)):
        grid[row][col] = 5
    for row, col in ((2, 14), (2, 15), (2, 16), (3, 16), (4, 14), (4, 15), (4, 16)):
        grid[row][col] = 5
    output = MODULE.rule_mirror(grid)
    assert output == independent_oracle(grid)
    assert all(output[row][col] == 8 for row in range(3, 4) for col in range(4, 14))
    assert MODULE.self_check(grid)


def test_third_same_color_box_blocks_but_different_color_box_does_not():
    grid = [[0] * 22 for _ in range(14)]
    for color, row1, col1, row2, col2 in (
        (4, 2, 2, 8, 6), (4, 2, 16, 8, 20), (4, 3, 10, 6, 12)
    ):
        for row in range(row1, row2 + 1):
            for col in range(col1, col2 + 1):
                grid[row][col] = color
    assert MODULE.rule_mirror(grid) == grid
    different = [row[:] for row in grid]
    for row in range(3, 7):
        for col in range(10, 13):
            different[row][col] = 6
    output = MODULE.rule_mirror(different)
    assert output == independent_oracle(different)
    assert any(value == 8 for row in output for value in row)


def test_diagonal_same_color_cells_are_distinct_four_connected_components():
    grid = [[0] * 18 for _ in range(12)]
    for row in range(2, 7):
        for col in range(2, 6):
            grid[row][col] = 3
        for col in range(12, 16):
            grid[row][col] = 3
    grid[8][8] = 3
    grid[9][9] = 3
    assert len(independent_components(grid)) == 4
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
        [], [[]], [[False] * 25 for _ in range(25)], [[10] * 25 for _ in range(25)],
        [[0] * 25 for _ in range(24)] + [[0] * 24], [[0] * 24 for _ in range(25)],
        [[0] * 25 for _ in range(31)], [[0] * 31 for _ in range(25)],
    ],
)
def test_malformed_and_out_of_curriculum_inputs_fail_closed(grid):
    assert MODULE.self_check(grid)


def test_structural_mutations_fail_closed():
    grid = MODULE.generate(811, 7, difficulty="medium", scene_profile="horizontal_pair")

    input_cyan = [row[:] for row in grid]
    input_cyan[0][0] = 8
    assert MODULE.self_check(input_cyan)

    hollow = [row[:] for row in grid]
    first = MODULE._analysis(grid)["facts"]["components"][0]
    row1, col1, row2, col2 = first["bbox"]
    hollow[(row1 + row2) // 2][(col1 + col2) // 2] = 0
    assert MODULE.self_check(hollow)

    no_bridge = [[0] * 30 for _ in range(30)]
    no_bridge[2][2] = no_bridge[20][20] = 4
    assert MODULE.self_check(no_bridge)


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
        {"scene_profile": "unknown"}, {"texture": "noise"}, {"grid_size": 30},
        {"object_count": 8}, {"bridge_axis": "horizontal"}, {"difficulty": "expert"},
    ],
)
def test_unknown_and_retired_controls_fail_closed(kwargs):
    with pytest.raises(ValueError):
        MODULE.generate(1, 2, **kwargs)


def test_both_base_authorities_and_reviewed_metadata_match_canonical_program():
    source = canonical_rows()[0]["program_solution"]
    for path in BASE_PATHS:
        base = json.loads(path.read_text())
        assert base["racket_target"]["raw_code"] == source
        assert base["racket_target"]["target_code"] == source
        description = base["description_target"]
        assert description["target_status"] == "reviewed_semantic_description"
        assert description["generator_parameters"] == ["scene_profile"]
        assert "third same-color" in description["target_text"]
        assert base["primitive_metadata"]["primitive_chain"][:2] == ["rows", "cols"]
