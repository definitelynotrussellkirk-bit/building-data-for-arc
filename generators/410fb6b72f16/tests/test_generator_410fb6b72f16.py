from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

import pytest

from scripts.canonical_profile_gate import canonical_pairs

TASK_ID = "410fb6b72f16"
gen = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")


def _pair_rows():
    return canonical_pairs(TASK_ID)


def test_canonical_inputs_and_outputs_match_rule_mirror():
    pairs = _pair_rows()
    assert len(pairs) == 3
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert gen.strict_canonical_like(pair["input"]) == []


def test_exact_override_boundaries_are_observable():
    cases = [
        dict(grid_h=8, grid_w=8, singleton_count=2, large_size=3, distractor_count=0),
        dict(grid_h=10, grid_w=11, singleton_count=4, large_size=4, distractor_count=1),
    ]
    for difficulty in ("easy", "medium", "hard"):
        for seed, requested in enumerate(cases):
            grid = gen.generate(seed, 0, difficulty=difficulty, **requested)
            assert gen.observe_overrides(grid) == requested
            assert gen.self_check(grid, meta={"overrides": requested}) == []


def test_unknown_and_out_of_domain_overrides_reject():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(0, 0, bogus_axis=1)
    with pytest.raises(ValueError, match="outside 8..10"):
        gen.generate(0, 0, grid_h=7)
    with pytest.raises(ValueError, match="outside 0..1"):
        gen.generate(0, 0, distractor_count=2)


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(918273)
    state = random.getstate()
    first = gen.generate(77, 5, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(77, 5, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9
    assert second[0][0] != 9


def test_self_check_rejects_targeted_impostors():
    valid = gen.generate(11, 0, difficulty="medium")

    wrong_color = copy.deepcopy(valid)
    zero = next((r, c) for r, row in enumerate(wrong_color) for c, v in enumerate(row) if v == 0)
    wrong_color[zero[0]][zero[1]] = 2
    assert gen.self_check(wrong_color)

    only_singletons = [[0] * 8 for _ in range(8)]
    only_singletons[1][1] = only_singletons[3][3] = 1
    assert any("multi-cell" in reason for reason in gen.self_check(only_singletons))

    only_multi = [[0] * 8 for _ in range(8)]
    only_multi[1][1] = only_multi[1][2] = 1
    assert any("singleton blue" in reason for reason in gen.self_check(only_multi))

    green_domino = copy.deepcopy(valid)
    green = next((r, c) for r, row in enumerate(green_domino) for c, v in enumerate(row) if v == 3)
    r, c = green
    neighbor = next(
        (nr, nc)
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
        if 0 <= (nr := r + dr) < len(green_domino)
        and 0 <= (nc := c + dc) < len(green_domino[0])
        and green_domino[nr][nc] == 0
    )
    green_domino[neighbor[0]][neighbor[1]] = 3
    assert any("green distractors" in reason for reason in gen.self_check(green_domino))

    nonrectangular = copy.deepcopy(valid)
    nonrectangular[-1].pop()
    assert gen.self_check(nonrectangular)


def test_every_three_demo_window_is_identifiable():
    for difficulty in ("easy", "medium", "hard"):
        for start in range(9):
            demos = []
            for sample_index in range(start, start + gen.EXAMPLES_NEEDED):
                grid = gen.generate(1000 + start, sample_index, difficulty=difficulty)
                demos.append({"input": grid, "output": gen.rule_mirror(grid)})
            query_grid = gen.generate(
                1000 + start, start + gen.EXAMPLES_NEEDED, difficulty=difficulty
            )
            query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
            assert gen.lesson_identifiable(demos, query) == []


def test_named_rivals_have_decisive_generated_witnesses():
    grids = [gen.generate(31337, i, difficulty="medium") for i in range(3)]
    truth = [gen.rule_mirror(grid) for grid in grids]
    for rival_name, rival in gen.SEMANTIC_RIVALS.items():
        assert any(rival(grid) != expected for grid, expected in zip(grids, truth)), rival_name
