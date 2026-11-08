from __future__ import annotations

from collections import Counter
import hashlib
import importlib
import json
from pathlib import Path
import random

import pytest

from reviewer_support import canonical_path, find_root


TASK = "c235e3da14f4"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = find_root(__file__)
CANONICAL = canonical_path(ROOT)
_BASE_CANDIDATES = (
    ROOT / "data/base/solutions/training/23b5c85d__c235e3da14f4.json",
    ROOT / "shared/data/base/solutions/training/23b5c85d__c235e3da14f4.json",
)
BASE = next((path for path in _BASE_CANDIDATES if path.is_file()), _BASE_CANDIDATES[0])
DELTAS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def canonical_row():
    rows = [
        json.loads(line)
        for line in CANONICAL.read_text().splitlines()
        if json.loads(line).get("task_id") == TASK
    ]
    assert len(rows) == 1
    return rows[0]


def frozen(grid):
    return tuple(map(tuple, grid))


def independent_objects(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    found = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 2 or (row, col) in seen:
                continue
            color = grid[row][col]
            queue = [(row, col)]
            seen.add((row, col))
            cells = []
            while queue:
                here = queue.pop(0)
                cells.append(here)
                for dr, dc in DELTAS:
                    neighbor = (here[0] + dr, here[1] + dc)
                    if (
                        0 <= neighbor[0] < height
                        and 0 <= neighbor[1] < width
                        and neighbor not in seen
                        and grid[neighbor[0]][neighbor[1]] == color
                    ):
                        seen.add(neighbor)
                        queue.append(neighbor)
            found.append({
                "color": color,
                "cells": tuple(cells),
                "size": len(cells),
                "bbox": (
                    min(r for r, _ in cells), min(c for _, c in cells),
                    max(r for r, _ in cells), max(c for _, c in cells),
                ),
            })
    return found


def independent_oracle(grid):
    objects = independent_objects(grid)
    if not objects:
        raise ValueError("no non-2 object")
    selected = min(objects, key=lambda item: item["size"])
    row0, col0, row1, col1 = selected["bbox"]
    return [row[col0:col1 + 1] for row in grid[row0:row1 + 1]]


def test_metadata_rule_hash_and_control_surface_are_exact():
    assert MODULE.VERSION == "3.0.0"
    assert MODULE.RULE_HASH == "f44de8fa965f"
    assert tuple(MODULE.AXES) == ("scene_profile",)
    assert MODULE.SCENE_PROFILES == MODULE.PUBLIC_PROFILES + MODULE.GENERAL_PROFILES
    assert MODULE.HELPFUL_TEXTURES == MODULE.DEGENERATE_TEXTURES == ()
    normalized = " ".join(canonical_row()["program_solution"].split())
    assert hashlib.sha256(normalized.encode()).hexdigest()[:12] == MODULE.RULE_HASH


@pytest.mark.parametrize("index", range(6))
def test_every_canonical_pair_is_exact_and_anchored(index):
    pair = (canonical_row()["train"] + canonical_row()["test"])[index]
    profile = f"public_{index + 1}"
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


@pytest.mark.parametrize("profile", MODULE.PUBLIC_PROFILES)
@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_randomized_public_embeddings_preserve_complete_recolored_d4_families(profile, band):
    grids = [MODULE._embed_public(profile, band, random.Random(20_000 + seed)) for seed in range(60)]
    assert len({frozen(grid) for grid in grids}) >= 48
    assert all(MODULE.canonical_family_signature(grid) == profile for grid in grids)
    assert all(MODULE.self_check(grid) == [] for grid in grids)
    assert all(MODULE.rule_mirror(grid) == independent_oracle(grid) for grid in grids)


@pytest.mark.parametrize("profile", MODULE.SCENE_PROFILES)
@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_profile_and_band_is_observable_valid_and_oracle_exact(profile, band):
    for seed in range(8):
        grid = MODULE.generate(10_000 + seed, seed * 31, difficulty=band, scene_profile=profile)
        analysis = MODULE._analysis(grid)
        assert analysis["errors"] == []
        assert analysis["scene_profile"] == profile
        assert MODULE.observe_overrides(grid) == {"scene_profile": profile}
        assert analysis["output"] == MODULE.rule_mirror(grid) == independent_oracle(grid)
        facts = analysis["facts"]
        assert 2 <= facts["object_count"] <= 6
        assert len(set(facts["object_sizes"])) == facts["object_count"]
        assert facts["selected"]["color"] not in (0, 2)
        assert facts["zero_object_size"] > facts["selected"]["size"]


def test_general_profiles_encode_distinct_object_and_crop_contrasts():
    for profile in MODULE.GENERAL_PROFILES:
        for seed in range(100):
            grid = MODULE.generate(30_000 + seed, seed, difficulty="hard", scene_profile=profile)
            facts = MODULE._analysis(grid)["facts"]
            selected_size = facts["selected"]["size"]
            if profile == "rectangular_contrast":
                assert facts["selected_solid_rectangle"]
                assert not facts["selected_crop_contains_2"]
                assert not any(size < selected_size for size in facts["excluded_color2_component_sizes"])
            elif profile == "excluded_smaller":
                assert any(size < selected_size for size in facts["excluded_color2_component_sizes"])
                assert not facts["selected_crop_contains_2"]
            elif profile == "shape_crop":
                assert not facts["selected_solid_rectangle"]
                assert not facts["selected_crop_contains_2"]
                assert not facts["diagonal_same_color"]
            elif profile == "diagonal_components":
                assert facts["diagonal_same_color"]
            else:
                assert facts["selected_crop_contains_2"]


def test_default_census_is_complete_band_aware_and_output_varied():
    output_minimum = {"easy": 580, "medium": 630, "hard": 640}
    medians = {}
    for band in ("easy", "medium", "hard"):
        inputs, outputs, output_shapes, output_colors = set(), set(), set(), set()
        object_counts, selected_sizes = set(), set()
        profiles = Counter()
        areas = []
        for index in range(1200):
            grid = MODULE.generate(800_000, index, difficulty=band)
            analysis = MODULE._analysis(grid)
            assert analysis["errors"] == []
            assert analysis["output"] == independent_oracle(grid)
            output = analysis["output"]
            facts = analysis["facts"]
            inputs.add(frozen(grid))
            outputs.add(frozen(output))
            output_shapes.add((len(output), len(output[0])))
            output_colors.update(value for row in output for value in row)
            object_counts.add(facts["object_count"])
            selected_sizes.add(facts["selected"]["size"])
            profiles[analysis["scene_profile"]] += 1
            areas.append(len(grid) * len(grid[0]))
        assert len(inputs) >= 1190
        assert len(outputs) >= output_minimum[band]
        assert set(profiles) == set(MODULE.SCENE_PROFILES)
        assert min(profiles.values()) >= 55
        assert len(output_shapes) >= {"easy": 15, "medium": 24, "hard": 34}[band]
        assert output_colors == set(range(10))
        assert {2, 3, 4, 5} <= object_counts
        assert min(selected_sizes) == 4 and max(selected_sizes) >= 12
        medians[band] = sorted(areas)[len(areas) // 2]
    assert medians["easy"] < medians["medium"] < medians["hard"]


def test_broad_rule_treats_zero_as_a_candidate_object():
    grid = [[2] * 9 for _ in range(9)]
    grid[1][1] = 0
    for row in range(4, 7):
        for col in range(4, 7):
            grid[row][col] = 6
    assert independent_objects(grid)[0]["color"] == 0
    assert MODULE.rule_mirror(grid) == [[0]] == independent_oracle(grid)
    assert MODULE.self_check(grid)


def test_broad_rule_excludes_color_two_even_when_it_is_visibly_smallest():
    grid = [[0] * 10 for _ in range(10)]
    grid[1][1] = 2
    for row in range(4, 6):
        for col in range(5, 8):
            grid[row][col] = 7
    assert MODULE.rule_mirror(grid) == [[7, 7, 7], [7, 7, 7]]
    assert MODULE.rule_mirror(grid) == independent_oracle(grid)


def test_broad_rule_uses_four_connectivity_for_diagonal_same_color_components():
    grid = [[0] * 11 for _ in range(11)]
    for row in range(2, 4):
        for col in range(2, 4):
            grid[row][col] = 5
    for row in range(4, 7):
        for col in range(4, 7):
            grid[row][col] = 5
    same = [item for item in independent_objects(grid) if item["color"] == 5]
    assert [item["size"] for item in same] == [4, 9]
    assert MODULE.rule_mirror(grid) == [[5, 5], [5, 5]] == independent_oracle(grid)


def test_broad_rule_keeps_touching_different_colors_as_distinct_objects():
    grid = [[0] * 10 for _ in range(10)]
    grid[2][2] = grid[2][3] = grid[3][2] = grid[3][3] = 4
    for row in range(2, 5):
        for col in range(4, 7):
            grid[row][col] = 6
    colored = [item for item in independent_objects(grid) if item["color"] != 0]
    assert len(colored) == 2
    assert MODULE.rule_mirror(grid) == [[4, 4], [4, 4]] == independent_oracle(grid)


def test_broad_rule_crops_original_bbox_instead_of_masking_selected_component():
    grid = [[0] * 12 for _ in range(12)]
    for row in range(3, 8):
        for col in range(3, 8):
            if row in (3, 7) or col in (3, 7):
                grid[row][col] = 8
            else:
                grid[row][col] = 2
    for row in range(8, 11):
        for col in range(1, 10):
            grid[row][col] = 6
    selected = min(independent_objects(grid), key=lambda item: item["size"])
    assert selected["color"] == 8
    output = MODULE.rule_mirror(grid)
    assert output == independent_oracle(grid)
    assert 2 in {value for row in output for value in row}
    assert len({value for row in output for value in row}) > 1


def test_broad_tied_minimum_selects_first_row_major_object():
    grid = [[0] * 12 for _ in range(10)]
    for row in range(1, 3):
        for col in range(1, 3):
            grid[row][col] = 3
    for row in range(6, 8):
        for col in range(8, 10):
            grid[row][col] = 7
    assert MODULE.rule_mirror(grid) == [[3, 3], [3, 3]] == independent_oracle(grid)
    assert MODULE.self_check(grid)


def test_rule_mirror_is_input_pure():
    grid = MODULE.generate(71, 19, difficulty="hard")
    before = frozen(grid)
    MODULE.rule_mirror(grid)
    assert frozen(grid) == before


def test_rule_mirror_rejects_all_excluded_grid():
    with pytest.raises(ValueError):
        MODULE.rule_mirror([[2] * 10 for _ in range(10)])


@pytest.mark.parametrize(
    "grid",
    [
        [],
        [[]],
        [[0] * 9 for _ in range(9)],
        [[2] * 9 for _ in range(9)],
        [[False] * 9 for _ in range(9)],
        [[10] * 9 for _ in range(9)],
        [[0] * 9 for _ in range(8)] + [[0] * 8],
        [[0 if (row, col) != (4, 4) else 3 for col in range(9)] for row in range(9)],
    ],
)
def test_malformed_and_minimal_impostors_fail_closed(grid):
    assert MODULE.self_check(grid)


def test_structural_mutations_fail_closed():
    grid = MODULE.generate(811, 7, difficulty="medium", scene_profile="rectangular_contrast")
    facts = MODULE._analysis(grid)["facts"]
    selected = facts["selected"]

    tied = [row[:] for row in grid]
    color = next(value for value in MODULE.NON_SPECIAL_COLORS if value not in facts["palette"])
    row0, col0, row1, col1 = selected["bbox"]
    height, width = row1 - row0 + 1, col1 - col0 + 1
    placed = False
    for row in range(1, len(tied) - height - 1):
        for col in range(1, len(tied[0]) - width - 1):
            if all(tied[r][c] == 0 for r in range(row, row + height) for c in range(col, col + width)):
                for r in range(row, row + height):
                    for c in range(col, col + width):
                        tied[r][c] = color
                placed = True
                break
        if placed:
            break
    assert placed and MODULE.self_check(tied)

    one_pixel = [row[:] for row in grid]
    one_pixel[0][0] = color
    assert MODULE.self_check(one_pixel)

    no_zero = [[1 if value == 0 else value for value in row] for row in grid]
    assert MODULE.self_check(no_zero)


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
        {"texture": "blob"},
        {"grid_h": 17},
        {"n_objects": 3},
        {"smallest_kind": "rect"},
        {"placement": "corners"},
        {"difficulty": "expert"},
    ],
)
def test_unknown_controls_fail_closed(kwargs):
    with pytest.raises(ValueError):
        MODULE.generate(1, 2, **kwargs)


def test_base_source_description_and_primitive_metadata_are_synchronized():
    row = canonical_row()
    base = json.loads(BASE.read_text())
    target = base["racket_target"]
    normalize = lambda source: " ".join(source.split())
    assert normalize(target["raw_code"]) == normalize(target["target_code"]) == normalize(row["program_solution"])
    description = base["description_target"]
    assert description["target_status"] == "reviewed_semantic_description"
    notes = description["ambiguity_notes"]
    assert "excluded color is 2" in notes
    assert "zero regions" in notes
    assert "row-major" in notes
    assert "rather than masking" in notes
    assert base["primitive_metadata"]["primitive_chain"] == [
        "rows", "cols", "objects", "pick-min", "crop-object"
    ]
