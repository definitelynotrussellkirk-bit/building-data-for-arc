from __future__ import annotations

import copy
import random

import pytest

from puzzle_generators.per_puzzle.f1347e0836ec import generator as gen
from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash


def test_rule_hash_and_canonical_pairs_match_selected_authority():
    assert gen.RULE_HASH == canonical_rule_hash(gen.TASK_ID)
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 4
    for pair in pairs:
        assert gen.self_check(copy.deepcopy(pair["input"])) == []
        assert gen.rule_mirror(copy.deepcopy(pair["input"])) == pair["output"]


def test_exact_overrides_are_observable_and_unknown_keys_reject():
    for band in ("easy", "medium", "hard"):
        for grid_n in (5, 16):
            for bg_color in (2, 9):
                for on_diagonal in (False, True):
                    grid = gen.generate(
                        91,
                        7,
                        difficulty=band,
                        grid_n=grid_n,
                        bg_color=bg_color,
                        on_diagonal=on_diagonal,
                    )
                    observed = gen.observe_overrides(grid)
                    assert observed == {
                        "grid_n": grid_n,
                        "bg_color": bg_color,
                        "on_diagonal": on_diagonal,
                    }
                    assert gen.self_check(
                        grid,
                        difficulty=band,
                        meta={
                            "overrides": {
                                "grid_n": grid_n,
                                "bg_color": bg_color,
                                "on_diagonal": on_diagonal,
                            }
                        },
                    ) == []
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, typo_axis=3)
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, dot_color=4)


def test_every_four_demo_schedule_window_refutes_named_rivals():
    for band in ("easy", "medium", "hard"):
        for seed in (137, 911):
            for start in range(8):
                demos = []
                branches = set()
                for sample_index in range(start, start + gen.EXAMPLES_NEEDED):
                    grid = gen.generate(seed, sample_index, difficulty=band)
                    branches.add(gen.observe_overrides(grid)["on_diagonal"])
                    demos.append({"input": grid, "output": gen.rule_mirror(grid)})
                query_grid = gen.generate(
                    seed, start + gen.EXAMPLES_NEEDED, difficulty=band
                )
                query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
                assert branches == {False, True}
                assert gen.lesson_identifiable(demos, query) == []
                for name, rival in gen.LESSON_COMPETITORS.items():
                    assert any(
                        rival(demo["input"]) != demo["output"] for demo in demos
                    ), name


def test_self_check_rejects_targeted_rule_hiding_impostors():
    base = gen.generate(55, 0, difficulty="medium")
    analysis = gen._grid_analysis(base)
    n = analysis["grid_n"]
    bg = analysis["bg_color"]
    dot = analysis["dot_color"]
    row = analysis["dot_row"]
    col = analysis["dot_col"]

    no_dot = [[bg] * n for _ in range(n)]
    assert gen.self_check(no_dot)

    multiple = copy.deepcopy(base)
    extra = (1, n - 2)
    if extra == (row, col):
        extra = (n - 2, 1)
    multiple[extra[0]][extra[1]] = dot
    assert gen.self_check(multiple)

    edge_dot = [[bg] * n for _ in range(n)]
    edge_dot[0][n // 2] = dot
    assert gen.self_check(edge_dot)

    bg_one = [[1] * n for _ in range(n)]
    bg_one[row][col] = dot
    assert gen.self_check(bg_one)

    dot_one = [[bg] * n for _ in range(n)]
    dot_one[row][col] = 1
    assert gen.self_check(dot_one)


def test_replay_is_deterministic_fresh_and_global_rng_pure():
    random.seed(20260816)
    state = random.getstate()
    first = gen.generate(12345, 19, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(12345, 19, difficulty="hard")
    assert random.getstate() == state
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 0
    assert second[0][0] != 0
