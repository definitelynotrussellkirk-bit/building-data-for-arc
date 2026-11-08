from __future__ import annotations

from collections import Counter, deque
import hashlib
import importlib
import json
from pathlib import Path
import random

import pytest

from arcpuzzles.catalog import Catalog
from reviewer_support import find_root


TASK = "c2a1ba1a45fd"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = find_root(__file__)
BASE = ROOT / "shared" / "data" / "base" / "solutions" / "training" / "1da012fc__c2a1ba1a45fd.json"
DELTAS_8 = tuple(
    (dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if (dr, dc) != (0, 0)
)


def canonical_row():
    rows = Catalog(ROOT)._variants()[TASK]
    assert len(rows) == 1
    return rows[0]


def frozen(grid):
    return tuple(map(tuple, grid))


def independent_objects_8(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    found = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            color = grid[row][col]
            queue = deque([(row, col)])
            seen.add((row, col))
            cells = []
            while queue:
                here = queue.popleft()
                cells.append(here)
                for dr, dc in DELTAS_8:
                    neighbor = (here[0] + dr, here[1] + dc)
                    if (
                        0 <= neighbor[0] < height
                        and 0 <= neighbor[1] < width
                        and neighbor not in seen
                        and grid[neighbor[0]][neighbor[1]] == color
                    ):
                        seen.add(neighbor)
                        queue.append(neighbor)
            found.append({"color": color, "cells": tuple(sorted(cells))})
    return found


def independent_facts(grid):
    grays = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 5
    ]
    if not grays:
        raise ValueError("no gray")
    bbox = (
        min(row for row, _ in grays), min(col for _, col in grays),
        max(row for row, _ in grays), max(col for _, col in grays),
    )

    def inside(cell):
        return bbox[0] <= cell[0] <= bbox[2] and bbox[1] <= cell[1] <= bbox[3]

    counts = {
        color: sum(
            value == color and not inside((row, col))
            for row, values in enumerate(grid)
            for col, value in enumerate(values)
        )
        for color in range(1, 10)
    }
    source, best = 0, 0
    for color in range(1, 10):
        if counts[color] > best:
            source, best = color, counts[color]
    dots = tuple(
        (row, col, grid[row][col])
        for row in range(bbox[0], bbox[2] + 1)
        for col in range(bbox[1], bbox[3] + 1)
        if grid[row][col] not in (0, 5, source)
    )
    objects = tuple(sorted(
        (
            item for item in independent_objects_8(grid)
            if item["color"] == source and not any(inside(cell) for cell in item["cells"])
        ),
        key=lambda item: min(item["cells"]),
    ))
    return {"bbox": bbox, "counts": counts, "source": source, "dots": dots, "objects": objects}


def independent_oracle(grid):
    facts = independent_facts(grid)
    output = [row[:] for row in grid]
    for dot, obj in zip(facts["dots"], facts["objects"]):
        for row, col in obj["cells"]:
            output[row][col] = dot[2]
    return output


def test_metadata_hash_and_control_surface_are_exact():
    assert MODULE.VERSION == "3.0.0"
    assert MODULE.RULE_HASH == "35ba3ac2fe27"
    assert tuple(MODULE.AXES) == ("scene_profile",)
    assert MODULE.SCENE_PROFILES == MODULE.PUBLIC_PROFILES + MODULE.GENERAL_PROFILES
    assert MODULE.HELPFUL_TEXTURES == MODULE.DEGENERATE_TEXTURES == ()
    normalized = " ".join(canonical_row()["program_solution"].split())
    assert hashlib.sha256(normalized.encode()).hexdigest()[:12] == MODULE.RULE_HASH


@pytest.mark.parametrize("index", range(3))
def test_all_canonical_pairs_are_exact_and_anchored(index):
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
def test_random_public_embeddings_preserve_complete_recolored_families(profile):
    grids = [MODULE._embed_public(profile, random.Random(20_000 + seed)) for seed in range(60)]
    assert len({frozen(grid) for grid in grids}) >= 58
    assert all(MODULE.canonical_family_signature(grid) == profile for grid in grids)
    assert all(MODULE.self_check(grid) == [] for grid in grids)
    assert all(MODULE.rule_mirror(grid) == independent_oracle(grid) for grid in grids)


@pytest.mark.parametrize("profile", MODULE.SCENE_PROFILES)
@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_profile_and_band_is_observable_valid_and_oracle_exact(profile, band):
    for seed in range(6):
        grid = MODULE.generate(10_000 + seed, seed * 31, difficulty=band, scene_profile=profile)
        analysis = MODULE._analysis(grid)
        assert analysis["errors"] == []
        assert analysis["scene_profile"] == profile
        assert MODULE.observe_overrides(grid) == {"scene_profile": profile}
        assert analysis["output"] == MODULE.rule_mirror(grid) == independent_oracle(grid)
        facts = analysis["facts"]
        assert 2 <= facts["pair_count"] <= 6
        assert facts["source_count"] > max(
            count for color, count in facts["outside_counts"].items()
            if color != facts["source_color"]
        )


def test_general_profiles_encode_distinct_rule_boundaries():
    for profile in MODULE.GENERAL_PROFILES:
        for seed in range(40):
            grid = MODULE.generate(30_000 + seed, seed, difficulty="hard", scene_profile=profile)
            facts = MODULE._analysis(grid)["facts"]
            if profile == "extra_dot":
                assert facts["dot_count"] == facts["object_count"] + 1
            elif profile == "extra_object":
                assert facts["object_count"] == facts["dot_count"] + 1
            elif profile == "source_dot_ignored":
                bbox, source = facts["legend_bbox"], facts["source_color"]
                assert any(
                    grid[row][col] == source
                    for row in range(bbox[0], bbox[2] + 1)
                    for col in range(bbox[1], bbox[3] + 1)
                )
            elif profile == "diagonal_object":
                assert any(
                    MODULE._cardinal_component_count(item["cells"]) > 1
                    for item in facts["source_objects"]
                )
            elif profile == "source_frequency":
                bbox, source = facts["legend_bbox"], facts["source_color"]
                assert any(
                    value not in (0, 5, source) and not MODULE._inside((row, col), bbox)
                    for row, values in enumerate(grid)
                    for col, value in enumerate(values)
                )
            elif profile == "repeated_dot_color":
                colors = [value for _, _, value in facts["dots"]]
                assert len(set(colors)) < len(colors)
            else:
                assert facts["dot_count"] == facts["object_count"]


def test_default_census_is_complete_band_aware_and_diverse():
    medians = {}
    for band in ("easy", "medium", "hard"):
        inputs, outputs, shapes = set(), set(), set()
        profiles = Counter()
        object_counts, source_colors, areas = set(), set(), []
        for index in range(1000):
            grid = MODULE.generate(800_000, index, difficulty=band)
            analysis = MODULE._analysis(grid)
            assert analysis["errors"] == []
            assert analysis["output"] == independent_oracle(grid)
            inputs.add(frozen(grid))
            outputs.add(frozen(analysis["output"]))
            shapes.add((len(grid), len(grid[0])))
            profiles[analysis["scene_profile"]] += 1
            object_counts.add(analysis["facts"]["object_count"])
            source_colors.add(analysis["facts"]["source_color"])
            areas.append(len(grid) * len(grid[0]))
        assert len(inputs) >= 990
        assert len(outputs) >= 980
        assert set(profiles) == set(MODULE.SCENE_PROFILES)
        assert min(profiles.values()) >= 45
        assert len(shapes) >= 20
        assert source_colors == set(MODULE.NON_SPECIAL_COLORS)
        assert len(object_counts) >= 3
        medians[band] = sorted(areas)[len(areas) // 2]
    assert medians["easy"] < medians["medium"] < medians["hard"]


def test_broad_rule_uses_first_lower_color_on_frequency_tie():
    grid = [[0] * 15 for _ in range(12)]
    for row in range(2, 7):
        for col in range(1, 6):
            grid[row][col] = 5
    grid[3][2], grid[5][4] = 7, 8
    for row, col in ((1, 9), (1, 10), (2, 9), (8, 2), (8, 3), (9, 2)):
        grid[row][col] = 2
    for row, col in ((3, 11), (3, 12), (4, 11), (9, 10), (9, 11), (10, 10)):
        grid[row][col] = 4
    facts = independent_facts(grid)
    assert facts["counts"][2] == facts["counts"][4] == 6
    assert facts["source"] == 2
    assert MODULE.rule_mirror(grid) == independent_oracle(grid)
    assert MODULE.self_check(grid)


def test_broad_rule_ignores_source_colored_legend_cells_as_dots():
    grid = MODULE.generate(41, 9, difficulty="medium", scene_profile="source_dot_ignored")
    facts = independent_facts(grid)
    bbox = facts["bbox"]
    source_inside = [
        (row, col) for row in range(bbox[0], bbox[2] + 1)
        for col in range(bbox[1], bbox[3] + 1) if grid[row][col] == facts["source"]
    ]
    assert len(source_inside) == 1
    assert all((row, col) != source_inside[0] for row, col, _ in facts["dots"])


def test_broad_rule_uses_eight_connectivity():
    grid = MODULE.generate(51, 3, difficulty="medium", scene_profile="diagonal_object")
    facts = independent_facts(grid)
    assert any(MODULE._cardinal_component_count(item["cells"]) > 1 for item in facts["objects"])
    assert MODULE.rule_mirror(grid) == independent_oracle(grid)


def test_broad_rule_pairs_only_the_shorter_count_and_preserves_unpaired_content():
    for profile in ("extra_dot", "extra_object", "source_frequency"):
        grid = MODULE.generate(61, 4, difficulty="hard", scene_profile=profile)
        facts = independent_facts(grid)
        output = MODULE.rule_mirror(grid)
        assert output == independent_oracle(grid)
        bbox = facts["bbox"]
        assert all(
            output[row][col] == grid[row][col]
            for row in range(bbox[0], bbox[2] + 1)
            for col in range(bbox[1], bbox[3] + 1)
        )
        if profile == "extra_object":
            for row, col in facts["objects"][-1]["cells"]:
                assert output[row][col] == facts["source"]


def test_rule_mirror_is_input_pure_and_requires_gray():
    grid = MODULE.generate(71, 19, difficulty="hard")
    before = frozen(grid)
    MODULE.rule_mirror(grid)
    assert frozen(grid) == before
    with pytest.raises(ValueError):
        MODULE.rule_mirror([[0] * 10 for _ in range(10)])


@pytest.mark.parametrize(
    "grid",
    [
        [], [[]], [[0] * 9 for _ in range(9)], [[5] * 9 for _ in range(9)],
        [[False] * 9 for _ in range(9)], [[10] * 9 for _ in range(9)],
        [[0] * 9 for _ in range(8)] + [[0] * 8],
    ],
)
def test_malformed_and_degenerate_inputs_fail_closed(grid):
    assert MODULE.self_check(grid)


def test_structural_mutations_fail_closed():
    grid = MODULE.generate(811, 7, difficulty="medium", scene_profile="ordered_shapes")
    no_zero = [[5 if value == 0 else value for value in row] for row in grid]
    assert MODULE.self_check(no_zero)
    no_gray = [[0 if value == 5 else value for value in row] for row in grid]
    assert MODULE.self_check(no_gray)
    one_mapping = [row[:] for row in grid]
    facts = MODULE._analysis(one_mapping)["facts"]
    for item in facts["source_objects"][1:]:
        for row, col in item["cells"]:
            one_mapping[row][col] = 0
    assert MODULE.self_check(one_mapping)
    zero_hole = [row[:] for row in grid]
    bbox = facts["legend_bbox"]
    zero_hole[bbox[0] + 1][bbox[1] + 1] = 0
    assert MODULE.self_check(zero_hole)


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
        {"scene_profile": "unknown"}, {"texture": "warm"}, {"grid_h": 17},
        {"n_shapes": 3}, {"palette_kind": "cool"}, {"anchor_corner": True},
        {"difficulty": "expert"},
    ],
)
def test_unknown_controls_fail_closed(kwargs):
    with pytest.raises(ValueError):
        MODULE.generate(1, 2, **kwargs)


def test_base_authority_matches_canonical_program():
    base = json.loads(BASE.read_text())
    source = " ".join(canonical_row()["program_solution"].split())
    assert " ".join(base["racket_target"]["raw_code"].split()) == source
    assert " ".join(base["racket_target"]["target_code"].split()) == source
