from __future__ import annotations
import copy, importlib, json
from pathlib import Path
gen = importlib.import_module("puzzle_generators.per_puzzle.6e18fab2c2e5.generator")

def _canonical_row():
    return next(json.loads(line) for line in Path("data/canonical/puzzles.jsonl").read_text().splitlines() if json.loads(line).get("content_hash") == gen.TASK_ID)

def test_canonical_inputs_and_outputs_are_accepted():
    for pair in _canonical_row()["train"] + _canonical_row()["test"]:
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]

def test_override_boundaries_are_exact_and_observable():
    for band in ("easy", "medium", "hard"):
        for size in (12, 26):
            for n in (1, 5):
                for slope in gen.SLOPES:
                    grid = gen.generate(91, 7, difficulty=band, grid_size=size, n_cells=n, diagonal_slope=slope)
                    assert gen.self_check(grid) == []
                    assert gen.observe_overrides(grid) == {"grid_size": size, "n_cells": n, "diagonal_slope": slope}

def test_five_consecutive_demos_identify_the_rule():
    demos = []
    for i in range(5):
        grid = gen.generate(1234, i, difficulty="medium"); demos.append({"input": grid, "output": gen.rule_mirror(grid)})
    q = gen.generate(1234, 5, difficulty="medium")
    assert gen.lesson_identifiable(demos, {"input": q, "output": gen.rule_mirror(q)}) == []

def test_self_check_rejects_structural_impostors():
    good = gen.generate(55, 3, difficulty="medium")
    bad = copy.deepcopy(good); bad[0][0] = 4; assert gen.self_check(bad)
    horizontal = [[7] * 16 for _ in range(16)]; horizontal[8][8] = horizontal[8][9] = 2; assert gen.self_check(horizontal)
    too_many = [[7] * 16 for _ in range(16)]
    for i in range(6): too_many[8 + i][i] = 2
    assert gen.self_check(too_many)
    non_square = [[7] * 13 for _ in range(12)]; non_square[6][6] = 2; assert gen.self_check(non_square)

def test_replay_is_deterministic_and_fresh():
    a = gen.generate(100, 9, difficulty="hard"); b = gen.generate(100, 9, difficulty="hard")
    assert a == b and a is not b and all(x is not y for x, y in zip(a, b))
    a[0][0] = 2; assert gen.generate(100, 9, difficulty="hard") == b

def test_unknown_override_is_rejected():
    try: gen.generate(1, 0, imaginary_axis=3)
    except ValueError as exc: assert "unknown override" in str(exc)
    else: raise AssertionError("unknown override accepted")
