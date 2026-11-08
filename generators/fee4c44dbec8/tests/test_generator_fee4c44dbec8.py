from __future__ import annotations

import copy
import random

from puzzle_generators.per_puzzle.fee4c44dbec8 import generator as gen


def _blank(h: int = 8, w: int = 10):
    return [[0 for _ in range(w)] for _ in range(h)]


def test_rule_hash_and_canonical_inputs_are_accepted():
    assert gen.RULE_HASH == "934d81b66c5f"
    canonical = [
        [
            [int(value) for value in row]
            for row in rows
        ]
        for rows in [
            ["00000000000", "02002000000", "00000000000", "00330000000", "00000000000", "00000003000", "00000000044", "00000000040"],
            ["0000000000", "0550005000", "0000000000", "0000000000", "0020000000", "0000000000", "0000020000", "0000000020", "0000000000"],
            ["000000000000", "060000004400", "000000004000", "000600000000", "000000000000", "000006000000", "000000000000", "000000000400", "000000000000", "000000000000"],
            ["00000000000", "00000000000", "00700007700", "00000000000", "00000000000", "03000300030", "00000000000", "00000000000", "00000000000"],
            ["0000000000", "0200020020", "0000000000", "0000000000", "0044000000", "0000000000", "0000005000", "0000000000", "0000000000", "0000000000"],
        ]
    ]
    assert all(gen.self_check(grid) == [] for grid in canonical)
    assert all(gen.strict_canonical_like(grid) == [] for grid in canonical)


def test_exact_override_boundaries_are_observable():
    for band in ("easy", "medium", "hard"):
        for overrides in (
            {"grid_h": 8, "grid_w": 10, "n_colors": 2, "comp_count": 2, "blob_size": 2},
            {"grid_h": 10, "grid_w": 12, "n_colors": 3, "comp_count": 3, "blob_size": 3},
        ):
            grid = gen.generate(17, 31, difficulty=band, **overrides)
            assert gen.observe_overrides(grid) == overrides
            assert gen.self_check(grid) == []


def test_regression_ignored_comp_count_and_blob_size_are_now_exact():
    count_grid = gen.generate(1, 20, difficulty="easy", comp_count=3)
    size_grid = gen.generate(0, 3, difficulty="easy", blob_size=3)
    assert gen.observe_overrides(count_grid)["comp_count"] == 3
    assert gen.observe_overrides(size_grid)["blob_size"] == 3


def test_determinism_freshness_and_global_rng_purity():
    random.seed(90210)
    state = random.getstate()
    first = gen.generate(9, 27, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(9, 27, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 99
    assert gen.generate(9, 27, difficulty="hard") == second


def test_difficulty_streams_are_not_byte_identical():
    grids = [gen.generate(5, 19, difficulty=band) for band in ("easy", "medium", "hard")]
    assert len({repr(grid) for grid in grids}) == 3


def test_self_check_rejects_targeted_impostors():
    one_color = _blank()
    one_color[0][0] = one_color[3][3] = 2

    equal_counts = _blank()
    for color, cells in {2: [(0, 0), (3, 0)], 4: [(0, 3), (3, 3)]}.items():
        for r, c in cells:
            equal_counts[r][c] = color

    all_singletons = _blank()
    for color, cells in {2: [(0, 0), (3, 0)], 4: [(0, 3)]}.items():
        for r, c in cells:
            all_singletons[r][c] = color

    oversized = _blank()
    oversized[0][0] = oversized[0][1] = oversized[1][0] = oversized[1][1] = 2
    oversized[4][0] = oversized[4][1] = 4
    oversized[7][4] = 4

    touching_colors = _blank()
    touching_colors[0][0] = touching_colors[0][1] = 2
    touching_colors[0][2] = 4
    touching_colors[3][0] = 2

    for grid in (one_color, equal_counts, all_singletons, oversized, touching_colors):
        assert gen.self_check(grid), grid


def test_semantic_witnesses_and_lesson_identifiability():
    pairs = []
    for index in range(4):
        grid = gen.generate(100 + index, index, difficulty="medium")
        pairs.append({"input": grid, "output": gen._solve_grid(grid)})
    assert gen.lesson_identifiable(pairs[:3], pairs[3]) == []

    hits = {name: 0 for name in gen.SEMANTIC_WITNESSES}
    for band in ("easy", "medium", "hard"):
        for seed in range(80):
            grid = gen.generate(seed + 500, seed, difficulty=band)
            for name, witness in gen.SEMANTIC_WITNESSES.items():
                hits[name] += int(witness(grid))
    assert all(value > 0 for value in hits.values()), hits


def test_self_check_and_observers_do_not_mutate_inputs():
    grid = gen.generate(33, 44, difficulty="medium")
    before = copy.deepcopy(grid)
    gen.self_check(grid)
    gen.strict_canonical_like(grid)
    gen.observe_overrides(grid)
    for witness in gen.SEMANTIC_WITNESSES.values():
        witness(grid)
    assert grid == before
