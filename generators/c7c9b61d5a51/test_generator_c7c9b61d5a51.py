from __future__ import annotations

import copy
import random

import pytest

from puzzle_generators.per_puzzle.c7c9b61d5a51 import generator as gen
from scripts.canonical_profile_gate import canonical_pairs


def _pair_with_selected(grid, selected: int):
    facts = gen._analyze(grid)
    return next(pair for pair in facts["pairs"] if pair["selected"] == selected)


def test_rule_hash_and_all_canonical_pairs() -> None:
    assert gen.RULE_HASH == "82200d439ef3"
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 5
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_self_check_rejects_targeted_impostors() -> None:
    valid = gen.generate(9001, 1, difficulty="medium")
    assert gen.self_check(valid) == []
    assert gen.strict_canonical_like(valid) == []
    facts = gen._analyze(valid)

    no_blockers = [
        [0 if value == gen.BLOCKER_COLOR else value for value in row]
        for row in valid
    ]

    third_endpoint = copy.deepcopy(valid)
    color = facts["pairs"][0]["color"]
    empty = next(
        (row, col)
        for row, values in enumerate(third_endpoint)
        for col, value in enumerate(values)
        if value == 0
    )
    third_endpoint[empty[0]][empty[1]] = color

    aligned_pair = copy.deepcopy(valid)
    pair = facts["pairs"][0]
    (r1, c1), (r2, c2) = pair["cells"]
    aligned_pair[r2][c2] = 0
    replacement_col = next(
        col
        for col in range(len(aligned_pair[0]))
        if col != c1 and aligned_pair[r1][col] == 0
    )
    aligned_pair[r1][replacement_col] = pair["color"]

    both_routes_blocked = copy.deepcopy(valid)
    pair = facts["pairs"][0]
    selected = pair["selected"]
    clear_only = next(
        cell
        for cell in pair["routes"][selected]
        if cell not in pair["cells"] and both_routes_blocked[cell[0]][cell[1]] == 0
    )
    both_routes_blocked[clear_only[0]][clear_only[1]] = gen.BLOCKER_COLOR

    invalid_cell = copy.deepcopy(valid)
    invalid_cell[0][0] = 12

    for name, impostor in {
        "no_blockers": no_blockers,
        "third_endpoint": third_endpoint,
        "aligned_pair": aligned_pair,
        "both_routes_blocked": both_routes_blocked,
        "invalid_cell": invalid_cell,
    }.items():
        assert gen.self_check(impostor), name


def test_strict_gate_rejects_rule_hiding_both_clear_scene() -> None:
    grid = gen.generate(811, 0, difficulty="easy", pair_count=2, route_pattern="first")
    facts = gen._analyze(grid)
    pair = facts["pairs"][0]
    blocked_index = 1 - pair["selected"]
    blocker = next(
        cell
        for cell in pair["routes"][blocked_index]
        if grid[cell[0]][cell[1]] == gen.BLOCKER_COLOR
    )
    ambiguous = copy.deepcopy(grid)
    ambiguous[blocker[0]][blocker[1]] = 0

    # The Racket authority can still choose its first clear route, but this is
    # not a useful teaching scene because the blocker cue no longer decides it.
    assert gen.self_check(ambiguous) == []
    assert gen.strict_canonical_like(ambiguous)
    assert gen.rule_mirror(ambiguous)


def test_all_exact_override_combinations_are_observable() -> None:
    for band in ("easy", "medium", "hard"):
        for height in gen.GRID_HEIGHTS:
            for width in gen.GRID_WIDTHS:
                for pair_count in gen.PAIR_COUNTS:
                    for route_pattern in gen.ROUTE_PATTERNS:
                        grid = gen.generate(
                            20260727,
                            17,
                            difficulty=band,
                            grid_h=height,
                            grid_w=width,
                            pair_count=pair_count,
                            route_pattern=route_pattern,
                        )
                        assert gen.observe_overrides(grid) == {
                            "grid_h": height,
                            "grid_w": width,
                            "pair_count": pair_count,
                            "route_pattern": route_pattern,
                        }


def test_unknown_override_is_rejected() -> None:
    with pytest.raises(TypeError, match="unknown override"):
        gen.generate(1, 0, difficulty="easy", typo_axis="first")


def test_generation_is_deterministic_fresh_and_global_rng_pure() -> None:
    random.seed(123456)
    before = random.getstate()
    first = gen.generate(42, 9, difficulty="hard")
    after = random.getstate()
    second = gen.generate(42, 9, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))


def test_named_rivals_are_killed_and_every_window_is_identifiable() -> None:
    mixed_two = gen.generate(
        77, 1, difficulty="medium", pair_count=2, route_pattern="mixed"
    )
    truth = gen.rule_mirror(mixed_two)
    assert gen._rival_always_first(mixed_two) != truth
    assert gen._rival_always_second(mixed_two) != truth
    assert gen._rival_connect_color_five(mixed_two) != truth

    for band in ("easy", "medium", "hard"):
        for start in range(8):
            pairs = []
            for offset in range(gen.EXAMPLES_NEEDED + 1):
                grid = gen.generate(1000 + start, start + offset, difficulty=band)
                pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
            assert gen.lesson_identifiable(pairs[:-1], pairs[-1]) == []
