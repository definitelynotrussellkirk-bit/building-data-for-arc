"""Focused semantic and contract regressions for generator 5b3c69ad7276."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from collections import Counter
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "5b3c69ad7276"
MODULE = importlib.import_module(
    "puzzle_generators.per_puzzle.5b3c69ad7276.generator"
)


def _normalized_rule_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _canonical_row() -> dict:
    rows = []
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                rows.append(row)
    assert len(rows) == 1
    return rows[0]


def _pairs(row: dict) -> list[dict]:
    test = row["test"]
    return row["train"] + ([test] if isinstance(test, dict) else test)


def _frozen(grid) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def _single_seed_grid(height: int, width: int, row: int, col: int, color: int):
    grid = [[0] * width for _ in range(height)]
    grid[row][col] = color
    return grid


def test_rule_authorities_version_and_axis_contract_are_synchronized():
    row = _canonical_row()
    base_paths = sorted((ROOT / "data/base/solutions").rglob(f"*{TASK_ID}*.json"))
    assert len(base_paths) == 1
    base = json.loads(base_paths[0].read_text(encoding="utf-8"))

    assert MODULE.VERSION == "2.0.0"
    assert MODULE.RULE_HASH == "2ee7e1a5f677"
    assert MODULE.RULE_HASH == _normalized_rule_hash(row["program_solution"])
    assert MODULE.RULE_HASH == _normalized_rule_hash(
        base["racket_target"]["target_code"]
    )
    assert set(MODULE.AXES) == {"grid_h", "grid_w", "anchor_kind", "color"}
    assert tuple(MODULE.HELPFUL_TEXTURES) == ()
    assert tuple(MODULE.DEGENERATE_TEXTURES) == ()


def test_every_canonical_pair_is_accepted_and_replayed_exactly_without_mutation():
    pairs = _pairs(_canonical_row())
    assert len(pairs) == 3
    for index, pair in enumerate(pairs):
        source = copy.deepcopy(pair["input"])
        assert MODULE.self_check(source) == []
        assert MODULE.rule_mirror(source) == pair["output"], index
        assert source == pair["input"], index


def test_every_exact_axis_boundary_is_observable_in_every_band():
    for band in (None, "easy", "medium", "hard"):
        for height in (4, 12):
            for width in (4, 12):
                for anchor_kind in MODULE.ANCHOR_KINDS:
                    for color in (1, 9):
                        grid = MODULE.generate(
                            17,
                            29,
                            difficulty=band,
                            grid_h=height,
                            grid_w=width,
                            anchor_kind=anchor_kind,
                            color=color,
                        )
                        assert MODULE.self_check(grid) == []
                        assert MODULE.observe_overrides(grid) == {
                            "grid_h": height,
                            "grid_w": width,
                            "anchor_kind": anchor_kind,
                            "color": color,
                        }
                        output = MODULE.rule_mirror(grid)
                        seed_row, seed_col, _ = next(
                            (row, col, value)
                            for row, values in enumerate(grid)
                            for col, value in enumerate(values)
                            if value
                        )
                        expected_count = height + width - 1
                        assert sum(value == color for row in output for value in row) == expected_count
                        assert all(value == color for value in output[seed_row])
                        assert all(output[row][seed_col] == color for row in range(height))


def test_default_distribution_covers_all_rule_relevant_branches_and_varies_geometry():
    minimum_shapes = {"easy": 10, "medium": 20, "hard": 20}
    minimum_positions = {"easy": 240, "medium": 400, "hard": 400}
    for band_index, band in enumerate(("easy", "medium", "hard")):
        anchor_counts = Counter()
        colors = set()
        shapes = set()
        positions = set()
        inputs = set()
        outputs = set()
        for seed in range(600):
            grid = MODULE.generate(
                100_000 * band_index + seed,
                seed * 37 + 11,
                difficulty=band,
            )
            assert MODULE.self_check(grid) == []
            facts, errors = MODULE._scene_analysis(grid)
            assert errors == []
            anchor_counts[facts["anchor_kind"]] += 1
            colors.add(facts["color"])
            shapes.add((facts["grid_h"], facts["grid_w"]))
            positions.add((facts["grid_h"], facts["grid_w"], facts["seed_row"], facts["seed_col"]))
            inputs.add(_frozen(grid))
            output = MODULE.rule_mirror(grid)
            outputs.add(_frozen(output))
            assert grid != output
        assert set(anchor_counts) == set(MODULE.ANCHOR_KINDS)
        assert min(anchor_counts.values()) >= 140
        assert colors == set(range(1, 10))
        assert len(shapes) >= minimum_shapes[band]
        assert len(positions) >= minimum_positions[band]
        assert len(inputs) >= 500
        assert len(outputs) >= 500


def test_competing_shortcuts_are_falsified_by_lawful_witnesses():
    left = _single_seed_grid(6, 7, 1, 2, 4)
    right = _single_seed_grid(6, 7, 4, 5, 4)
    left_out = MODULE.rule_mirror(left)
    right_out = MODULE.rule_mirror(right)

    # Same dimensions and color but distinct seed positions require distinct answers.
    assert left_out != right_out
    # The output is neither the marker alone, one arm alone, nor a full fill.
    for grid, output in ((left, left_out), (right, right_out)):
        facts, errors = MODULE._scene_analysis(grid)
        assert errors == []
        color = facts["color"]
        nonzero = {(row, col) for row, values in enumerate(output) for col, value in enumerate(values) if value}
        row_only = {(facts["seed_row"], col) for col in range(facts["grid_w"])}
        col_only = {(row, facts["seed_col"]) for row in range(facts["grid_h"])}
        assert nonzero != {(facts["seed_row"], facts["seed_col"])}
        assert nonzero != row_only
        assert nonzero != col_only
        assert nonzero != {
            (row, col)
            for row in range(facts["grid_h"])
            for col in range(facts["grid_w"])
        }
        assert all(value in (0, color) for row in output for value in row)


@pytest.mark.parametrize(
    "grid",
    [
        [],
        [[]],
        [[0, 1], [0]],
        [[0] * 4 for _ in range(3)],
        [[0] * 4 for _ in range(13)],
        [[0] * 4 for _ in range(4)],
        [[1, 1, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
        [[True, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
        [[10, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
        [[-1, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
    ],
)
def test_self_check_rejects_malformed_or_ruleless_impostors(grid):
    assert MODULE.self_check(grid)


def test_generation_is_deterministic_fresh_and_global_rng_isolated():
    random.seed(987654321)
    before = random.getstate()
    for band in (None, "easy", "medium", "hard"):
        first = MODULE.generate(123, 456, difficulty=band)
        second = MODULE.generate(123, 456, difficulty=band)
        pristine = copy.deepcopy(first)
        assert first == second
        assert first is not second
        assert all(left is not right for left, right in zip(first, second))
        first[0][0] = 9 if first[0][0] != 9 else 8
        assert MODULE.generate(123, 456, difficulty=band) == pristine
        assert random.getstate() == before


def test_invalid_difficulty_axes_types_and_ranges_fail_closed():
    with pytest.raises(ValueError):
        MODULE.generate(1, 2, difficulty="extreme")
    with pytest.raises(TypeError):
        MODULE.generate(1, 2, mystery_axis=3)

    invalid_overrides = [
        {"grid_h": 3},
        {"grid_h": 13},
        {"grid_h": True},
        {"grid_w": 3},
        {"grid_w": 13},
        {"grid_w": 5.0},
        {"anchor_kind": "center"},
        {"color": 0},
        {"color": 10},
        {"color": True},
    ]
    for overrides in invalid_overrides:
        with pytest.raises(ValueError):
            MODULE.generate(1, 2, **overrides)
