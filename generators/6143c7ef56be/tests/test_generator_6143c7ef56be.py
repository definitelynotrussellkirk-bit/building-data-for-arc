from __future__ import annotations

from collections import Counter
import hashlib
import importlib
import json
from pathlib import Path
import random

import pytest

from reviewer_support import (
    canonical_pairs as load_canonical_pairs,
    canonical_path,
    find_root,
)


ROOT = find_root(__file__)
MODULE = importlib.import_module("puzzle_generators.per_puzzle.6143c7ef56be.generator")


def _data_path(relative: str) -> Path:
    for prefix in (Path(), Path("shared")):
        candidate = ROOT / prefix / relative
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"missing {relative} beneath {ROOT}")


BASE_FILES = (
    _data_path("data/base/solutions/training/d89b689b__6143c7ef56be.json"),
    _data_path("data/base/solutions/augmented/d89b689b__d73bf975ba48.json"),
)


def frozen(grid):
    return tuple(tuple(row) for row in grid)


def canonical_rows():
    rows = []
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == MODULE.TASK_ID:
                rows.append(row)
    return rows


def canonical_pairs():
    return load_canonical_pairs(MODULE.TASK_ID, root=ROOT, labeled_only=True)


def independent_rule(grid):
    height, width = len(grid), len(grid[0])
    cyan = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 8
    ]
    block_row = min(row for row, _ in cyan)
    block_col = min(col for _, col in cyan)
    output = [[0] * width for _ in range(height)]
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color in (0, 8):
                continue
            out_row = block_row if row < block_row else block_row + 1
            out_col = block_col if col < block_col else block_col + 1
            output[out_row][out_col] = color
    return output


def marker_cells(grid):
    return [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value not in (0, 8)
    ]


def test_all_canonical_rows_and_pairs_match_exact_rule():
    assert len(canonical_rows()) == 2
    assert len(canonical_pairs()) == 8
    for pair in canonical_pairs():
        before = json.loads(json.dumps(pair["input"]))
        assert MODULE.self_check(pair["input"]) == []
        assert MODULE.rule_mirror(pair["input"]) == independent_rule(pair["input"]) == pair["output"]
        assert pair["input"] == before
        output_nonzero = [
            (row, col, value)
            for row, values in enumerate(pair["output"])
            for col, value in enumerate(values)
            if value != 0
        ]
        assert len(output_nonzero) == 4
        assert all(value != 8 for _, _, value in output_nonzero)


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
@pytest.mark.parametrize("layout", MODULE.MARKER_LAYOUTS)
def test_every_layout_override_is_exact_observable_and_semantically_live(layout, difficulty):
    for seed in range(10):
        grid = MODULE.generate(
            10_000 + seed,
            seed * 17 + 3,
            difficulty=difficulty,
            marker_layout=layout,
        )
        observed = MODULE.observe_overrides(grid)
        assert observed["marker_layout"] == layout
        assert MODULE.self_check(grid, meta={"overrides": {"marker_layout": layout}}) == []
        output = MODULE.rule_mirror(grid)
        assert output == independent_rule(grid)
        facts = MODULE._analyze(grid)
        block_cells = {
            (facts["block_row"], facts["block_col"]),
            (facts["block_row"], facts["block_col"] + 1),
            (facts["block_row"] + 1, facts["block_col"]),
            (facts["block_row"] + 1, facts["block_col"] + 1),
        }
        assert {
            (row, col)
            for row, values in enumerate(output)
            for col, value in enumerate(values)
            if value != 0
        } == block_cells
        assert all(output[row][col] == 0 for row, col in facts["marker_positions"].values())


def test_exact_numeric_boundary_overrides_and_dependent_rejections():
    valid_calls = (
        {"grid_h": 8, "grid_w": 8, "block_row": 2, "block_col": 2},
        {"grid_h": 18, "grid_w": 18, "block_row": 14, "block_col": 14},
        {"grid_h": 8, "grid_w": 18, "block_row": 4, "block_col": 14},
        {"grid_h": 18, "grid_w": 8, "block_row": 14, "block_col": 4},
    )
    for overrides in valid_calls:
        for layout in MODULE.MARKER_LAYOUTS:
            expected = {**overrides, "marker_layout": layout}
            grid = MODULE.generate(29, 31, **expected)
            assert MODULE.observe_overrides(grid) == expected
            assert MODULE.self_check(grid, meta={"overrides": expected}) == []

    with pytest.raises(ValueError):
        MODULE.generate(1, 0, grid_h=8, block_row=5)
    with pytest.raises(ValueError):
        MODULE.generate(1, 0, grid_w=8, block_col=5)


def test_default_distribution_covers_all_layouts_and_nonshortcut_geometry():
    for difficulty in ("easy", "medium", "hard"):
        grids = [
            MODULE.generate(40_000 + seed, seed * 23 + 5, difficulty=difficulty)
            for seed in range(240)
        ]
        analyses = [MODULE._analyze(grid) for grid in grids]
        layouts = Counter(item["marker_layout"] for item in analyses)
        assert set(layouts) == set(MODULE.MARKER_LAYOUTS)
        assert min(layouts.values()) >= 35
        assert all(item["errors"] == [] for item in analyses)
        assert len({frozen(grid) for grid in grids}) >= 235
        assert len({frozen(MODULE.rule_mirror(grid)) for grid in grids}) >= 225
        independent = [item for item in analyses if item["marker_layout"] == "independent"]
        assert independent
        assert any(
            len({pos[0] for pos in item["marker_positions"].values()}) == 4
            for item in independent
        )
        assert any(
            len({pos[1] for pos in item["marker_positions"].values()}) == 4
            for item in independent
        )


def test_self_check_rejects_targeted_semantic_impostors():
    valid = MODULE.generate(91, 7, grid_h=12, grid_w=13, block_row=5, block_col=6)
    assert MODULE.self_check(valid) == []
    facts = MODULE._analyze(valid)

    extra_cyan = [row[:] for row in valid]
    extra_cyan[0][0] = 8
    assert any("exactly four cyan" in error for error in MODULE.self_check(extra_cyan))

    broken_block = [row[:] for row in valid]
    br, bc = facts["block_row"], facts["block_col"]
    broken_block[br + 1][bc + 1] = 0
    broken_block[br + 2][bc + 1] = 8
    assert any("solid 2x2" in error for error in MODULE.self_check(broken_block))

    duplicate_color = [row[:] for row in valid]
    cells = marker_cells(duplicate_color)
    duplicate_color[cells[1][0]][cells[1][1]] = cells[0][2]
    assert any("pairwise distinct" in error for error in MODULE.self_check(duplicate_color))

    missing_marker = [row[:] for row in valid]
    row, col, _ = marker_cells(missing_marker)[0]
    missing_marker[row][col] = 0
    assert any("exactly four marker" in error for error in MODULE.self_check(missing_marker))

    nonquadrant_marker = [row[:] for row in valid]
    row, col, color = marker_cells(nonquadrant_marker)[0]
    nonquadrant_marker[row][col] = 0
    nonquadrant_marker[br][0] = color
    errors = MODULE.self_check(nonquadrant_marker)
    assert any("strict block-relative quadrant" in error for error in errors)
    assert any("missing marker quadrant" in error for error in errors)

    two_in_one_quadrant = [row[:] for row in valid]
    positions = facts["marker_positions"]
    tr_row, tr_col = positions["tr"]
    color = two_in_one_quadrant[tr_row][tr_col]
    two_in_one_quadrant[tr_row][tr_col] = 0
    tl_row, tl_col = positions["tl"]
    target_col = next(col for col in range(bc) if col != tl_col)
    two_in_one_quadrant[tl_row][target_col] = color
    errors = MODULE.self_check(two_in_one_quadrant)
    assert any("more than one marker" in error for error in errors)
    assert any("missing marker quadrant" in error for error in errors)


def test_determinism_fresh_returns_input_purity_and_global_rng_isolation():
    random.seed(9157)
    state = random.getstate()
    first = MODULE.generate(101, 13, difficulty="hard", marker_layout="independent")
    assert random.getstate() == state
    second = MODULE.generate(101, 13, difficulty="hard", marker_layout="independent")
    assert first == second and first is not second and first[0] is not second[0]
    before = [row[:] for row in first]
    expected = MODULE.rule_mirror(first)
    assert first == before
    first[0][0] = 9
    assert MODULE.generate(101, 13, difficulty="hard", marker_layout="independent") == second
    assert MODULE.rule_mirror(second) == expected


def test_axis_contract_is_literal_minimal_and_unknown_controls_reject():
    assert set(MODULE.AXES) == {
        "grid_h", "grid_w", "block_row", "block_col", "marker_layout"
    }
    assert tuple(MODULE.AXES["marker_layout"]["valid"].split("|")) == MODULE.MARKER_LAYOUTS
    with pytest.raises(ValueError):
        MODULE.generate(1, 0, marker_layout="diagonal")
    with pytest.raises(ValueError):
        MODULE.generate(1, 0, texture="no_markers")
    with pytest.raises(ValueError):
        MODULE.generate(1, 0, difficulty="expert")


def test_rule_hash_and_task_local_authorities_are_exactly_synchronized():
    programs = {row["program_solution"] for row in canonical_rows()}
    assert len(programs) == 1
    canonical = programs.pop()
    digest = hashlib.sha256(" ".join(canonical.split()).encode()).hexdigest()[:12]
    assert MODULE.RULE_HASH == digest == "9c659fa323b2"
    for path in BASE_FILES:
        target = json.loads(path.read_text())["racket_target"]
        assert " ".join(target["raw_code"].split()) == " ".join(canonical.split())
        assert " ".join(target["target_code"].split()) == " ".join(canonical.split())
