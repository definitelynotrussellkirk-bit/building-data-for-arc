"""Focused regression tests for generator 1b7191b100da."""
from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

import pytest


MODULE = importlib.import_module(
    "puzzle_generators.per_puzzle.1b7191b100da.generator"
)
ROOT = Path(__file__).resolve().parents[1]


def _canonical_row() -> dict:
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            if '"content_hash": "1b7191b100da"' in line:
                return json.loads(line)
    raise AssertionError("canonical task row not found")


def test_rule_hash_and_canonical_inputs_are_accepted() -> None:
    assert MODULE.RULE_HASH == "90961ca428e3"
    row = _canonical_row()
    inputs = [pair["input"] for split in ("train", "test") for pair in row[split]]
    assert len(inputs) == 4
    for grid in inputs:
        assert MODULE.self_check(grid) == []
        assert MODULE.strict_canonical_like(grid) == []


def test_exact_override_boundaries_are_observable_and_unknowns_reject() -> None:
    cases = [
        {
            "grid_h": 8,
            "grid_w": 9,
            "n_9": 1,
            "template_h": 2,
            "template_w": 2,
            "template_color": 1,
        },
        {
            "grid_h": 11,
            "grid_w": 12,
            "n_9": 4,
            "template_h": 4,
            "template_w": 4,
            "template_color": 8,
        },
    ]
    for difficulty in ("easy", "medium", "hard"):
        for case in cases:
            grid = MODULE.generate(91, 7, difficulty=difficulty, **case)
            assert (len(grid), len(grid[0])) == (case["grid_h"], case["grid_w"])
            observed = MODULE.observe_overrides(grid)
            for key in ("n_9", "template_h", "template_w", "template_color"):
                assert observed[key] == case[key]
    with pytest.raises(ValueError, match="unknown override"):
        MODULE.generate(1, 0, typo_axis=3)


def test_self_check_rejects_targeted_impostors() -> None:
    grid = MODULE.generate(
        1234,
        2,
        difficulty="hard",
        n_9=4,
        template_h=4,
        template_w=4,
        template_color=6,
    )
    assert MODULE.self_check(grid) == []

    no_markers = [[0 if value == 9 else value for value in row] for row in grid]
    assert any("marker" in reason for reason in MODULE.self_check(no_markers))

    solid_bbox = copy.deepcopy(grid)
    cells, _, (r0, c0, r1, c1) = MODULE._template_info(solid_bbox)
    color = solid_bbox[cells[0][0]][cells[0][1]]
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            if solid_bbox[r][c] == 0:
                solid_bbox[r][c] = color
    assert any("solid" in reason for reason in MODULE.self_check(solid_bbox))

    multicolor = copy.deepcopy(grid)
    tr, tc = cells[0]
    multicolor[tr][tc] = 1 if color != 1 else 2
    assert any("monochrome" in reason for reason in MODULE.self_check(multicolor))

    marker_inside_bbox = copy.deepcopy(grid)
    hole = next(
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if marker_inside_bbox[r][c] == 0
    )
    marker_inside_bbox[hole[0]][hole[1]] = 9
    assert any(
        "inside the template" in reason
        for reason in MODULE.self_check(marker_inside_bbox)
    )


def test_every_four_demo_window_identifies_the_query_rule() -> None:
    for difficulty in ("easy", "medium", "hard"):
        for start in range(20):
            pairs = []
            for sample_index in range(start, start + 5):
                grid = MODULE.generate(
                    seed=50_000 + sample_index,
                    sample_index=sample_index,
                    difficulty=difficulty,
                )
                pairs.append({"input": grid, "output": MODULE._true_output(grid)})
            assert MODULE.lesson_identifiable(pairs[:4], pairs[4]) == []


def test_deterministic_fresh_returns_and_global_rng_purity() -> None:
    random.seed(20260726)
    before = random.getstate()
    first = MODULE.generate(77, 11, difficulty="medium")
    middle = random.getstate()
    second = MODULE.generate(77, 11, difficulty="medium")
    after = random.getstate()
    assert before == middle == after
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
