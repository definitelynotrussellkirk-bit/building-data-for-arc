from __future__ import annotations

from collections import Counter
import hashlib
import importlib
import json
from pathlib import Path
import random

import pytest


TASK = "cf6d343a2d09"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "data" / "canonical" / "puzzles.jsonl"
BASE_PATH = ROOT / "data" / "base" / "solutions" / "banks" / "8edfaf6db623" / "M101__cf6d343a2d09.json"


def canonical_row():
    rows = [
        json.loads(line)
        for line in CANONICAL.read_text().splitlines()
        if json.loads(line).get("task_id") == TASK
    ]
    assert len(rows) == 1
    assert (rows[0]["source"], len(rows[0]["train"]), len(rows[0]["test"])) == (
        "bank:8edfaf6db623", 4, 1
    )
    return rows[0]


def canonical_pairs():
    row = canonical_row()
    return row["train"] + row["test"]


def frozen(grid):
    return tuple(map(tuple, grid))


def independent_components(grid, color=7):
    height, width = len(grid), len(grid[0])
    remaining = {
        (row, col)
        for row in range(height) for col in range(width)
        if grid[row][col] == color
    }
    output = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack, cells = [start], {start}
        while stack:
            row, col = stack.pop()
            for neighbor in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    cells.add(neighbor)
                    stack.append(neighbor)
        output.append(frozenset(cells))
    return tuple(output)


def independent_oracle(grid):
    output = [row[:] for row in grid]
    for component in independent_components(grid):
        if any(row == 0 for row, _ in component) and any(col == 0 for _, col in component):
            for row, col in component:
                output[row][col] = 8
    return output


def independent_signature(grid):
    target, top, left, interior = [], [], [], []
    for component in independent_components(grid):
        touches_top = any(row == 0 for row, _ in component)
        touches_left = any(col == 0 for _, col in component)
        if touches_top and touches_left:
            target.append(component)
        elif touches_top:
            top.append(component)
        elif touches_left:
            left.append(component)
        else:
            interior.append(component)
    if len(target) != 1:
        return None
    return (
        (0, 0) in target[0], len(target[0]), tuple(sorted(map(len, top))),
        tuple(sorted(map(len, left))), tuple(sorted(map(len, interior))),
    )


def test_metadata_hash_and_control_surface_are_exact():
    assert MODULE.VERSION == "2.0.0"
    assert MODULE.RULE_HASH == "ae8814a935b3"
    assert tuple(MODULE.AXES) == ("scene_profile",)
    assert MODULE.SCENE_PROFILES == MODULE.PUBLIC_PROFILES + MODULE.GENERAL_PROFILES
    assert MODULE.HELPFUL_TEXTURES == MODULE.DEGENERATE_TEXTURES == ()
    normalized = " ".join(canonical_row()["program_solution"].split())
    assert hashlib.sha256(normalized.encode()).hexdigest()[:12] == MODULE.RULE_HASH


@pytest.mark.parametrize("index", range(5))
def test_every_canonical_pair_is_exact_and_anchored(index):
    pair = canonical_pairs()[index]
    profile = f"public_{index + 1}"
    assert MODULE.canonical_profile_signature(pair["input"]) == profile
    assert MODULE.canonical_family_signature(pair["input"]) == profile
    assert independent_signature(pair["input"]) == MODULE.PROFILE_SIGNATURES[profile]
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


@pytest.mark.parametrize("profile", MODULE.SCENE_PROFILES)
@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_profile_and_band_is_observable_valid_and_oracle_exact(profile, band):
    height = MODULE._HEIGHTS[band][0]
    for index in range(12):
        grid = MODULE._construct_scene(
            profile, height, 8 + index % 6, random.Random(30_000 + index), 70_000 + index
        )
        analysis = MODULE._analysis(grid)
        assert analysis["errors"] == []
        assert analysis["scene_profile"] == profile
        assert analysis["facts"]["signature"] == independent_signature(grid)
        assert MODULE.observe_overrides(grid) == {"scene_profile": profile}
        assert analysis["output"] == MODULE.rule_mirror(grid) == independent_oracle(grid)


def test_default_census_is_balanced_unique_complete_and_band_separated():
    shapes_by_band = {}
    for band in (None, "easy", "medium", "hard"):
        inputs, outputs = set(), set()
        profiles = Counter()
        shapes = set()
        distractor_colors = set()
        for sample_index in range(1200):
            grid = MODULE.generate(810_000, sample_index, difficulty=band)
            analysis = MODULE._analysis(grid)
            assert analysis["errors"] == []
            assert analysis["output"] == independent_oracle(grid)
            inputs.add(frozen(grid))
            outputs.add(frozen(analysis["output"]))
            profiles[analysis["scene_profile"]] += 1
            shapes.add((len(grid), len(grid[0])))
            distractor_colors.add(analysis["facts"]["distractor"][2])
        assert len(inputs) == len(outputs) == 1200
        assert set(profiles) == set(MODULE.SCENE_PROFILES)
        assert max(profiles.values()) - min(profiles.values()) <= 1
        assert distractor_colors == set(MODULE.DISTRACTOR_COLORS)
        shapes_by_band[band] = shapes
    for first, first_shapes in shapes_by_band.items():
        for second, second_shapes in shapes_by_band.items():
            if first != second:
                assert first_shapes.isdisjoint(second_shapes)


def test_off_corner_bridge_touches_both_borders_without_upper_left_cell():
    grid = MODULE._construct_scene(
        "off_corner_bridge", 10, 11, random.Random(41), 100
    )
    facts = MODULE._analysis(grid)["facts"]
    assert len(facts["targets"]) == 1
    target = facts["targets"][0]
    assert (0, 0) not in target
    assert any(row == 0 for row, _ in target)
    assert any(col == 0 for _, col in target)
    assert MODULE.rule_mirror(grid) == independent_oracle(grid)


def test_size_tie_refutes_largest_or_unique_size_shortcut():
    grid = MODULE._construct_scene("size_tie", 11, 12, random.Random(42), 101)
    facts = MODULE._analysis(grid)["facts"]
    target_size = len(facts["targets"][0])
    assert target_size == 4
    assert any(len(component) == target_size for component in facts["top_only"])
    output = MODULE.rule_mirror(grid)
    assert sum(value == 8 for row in output for value in row) == target_size


def test_singleton_decoys_are_preserved_while_corner_target_changes():
    grid = MODULE._construct_scene("singleton_decoys", 9, 10, random.Random(43), 102)
    facts = MODULE._analysis(grid)["facts"]
    decoys = facts["top_only"] + facts["left_only"] + facts["interior"]
    assert [len(component) for component in decoys] == [1, 1, 1]
    output = MODULE.rule_mirror(grid)
    assert all(output[row][col] == 7 for component in decoys for row, col in component)


def test_broad_rule_recolors_every_qualifying_component():
    grid = [[0] * 8 for _ in range(8)]
    grid[0][0] = 7
    second = {(0, 4), (1, 4), (2, 4), (3, 4), (3, 3), (3, 2), (3, 1), (3, 0)}
    for row, col in second:
        grid[row][col] = 7
    output = MODULE.rule_mirror(grid)
    assert len(independent_components(grid)) == 2
    assert output[0][0] == 8
    assert all(output[row][col] == 8 for row, col in second)
    assert output == independent_oracle(grid)
    assert MODULE.self_check(grid)


def test_four_connectivity_keeps_diagonal_orange_cells_separate():
    grid = [[0] * 8 for _ in range(7)]
    grid[0][0] = 7
    grid[1][1] = 7
    grid[3][3] = 5
    output = MODULE.rule_mirror(grid)
    assert output[0][0] == 8
    assert output[1][1] == 7
    assert output[3][3] == 5
    assert len(independent_components(grid)) == 2


def test_nonqualifying_orange_and_every_nonorange_color_are_preserved():
    grid = [[0] * 10 for _ in range(9)]
    for cell in ((0, 0), (0, 1), (1, 0)):
        grid[cell[0]][cell[1]] = 7
    for cell in ((0, 7), (0, 8), (5, 0), (6, 0), (6, 1), (5, 7), (5, 8)):
        grid[cell[0]][cell[1]] = 7
    for index, color in enumerate((1, 2, 3, 4, 5, 6, 9)):
        grid[8][index + 2] = color
    output = MODULE.rule_mirror(grid)
    assert sum(value == 8 for row in output for value in row) == 3
    assert output[8][2:9] == [1, 2, 3, 4, 5, 6, 9]
    assert output == independent_oracle(grid)


def test_broad_no_target_is_identity_but_rejected_from_curriculum():
    grid = [[0] * 8 for _ in range(7)]
    grid[0][5] = grid[1][5] = grid[4][0] = grid[5][0] = 7
    assert MODULE.rule_mirror(grid) == grid
    assert MODULE.self_check(grid)


def test_rule_mirror_is_input_pure():
    grid = MODULE.generate(91, 9, difficulty="hard")
    before = frozen(grid)
    first = MODULE.rule_mirror(grid)
    second = MODULE.rule_mirror(grid)
    assert frozen(grid) == before
    assert first == second and first is not second and first[0] is not second[0]


@pytest.mark.parametrize(
    "grid",
    [
        [], [[]], [[0] * 8 for _ in range(7)], [[7] * 8 for _ in range(7)],
        [[False] * 8 for _ in range(7)], [[10] * 8 for _ in range(7)],
        [[0] * 8 for _ in range(6)] + [[0] * 7],
    ],
)
def test_malformed_and_degenerate_inputs_fail_closed(grid):
    assert MODULE.self_check(grid)


def test_structural_mutations_fail_closed():
    grid = MODULE.generate(811, 7, difficulty="medium")

    no_distractor = [row[:] for row in grid]
    for row, values in enumerate(no_distractor):
        for col, value in enumerate(values):
            if value not in (0, 7):
                no_distractor[row][col] = 0
    assert MODULE.self_check(no_distractor)

    extra_distractor = [row[:] for row in grid]
    spot = next((row, col) for row, values in enumerate(extra_distractor) for col, value in enumerate(values) if value == 0)
    extra_distractor[spot[0]][spot[1]] = 4
    assert MODULE.self_check(extra_distractor)

    bad_color = [row[:] for row in grid]
    spot = next((row, col) for row, values in enumerate(bad_color) for col, value in enumerate(values) if value not in (0, 7))
    bad_color[spot[0]][spot[1]] = 8
    assert MODULE.self_check(bad_color)

    remove_target = [row[:] for row in grid]
    for row, col in MODULE._analysis(grid)["facts"]["targets"][0]:
        remove_target[row][col] = 0
    assert MODULE.self_check(remove_target)


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
        {"scene_profile": "unknown"}, {"texture": "no_corner_object"},
        {"grid_h": 9}, {"n_other": 3}, {"palette_kind": "warm"},
        {"difficulty": "expert"},
    ],
)
def test_unknown_and_retired_controls_fail_closed(kwargs):
    with pytest.raises(ValueError):
        MODULE.generate(1, 2, **kwargs)


def test_base_authorities_and_reviewed_metadata_match_canonical_program():
    base = json.loads(BASE_PATH.read_text())
    source = canonical_row()["program_solution"]
    assert base["racket_target"]["raw_code"] == source
    assert base["racket_target"]["target_code"] == source
    description = base["description_target"]
    assert description["target_status"] == "reviewed_semantic_description"
    assert description["generator_parameters"] == ["scene_profile"]
    assert "top" in description["target_text"] and "left" in description["target_text"]
    assert "non-orange" in description["target_text"]
