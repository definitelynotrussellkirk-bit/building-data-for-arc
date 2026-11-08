"""Focused semantic, structural, and source-contract tests for 8c7daa3d3cef."""
from __future__ import annotations

import hashlib
import importlib
import json
import random
from collections import Counter
from pathlib import Path

import pytest


MODULE = importlib.import_module(
    "puzzle_generators.per_puzzle.8c7daa3d3cef.generator"
)
ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "data/canonical/puzzles.jsonl"
BASE_FILE = (
    ROOT
    / "data/base/solutions/banks/2f7d84161f6a/"
    "H12__8c7daa3d3cef.json"
)


def canonical_row():
    rows = [
        json.loads(line)
        for line in CANONICAL.read_text().splitlines()
        if json.loads(line).get("task_id") == MODULE.TASK_ID
    ]
    assert len(rows) == 1
    return rows[0]


def independent_oracle(grid):
    colored = {
        color: {
            (row, col)
            for row, values in enumerate(grid)
            for col, value in enumerate(values)
            if value == color
        }
        for color in (1, 4)
    }

    def bbox(cells):
        rows = [row for row, _col in cells]
        cols = [col for _row, col in cells]
        return min(rows), min(cols), max(rows), max(cols)

    outer = bbox(colored[4])
    inner = bbox(colored[1])
    output = [row[:] for row in grid]
    for row in range(outer[0] + 1, outer[2]):
        for col in range(outer[1] + 1, outer[3]):
            if not (
                inner[0] <= row <= inner[2]
                and inner[1] <= col <= inner[3]
            ):
                output[row][col] = 8
    return output


def frozen(grid):
    return tuple(map(tuple, grid))


def test_all_canonical_inputs_and_outputs_match_the_nested_frame_rule():
    row = canonical_row()
    pairs = row["train"] + row["test"]
    assert len(pairs) == 3
    for pair in pairs:
        source = pair["input"]
        snapshot = frozen(source)
        assert MODULE.self_check(source) == []
        assert independent_oracle(source) == pair["output"]
        assert frozen(source) == snapshot
        observed = MODULE.observe_overrides(source)
        assert 7 <= observed["grid_h"] <= 16
        assert 7 <= observed["grid_w"] <= 16
        assert observed["annular_thickness"] == 1


def test_rule_hash_and_task_local_authorities_are_exactly_synchronized():
    row = canonical_row()
    canonical = row["program_solution"]
    normalized = " ".join(canonical.split())
    assert hashlib.sha256(normalized.encode()).hexdigest()[:12] == MODULE.RULE_HASH
    target = json.loads(BASE_FILE.read_text())["racket_target"]
    assert target["raw_code"] == target["target_code"] == canonical
    assert MODULE.VERSION == "4.0.0"
    assert set(MODULE.AXES) == {
        "grid_h",
        "grid_w",
        "annular_thickness",
    }
    assert MODULE.HELPFUL_TEXTURES == MODULE.DEGENERATE_TEXTURES == ()


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_exact_axes_are_observable_and_boundary_complete(difficulty):
    cases = (
        {"grid_h": 7},
        {"grid_h": 16},
        {"grid_w": 7},
        {"grid_w": 16},
        {"annular_thickness": 1},
        {"annular_thickness": 2},
        {"grid_h": 9, "grid_w": 9, "annular_thickness": 2},
        {"grid_h": 16, "grid_w": 16, "annular_thickness": 2},
    )
    for index, overrides in enumerate(cases):
        grid = MODULE.generate(
            80_000 + index,
            index * 31 + 7,
            difficulty=difficulty,
            **overrides,
        )
        assert MODULE.self_check(grid) == []
        observed = MODULE.observe_overrides(grid)
        for name, expected in overrides.items():
            assert observed[name] == expected
        assert independent_oracle(grid) != grid

    with pytest.raises(ValueError, match="cannot contain"):
        MODULE.generate(
            1,
            2,
            difficulty=difficulty,
            grid_h=7,
            annular_thickness=2,
        )
    with pytest.raises(ValueError, match="cannot contain"):
        MODULE.generate(
            1,
            2,
            difficulty=difficulty,
            grid_w=8,
            annular_thickness=2,
        )


def test_default_distribution_is_lawful_varied_and_branch_complete():
    expected_thicknesses = {
        "easy": {1},
        "medium": {1, 2},
        "hard": {1, 2},
    }
    for band_index, difficulty in enumerate(("easy", "medium", "hard")):
        observations = []
        grids = []
        outputs = []
        for offset in range(240):
            seed = 100_000 + band_index * 10_000 + offset
            grid = MODULE.generate(seed, seed * 19 + 5, difficulty=difficulty)
            assert MODULE.self_check(grid) == []
            observations.append(MODULE._analysis(grid)["facts"])
            grids.append(frozen(grid))
            output = independent_oracle(grid)
            assert output != grid
            outputs.append(frozen(output))
        assert {item["annular_thickness"] for item in observations} == expected_thicknesses[difficulty]
        minimum_unique = {"easy": 110, "medium": 190, "hard": 230}[difficulty]
        assert len(set(grids)) >= minimum_unique
        assert len(set(outputs)) >= minimum_unique
        assert len({item["outer_bbox"] for item in observations}) >= 40
        assert len({item["inner_bbox"] for item in observations}) >= 40
        assert len({item["outer_area"] for item in observations}) >= 8


def test_self_check_rejects_targeted_structural_impostors_and_recombination():
    valid = MODULE.generate(731, 19, difficulty="hard")
    facts = MODULE._analysis(valid)["facts"]
    outer = facts["outer_bbox"]
    inner = facts["inner_bbox"]

    missing_inner = [row[:] for row in valid]
    for row in range(len(missing_inner)):
        for col in range(len(missing_inner[0])):
            if missing_inner[row][col] == 1:
                missing_inner[row][col] = 0

    broken_outer = [row[:] for row in valid]
    broken_outer[outer[0]][outer[1]] = 0

    dirty_inner = [row[:] for row in valid]
    dirty_inner[inner[0] + 1][inner[1] + 1] = 1

    touching = [[0] * 9 for _ in range(9)]
    for row, col in MODULE._frame_cells((0, 0, 8, 8)):
        touching[row][col] = 4
    for row, col in MODULE._frame_cells((1, 1, 7, 7)):
        touching[row][col] = 1

    nonuniform = [[0] * 11 for _ in range(11)]
    for row, col in MODULE._frame_cells((0, 0, 10, 10)):
        nonuniform[row][col] = 4
    for row, col in MODULE._frame_cells((2, 2, 7, 8)):
        nonuniform[row][col] = 1

    recombined_plus = [[0] * 13 for _ in range(13)]
    for row, col in MODULE._frame_cells((0, 0, 8, 8)):
        recombined_plus[row][col] = 4
    for row, col in ((10, 10), (9, 10), (11, 10), (10, 9), (10, 11)):
        recombined_plus[row][col] = 1

    for impostor in (
        missing_inner,
        broken_outer,
        dirty_inner,
        touching,
        nonuniform,
        recombined_plus,
        [],
        [[0] * 8 for _ in range(8)],
        [[4] * 8 for _ in range(8)],
    ):
        assert MODULE.self_check(impostor), impostor
        assert MODULE.observe_overrides(impostor) == {}


def test_determinism_fresh_returns_global_rng_and_no_hidden_controls():
    random.seed(912_337)
    state = random.getstate()
    first = MODULE.generate(99, 123, difficulty="medium")
    assert random.getstate() == state
    second = MODULE.generate(99, 123, difficulty="medium")
    assert first == second
    assert first is not second and first[0] is not second[0]
    original = second[0][0]
    first[0][0] = 9
    assert second[0][0] == original
    assert MODULE.generate(99, 124, difficulty="medium") != second

    for kwargs in (
        {"texture": "frames_touching"},
        {"palette_kind": "default"},
        {"grid_h": 6},
        {"grid_w": 17},
        {"annular_thickness": 3},
        {"difficulty": "extreme"},
    ):
        with pytest.raises(ValueError):
            MODULE.generate(1, 0, **kwargs)
