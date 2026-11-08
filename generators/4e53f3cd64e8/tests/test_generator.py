"""Focused regressions for the legend-ordered component gallery generator."""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "4e53f3cd64e8"
HOME = Path(__file__).resolve().parents[1]
COUNTEREXAMPLES = HOME / "counterexamples"


def _load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
    spec = importlib.util.spec_from_file_location(f"reviewed_{TASK_ID}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()
PAIRS = canonical_pairs(TASK_ID, root=find_root(__file__))


@pytest.mark.parametrize(
    "pair",
    PAIRS,
    ids=lambda pair: f"{pair['split']}{pair['pair_index']}",
)
def test_self_check_accepts_every_canonical_input(pair):
    assert GEN.self_check(pair["input"]) == []


def test_validator_rejects_retained_missing_legend_blob_counterexample():
    import json

    fixture = json.loads(
        (COUNTEREXAMPLES / "missing-legend-component.json").read_text()
    )
    findings = GEN.self_check(fixture["input"])
    assert findings
    assert any("7" in finding and "component" in finding for finding in findings)


def test_rule_hash_is_pinned_to_the_selected_canonical_authority():
    assert GEN.RULE_HASH == "5bdc8d1d0941"


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        {"grid_h": 9, "grid_w": 12, "n_legend": 3, "palette_kind": "cool"},
        {"grid_h": 12, "grid_w": 16, "n_legend": 4, "palette_kind": "warm"},
        {"grid_h": 10, "grid_w": 14, "n_legend": 4, "palette_kind": "varied"},
    ],
)
def test_exact_overrides_round_trip_in_every_band(band, options):
    grid = GEN.generate(17, 9, difficulty=band, **options)
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == options
    assert grid == GEN.generate(17, 9, difficulty=band, **options)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"typo_axis": 1},
        {"grid_h": True},
        {"grid_h": 8},
        {"grid_w": 17},
        {"n_legend": 2},
        {"n_legend": 4.0},
        {"palette_kind": "unknown"},
        {"texture": "missing_legend_blob"},
    ],
)
def test_invalid_or_retired_overrides_are_rejected(kwargs):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **kwargs)


@pytest.mark.parametrize("difficulty", [0, True, 1.0, "unknown"])
def test_invalid_difficulty_is_rejected(difficulty):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, difficulty=difficulty)


@pytest.mark.parametrize("seed", [True, 1.5, "1"])
def test_invalid_seed_is_rejected(seed):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(seed, 0)


@pytest.mark.parametrize("sample_index", [-1, True, 1.5, "1"])
def test_invalid_sample_index_is_rejected(sample_index):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, sample_index)


def test_default_generation_is_lawful_deterministic_and_varied():
    seen = set()
    for band in ("easy", "medium", "hard"):
        for index in range(48):
            grid = GEN.generate(1000 + index, index, difficulty=band)
            assert GEN.self_check(grid) == []
            assert grid == GEN.generate(1000 + index, index, difficulty=band)
            seen.add(tuple(tuple(row) for row in grid))
    assert len(seen) >= 120


def _oracle_components(grid):
    body = grid[2:]
    height, width = len(body), len(body[0])
    seen = set()
    result = []
    for row in range(height):
        for col in range(width):
            if body[row][col] == 0 or (row, col) in seen:
                continue
            color = body[row][col]
            pending = [(row, col)]
            seen.add((row, col))
            cells = []
            while pending:
                rr, cc = pending.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    point = rr + dr, cc + dc
                    if (
                        0 <= point[0] < height
                        and 0 <= point[1] < width
                        and point not in seen
                        and body[point[0]][point[1]] != 0
                    ):
                        seen.add(point)
                        pending.append(point)
            result.append((color, cells))
    return result


def _independent_oracle(grid, order=None):
    legend = [value for value in grid[0] if value]
    order = legend if order is None else list(order)
    by_color = {color: cells for color, cells in _oracle_components(grid)}
    crops = []
    for color in order:
        cells = by_color[color]
        top = min(row for row, _ in cells)
        bottom = max(row for row, _ in cells)
        left = min(col for _, col in cells)
        right = max(col for _, col in cells)
        cell_set = set(cells)
        crops.append(
            [
                [
                    grid[2 + row][col] if (row, col) in cell_set else 0
                    for col in range(left, right + 1)
                ]
                for row in range(top, bottom + 1)
            ]
        )
    out_h = max(map(len, crops))
    out_w = sum(len(crop[0]) for crop in crops) + len(crops) - 1
    output = [[0] * out_w for _ in range(out_h)]
    cursor = 0
    for crop in crops:
        for row, values in enumerate(crop):
            output[row][cursor : cursor + len(values)] = values
        cursor += len(crop[0]) + 1
    return output


@pytest.mark.parametrize(
    "pair",
    PAIRS,
    ids=lambda pair: f"{pair['split']}{pair['pair_index']}",
)
def test_python_rule_mirror_matches_every_canonical_output(pair):
    assert GEN.solve(pair["input"]) == pair["output"]


def test_rule_mirror_matches_an_independent_oracle_on_generated_inputs():
    for band in ("easy", "medium", "hard"):
        for index in range(24):
            grid = GEN.generate(300 + index, index, difficulty=band)
            assert GEN.solve(grid) == _independent_oracle(grid)


def test_profile_anchor_hits_exact_canonical_support_in_every_band():
    canonical_profiles = {
        (len(pair["input"]), len(pair["input"][0]), len(set(sum(pair["input"], []))))
        for pair in PAIRS
    }
    for band in ("easy", "medium", "hard"):
        grid = GEN.generate(90210, 0, difficulty=band)
        profile = (len(grid), len(grid[0]), len(set(sum(grid, []))))
        assert profile in canonical_profiles


def test_generated_inputs_expose_and_refute_both_declared_rivals():
    expected = {
        "read_all_nonzero_legend_cells": "contiguous_prefix_only",
        "preserve_legend_order": "numeric_color_order",
    }
    assert GEN.WITNESS_RIVALS == {
        witness: [rival] for witness, rival in expected.items()
    }
    for index in range(24):
        grid = GEN.generate(700 + index, index, difficulty="medium")
        canonical = _independent_oracle(grid)
        for witness, rival_name in expected.items():
            assert GEN.SEMANTIC_WITNESSES[witness](grid) is True
            assert GEN.SEMANTIC_RIVALS[rival_name](grid) != canonical


def test_generated_lesson_is_identifiable_against_declared_competitors():
    pairs = []
    for index in range(3):
        grid = GEN.generate(800 + index, index, difficulty="hard")
        pairs.append({"input": grid, "output": _independent_oracle(grid)})
    assert GEN.lesson_identifiable(pairs[:2], pairs[2]) == []


def test_retained_semantic_counterexample_refutes_both_rivals():
    import json

    fixture = json.loads(
        (COUNTEREXAMPLES / "legend-gaps-and-order.json").read_text()
    )
    recipe = fixture["recipe"]
    grid = GEN.generate(
        recipe["seed"],
        recipe["sample_index"],
        difficulty=recipe["difficulty"],
        **recipe["overrides"],
    )
    expected = _independent_oracle(grid)
    assert GEN.SEMANTIC_WITNESSES["read_all_nonzero_legend_cells"](grid)
    assert GEN.SEMANTIC_WITNESSES["preserve_legend_order"](grid)
    assert GEN.SEMANTIC_RIVALS["contiguous_prefix_only"](grid) != expected
    assert GEN.SEMANTIC_RIVALS["numeric_color_order"](grid) != expected
