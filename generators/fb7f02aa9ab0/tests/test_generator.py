"""Task-local regression tests for fb7f02aa9ab0."""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK = "fb7f02aa9ab0"
HOME = Path(__file__).resolve().parents[1]


def _load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py")).resolve()
    spec = importlib.util.spec_from_file_location("reviewed_fb7f02aa9ab0", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


@pytest.mark.parametrize(
    "pair",
    canonical_pairs(TASK, root=find_root(__file__)),
    ids=lambda pair: f"{pair['split']}{pair['pair_index']}",
)
def test_self_check_accepts_every_canonical_input(pair):
    assert gen.self_check(pair["input"]) == []


def _norm(grid, color):
    cells = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color}
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return {(r - r0, c - c0) for r, c in cells}


@pytest.mark.parametrize(
    "control_position,control_color,relation_kind,origin_kind",
    [
        ("top_left", 3, "partial", "corner"),
        ("top_right", 4, "a_subset_b", "split"),
        ("bottom_left", 6, "b_subset_a", "corner"),
        ("bottom_right", 3, "partial", "split"),
    ],
)
def test_exact_structural_overrides_are_visible(
    control_position, control_color, relation_kind, origin_kind
):
    expected = {
        "grid_h": 9,
        "grid_w": 13,
        "control_color": control_color,
        "control_position": control_position,
        "relation_kind": relation_kind,
        "origin_kind": origin_kind,
    }
    grid = gen.generate(91, 7, difficulty="hard", **expected)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == expected

    a, b = _norm(grid, 1), _norm(grid, 2)
    if relation_kind == "partial":
        assert a & b and a - b and b - a
    elif relation_kind == "a_subset_b":
        assert a < b
    else:
        assert b < a
    assert ((0, 0) in a and (0, 0) in b) is (origin_kind == "corner")


@pytest.mark.parametrize("seed", [0, 1, 17, 91])
def test_consecutive_lesson_indices_cover_the_teaching_schedule(seed):
    observed = [gen.observe_overrides(gen.generate(seed, index)) for index in range(4)]
    assert {row["control_color"] for row in observed[:3]} == {3, 4, 6}
    assert {row["relation_kind"] for row in observed[:3]} == {
        "partial",
        "a_subset_b",
        "b_subset_a",
    }
    assert {row["origin_kind"] for row in observed[:2]} == {"corner", "split"}
    assert {row["control_position"] for row in observed} == {
        "top_left",
        "top_right",
        "bottom_left",
        "bottom_right",
    }


@pytest.mark.parametrize(
    "pair",
    canonical_pairs(TASK, root=find_root(__file__)),
    ids=lambda pair: f"oracle-{pair['split']}{pair['pair_index']}",
)
def test_python_semantic_oracle_matches_canonical_outputs(pair):
    assert gen._reference_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("control_color", [3, 4, 6])
def test_declared_fixed_operation_rivals_are_real_counterexamples(control_color):
    grid = gen.generate(
        708,
        control_color,
        grid_h=9,
        grid_w=13,
        control_color=control_color,
        relation_kind="partial",
        origin_kind="split",
    )
    expected = gen._reference_output(grid)
    names = {3: ("intersection_only", "xor_only"), 4: ("union_only", "xor_only"), 6: ("union_only", "intersection_only")}[control_color]
    witness = {3: "union_control", 4: "intersection_control", 6: "xor_control"}[control_color]
    assert gen.SEMANTIC_WITNESSES[witness](grid)
    assert set(gen.WITNESS_RIVALS[witness]) == set(names)
    for name in names:
        assert gen.SEMANTIC_RIVALS[name](grid) != expected


def test_independent_normalization_witness_refutes_absolute_coordinates():
    grid = gen.generate(
        809,
        2,
        grid_h=9,
        grid_w=13,
        control_color=4,
        relation_kind="partial",
        origin_kind="split",
    )
    expected = gen._reference_output(grid)
    assert gen.SEMANTIC_WITNESSES["independent_normalization"](grid)
    assert gen.SEMANTIC_RIVALS["absolute_coordinates"](grid) != expected
    assert grid == gen.generate(
        809,
        2,
        grid_h=9,
        grid_w=13,
        control_color=4,
        relation_kind="partial",
        origin_kind="split",
    )


def test_difficulty_bands_are_observably_distinct_without_losing_core_sizes():
    grids = [gen.generate(0, 0, difficulty=band) for band in ("easy", "medium", "hard")]
    assert len({tuple(map(tuple, grid)) for grid in grids}) == 3
    for band in ("easy", "medium", "hard"):
        sizes = {
            (len(gen.generate(seed, index, difficulty=band)), len(gen.generate(seed, index, difficulty=band)[0]))
            for index, seed in enumerate(range(20))
        }
        assert any(h <= 10 and w <= 13 for h, w in sizes)
