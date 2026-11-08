from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest


gen = importlib.import_module("puzzle_generators.per_puzzle.80b1344c17c8.generator")


def _canonical_row():
    for line in Path("data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == gen.TASK_ID:
            return row
    raise AssertionError("canonical task not found")


def _canonical_pairs():
    row = _canonical_row()
    pairs = list(row["train"])
    tests = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return pairs + tests


def test_rule_hash_and_all_canonical_inputs():
    row = _canonical_row()
    actual = hashlib.sha256(" ".join(row["program_solution"].split()).encode()).hexdigest()[:12]
    assert gen.RULE_HASH == actual == "d19ea091585d"
    pairs = _canonical_pairs()
    assert len(pairs) == 3
    assert all(gen.self_check(pair["input"]) == [] for pair in pairs)
    assert all(gen.strict_canonical_like(pair["input"]) == [] for pair in pairs)
    assert all(gen._solve(pair["input"]) == pair["output"] for pair in pairs)


def test_canonical_scale_and_full_exact_override_boundaries():
    cases = (
        dict(grid_h=5, grid_w=6, k_rot=1, shape_size=2, shape_color=2),
        dict(grid_h=12, grid_w=12, k_rot=4, shape_size=6, shape_color=8),
    )
    for sample_index, overrides in enumerate(cases):
        grid = gen.generate(20260725, sample_index, difficulty="easy", **overrides)
        assert gen.observe_overrides(grid) == overrides
        assert gen.self_check(grid) == []
        assert gen._solve(grid) != grid


def test_unknown_and_out_of_range_overrides_reject_loudly():
    with pytest.raises(ValueError):
        gen.generate(1, 0, texture="no_motifs")
    with pytest.raises(ValueError):
        gen.generate(1, 0, k_rot=0)
    with pytest.raises(ValueError):
        gen.generate(1, 0, shape_color=9)


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(4815162342)
    state = random.getstate()
    first = gen.generate(44, 7, difficulty="medium")
    assert random.getstate() == state
    second = gen.generate(44, 7, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert second == gen.generate(44, 7, difficulty="medium")


def test_self_check_rejects_targeted_impostors():
    valid = gen.generate(
        99,
        1,
        grid_h=7,
        grid_w=8,
        k_rot=2,
        shape_size=4,
        shape_color=5,
    )
    assert gen.self_check(valid) == []

    empty = [[0] * 8 for _ in range(7)]
    assert any("tally count" in error for error in gen.self_check(empty))
    assert any("anchor" in error for error in gen.self_check(empty))

    no_anchor = copy.deepcopy(valid)
    for row in no_anchor[1:]:
        for c, value in enumerate(row):
            if value == 9:
                row[c] = 0
    assert any("anchor" in error for error in gen.self_check(no_anchor))

    bad_header = copy.deepcopy(valid)
    marker = next(c for c, value in enumerate(bad_header[0]) if value == 1)
    bad_header[0][marker] = 2
    assert any("header may contain" in error for error in gen.self_check(bad_header))

    second_color = copy.deepcopy(valid)
    changed = False
    for row in second_color[1:]:
        for c, value in enumerate(row):
            if 2 <= value <= 8:
                row[c] = 6 if value != 6 else 7
                changed = True
                break
        if changed:
            break
    assert any("monochrome" in error for error in gen.self_check(second_color))

    far_cell = copy.deepcopy(valid)
    anchor_grid = next(
        (r, c)
        for r, row in enumerate(far_cell[1:], start=1)
        for c, value in enumerate(row)
        if value == 9
    )
    destination = next(
        (r, c)
        for r in range(1, len(far_cell))
        for c in range(len(far_cell[0]))
        if far_cell[r][c] == 0
        and max(abs(r - anchor_grid[0]), abs(c - anchor_grid[1])) > 1
    )
    moved = False
    for r, row in enumerate(far_cell[1:], start=1):
        for c, value in enumerate(row):
            if 2 <= value <= 8:
                row[c] = 0
                far_cell[destination[0]][destination[1]] = value
                moved = True
                break
        if moved:
            break
    assert any("one king-step" in error for error in gen.self_check(far_cell))

    closed_orbit = [[0] * 8 for _ in range(7)]
    closed_orbit[0][0:2] = [1, 1]
    closed_orbit[3][3] = 9
    for r, c in ((2, 3), (3, 4), (4, 3), (3, 2)):
        closed_orbit[r][c] = 4
    errors = gen.self_check(closed_orbit)
    assert any("gain at least one" in error for error in errors)


def test_sequential_lesson_is_identifiable_and_covers_all_k():
    seed = 20260725
    pairs = []
    for sample_index in range(gen.EXAMPLES_NEEDED + 1):
        inp = gen.generate(seed, sample_index)
        pairs.append({"input": inp, "output": gen._solve(inp)})
    assert {gen.observe_overrides(pair["input"])["k_rot"] for pair in pairs[:5]} == {1, 2, 3, 4}
    assert gen.lesson_identifiable(pairs[:5], pairs[5]) == []
