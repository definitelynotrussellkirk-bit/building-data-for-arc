"""Focused regressions for d336f5fb2da4 canonical generation."""
from __future__ import annotations

from copy import deepcopy

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK = "d336f5fb2da4"
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK, root=ROOT)


def _shape_signature(grid):
    scene = GEN._analyze_grid(grid)
    r0 = min(r for r, _ in scene["source"])
    c0 = min(c for _, c in scene["source"])
    return tuple(sorted((r - r0, c - c0) for r, c in scene["source"]))


def test_every_canonical_pair_is_owned_and_mirrored_exactly():
    pairs = canonical_pairs(TASK, root=ROOT)
    assert len(pairs) == 5
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_generated_lessons_vary_source_vector_and_control_without_invalid_draws():
    for band in ("easy", "medium", "hard"):
        grids = [GEN.generate(424200, i, difficulty=band) for i in range(24)]
        assert all(GEN.self_check(grid, difficulty=band) == [] for grid in grids)
        shapes = {_shape_signature(grid) for grid in grids}
        deltas = {GEN._analyze_grid(grid)["delta"] for grid in grids}
        controls = {GEN._analyze_grid(grid)["control"] for grid in grids}
        assert len(shapes) >= 4, (band, shapes)
        assert len(deltas) >= 6, (band, deltas)
        assert controls == {4, 6, 7}
        for start in range(0, 18, 3):
            demos = [
                {"input": grid, "output": GEN.rule_mirror(grid)}
                for grid in grids[start : start + 3]
            ]
            query_grid = grids[start + 3]
            query = {"input": query_grid, "output": GEN.rule_mirror(query_grid)}
            assert GEN.lesson_identifiable(demos, query) == []


def test_exact_controls_include_substantive_30x30_diagonal_case():
    grid = GEN.generate(
        17,
        8,
        difficulty="hard",
        grid_h=30,
        grid_w=30,
        control_color=6,
        source_profile="asym5",
        vector_profile="diag_down_right",
    )
    assert (len(grid), len(grid[0])) == (30, 30)
    scene = GEN._analyze_grid(grid)
    assert scene["control"] == 6
    assert scene["delta"][0] > 0 and scene["delta"][1] > 0
    assert len(scene["source"]) == 5
    output = GEN.rule_mirror(grid)
    cyan = {(r, c) for r, row in enumerate(output) for c, value in enumerate(row) if value == 8}
    assert len(cyan) >= 20
    assert max(r for r, _ in cyan) - min(r for r, _ in cyan) >= 15
    assert max(c for _, c in cyan) - min(c for _, c in cyan) >= 15
    assert GEN.observe_overrides(grid)["control_color"] == 6


@pytest.mark.parametrize(
    "mutator",
    [
        lambda g: [[0 if value == 1 else value for value in row] for row in g],
        lambda g: [[0 if value == 2 else value for value in row] for row in g],
        lambda g: [[0 if value == 3 else value for value in row] for row in g],
        lambda g: [[0 if value in (4, 6, 7) else value for value in row] for row in g],
    ],
)
def test_self_check_rejects_missing_semantic_roles(mutator):
    grid = GEN.generate(99, 2)
    broken = mutator(deepcopy(grid))
    assert GEN.self_check(broken)


def test_invalid_controls_fail_explicitly():
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 0, control_color=5)
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 0, source_profile="unknown")
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 0, vector_profile="unknown")
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 0, mystery_axis=1)
    with pytest.raises(ValueError):
        GEN.generate(1, 0, difficulty="impossible")
