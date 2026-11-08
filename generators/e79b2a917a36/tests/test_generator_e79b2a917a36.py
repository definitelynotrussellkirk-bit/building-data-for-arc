from __future__ import annotations

import copy
import importlib
import json
import random
import shutil
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from scripts.rule_smoke import purity_body, rule_application

MODULE = importlib.import_module(
    "puzzle_generators.per_puzzle.e79b2a917a36.generator"
)
ROOT = Path(__file__).resolve().parents[1]


def _canonical_inputs_outputs():
    for line in (ROOT / "data/canonical/puzzles.jsonl").open():
        row = json.loads(line)
        if row.get("task_id") != MODULE.TASK_ID:
            continue
        for split in ("train", "test"):
            for pair in row[split]:
                yield pair["input"], pair["output"]



def _canonical_rule():
    for line in (ROOT / "data/canonical/puzzles.jsonl").open():
        row = json.loads(line)
        if row.get("task_id") == MODULE.TASK_ID:
            return row["program_solution"]
    raise AssertionError("canonical rule missing")

def test_generator_e79b2a917a36_accepts_and_solves_all_canonical_pairs():
    pairs = list(_canonical_inputs_outputs())
    assert len(pairs) == 6
    for grid, expected in pairs:
        before = copy.deepcopy(grid)
        assert MODULE.self_check(grid) == []
        assert MODULE.rule_mirror(grid) == expected
        assert grid == before


def test_generator_e79b2a917a36_override_roundtrip_and_boundaries():
    cases = [
        dict(grid_h=20, grid_w=20, entry_count=1, max_icons_per=1,
             palette_position="top", shape_family="compact", edge_mode="interior"),
        dict(grid_h=26, grid_w=26, entry_count=4, max_icons_per=3,
             palette_position="bottom", shape_family="hollow", edge_mode="clipped"),
        dict(grid_h=20, grid_w=26, entry_count=4, max_icons_per=2,
             palette_position="top", shape_family="concave", edge_mode="clipped"),
    ]
    for index, overrides in enumerate(cases):
        grid = MODULE.generate(700 + index, index, difficulty="hard", **overrides)
        assert MODULE.self_check(grid) == []
        assert MODULE.observe_overrides(grid) == overrides
        assert MODULE.rule_mirror(grid) != grid


def test_generator_e79b2a917a36_rejects_unknown_override():
    with pytest.raises(TypeError, match="unknown override"):
        MODULE.generate(1, 0, typo_axis=3)


def test_generator_e79b2a917a36_is_deterministic_fresh_and_rng_pure():
    state = random.getstate()
    first = MODULE.generate(12345, 7, difficulty="medium")
    assert random.getstate() == state
    second = MODULE.generate(12345, 7, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 99
    third = MODULE.generate(12345, 7, difficulty="medium")
    assert third == second
    assert random.getstate() == state


def test_generator_e79b2a917a36_self_check_rejects_targeted_impostors():
    grid = MODULE.generate(
        991,
        5,
        difficulty="hard",
        grid_h=26,
        grid_w=26,
        entry_count=2,
        max_icons_per=2,
        palette_position="bottom",
        shape_family="hollow",
        edge_mode="clipped",
    )
    entries = MODULE._palette_entries(grid)
    assert len(entries) == 2

    missing_pair = copy.deepcopy(grid)
    row, _source, _frame = entries[0]
    missing_pair[row + 1][1] = 0
    assert MODULE.self_check(missing_pair)

    duplicate_palette_color = copy.deepcopy(grid)
    row0, source0, _frame0 = entries[0]
    row1, _source1, _frame1 = entries[1]
    duplicate_palette_color[row1][0] = source0
    duplicate_palette_color[row1 + 1][0] = source0
    assert MODULE.self_check(duplicate_palette_color)

    frame_leak = copy.deepcopy(grid)
    _row, _source, frame = entries[0]
    frame_leak[0][3] = frame
    assert any("frame color" in msg for msg in MODULE.self_check(frame_leak))

    missing_icons = copy.deepcopy(grid)
    _row, source, _frame = entries[0]
    for r, row_values in enumerate(missing_icons):
        for c, value in enumerate(row_values):
            if c > 1 and value == source:
                missing_icons[r][c] = 0
    assert any("0 icons" in msg for msg in MODULE.self_check(missing_icons))

    extra_color = copy.deepcopy(grid)
    used = {value for row_values in extra_color for value in row_values}
    new_color = next(color for color in range(1, 10) if color not in used)
    extra_color[0][2] = new_color
    assert any("absent from the palette" in msg for msg in MODULE.self_check(extra_color))


def test_generator_e79b2a917a36_a_b_a_purity():
    a1 = MODULE.generate(81, 0, difficulty="easy")
    b = MODULE.generate(82, 1, difficulty="hard")
    a2 = MODULE.generate(81, 0, difficulty="easy")
    assert a1 == a2
    assert a1 != b


@pytest.mark.skipif(shutil.which("racket") is None, reason="racket is not installed")
def test_generator_e79b2a917a36_real_racket_all_canonical_pairs_and_a_b_a():
    pairs = list(_canonical_inputs_outputs())
    rule = _canonical_rule()
    bridge = RacketBridge(max_calls_before_restart=64)
    try:
        for grid, expected in pairs:
            source = copy.deepcopy(grid)
            snapshot = copy.deepcopy(source)
            assert bridge.eval_text(rule_application(rule, source)) == expected
            assert source == snapshot
        probe = bridge.eval_text(purity_body(rule, pairs[0][0], pairs[-1][0]))
        assert probe == [pairs[0][1], pairs[0][1], pairs[0][0]]
    finally:
        bridge.shutdown()
