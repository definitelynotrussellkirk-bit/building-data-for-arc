from __future__ import annotations

import copy
import json
import random
from pathlib import Path

from puzzle_generators.per_puzzle.c0966960e255 import generator as gen

ROOT = Path(__file__).resolve().parents[1]


def _canonical_row():
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                return row
    raise AssertionError("canonical task not found")


def test_generator_c0966960e255_accepts_and_solves_every_canonical_pair():
    row = _canonical_row()
    for split in ("train", "test"):
        for pair in row[split]:
            assert gen.self_check(copy.deepcopy(pair["input"])) == []
            assert gen.strict_canonical_like(copy.deepcopy(pair["input"])) == []
            assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_generator_c0966960e255_exact_overrides_and_boundary_values():
    cases = [
        dict(grid_h=9, grid_w=10, n_sym=1, n_asym=1, n_gray=1),
        dict(grid_h=24, grid_w=24, n_sym=2, n_asym=2, n_gray=4),
    ]
    for index, overrides in enumerate(cases):
        grid = gen.generate(991 + index, 7, difficulty="hard", **overrides)
        assert gen.self_check(grid) == []
        assert gen.observe_overrides(grid) == overrides


def test_generator_c0966960e255_deterministic_fresh_and_global_rng_pure():
    random.seed(123456)
    state = random.getstate()
    first = gen.generate(17, 29, difficulty="medium")
    assert random.getstate() == state
    second = gen.generate(17, 29, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert gen.generate(17, 29, difficulty="medium") == second


def test_generator_c0966960e255_default_draws_expose_both_axes_and_shortcut_rebuttals():
    for band in ("easy", "medium", "hard"):
        for seed in range(12):
            grid = gen.generate(seed, seed * 19 + 5, difficulty=band)
            analysis = gen._analyze(grid)
            assert analysis["errors"] == []
            assert analysis["n_sym"] == 2
            assert analysis["n_asym"] == 2
            assert analysis["shared_sizes"]
            assert analysis["lr_only_symmetric"] >= 1
            assert analysis["tb_only_asymmetric"] >= 1
            assert set(gen.SEMANTIC_WITNESSES) == {
                name for name, predicate in gen.SEMANTIC_WITNESSES.items() if predicate(grid)
            }


def test_generator_c0966960e255_self_check_rejects_targeted_impostors():
    good = gen.generate(41, 3, difficulty="easy")
    assert gen.self_check(good) == []

    no_gray = [[0 if value == 5 else value for value in row] for row in good]
    assert any("gray distractor" in reason for reason in gen.self_check(no_gray))

    all_symmetric = copy.deepcopy(good)
    for component in gen._components(all_symmetric, 2):
        if not gen._left_right_symmetric(component):
            for row, col in component:
                all_symmetric[row][col] = 0
    assert any("asymmetric" in reason for reason in gen.self_check(all_symmetric))

    all_asymmetric = copy.deepcopy(good)
    for component in gen._components(all_asymmetric, 2):
        if gen._left_right_symmetric(component):
            for row, col in component:
                all_asymmetric[row][col] = 0
    assert any("left-right-symmetric" in reason for reason in gen.self_check(all_asymmetric))

    unexpected_color = copy.deepcopy(good)
    gray_row, gray_col = next(
        (row, col)
        for row, values in enumerate(unexpected_color)
        for col, value in enumerate(values)
        if value == 5
    )
    unexpected_color[gray_row][gray_col] = 4
    assert any("unexpected colors" in reason for reason in gen.self_check(unexpected_color))
