"""Task-local behavioral regressions for 3020cc038f3f.

Expected answers come from literal canonical outputs or the independent helper
in workspace, not production implementation helpers.  Set GENERATOR_UNDER_TEST
to replay this suite against a retained candidate source.
"""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    canonical_pairs,
    geometry_output,
    load_generator,
    observed,
    shape_statistics_shortcut,
    witness_input,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


@pytest.mark.parametrize("pair", canonical_pairs(), ids=["train0", "train1", "train2", "test0"])
def test_canonical_examples_are_owned_and_oracle_matches(pair):
    original = deepcopy(pair["input"])
    assert gen.self_check(pair["input"]) == []
    assert pair["input"] == original
    assert geometry_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("height,width", [(7, 9), (7, 11), (9, 9), (9, 11)])
@pytest.mark.parametrize("ctrl", [3, 4, 5])
@pytest.mark.parametrize("overlap", ["partial", "identical"])
def test_every_advertised_exact_override_is_constructive_and_observable(
    band, height, width, ctrl, overlap
):
    options = {
        "grid_h": height,
        "grid_w": width,
        "ctrl": ctrl,
        "overlap_kind": overlap,
    }
    grid = gen.generate(413, 29, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options


@pytest.mark.parametrize("key,value", [
    ("__unknown_axis__", 1),
    ("grid_h", 6), ("grid_h", 10), ("grid_h", True), ("grid_h", 7.0), ("grid_h", "7"),
    ("grid_w", 8), ("grid_w", 12), ("grid_w", False),
    ("ctrl", 2), ("ctrl", 6), ("ctrl", True), ("ctrl", "4"),
    ("overlap_kind", "none"), ("overlap_kind", True),
])
def test_invalid_and_unknown_overrides_are_rejected(key, value):
    with pytest.raises(ValueError):
        gen.generate(1, 2, **{key: value})


@pytest.mark.parametrize("difficulty", ["typo", "", True, 3, 0.5])
def test_invalid_difficulty_is_rejected(difficulty):
    with pytest.raises(ValueError):
        gen.generate(1, 2, difficulty=difficulty)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_none_override_uses_the_shared_unset_convention(band):
    baseline = gen.generate(22, 7, difficulty=band)
    for key in gen.AXES:
        assert gen.generate(22, 7, difficulty=band, **{key: None}) == baseline


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_draws_are_valid_reproducible_and_cover_semantics(band):
    controls = set()
    relations = set()
    disagreements = 0
    inputs = set()
    for index in range(180):
        grid = gen.generate(9000 + index, 13 * index + 1, difficulty=band)
        assert gen.self_check(grid) == []
        assert grid == gen.generate(9000 + index, 13 * index + 1, difficulty=band)
        stats = observed(grid)
        controls.add(stats["ctrl"])
        relations.add(stats["overlap_kind"])
        disagreements += geometry_output(grid) != shape_statistics_shortcut(grid)
        inputs.add(repr(grid))
    assert controls == {3, 4, 5}
    assert relations == {"partial", "identical"}
    assert disagreements >= 50
    assert len(inputs) >= 170


def test_declared_shortcut_fits_canonical_but_generated_witness_refutes_it():
    pairs = canonical_pairs()
    assert all(shape_statistics_shortcut(pair["input"]) == pair["output"] for pair in pairs)
    grid = witness_input()
    assert gen.self_check(grid) == []
    assert geometry_output(grid) != shape_statistics_shortcut(grid)
    assert gen.strict_canonical_like(grid) == []
    assert gen.SEMANTIC_WITNESSES["control_not_shape_statistics"](grid)
    assert (
        gen.SEMANTIC_RIVALS["shape_statistics_shortcut"](grid)
        == shape_statistics_shortcut(grid)
    )
    assert "shape_statistics_shortcut" in gen.WITNESS_RIVALS["control_not_shape_statistics"]
    assert "shape_statistics_shortcut" in gen.CANONICAL_SHORTCUTS
    assert "shape_statistics_shortcut" in gen.LESSON_COMPETITORS


@pytest.mark.parametrize("mutation", [
    "unknown_color",
    "extra_control",
    "erase_control",
    "disconnect_color_1",
    "remove_color_2",
    "touch_bounding_boxes",
])
def test_self_check_rejects_destructive_mutations(mutation):
    grid = gen.generate(
        31,
        8,
        grid_h=9,
        grid_w=11,
        ctrl=3,
        overlap_kind="partial",
    )
    if mutation == "unknown_color":
        grid[-1][-1] = 9
    elif mutation == "extra_control":
        grid[-1][-1] = 4
    elif mutation == "erase_control":
        grid[0][0] = 0
    elif mutation == "disconnect_color_1":
        cells = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 1]
        r, c = cells[-1]
        grid[r][c] = 0
        grid[-1][-1] = 1
    elif mutation == "remove_color_2":
        for row in grid:
            for c, value in enumerate(row):
                if value == 2:
                    row[c] = 0
    elif mutation == "touch_bounding_boxes":
        # Extend color 2 through the blank separator until the two operand
        # bounding boxes have no blank row/column between them.
        one = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 1]
        two = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2]
        a = (min(r for r, _ in one), min(c for _, c in one),
             max(r for r, _ in one), max(c for _, c in one))
        b = (min(r for r, _ in two), min(c for _, c in two),
             max(r for r, _ in two), max(c for _, c in two))
        if a[3] < b[1]:
            r, c = next((r, c) for r, c in two if c == b[1])
            for cc in range(a[3] + 1, c):
                grid[r][cc] = 2
        elif b[3] < a[1]:
            r, c = next((r, c) for r, c in two if c == b[3])
            for cc in range(c + 1, a[1]):
                grid[r][cc] = 2
        elif a[2] < b[0]:
            r, c = next((r, c) for r, c in two if r == b[0])
            for rr in range(a[2] + 1, r):
                grid[rr][c] = 2
        else:
            r, c = next((r, c) for r, c in two if r == b[2])
            for rr in range(r + 1, a[0]):
                grid[rr][c] = 2
    assert gen.self_check(grid)


@pytest.mark.parametrize("grid", [
    None,
    [],
    [[]],
    [[0], [0, 0]],
    [[True] * 9 for _ in range(7)],
    [[0.0] * 9 for _ in range(7)],
    [[0] * 8 for _ in range(6)],
])
def test_malformed_grid_returns_diagnostics_not_exceptions(grid):
    errors = gen.self_check(grid)
    assert isinstance(errors, list)
    assert errors
    assert all(isinstance(error, str) and error for error in errors)


def test_oracle_and_observer_do_not_mutate_input():
    grid = gen.generate(77, 12, ctrl=5, overlap_kind="identical")
    original = deepcopy(grid)
    gen.oracle_output(grid)
    gen.observe_overrides(grid)
    gen.self_check(grid)
    assert grid == original


def test_partial_partner_construction_has_no_size_pair_hole_regression():
    """Seed 424 previously drew a 6-cell first shape and impossible 3-cell partner."""
    grid = gen.generate(424, 424 * 17 + 3, difficulty="medium")
    assert gen.self_check(grid) == []
    assert observed(grid)["overlap_kind"] in {"partial", "identical"}
