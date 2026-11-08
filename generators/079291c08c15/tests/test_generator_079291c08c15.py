"""Focused semantic regression tests for generator 079291c08c15."""
from __future__ import annotations

import hashlib
import importlib
import json
import random
from collections import Counter
from pathlib import Path

import pytest

MODULE = importlib.import_module(
    "puzzle_generators.per_puzzle.079291c08c15.generator"
)
ROOT = Path(__file__).resolve().parents[1]


def canonical_row() -> dict:
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == MODULE.TASK_ID:
                return row
    raise AssertionError("canonical row not found")


def canonical_pairs() -> list[dict]:
    row = canonical_row()
    tests = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return row["train"] + tests


def normalized_rule_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()


def components(grid: list[list[int]]) -> list[dict]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict] = []
    for start_row in range(height):
        for start_col in range(width):
            color = grid[start_row][start_col]
            if color == 0 or (start_row, start_col) in seen:
                continue
            stack = [(start_row, start_col)]
            seen.add((start_row, start_col))
            cells: set[tuple[int, int]] = set()
            while stack:
                row, col = stack.pop()
                cells.add((row, col))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    neighbor = (row + dr, col + dc)
                    nr, nc = neighbor
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and neighbor not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            top = min(row for row, _ in cells)
            left = min(col for _, col in cells)
            result.append(
                {
                    "color": color,
                    "cells": cells,
                    "top": top,
                    "left": left,
                    "bottom": max(row for row, _ in cells),
                    "right": max(col for _, col in cells),
                    "normalized": {
                        (row - top, col - left) for row, col in cells
                    },
                }
            )
    return sorted(result, key=lambda item: (item["left"], item["top"]))


def independent_rule(grid: list[list[int]]) -> list[list[int]]:
    height, width = len(grid), len(grid[0])
    left, right = components(grid)
    output = [[0] * width for _ in range(height)]
    for row, col in left["normalized"]:
        output[right["top"] + row][right["left"] + col] = left["color"]
    for row, col in right["normalized"]:
        output[left["top"] + row][left["left"] + col] = right["color"]
    return output


def freeze(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def test_rule_hash_authority_and_all_canonical_pairs() -> None:
    row = canonical_row()
    base = json.loads(
        (
            ROOT
            / "data/base/solutions/banks/276b5e4c56a1/"
            "medium_b04__079291c08c15.json"
        ).read_text()
    )["racket_target"]
    source = row["program_solution"]
    assert base["raw_code"] == source
    assert base["target_code"] == source
    assert MODULE.RULE_HASH == normalized_rule_hash(source)[:12]

    pairs = canonical_pairs()
    assert len(pairs) == 4
    for pair in pairs:
        snapshot = [row[:] for row in pair["input"]]
        assert MODULE.self_check(pair["input"]) == []
        assert independent_rule(pair["input"]) == pair["output"]
        assert MODULE.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == snapshot


def test_exact_dimension_overrides_work_in_every_band() -> None:
    for band in ("easy", "medium", "hard"):
        for height in (8, 9, 13, 18):
            for width in (10, 11, 16, 20):
                for seed in range(4):
                    grid = MODULE.generate(
                        seed,
                        seed * 17 + 5,
                        difficulty=band,
                        grid_h=height,
                        grid_w=width,
                    )
                    assert (len(grid), len(grid[0])) == (height, width)
                    assert MODULE.observe_overrides(grid) == {
                        "grid_h": height,
                        "grid_w": width,
                    }
                    assert MODULE.self_check(grid) == []
                    assert MODULE.rule_mirror(grid) == independent_rule(grid)


@pytest.mark.parametrize("bad_difficulty", ["extreme", "", 2])
def test_invalid_difficulty_rejects(bad_difficulty) -> None:
    with pytest.raises(ValueError):
        MODULE.generate(1, 2, difficulty=bad_difficulty)


def test_unknown_and_retired_texture_overrides_reject() -> None:
    for overrides in (
        {"bogus_axis": 1},
        {"texture": "third_object"},
        {"texture": "clip"},
        {"texture": "swap_overlap"},
    ):
        with pytest.raises(ValueError):
            MODULE.generate(1, 2, **overrides)


def test_distribution_is_lawful_stable_and_varied() -> None:
    for seed_base in (100_000, 600_000):
        for band_index, band in enumerate(("easy", "medium", "hard")):
            inputs = set()
            outputs = set()
            dimensions = set()
            shape_pairs = set()
            top_relations = Counter()
            size_relations = Counter()
            colors = set()
            for sample_index in range(240):
                seed = seed_base + band_index * 10_000 + sample_index
                grid = MODULE.generate(
                    seed,
                    sample_index * 31 + 7,
                    difficulty=band,
                )
                assert MODULE.self_check(grid) == []
                found = components(grid)
                assert len(found) == 2
                left, right = found
                assert left["color"] != right["color"]
                assert left["right"] < right["left"]
                assert left["normalized"] != right["normalized"]
                output = independent_rule(grid)
                assert MODULE.rule_mirror(grid) == output
                signature = MODULE.semantic_signature(grid)
                assert signature["valid"] is True
                assert signature["swap_fits"] is True
                assert signature["swap_overlap"] is False
                top_relations[signature["top_relation"]] += 1
                size_relations[signature["size_relation"]] += 1
                colors.update((left["color"], right["color"]))
                shape_pairs.add(
                    (
                        tuple(sorted(left["normalized"])),
                        tuple(sorted(right["normalized"])),
                    )
                )
                dimensions.add((len(grid), len(grid[0])))
                inputs.add(freeze(grid))
                outputs.add(freeze(output))
            assert set(top_relations) == {
                "left_higher",
                "left_lower",
                "same_top",
            }
            assert set(size_relations) == {
                "left_larger",
                "right_larger",
                "equal_size",
            }
            assert colors == set(range(1, 10))
            assert len(dimensions) >= 4
            assert len(shape_pairs) >= 120
            assert len(inputs) >= 238
            assert len(outputs) >= 238


def test_self_check_rejects_targeted_semantic_impostors() -> None:
    canonical = canonical_pairs()[0]["input"]

    one_object = [row[:] for row in canonical]
    right_color = 5
    one_object = [
        [0 if value == right_color else value for value in row]
        for row in one_object
    ]

    third_object = [row[:] for row in canonical]
    third_object[6][9] = 9

    same_color = [row[:] for row in canonical]
    same_color = [
        [3 if value == 5 else value for value in row]
        for row in same_color
    ]

    same_shape = [[0] * 10 for _ in range(8)]
    for row, col in ((1, 1), (2, 1), (2, 2)):
        same_shape[row][col] = 2
    for row, col in ((4, 6), (5, 6), (5, 7)):
        same_shape[row][col] = 8

    clipping = [[0] * 10 for _ in range(6)]
    for row, col in ((0, 1), (1, 1), (2, 1), (2, 2)):
        clipping[row][col] = 3
    for row, col in ((4, 8), (4, 9)):
        clipping[row][col] = 7

    overlap = [[0] * 10 for _ in range(7)]
    for row, col in ((1, 1), (2, 1), (3, 1)):
        overlap[row][col] = 4
    for row, col in ((1, 3), (1, 4), (1, 5)):
        overlap[row][col] = 6

    bbox_column_tie = [[0] * 8 for _ in range(8)]
    for row, col in ((0, 2), (1, 2), (1, 3)):
        bbox_column_tie[row][col] = 1
    for row, col in ((5, 2), (6, 2), (6, 3), (7, 3)):
        bbox_column_tie[row][col] = 9

    invalid_color = [row[:] for row in canonical]
    invalid_color[0][0] = 10
    boolean_cell = [row[:] for row in canonical]
    boolean_cell[0][0] = True
    ragged = [row[:] for row in canonical]
    ragged[-1] = ragged[-1][:-1]

    impostors = {
        "one_object": one_object,
        "third_object": third_object,
        "same_color": same_color,
        "same_shape": same_shape,
        "clipping": clipping,
        "overlap": overlap,
        "bbox_column_tie": bbox_column_tie,
        "invalid_color": invalid_color,
        "boolean_cell": boolean_cell,
        "ragged": ragged,
        "empty": [],
    }
    for name, grid in impostors.items():
        assert MODULE.self_check(grid), name

    # These malformed lessons still exercise executable-oracle edge behavior;
    # oracle non-crash does not make them valid teaching scenes.
    assert MODULE.rule_mirror(third_object) is not None
    assert MODULE.rule_mirror(clipping) is not None
    assert MODULE.rule_mirror(overlap) is not None


def test_determinism_fresh_returns_and_global_rng_purity() -> None:
    random.seed(271_828)
    state = random.getstate()
    first = MODULE.generate(777, 888, difficulty="hard")
    assert random.getstate() == state
    second = MODULE.generate(777, 888, difficulty="hard")
    assert first == second
    assert first is not second
    assert first[0] is not second[0]
    second[0][0] = (second[0][0] + 1) % 10
    third = MODULE.generate(777, 888, difficulty="hard")
    assert first == third
