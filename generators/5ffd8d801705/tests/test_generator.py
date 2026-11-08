"""Source-bound regressions for the 2x2-to-main-diagonal generator."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
SPEC = importlib.util.spec_from_file_location("generator_under_test", SOURCE)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)

TASK_ID = "5ffd8d801705"


def _canonical_row() -> dict:
    from reviewer_support import canonical_path, find_root

    with canonical_path(find_root(__file__)).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise KeyError(TASK_ID)


def _canonical_pairs() -> list[dict]:
    row = _canonical_row()
    return [pair for split in ("train", "test") for pair in row[split]]


def _solid_blocks(grid: list[list[int]]) -> list[tuple[int, int, int]]:
    """Return all solid monochrome 2x2 windows as (row, col, color)."""
    h, w = len(grid), len(grid[0])
    out = []
    for r in range(h - 1):
        for c in range(w - 1):
            color = grid[r][c]
            if color and all(
                grid[rr][cc] == color
                for rr, cc in ((r, c + 1), (r + 1, c), (r + 1, c + 1))
            ):
                out.append((r, c, color))
    return out


def _rule_output(grid: list[list[int]]) -> list[list[int]]:
    """Independent mirror of the canonical scan-and-preserve program."""
    h, w = len(grid), len(grid[0])
    blocks = _solid_blocks(grid)
    used = {
        (rr, cc)
        for r, c, _ in blocks
        for rr, cc in ((r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1))
    }
    out = [[0] * w for _ in range(h)]
    for r, c, color in blocks:
        out[r][c] = color
        out[r + 1][c + 1] = color
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color and (r, c) not in used:
                out[r][c] = color
    return out


def _mod3_rival(grid: list[list[int]]) -> list[list[int]]:
    return [
        [value if value and r % 3 == c % 3 else 0 for c, value in enumerate(row)]
        for r, row in enumerate(grid)
    ]


def _global_checkerboard_rival(grid: list[list[int]]) -> list[list[int]]:
    blocks = _solid_blocks(grid)
    parity = (blocks[0][0] + blocks[0][1]) % 2
    return [
        [value if value and (r + c) % 2 == parity else 0 for c, value in enumerate(row)]
        for r, row in enumerate(grid)
    ]


def test_rule_hash_is_pinned_to_the_selected_canonical_program():
    assert GEN.RULE_HASH == "c845504525a2"


def test_canonical_pairs_are_accepted_and_match_independent_oracle():
    for pair in _canonical_pairs():
        original = deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert _rule_output(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_every_default_sample_refutes_the_retained_modulo_three_shortcut():
    for band in (None, "easy", "medium", "hard"):
        for index in range(24):
            grid = GEN.generate(10_000 + index, index, difficulty=band)
            assert GEN.self_check(grid) == []
            assert _mod3_rival(grid) != _rule_output(grid)


def test_every_default_sample_refutes_one_global_checkerboard_mask():
    for band in (None, "easy", "medium", "hard"):
        for index in range(24):
            grid = GEN.generate(20_000 + index, index, difficulty=band)
            assert _global_checkerboard_rival(grid) != _rule_output(grid)


def test_default_samples_include_an_edge_block_and_mixed_anchor_residues():
    for index in range(24):
        grid = GEN.generate(30_000 + index, index)
        h, w = len(grid), len(grid[0])
        blocks = _solid_blocks(grid)
        assert any(r in (0, h - 2) or c in (0, w - 2) for r, c, _ in blocks)
        assert len({(r % 3, c % 3) for r, c, _ in blocks}) >= 2
        assert {(r + c) % 2 for r, c, _ in blocks} == {0, 1}


def test_exact_block_count_is_realized_or_rejected_loudly():
    grid = GEN.generate(41, 7, grid_h=14, grid_w=14, n_blocks=8)
    assert len(_solid_blocks(grid)) == 8
    with pytest.raises(ValueError, match="fit|capacity|place") as caught:
        GEN.generate(41, 7, grid_h=4, grid_w=4, n_blocks=8)
    assert set(caught.value.incompatible_axes) == {"grid_h", "grid_w", "n_blocks"}


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0, 0], [0]],
        [[1, 0], [0, 0]],
        [[1, 1, 1], [1, 1, 1], [1, 1, 1]],
        [[1, 1, 0, 2, 2], [1, 1, 0, 2, 0]],
    ],
)
def test_validator_rejects_malformed_or_incomplete_scenes(grid):
    assert GEN.self_check(grid)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"difficulty": "expert"},
        {"typo_axis": 1},
        {"grid_h": True},
        {"grid_w": 15},
        {"n_blocks": 0},
        {"n_blocks": 9},
    ],
)
def test_invalid_public_controls_fail_closed(kwargs):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 0, **kwargs)


def test_named_rivals_are_refuted_and_lesson_gate_is_clean():
    assert GEN.CANONICAL_SHORTCUTS == {}
    assert set(GEN.SEMANTIC_RIVALS) >= {"global_mod3", "global_checkerboard"}
    grids = [GEN.generate(50_000, index) for index in range(4)]
    pairs = [{"input": grid, "output": _rule_output(grid)} for grid in grids]
    for query_index in range(4):
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        assert GEN.lesson_identifiable(demos, pairs[query_index]) == []


def test_real_racket_matches_independent_oracle_on_repaired_surfaces():
    from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
    from puzzle_generators.rule_wrap import wrap_rule

    def rule_application(source, grid):
        rows = " ".join("(" + " ".join(str(value) for value in row) + ")" for row in grid)
        return f"({wrap_rule(source)} '({rows}))"

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    source = _canonical_row()["program_solution"]
    grids = [GEN.generate(60_000 + index, index) for index in range(8)]
    bridge = RacketBridge(max_calls_before_restart=16)
    try:
        for grid in grids:
            original = deepcopy(grid)
            assert bridge.eval_text(rule_application(source, grid)) == _rule_output(grid)
            assert grid == original
    finally:
        bridge.shutdown()
