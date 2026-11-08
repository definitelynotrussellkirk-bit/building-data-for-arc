"""Portable regressions for per-component bounding-box framing.

The oracle and component parser are independent of generator helpers. Canonical
labels and actual Racket execution constrain the oracle; generator mirrors never
supply authority labels.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root

TASK_ID = "9bde2c3e0346"
ROOT = find_root(__file__)
SOURCE = Path(__file__).resolve().parents[1] / "generator.py"
SPEC = importlib.util.spec_from_file_location("bbox_frame_subject", SOURCE)
GEN = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(GEN)
CANONICAL = canonical_pairs(TASK_ID, root=ROOT)
CASE_PATH = SOURCE.parent / "counterexamples" / "interior-retention-shortcut" / "case.json"
CASE = json.loads(CASE_PATH.read_text())


def components(grid):
    """Four-connected, same-color components in row-major discovery order."""
    pending = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    }
    groups = []
    while pending:
        start = min(pending)
        color = grid[start[0]][start[1]]
        pending.remove(start)
        stack = [start]
        cells = {start}
        while stack:
            r, c = stack.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in pending and grid[point[0]][point[1]] == color:
                    pending.remove(point)
                    stack.append(point)
                    cells.add(point)
        groups.append((color, cells))
    return groups


def bbox_frame(cells):
    top = min(r for r, _ in cells)
    bottom = max(r for r, _ in cells)
    left = min(c for _, c in cells)
    right = max(c for _, c in cells)
    return (
        {(top, c) for c in range(left, right + 1)}
        | {(bottom, c) for c in range(left, right + 1)}
        | {(r, left) for r in range(top, bottom + 1)}
        | {(r, right) for r in range(top, bottom + 1)}
    )


def oracle(grid):
    result = [[0] * len(grid[0]) for _ in grid]
    for color, cells in components(grid):
        for r, c in bbox_frame(cells):
            result[r][c] = color
    return result


def keep_original_interior_rival(grid):
    result = oracle(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                result[r][c] = value
    return result


def witness_grid():
    return copy.deepcopy(CASE["input"])


@pytest.mark.parametrize(
    "pair",
    CANONICAL,
    ids=lambda p: f"v{p['variant']}-{p['split']}-{p['pair_index']}",
)
def test_canonical_inputs_are_accepted_and_match_independent_oracle(pair):
    assert GEN.self_check(pair["input"]) == []
    assert oracle(pair["input"]) == pair["output"]


def test_contract_is_small_exact_and_pinned_to_selected_authority():
    assert GEN.RULE_HASH == "8f9e53b42241"
    assert GEN.VERSION == "3.0.0"
    assert set(GEN.AXES) == {"grid_h", "grid_w", "n_objects"}
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert not hasattr(GEN, "DEGENERATE_TEXTURES")


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_joint_exact_overrides_are_observable_in_every_band(band):
    requested = {"grid_h": 12, "grid_w": 11, "n_objects": 3}
    for index in range(4):
        grid = GEN.generate(71, index, difficulty=band, **requested)
        assert GEN.self_check(grid, difficulty=band) == []
        assert GEN.observe_overrides(grid) == requested
        assert len(components(grid)) == 3
        assert grid == GEN.generate(71, index, difficulty=band, **requested)


@pytest.mark.parametrize(
    "key,value",
    [
        ("palette_kind", "warm"),
        ("texture", "all_solid_rects"),
        ("n_blobs", 2),
        ("palette_size", 2),
        ("position_bias", "fixed"),
        ("density", "sparse"),
        ("unknown_axis", 1),
    ],
)
def test_removed_and_unknown_controls_fail_closed(key, value):
    assert key not in GEN.AXES
    with pytest.raises(ValueError):
        GEN.generate(5, 0, **{key: value})


@pytest.mark.parametrize(
    "key,value",
    [
        ("grid_h", 7), ("grid_h", 13), ("grid_h", True),
        ("grid_h", 9.0), ("grid_h", "9"),
        ("grid_w", 7), ("grid_w", 13), ("grid_w", False),
        ("grid_w", 9.0), ("grid_w", "9"),
        ("n_objects", 1), ("n_objects", 4), ("n_objects", True),
        ("n_objects", 2.0), ("n_objects", "2"),
    ],
)
def test_exact_controls_reject_out_of_range_or_noninteger_values(key, value):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(5, 0, **{key: value})


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_generated_population_teaches_adding_and_clearing(band):
    for index in range(32):
        grid = GEN.generate(2026, index, difficulty=band)
        expected = oracle(grid)
        assert GEN.self_check(grid, difficulty=band) == []
        assert GEN.strict_canonical_like(grid) == []
        assert GEN.SEMANTIC_WITNESSES["adds_missing_border"](grid)
        assert GEN.SEMANTIC_WITNESSES["clears_original_interior"](grid)
        assert GEN.rule_mirror(grid) == expected
        for name, rival in GEN.SEMANTIC_RIVALS.items():
            assert rival(grid) != expected, name


def test_declared_canonical_shortcut_really_fits_every_canonical_pair():
    assert set(GEN.CANONICAL_SHORTCUTS) == {"add_frame_keep_interior"}
    rival = GEN.CANONICAL_SHORTCUTS["add_frame_keep_interior"]
    assert all(rival(pair["input"]) == pair["output"] for pair in CANONICAL)


def test_retained_interior_counterexample_changes_the_shortcut_prediction():
    grid = witness_grid()
    expected = oracle(grid)
    assert CASE["generator_sha256"] == hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    assert CASE["racket_output"] == expected
    assert GEN.self_check(grid) == []
    assert expected[2][2] == 0
    assert CASE["rival_output"][2][2] == 4
    assert keep_original_interior_rival(grid) == CASE["rival_output"]
    assert GEN.CANONICAL_SHORTCUTS["add_frame_keep_interior"](grid) != expected


def test_lesson_hook_rejects_survivors_and_accepts_witnessed_lesson():
    grid = witness_grid()
    pair = {"input": grid, "output": oracle(grid)}
    assert GEN.lesson_identifiable([pair], {"input": grid}) == []
    bad = {"input": grid, "output": keep_original_interior_rival(grid)}
    assert GEN.lesson_identifiable([bad], {"input": grid})


def test_self_check_rejects_malformed_grids_without_raising():
    valid = witness_grid()
    malformed = [
        [],
        [[0, 0], [0]],
        [[0] * 8 for _ in range(7)],
        [[0] * 13 for _ in range(8)],
        [[0] * 8 for _ in range(8)],
        copy.deepcopy(valid),
    ]
    malformed[-1][0][0] = 10
    for grid in malformed:
        errors = GEN.self_check(grid)
        assert isinstance(errors, list) and errors
        assert all(isinstance(error, str) and error for error in errors)


def test_actual_racket_matches_independent_oracle_on_canonical_and_generated_grids():
    grids = [pair["input"] for pair in CANONICAL]
    grids.extend(
        GEN.generate(903 + band_index, index, difficulty=band)
        for band_index, band in enumerate(("easy", "medium", "hard"))
        for index in range(3)
    )
    receipt = Catalog(ROOT).apply(TASK_ID, grids, reference="canonical", timeout=180)
    assert receipt["rule_hash_matches_catalog"] is True
    assert receipt["executed_rule_hash"] == "8f9e53b42241"
    assert [row["output"] for row in receipt["results"]] == [oracle(grid) for grid in grids]
