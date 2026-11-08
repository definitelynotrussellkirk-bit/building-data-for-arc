from __future__ import annotations

import copy
import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash

TASK = "00af0f134576"
gen = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")


def test_rule_hash_and_canonical_pairs_are_accepted_and_solved_by_mirror():
    assert gen.RULE_HASH == canonical_rule_hash(TASK)
    pairs = canonical_pairs(TASK)
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_exact_override_boundaries_round_trip_in_every_band(band):
    cases = [
        {"grid_size": 7, "n_lines": 2, "diagonal_count": 0},
        {"grid_size": 16, "n_lines": 6, "diagonal_count": 2},
        {"grid_size": 7, "n_lines": 6, "diagonal_count": 2},
        {"grid_size": 16, "n_lines": 2, "diagonal_count": 2},
    ]
    for index, overrides in enumerate(cases):
        grid = gen.generate(4100 + index, index, difficulty=band, **overrides)
        assert gen.self_check(grid) == []
        assert gen.observe_overrides(grid) == overrides


def test_unknown_override_is_rejected_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, __typo_axis__=3)


def test_four_slot_schedule_carries_all_decisive_witnesses():
    grids = [gen.generate(9001, i, difficulty="medium") for i in range(4)]
    assert gen._has_depth_not_color_counterexample(grids[0])
    assert gen._has_diagonal(grids[1])
    assert gen._has_visible_count_counterexample(grids[1])
    assert gen._has_tie_break_witness(grids[2])
    assert gen._has_deep_pile(grids[3])
    for start in range(8):
        window = [gen.generate(9200, i, difficulty="hard") for i in range(start, start + 4)]
        assert any(gen._has_depth_not_color_counterexample(g) for g in window)
        assert any(gen._has_visible_count_counterexample(g) for g in window)
        assert any(gen._has_tie_break_witness(g) for g in window)
        assert any(gen._has_deep_pile(g) for g in window)


def test_self_check_rejects_targeted_impostors():
    base = gen.generate(77, 3, difficulty="hard")

    blank = [[7 for _ in row] for row in base]
    assert gen.self_check(blank)

    stray = copy.deepcopy(base)
    present = {v for row in stray for v in row}
    absent = next(c for c in range(10) if c not in present)
    placed = False
    for r, row in enumerate(stray):
        for c, value in enumerate(row):
            if value == 7:
                stray[r][c] = absent
                placed = True
                break
        if placed:
            break
    assert gen.self_check(stray)

    holed = copy.deepcopy(base)
    infos = gen._line_analysis(base)
    target = next(info for info in infos if info.shown >= 3)
    r, c = next(iter(target.positions))
    holed[r][c] = 7
    assert gen.self_check(holed)

    duplicated = copy.deepcopy(base)
    dense_row = max(range(len(base)), key=lambda r: sum(v != 7 for v in base[r]))
    target_row = 0 if dense_row != 0 else len(base) - 1
    duplicated[target_row] = list(base[dense_row])
    assert gen.self_check(duplicated)


def test_replay_returns_fresh_objects_and_preserves_global_rng():
    random.seed(1234567)
    state = random.getstate()
    a = gen.generate(12345, 2, difficulty="medium")
    assert random.getstate() == state
    b = gen.generate(12345, 2, difficulty="medium")
    assert random.getstate() == state
    assert a == b
    assert a is not b
    assert all(x is not y for x, y in zip(a, b))
    a[0][0] = (a[0][0] + 1) % 10
    assert a != b
