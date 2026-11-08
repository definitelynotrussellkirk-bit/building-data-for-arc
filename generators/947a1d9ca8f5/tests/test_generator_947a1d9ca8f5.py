from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from collections import Counter, deque
from pathlib import Path

import pytest

GENERATOR = importlib.import_module(
    "puzzle_generators.per_puzzle.947a1d9ca8f5.generator"
)
TASK_ID = "947a1d9ca8f5"
REPO_ROOT = Path(__file__).resolve().parents[1]
CARDINALS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def canonical_row():
    with (REPO_ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"missing canonical row {TASK_ID}")


def components(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    found = []
    for start_row in range(height):
        for start_col in range(width):
            color = grid[start_row][start_col]
            if color in (0, 9) or (start_row, start_col) in seen:
                continue
            queue = deque([(start_row, start_col)])
            seen.add((start_row, start_col))
            cells = []
            while queue:
                row, col = queue.popleft()
                cells.append((row, col))
                for dr, dc in CARDINALS:
                    neighbor = row + dr, col + dc
                    if (
                        0 <= neighbor[0] < height
                        and 0 <= neighbor[1] < width
                        and neighbor not in seen
                        and grid[neighbor[0]][neighbor[1]] == color
                    ):
                        seen.add(neighbor)
                        queue.append(neighbor)
            top = min(row for row, _ in cells)
            left = min(col for _, col in cells)
            normalized = sorted((row - top, col - left) for row, col in cells)
            found.append(
                {
                    "color": color,
                    "cells": sorted(cells),
                    "normalized": normalized,
                    "size": len(cells),
                    "top_left": min(cells),
                }
            )
    return found


def independent_oracle(grid):
    found = components(grid)
    minimum = min(item["size"] for item in found)
    template_candidates = [item for item in found if item["size"] == minimum]
    assert len(template_candidates) == 1
    template = template_candidates[0]
    output = [[0 for _ in row] for row in grid]
    markers = [
        (row, col)
        for row, line in enumerate(grid)
        for col, value in enumerate(line)
        if value == 9
    ]
    for marker_row, marker_col in markers:
        for dr, dc in template["normalized"]:
            output[marker_row + dr][marker_col + dc] = template["color"]
    return output


def strict_canonical_like(grid):
    analysis = GENERATOR._analysis(grid)
    if analysis["errors"]:
        return False
    observed = GENERATOR.observe_overrides(grid)
    if observed != {
        "grid_size": observed["grid_size"],
        "template_cells": 3,
        "marker_count": 3,
        "distractor_count": 1,
        "color_relation": "distinct",
    }:
        return False
    if observed["grid_size"] not in (10, 11, 12):
        return False
    template = analysis["template"]
    distractor = analysis["distractors"][0]
    return (
        (template["height"], template["width"], template["size"])
        == (2, 2, 3)
        and (
            distractor["height"],
            distractor["width"],
            distractor["size"],
        )
        == (3, 3, 5)
    )


def test_rule_hash_and_canonical_pairs_are_synchronized():
    row = canonical_row()
    digest = hashlib.sha256(
        " ".join(row["program_solution"].split()).encode()
    ).hexdigest()[:12]
    assert GENERATOR.RULE_HASH == digest == "6e780392649f"
    pairs = row["train"] + row["test"]
    assert len(pairs) == 3
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert independent_oracle(pair["input"]) == pair["output"]
        assert GENERATOR.self_check(pair["input"]) == []
        assert pair["input"] == before


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("grid_size", [10, 16])
@pytest.mark.parametrize("template_cells", [3, 5])
@pytest.mark.parametrize("marker_count", [2, 5])
@pytest.mark.parametrize("distractor_count", [1, 2])
@pytest.mark.parametrize("color_relation", ["distinct", "template_reused"])
def test_every_override_boundary_is_realized_exactly(
    difficulty,
    grid_size,
    template_cells,
    marker_count,
    distractor_count,
    color_relation,
):
    expected = {
        "grid_size": grid_size,
        "template_cells": template_cells,
        "marker_count": marker_count,
        "distractor_count": distractor_count,
        "color_relation": color_relation,
    }
    for seed in range(3):
        grid = GENERATOR.generate(
            50_000 + seed,
            70_000 + seed * 19,
            difficulty=difficulty,
            **expected,
        )
        assert GENERATOR.self_check(grid) == []
        assert GENERATOR.observe_overrides(grid) == expected
        assert independent_oracle(grid) != grid


@pytest.mark.parametrize(
    "kwargs",
    [
        {"grid_size": 9},
        {"grid_size": 17},
        {"template_cells": 2},
        {"template_cells": 6},
        {"marker_count": 1},
        {"marker_count": 6},
        {"distractor_count": 0},
        {"distractor_count": 3},
        {"color_relation": "unknown"},
    ],
)
def test_invalid_overrides_reject_loudly(kwargs):
    with pytest.raises((TypeError, ValueError)):
        GENERATOR.generate(1, 2, **kwargs)


def test_default_distribution_covers_every_semantic_branch_and_canonical_manifold():
    for band in ("easy", "medium", "hard"):
        grids = [
            GENERATOR.generate(
                200_000 + index,
                300_000 + index * 29,
                difficulty=band,
            )
            for index in range(400)
        ]
        observations = [GENERATOR.observe_overrides(grid) for grid in grids]
        assert {item["grid_size"] for item in observations} == set(range(10, 17))
        assert {item["template_cells"] for item in observations} == {3, 4, 5}
        assert {item["marker_count"] for item in observations} == {2, 3, 4, 5}
        assert {item["distractor_count"] for item in observations} == {1, 2}
        assert {item["color_relation"] for item in observations} == {
            "distinct",
            "template_reused",
        }
        canonical_hits = sum(strict_canonical_like(grid) for grid in grids)
        assert canonical_hits >= 20, (band, canonical_hits)


def test_smallest_object_not_position_color_count_or_fixed_shape_shortcut():
    template_reading_positions = set()
    template_shapes = set()
    reused_color_counterexamples = 0
    for seed in range(240):
        grid = GENERATOR.generate(
            410_000 + seed,
            510_000 + seed * 37,
            difficulty="hard",
            distractor_count=2,
            color_relation="template_reused",
        )
        analysis = GENERATOR._analysis(grid)
        template = analysis["template"]
        ordered = sorted(analysis["components"], key=lambda item: item["cells"][0])
        template_reading_positions.add(ordered.index(template))
        template_shapes.add(template["normalized"])
        totals = Counter(
            value
            for row in grid
            for value in row
            if value not in (0, 9)
        )
        other_totals = [
            totals[item["color"]]
            for item in analysis["distractors"]
            if item["color"] != template["color"]
        ]
        if other_totals and totals[template["color"]] > min(other_totals):
            reused_color_counterexamples += 1
        assert independent_oracle(grid) != grid
    assert len(template_reading_positions) >= 2
    assert len(template_shapes) >= 8
    assert reused_color_counterexamples == 240


def test_generated_inputs_have_exact_independent_outputs():
    for band_index, band in enumerate(("easy", "medium", "hard")):
        outputs = set()
        for seed in range(40):
            grid = GENERATOR.generate(
                620_000 + band_index * 1_000 + seed,
                720_000 + seed * 41,
                difficulty=band,
            )
            assert GENERATOR.self_check(grid) == []
            output = independent_oracle(grid)
            assert output != grid
            outputs.add(tuple(map(tuple, output)))
        assert len(outputs) == 40


def test_self_check_rejects_targeted_structural_impostors():
    grid = GENERATOR.generate(
        830_001,
        930_001,
        grid_size=12,
        template_cells=3,
        marker_count=3,
        distractor_count=2,
        color_relation="distinct",
    )
    analysis = GENERATOR._analysis(grid)

    missing_distractors = copy.deepcopy(grid)
    for item in analysis["distractors"]:
        for row, col in item["cells"]:
            missing_distractors[row][col] = 0
    assert GENERATOR.self_check(missing_distractors)

    tied_smallest = copy.deepcopy(grid)
    distractor = analysis["distractors"][0]
    for row, col in distractor["cells"][3:]:
        tied_smallest[row][col] = 0
    assert GENERATOR.self_check(tied_smallest)

    adjacent_markers = copy.deepcopy(grid)
    old_marker = analysis["markers"][-1]
    adjacent_markers[old_marker[0]][old_marker[1]] = 0
    first_marker = analysis["markers"][0]
    target = None
    for dr, dc in CARDINALS:
        row, col = first_marker[0] + dr, first_marker[1] + dc
        if 0 <= row < 12 and 0 <= col < 12 and adjacent_markers[row][col] == 0:
            target = row, col
            break
    assert target is not None
    adjacent_markers[target[0]][target[1]] = 9
    assert GENERATOR.self_check(adjacent_markers)

    out_of_bounds_stamp = copy.deepcopy(grid)
    for row, col in analysis["markers"]:
        out_of_bounds_stamp[row][col] = 0
    out_of_bounds_stamp[-1][-1] = 9
    out_of_bounds_stamp[0][0] = 9
    out_of_bounds_stamp[0][5] = 9
    assert GENERATOR.self_check(out_of_bounds_stamp)

    footprint_collision = copy.deepcopy(grid)
    marker = analysis["markers"][0]
    offset = next(cell for cell in analysis["template"]["normalized"] if cell != (0, 0))
    row, col = marker[0] + offset[0], marker[1] + offset[1]
    footprint_collision[row][col] = analysis["template"]["color"]
    assert GENERATOR.self_check(footprint_collision)


def test_determinism_fresh_returns_and_process_rng_preservation():
    kwargs = {
        "difficulty": "hard",
        "grid_size": 16,
        "template_cells": 5,
        "marker_count": 5,
        "distractor_count": 2,
        "color_relation": "template_reused",
    }
    random.seed(947_001)
    state = random.getstate()
    first = GENERATOR.generate(42, 77, **kwargs)
    assert random.getstate() == state
    second = GENERATOR.generate(42, 77, **kwargs)
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 8
    assert GENERATOR.generate(42, 77, **kwargs) == second


def test_stamp_footprints_are_pairwise_disjoint():
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for i in range(40):
            grid = GENERATOR.generate(930_000 + band_index * 1000 + i, 940_000 + i, difficulty=band)
            analysis = GENERATOR._analysis(grid)
            footprints = analysis["stamp_footprints"]
            assert all(
                not (footprints[left] & footprints[right])
                for left in range(len(footprints))
                for right in range(left)
            )
            expected_cells = len(analysis["markers"]) * analysis["template"]["size"]
            assert sum(value != 0 for row in independent_oracle(grid) for value in row) == expected_cells
