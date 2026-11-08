"""Task-local regressions for the single-color rectangle-corner sampler."""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest


HOME = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
SPEC = importlib.util.spec_from_file_location("generator_under_test_da16c00eed25", SOURCE)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def geometry(grid):
    cells = [(r, c, value) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    assert len(cells) == 3
    colors = {value for _, _, value in cells}
    assert len(colors) == 1
    rows = sorted({r for r, _, _ in cells})
    cols = sorted({c for _, c, _ in cells})
    assert len(rows) == len(cols) == 2
    present = {(r, c) for r, c, _ in cells}
    corners = [(rows[0], cols[0]), (rows[0], cols[1]), (rows[1], cols[0]), (rows[1], cols[1])]
    missing = next(index for index, point in enumerate(corners) if point not in present)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "row_gap": rows[1] - rows[0],
        "col_gap": cols[1] - cols[0],
        "missing_corner": missing,
        "corner_color": next(iter(colors)),
        "rows": rows,
        "cols": cols,
    }


def complete_rectangle(grid):
    out = [list(row) for row in grid]
    info = geometry(grid)
    point = [
        (info["rows"][0], info["cols"][0]),
        (info["rows"][0], info["cols"][1]),
        (info["rows"][1], info["cols"][0]),
        (info["rows"][1], info["cols"][1]),
    ][info["missing_corner"]]
    out[point[0]][point[1]] = info["corner_color"]
    return out


def test_adjacent_gaps_are_exact_observable_overrides():
    grid = GEN.generate(
        11,
        7,
        grid_h=4,
        grid_w=4,
        row_gap=1,
        col_gap=1,
        missing_corner=0,
        corner_color=9,
    )
    expected = {
        "grid_h": 4,
        "grid_w": 4,
        "row_gap": 1,
        "col_gap": 1,
        "missing_corner": 0,
        "corner_color": 9,
    }
    actual = geometry(grid)
    assert {name: actual[name] for name in expected} == expected
    assert GEN.observe_overrides(grid) == expected
    assert GEN.self_check(grid) == []


def test_unknown_and_invalid_overrides_are_rejected():
    with pytest.raises(ValueError):
        GEN.generate(0, 0, typo_axis=1)
    with pytest.raises(ValueError):
        GEN.generate(0, 0, grid_h=True)
    with pytest.raises(ValueError):
        GEN.generate(0, 0, row_gap=0)
    with pytest.raises(ValueError):
        GEN.generate(0, 0, grid_h=4, row_gap=4)


def test_self_check_accepts_canonical_geometry_and_rejects_mutations():
    canonical = [
        [0, 0, 0, 0],
        [0, 4, 4, 0],
        [0, 4, 0, 0],
        [0, 0, 0, 0],
    ]
    assert hasattr(GEN, "self_check")
    assert GEN.self_check(canonical) == []
    assert GEN.self_check([[0] * 4 for _ in range(4)])
    all_four = [row[:] for row in canonical]
    all_four[2][2] = 4
    assert GEN.self_check(all_four)
    mixed = [row[:] for row in canonical]
    mixed[1][2] = 7
    assert GEN.self_check(mixed)


def test_default_distribution_covers_adjacent_top_left_and_all_missing_corners():
    adjacent_row = adjacent_col = touches_top = touches_left = False
    missing = set()
    for index in range(256):
        grid = GEN.generate(9000 + index, index, difficulty=("easy", "medium", "hard")[index % 3])
        info = geometry(grid)
        assert GEN.self_check(grid) == []
        adjacent_row |= info["row_gap"] == 1
        adjacent_col |= info["col_gap"] == 1
        touches_top |= info["rows"][0] == 0
        touches_left |= info["cols"][0] == 0
        missing.add(info["missing_corner"])
    assert adjacent_row and adjacent_col
    assert touches_top and touches_left
    assert missing == {0, 1, 2, 3}


def test_declared_shortcuts_fit_canonical_style_but_generated_witnesses_refute_them():
    assert set(GEN.CANONICAL_SHORTCUTS) >= {"min_gap_two", "bottom_missing_only", "interior_only"}
    adjacent = GEN.generate(3, 4, grid_h=4, grid_w=4, row_gap=1, col_gap=1, missing_corner=0)
    intended = complete_rectangle(adjacent)
    assert GEN.SEMANTIC_WITNESSES["adjacent_gap"](adjacent)
    assert GEN.CANONICAL_SHORTCUTS["min_gap_two"](adjacent) != intended

    top_missing = GEN.generate(5, 6, grid_h=6, grid_w=7, row_gap=3, col_gap=3, missing_corner=0)
    intended = complete_rectangle(top_missing)
    assert GEN.SEMANTIC_WITNESSES["top_missing"](top_missing)
    assert GEN.CANONICAL_SHORTCUTS["bottom_missing_only"](top_missing) != intended

    edge = None
    for index in range(128):
        candidate = GEN.generate(700 + index, index)
        if GEN.SEMANTIC_WITNESSES["edge_touching"](candidate):
            edge = candidate
            break
    assert edge is not None
    assert GEN.CANONICAL_SHORTCUTS["interior_only"](edge) != complete_rectangle(edge)


def test_every_cyclic_four_demo_lesson_refutes_all_declared_shortcuts():
    assert hasattr(GEN, "lesson_identifiable")
    assert hasattr(GEN, "schedule_profile")
    assert set(GEN.LESSON_COMPETITORS) == set(GEN.CANONICAL_SHORTCUTS)

    period = len(GEN.SCHEDULE_PROFILES)
    assert period == GEN.EXAMPLES_NEEDED
    for band in ("easy", "medium", "hard"):
        for start in range(period):
            demos = []
            for sample_index in range(start, start + GEN.EXAMPLES_NEEDED):
                grid = GEN.generate(424242, sample_index, difficulty=band)
                demos.append({"input": grid, "output": complete_rectangle(grid)})
            query_grid = GEN.generate(
                424242, start + GEN.EXAMPLES_NEEDED, difficulty=band
            )
            query = {"input": query_grid, "output": complete_rectangle(query_grid)}

            assert GEN.lesson_identifiable(demos, query) == []
            for name, rival in GEN.CANONICAL_SHORTCUTS.items():
                assert any(
                    rival(demo["input"]) != demo["output"] for demo in demos
                ), f"{band=} {start=} did not refute {name}"
