from __future__ import annotations

import json
from pathlib import Path
import random
import sys

import pytest

try:
    from reviewer_support import canonical_path, find_root, load_selected_generator
except ModuleNotFoundError as error:
    if error.name != "reviewer_support":
        raise
    # Source checkouts need a local-runtime path; prepared runtimes already
    # expose reviewer_support and keep their existing loader behavior.
    for ancestor in Path(__file__).resolve().parents:
        runtime = ancestor / "shared" / "runtime"
        if (runtime / "reviewer_support.py").is_file():
            sys.path.insert(0, str(runtime))
            break
    from reviewer_support import canonical_path, find_root, load_selected_generator


TASK_ID = "b98cdd1751a7"
ROOT = find_root(__file__)
MODULE, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def canonical_row():
    rows = []
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            rows.append(row)
    assert len(rows) == 1
    return rows[0]


def selected_data_path(relative):
    for prefix in ("data", "shared/data"):
        candidate = ROOT / prefix / relative
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"No selected data file {relative!r} under {ROOT}")


def frozen(grid):
    return tuple(map(tuple, grid))


def independent_components(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    components = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                here_row, here_col = stack.pop()
                cells.append((here_row, here_col))
                for row_delta in (-1, 0, 1):
                    for col_delta in (-1, 0, 1):
                        next_row = here_row + row_delta
                        next_col = here_col + col_delta
                        if (
                            (row_delta or col_delta)
                            and 0 <= next_row < height
                            and 0 <= next_col < width
                            and (next_row, next_col) not in seen
                            and grid[next_row][next_col] == color
                        ):
                            seen.add((next_row, next_col))
                            stack.append((next_row, next_col))
            components.append({
                "color": color,
                "cells": tuple(sorted(cells)),
                "row0": min(r for r, _ in cells),
                "col0": min(c for _, c in cells),
            })
    return components


def independent_oracle(grid):
    components = sorted(
        independent_components(grid),
        key=lambda component: (component["row0"], component["col0"]),
    )
    if not components:
        raise ValueError("no objects")
    midpoint = (components[0]["row0"] + components[-1]["row0"]) / 2.0
    upper = sorted(
        (component for component in components if component["row0"] < midpoint),
        key=lambda component: component["col0"],
    )
    lower = sorted(
        (component for component in components if component["row0"] >= midpoint),
        key=lambda component: component["col0"],
    )
    output = [[0] * 7 for _ in range(7)]
    for component, (target_row, target_col) in zip(
        (upper + lower)[:4], ((0, 0), (0, 4), (4, 0), (4, 4))
    ):
        for row, col in component["cells"]:
            new_row = target_row + row - component["row0"]
            new_col = target_col + col - component["col0"]
            if 0 <= new_row < 7 and 0 <= new_col < 7:
                output[new_row][new_col] = grid[row][col]
    return output


def paint(grid, row0, col0, rows, color):
    for row, values in enumerate(rows):
        for col, value in enumerate(values):
            if value:
                grid[row0 + row][col0 + col] = color


def test_metadata_and_control_surface_are_exact():
    assert MODULE.VERSION == "3.0.0"
    assert MODULE.RULE_HASH == "62a9653b2441"
    assert SOURCE.is_file()
    assert SOURCE.resolve().is_relative_to(ROOT.resolve())
    assert SOURCE.name == "generator.py"
    assert len(SOURCE_SHA256) == 64
    assert tuple(MODULE.AXES) == ("scene_profile",)
    assert tuple(MODULE.SCENE_PROFILES) == MODULE.PUBLIC_PROFILES + MODULE.GENERAL_PROFILES
    assert MODULE.HELPFUL_TEXTURES == MODULE.DEGENERATE_TEXTURES == ()


@pytest.mark.parametrize("index", range(4))
def test_every_canonical_pair_is_exact_and_anchored(index):
    pair = (canonical_row()["train"] + canonical_row()["test"])[index]
    profile = f"public_{index + 1}"
    assert MODULE.canonical_profile_signature(pair["input"]) == profile
    assert MODULE.canonical_family_signature(pair["input"]) == profile
    assert MODULE.self_check(pair["input"]) == []
    assert MODULE.rule_mirror(pair["input"]) == pair["output"]
    assert independent_oracle(pair["input"]) == pair["output"]


@pytest.mark.parametrize("profile", MODULE.PUBLIC_PROFILES)
@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_forced_public_profiles_are_exact_immutable_anchors(profile, band):
    first = MODULE.generate(19, 7, difficulty=band, scene_profile=profile)
    second = MODULE.generate(999, 333, difficulty=band, scene_profile=profile)
    expected = MODULE._PUBLIC_INPUTS[profile]
    assert first == second == expected
    assert first is not expected and first[0] is not expected[0]
    assert MODULE.canonical_profile_signature(first) == profile


@pytest.mark.parametrize("profile", MODULE.SCENE_PROFILES)
@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_profile_and_band_is_observable_valid_and_oracle_exact(profile, band):
    for seed in range(8):
        grid = MODULE.generate(10_000 + seed, seed * 31, difficulty=band, scene_profile=profile)
        analysis = MODULE._analysis(grid)
        assert analysis["errors"] == []
        assert analysis["scene_profile"] == profile
        assert MODULE.observe_overrides(grid) == {"scene_profile": profile}
        assert analysis["output"] == MODULE.rule_mirror(grid) == independent_oracle(grid)
        assert len(analysis["facts"]["objects"]) == 4
        assert analysis["facts"]["upper_count"] == analysis["facts"]["lower_count"] == 2


@pytest.mark.parametrize("profile", MODULE.PUBLIC_PROFILES)
def test_randomized_public_families_preserve_shape_orbits_but_vary_lessons(profile):
    grids = [MODULE._random_scene(profile, None, random.Random(20_000 + seed)) for seed in range(40)]
    assert len({frozen(grid) for grid in grids}) == 40
    assert len({frozen(MODULE.rule_mirror(grid)) for grid in grids}) >= 38
    assert all(MODULE.canonical_family_signature(grid) == profile for grid in grids)
    assert {MODULE._analysis(grid)["facts"]["colors"][0] for grid in grids} == set(range(1, 10))


def test_general_profiles_encode_distinct_contrasts():
    novel = MODULE.generate(31, 1, scene_profile="novel_uniform")
    recolored = MODULE.generate(32, 2, scene_profile="recolored_uniform")
    distinct = MODULE.generate(33, 3, scene_profile="distinct_palette")
    varied = MODULE.generate(34, 4, scene_profile="varied_extent")
    novel_facts = MODULE._analysis(novel)["facts"]
    recolored_facts = MODULE._analysis(recolored)["facts"]
    distinct_facts = MODULE._analysis(distinct)["facts"]
    varied_facts = MODULE._analysis(varied)["facts"]
    assert set(novel_facts["colors"]) == {2}
    assert len(set(recolored_facts["colors"])) == 1 and recolored_facts["colors"][0] != 2
    assert len(set(distinct_facts["colors"])) == 4
    assert any(dimensions != (3, 3) for dimensions in varied_facts["bbox_dimensions"])
    assert all(dimensions == (3, 3) for dimensions in novel_facts["bbox_dimensions"])


def test_default_census_covers_all_profiles_palettes_extents_and_high_diversity():
    for band in ("easy", "medium", "hard"):
        inputs, outputs, profiles, colors, extents = set(), set(), set(), set(), set()
        for index in range(1200):
            grid = MODULE.generate(800_000 + index, index * 17, difficulty=band)
            analysis = MODULE._analysis(grid)
            assert analysis["errors"] == []
            assert analysis["output"] == independent_oracle(grid)
            inputs.add(frozen(grid))
            outputs.add(frozen(analysis["output"]))
            profiles.add(analysis["scene_profile"])
            colors.update(analysis["facts"]["colors"])
            extents.update(analysis["facts"]["bbox_dimensions"])
        assert len(inputs) == 1200
        assert len(outputs) >= 1180
        assert profiles == set(MODULE.SCENE_PROFILES)
        assert colors == set(range(1, 10))
        assert {(3, 3), (2, 3), (3, 2), (2, 2), (1, 3), (3, 1)} <= extents


def test_difficulty_scales_randomized_canvas_area():
    medians = []
    for band in ("easy", "medium", "hard"):
        areas = []
        for index in range(300):
            grid = MODULE.generate(900_000 + index, index, difficulty=band, scene_profile="novel_uniform")
            areas.append(len(grid) * len(grid[0]))
        medians.append(sorted(areas)[len(areas) // 2])
    assert medians[0] < medians[1] < medians[2]


def test_broad_rule_uses_minimum_rows_not_centroids_and_allows_unbalanced_groups():
    grid = [[0] * 18 for _ in range(18)]
    paint(grid, 1, 1, ((1, 1), (1, 0)), 3)
    paint(grid, 4, 8, ((1, 0), (1, 1)), 4)
    paint(grid, 6, 2, ((1, 1), (0, 1)), 5)
    paint(grid, 13, 12, ((1, 1), (1, 0)), 6)
    components = sorted(independent_components(grid), key=lambda component: component["row0"])
    midpoint = (components[0]["row0"] + components[-1]["row0"]) / 2
    assert sum(component["row0"] < midpoint for component in components) == 3
    assert MODULE.rule_mirror(grid) == independent_oracle(grid)


def test_broad_rule_keeps_touching_different_colors_as_distinct_objects():
    grid = [[0] * 12 for _ in range(12)]
    grid[1][1] = grid[1][2] = 3
    grid[2][2] = grid[2][3] = 4
    grid[8][1] = grid[8][2] = 5
    grid[8][8] = grid[9][8] = 6
    assert len(independent_components(grid)) == 4
    assert MODULE.rule_mirror(grid) == independent_oracle(grid)
    assert MODULE.self_check(grid)


def test_broad_rule_ignores_objects_after_first_four_and_clips_large_crops():
    grid = [[0] * 20 for _ in range(20)]
    for index, (row, col) in enumerate(((1, 1), (2, 10), (10, 1), (11, 10), (16, 5))):
        color = index + 1
        for offset in range(5 if index == 0 else 2):
            grid[row][col + offset] = color
    assert len(independent_components(grid)) == 5
    assert MODULE.rule_mirror(grid) == independent_oracle(grid)


def test_rule_mirror_is_input_pure():
    grid = MODULE.generate(71, 19, difficulty="hard")
    before = frozen(grid)
    MODULE.rule_mirror(grid)
    assert frozen(grid) == before


def test_rule_mirror_rejects_no_object_input():
    with pytest.raises(ValueError):
        MODULE.rule_mirror([[0] * 10 for _ in range(10)])


@pytest.mark.parametrize(
    "grid",
    [
        [],
        [[]],
        [[0] * 9 for _ in range(9)],
        [[False] * 12 for _ in range(12)],
        [[10] * 12 for _ in range(12)],
        [[0] * 12 for _ in range(11)] + [[0] * 11],
        [[0] * 12 for _ in range(12)],
        [[2] * 12 for _ in range(12)],
    ],
)
def test_malformed_and_minimal_impostors_fail_closed(grid):
    assert MODULE.self_check(grid)


def test_structural_mutations_fail_closed():
    grid = MODULE.generate(811, 7, scene_profile="distinct_palette")
    analysis = MODULE._analysis(grid)
    first = analysis["facts"]["objects"][0]
    missing = [row[:] for row in grid]
    for row, col in first["cells"]:
        missing[row][col] = 0
    assert MODULE.self_check(missing)

    merged_palette = [row[:] for row in grid]
    first_color = analysis["facts"]["objects"][0]["color"]
    second = analysis["facts"]["objects"][1]
    for row, col in second["cells"]:
        merged_palette[row][col] = first_color
    assert MODULE.self_check(merged_palette)

    oversized = [[0] * 16 for _ in range(16)]
    paint(oversized, 1, 1, ((1, 1, 1, 1),), 2)
    paint(oversized, 1, 10, ((1, 1),), 2)
    paint(oversized, 10, 1, ((1, 1),), 2)
    paint(oversized, 10, 10, ((1, 1),), 2)
    assert any("3x3" in error for error in MODULE.self_check(oversized))

    same_column = [[0] * 18 for _ in range(18)]
    for row, col in ((1, 1), (4, 1), (12, 1), (12, 10)):
        paint(same_column, row, col, ((1, 1),), 2)
    assert MODULE.self_check(same_column)


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
        {"texture": "warm"},
        {"grid_h": 17},
        {"palette_kind": "broad"},
        {"anchor_corner": True},
        {"shape_variant": "rng"},
    ],
)
def test_unknown_controls_fail_closed(kwargs):
    with pytest.raises(ValueError):
        MODULE.generate(1, 2, **kwargs)


def test_unknown_difficulty_fails_closed():
    with pytest.raises(ValueError):
        MODULE.generate(1, 2, difficulty="extreme")


def test_base_source_is_synchronized_to_canonical_program():
    row = canonical_row()
    base = json.loads(
        selected_data_path("base/solutions/training/1990f7a8__b98cdd1751a7.json").read_text()
    )
    assert base["racket_target"]["raw_code"] == row["program_solution"]
    assert base["racket_target"]["target_code"] == row["program_solution"]
    assert base["description_target"]["target_status"] == "reviewed_semantic_description"
    assert "minimum row" in base["description_target"]["ambiguity_notes"]
