"""Focused regression tests for generator 9758187b19ad."""
from __future__ import annotations

import copy
import importlib
import json
import sys
from pathlib import Path

import pytest


TASK_ID = "9758187b19ad"
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.9758187b19ad.generator"
)


def _canonical_inputs():
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") != TASK_ID:
            continue
        for pair in row["train"]:
            yield pair["input"]
        test = row["test"] if isinstance(row["test"], list) else [row["test"]]
        for pair in test:
            yield pair["input"]


def test_rule_hash_and_color6_mapping_are_pinned():
    assert GEN.RULE_HASH == "bb29b95b6fe8"
    grid = GEN.generate(101, 0, difficulty="easy")
    assert GEN._solve_candidate(grid) != GEN._solve_candidate(
        grid, color6_transpose=True
    )


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_all_declared_axes_are_exactly_observable(difficulty):
    for h in (12, 18):
        for w in (19, 24):
            for n_markers in (4, 6):
                grid = GEN.generate(
                    202,
                    5,
                    difficulty=difficulty,
                    grid_h=h,
                    grid_w=w,
                    n_markers=n_markers,
                )
                assert GEN.observe_overrides(grid) == {
                    "grid_h": h,
                    "grid_w": w,
                    "n_markers": n_markers,
                }
                assert GEN.self_check(grid) == []


def test_unknown_override_is_rejected():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, typo_axis=7)


def test_canonical_inputs_are_accepted():
    inputs = list(_canonical_inputs())
    assert len(inputs) == 3
    assert [GEN.self_check(grid) for grid in inputs] == [[], [], []]


def test_structural_mutations_are_rejected():
    grid = GEN.generate(303, 1, difficulty="medium")
    assert GEN.self_check(grid) == []

    # 1. Delete the only color-6 marker.
    missing_code = copy.deepcopy(grid)
    for r, row in enumerate(missing_code):
        for c, value in enumerate(row):
            if value == 6:
                missing_code[r][c] = 0
                break
        else:
            continue
        break
    assert any("missing marker code" in err for err in GEN.self_check(missing_code))

    # 2. Collapse the stencil palette to one color.
    monochrome = copy.deepcopy(grid)
    for r, row in enumerate(monochrome):
        for c, value in enumerate(row):
            if value in GEN._TEMPLATE_COLORS:
                monochrome[r][c] = 1
    assert any("exactly four colors" in err for err in GEN.self_check(monochrome))

    # 3. Put a rotation marker at the bottom-right so its stamp exits the grid.
    out_of_bounds = copy.deepcopy(grid)
    for r, row in enumerate(out_of_bounds):
        for c, value in enumerate(row):
            if value == 6:
                out_of_bounds[r][c] = 0
    out_of_bounds[-1][-1] = 6
    assert any("out of bounds" in err for err in GEN.self_check(out_of_bounds))

    # 4. Move a marker into another marker's stamp box.
    overlapping = copy.deepcopy(grid)
    markers = [
        (r, c, value)
        for r, row in enumerate(overlapping)
        for c, value in enumerate(row)
        if value in GEN._MARKER_COLORS
    ]
    r0, c0, _ = markers[0]
    r1, c1, color1 = markers[1]
    overlapping[r1][c1] = 0
    overlapping[r0][c0 + 1] = color1
    assert any("overlaps" in err for err in GEN.self_check(overlapping))


def test_schedule_covers_shape_and_anchor_branches():
    grids = [GEN.generate(404, i, difficulty="hard") for i in range(6)]
    assert {GEN.schedule_profile(404, i, "hard") for i in range(6)} == set(
        GEN.SCHEDULE_PROFILES
    )
    assert any(GEN.SEMANTIC_WITNESSES["square_template"](g) for g in grids)
    assert any(GEN.SEMANTIC_WITNESSES["non_square_template"](g) for g in grids)
    assert any(GEN.SEMANTIC_WITNESSES["empty_top_left_anchor"](g) for g in grids)
    assert all(GEN.SEMANTIC_WITNESSES["all_four_transforms_distinct"](g) for g in grids)


def test_fresh_returns_and_determinism():
    first = GEN.generate(505, 2, difficulty="easy")
    second = GEN.generate(505, 2, difficulty="easy")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert first != second


def test_generation_does_not_mutate_process_global_random_state():
    import random

    random.seed(8675309)
    before = random.getstate()
    GEN.generate(606, 3, difficulty="medium", grid_h=18, grid_w=24, n_markers=6)
    after = random.getstate()
    assert after == before
