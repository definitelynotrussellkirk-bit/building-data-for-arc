from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest


TASK = "79b307b1e4da"
GENERATOR = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK}.generator"
)
ROOT = Path(__file__).resolve().parents[1]


def canonical_row():
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            return row
    raise AssertionError(f"missing canonical row for {TASK}")


def independent_components(body):
    height = len(body)
    width = len(body[0]) if body else 0
    seen = set()
    objects = []
    for start_row in range(height):
        for start_col in range(width):
            color = body[start_row][start_col]
            if color == 0 or (start_row, start_col) in seen:
                continue
            stack = [(start_row, start_col)]
            seen.add((start_row, start_col))
            cells = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    neighbor = row + dr, col + dc
                    if (
                        0 <= neighbor[0] < height
                        and 0 <= neighbor[1] < width
                        and neighbor not in seen
                        and body[neighbor[0]][neighbor[1]] == color
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            top = min(row for row, _ in cells)
            left = min(col for _, col in cells)
            bottom = max(row for row, _ in cells)
            right = max(col for _, col in cells)
            objects.append(
                {
                    "id": (start_row, start_col),
                    "color": color,
                    "cells": cells,
                    "height": bottom - top + 1,
                    "width": right - left + 1,
                    "size": len(cells),
                    "normalized": sorted(
                        (row - top, col - left) for row, col in cells
                    ),
                }
            )
    return objects


def independent_oracle(grid):
    palette = [value for value in grid[0] if value != 0]
    objects = sorted(
        independent_components(grid[1:]),
        key=lambda item: (-item["height"], -item["width"]),
    )
    output_height = max(item["height"] for item in objects)
    output_width = sum(item["width"] for item in objects) + len(objects) - 1
    output = [[0] * output_width for _ in range(output_height)]
    left = 0
    for color, item in zip(palette, objects):
        for row, col in item["normalized"]:
            output[row][left + col] = color
        left += item["width"] + 1
    return output


def frozen(grid):
    return tuple(map(tuple, grid))


def sort_signature(objects):
    return tuple(
        (item["height"], item["width"], item["size"])
        for item in sorted(
            objects,
            key=lambda item: (-item["height"], -item["width"]),
        )
    )


def test_rule_hash_and_canonical_outputs_are_synchronized():
    row = canonical_row()
    source = row["program_solution"]
    digest = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
    assert GENERATOR.RULE_HASH == digest == "2943fbde1fb4"
    pairs = row["train"] + [row["test"]]
    assert len(pairs) == 3
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert independent_oracle(pair["input"]) == pair["output"]
        assert GENERATOR.self_check(pair["input"]) == []
        assert pair["input"] == before


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("profile", GENERATOR.SCENE_PROFILES)
def test_every_scene_profile_is_exact_and_oracle_lawful(profile, difficulty):
    for seed in range(12):
        grid = GENERATOR.generate(
            seed + 10_000,
            seed * 23 + 7,
            difficulty=difficulty,
            scene_profile=profile,
        )
        analysis = GENERATOR._analysis(grid)
        objects = analysis["objects"]
        ordered = sorted(
            objects,
            key=lambda item: (-item["height"], -item["width"]),
        )
        ordered_ids = [item["id"] for item in ordered]
        assert analysis["errors"] == []
        assert analysis["profile"] == profile
        assert GENERATOR.observe_overrides(grid) == {"scene_profile": profile}
        assert independent_oracle(grid) != grid
        assert [item["id"] for item in objects] != ordered_ids
        assert sum(
            item["color"] != color
            for item, color in zip(ordered, analysis["palette"])
        ) >= 2


@pytest.mark.parametrize("height", [7, 12])
@pytest.mark.parametrize("width", [9, 14])
@pytest.mark.parametrize("profile", GENERATOR.SCENE_PROFILES)
def test_all_override_boundaries_are_realizable(height, width, profile):
    for seed in range(8):
        grid = GENERATOR.generate(
            seed,
            40_000 + seed,
            grid_h=height,
            grid_w=width,
            scene_profile=profile,
        )
        assert (len(grid), len(grid[0])) == (height, width)
        assert GENERATOR.self_check(grid) == []
        assert GENERATOR.observe_overrides(grid) == {"scene_profile": profile}


def test_default_distribution_covers_every_profile_and_relation_in_each_band():
    expected_profiles = set(GENERATOR.SCENE_PROFILES)
    for difficulty in ("easy", "medium", "hard"):
        analyses = [
            GENERATOR._analysis(
                GENERATOR.generate(
                    80_000 + seed,
                    seed * 31 + 11,
                    difficulty=difficulty,
                )
            )
            for seed in range(240)
        ]
        assert {analysis["profile"] for analysis in analyses} == expected_profiles
        overlap_sizes = {
            len(
                set(analysis["palette"])
                & {item["color"] for item in analysis["objects"]}
            )
            for analysis in analyses
        }
        assert {0, 1, 3} <= overlap_sizes
        assert all(analysis["errors"] == [] for analysis in analyses)


def test_default_distribution_preserves_canonical_morphology_and_breaks_shortcuts():
    canonical_signatures = {
        "monochrome_disjoint": ((3, 1, 3), (2, 2, 4), (1, 3, 3)),
        "tie_partial": ((3, 2, 6), (3, 1, 3), (1, 2, 2)),
        "distinct_partial": ((3, 2, 6), (2, 2, 3), (1, 1, 1)),
    }
    for difficulty in ("easy", "medium", "hard"):
        canonical_hits = {profile: 0 for profile in canonical_signatures}
        descending_size_matches = 0
        descending_size_disagrees = 0
        ascending_size_disagrees = 0
        for seed in range(400):
            grid = GENERATOR.generate(
                280_000 + seed,
                60_000 + seed * 43,
                difficulty=difficulty,
            )
            analysis = GENERATOR._analysis(grid)
            objects = analysis["objects"]
            ordered = sorted(
                objects,
                key=lambda item: (-item["height"], -item["width"]),
            )
            ordered_ids = [item["id"] for item in ordered]
            signature = sort_signature(objects)
            profile = analysis["profile"]
            if canonical_signatures.get(profile) == signature:
                canonical_hits[profile] += 1
            desc_matches = [
                item["id"] for item in sorted(objects, key=lambda item: -item["size"])
            ] == ordered_ids
            asc_matches = [
                item["id"] for item in sorted(objects, key=lambda item: item["size"])
            ] == ordered_ids
            descending_size_matches += int(desc_matches)
            descending_size_disagrees += int(not desc_matches)
            ascending_size_disagrees += int(not asc_matches)

        assert all(count >= 10 for count in canonical_hits.values())
        assert descending_size_matches >= 20
        assert descending_size_disagrees >= 100
        assert ascending_size_disagrees == 400


def test_determinism_fresh_returns_and_global_rng_independence():
    random.seed(9917)
    state = random.getstate()
    first = GENERATOR.generate(
        7123,
        99,
        difficulty="hard",
        scene_profile="tie_partial",
        grid_h=12,
        grid_w=14,
    )
    assert random.getstate() == state
    second = GENERATOR.generate(
        7123,
        99,
        difficulty="hard",
        scene_profile="tie_partial",
        grid_h=12,
        grid_w=14,
    )
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 0
    assert GENERATOR.generate(
        7123,
        99,
        difficulty="hard",
        scene_profile="tie_partial",
        grid_h=12,
        grid_w=14,
    ) == second


def test_structural_mutations_fail_closed():
    grid = GENERATOR.generate(
        987654,
        321,
        difficulty="medium",
        scene_profile="monochrome_disjoint",
    )
    analysis = GENERATOR._analysis(grid)
    objects = analysis["objects"]

    dropped = copy.deepcopy(grid)
    dropped[0][0] = 0
    assert GENERATOR.self_check(dropped)

    noncontiguous = copy.deepcopy(grid)
    noncontiguous[0][-1] = noncontiguous[0][0]
    noncontiguous[0][0] = 0
    assert GENERATOR.self_check(noncontiguous)

    erased = copy.deepcopy(grid)
    for row, col in objects[-1]["cells"]:
        erased[row + 1][col] = 0
    assert GENERATOR.self_check(erased)

    echoed = copy.deepcopy(grid)
    ordered = sorted(
        objects,
        key=lambda item: (-item["height"], -item["width"]),
    )
    for item, color in zip(ordered, analysis["palette"]):
        for row, col in item["cells"]:
            echoed[row + 1][col] = color
    assert GENERATOR.self_check(echoed)

    duplicate_key = copy.deepcopy(grid)
    # Replace the smallest object's cells with a translated 2x3 rectangle,
    # duplicating the middle object's bbox key without touching its neighbors.
    for row, col in objects[-1]["cells"]:
        duplicate_key[row + 1][col] = 0
    body_h = len(grid) - 1
    width = len(grid[0])
    occupied = {
        (row, col)
        for row, line in enumerate(duplicate_key[1:])
        for col, value in enumerate(line)
        if value
    }
    replacement = None
    for top in range(body_h - 1):
        for left in range(width - 2):
            cells = {(top + dr, left + dc) for dr in range(2) for dc in range(3)}
            halo = {
                (row + dr, col + dc)
                for row, col in cells
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
            }
            if not (cells | halo) & occupied:
                replacement = cells
                break
        if replacement:
            break
    assert replacement is not None
    color = objects[-1]["color"]
    for row, col in replacement:
        duplicate_key[row + 1][col] = color
    assert any("bbox sort keys" in error for error in GENERATOR.self_check(duplicate_key))


@pytest.mark.parametrize(
    "kwargs",
    [
        {"grid_h": 6},
        {"grid_h": 13},
        {"grid_w": 8},
        {"grid_w": 15},
        {"scene_profile": "unknown"},
        {"difficulty": "expert"},
        {"palette_kind": "distinct"},
    ],
)
def test_invalid_or_historical_controls_fail_loudly(kwargs):
    with pytest.raises((TypeError, ValueError)):
        GENERATOR.generate(1, 0, **kwargs)


def test_axis_contract_is_literal_and_minimal():
    assert set(GENERATOR.AXES) == {"grid_h", "grid_w", "scene_profile"}
    assert tuple(GENERATOR.AXES["scene_profile"]["valid"].split("|")) == GENERATOR.SCENE_PROFILES
    assert GENERATOR.VERSION == "3.1.0"
    assert "bbox height" in GENERATOR.SUMMARY
    assert "pack them horizontally" in GENERATOR.SUMMARY
