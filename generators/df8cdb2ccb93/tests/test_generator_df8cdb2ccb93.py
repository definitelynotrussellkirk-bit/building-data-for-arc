"""Focused regressions for the df8cdb2ccb93 generator repair."""
from __future__ import annotations

import copy
import importlib
import random

import pytest

from puzzle_generators import base
from scripts.canonical_profile_gate import canonical_pairs


gen = importlib.import_module("puzzle_generators.per_puzzle.df8cdb2ccb93.generator")


def _pair(seed: int, sample_index: int, band: str) -> dict:
    grid = gen.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_rule_hash_and_all_canonical_pairs_are_exact_and_input_pure():
    assert gen.RULE_HASH == "036ea461f9e6"
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 4
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


def test_default_draws_are_lawful_and_keyed_axes_are_observable():
    for band in ("easy", "medium", "hard"):
        for sample_index in range(24):
            captured = []
            base.set_ctx_observer(captured.append)
            try:
                grid = gen.generate(5000 + sample_index, sample_index, difficulty=band)
            finally:
                base.set_ctx_observer(None)
            assert gen.self_check(grid) == []
            recorded = {
                name: value
                for name, value in captured[-1].recorded_draws().items()
                if name in gen.AXES
            }
            assert recorded == gen.observe_overrides(grid)


def test_every_three_demo_window_refutes_every_named_competitor():
    for band in ("easy", "medium", "hard"):
        for start in range(16):
            pairs = [_pair(7000 + start, start + offset, band) for offset in range(4)]
            demos, query = pairs[: gen.EXAMPLES_NEEDED], pairs[gen.EXAMPLES_NEEDED]
            assert gen.lesson_identifiable(demos, query) == []
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(rival(pair["input"]) != pair["output"] for pair in demos), name


def test_eight_slot_schedule_has_all_profiles_and_every_window_has_shared_control():
    expected = set(gen.SCHEDULE_PROFILES)
    for start in range(8):
        observed = {gen.schedule_profile(0, start + offset) for offset in range(8)}
        assert observed == expected
        layouts = [
            gen.observe_overrides(gen.generate(0, start + offset))["layout_kind"]
            for offset in range(gen.EXAMPLES_NEEDED)
        ]
        assert "boundary_shared" in layouts


def test_exact_override_surface_round_trips_or_rejects_declared_conflict():
    for band in ("easy", "medium", "hard"):
        for grid_h in (7, 10):
            for grid_w in (7, 10):
                for seeds in (2, 4):
                    for layout_kind in gen.LAYOUT_KINDS:
                        requested = {
                            "grid_h": grid_h,
                            "grid_w": grid_w,
                            "seeds": seeds,
                            "layout_kind": layout_kind,
                        }
                        if layout_kind == "boundary_shared" and seeds == 2:
                            with pytest.raises(ValueError, match="requires at least three"):
                                gen.generate(99, 17, difficulty=band, **requested)
                            continue
                        grid = gen.generate(99, 17, difficulty=band, **requested)
                        assert gen.self_check(grid) == []
                        assert gen.observe_overrides(grid) == requested


def test_unknown_and_mistyped_overrides_fail_loudly():
    with pytest.raises(TypeError, match="unknown override"):
        gen.generate(0, 0, typo_palette="warm")
    with pytest.raises(ValueError, match="grid_h must be an integer"):
        gen.generate(0, 0, grid_h=True)
    with pytest.raises(ValueError, match="layout_kind must be a string"):
        gen.generate(0, 0, layout_kind=3)


def test_self_check_rejects_targeted_structural_impostors():
    blank = [[0] * 8 for _ in range(8)]

    wrong_color = gen.generate(100, 0)
    wrong_color[0][0] = 1

    adjacent = [[0] * 8 for _ in range(8)]
    adjacent[3][3] = adjacent[3][4] = 2

    corner = [[0] * 8 for _ in range(8)]
    corner[0][0] = 2
    corner[4][4] = 2

    two_boundaries = [[0] * 8 for _ in range(8)]
    two_boundaries[0][3] = 2
    two_boundaries[7][4] = 2

    for fixture in (blank, wrong_color, adjacent, corner, two_boundaries):
        assert gen.self_check(fixture), fixture


def test_negative_recombination_is_rejected_but_oracle_mirror_executes():
    grid = gen.generate(314, 1, layout_kind="edge", seeds=2)
    boundary = gen._seed_facts(grid)["boundary"][0]
    r, c = boundary
    # Add a novel isolated red seed on another boundary. The transformation is
    # still executable, but the teaching grammar rejects multiple boundary seeds.
    candidates = [
        (rr, cc)
        for rr in range(len(grid))
        for cc in range(len(grid[0]))
        if gen._is_boundary((rr, cc), len(grid), len(grid[0]))
        and not gen._is_corner((rr, cc), len(grid), len(grid[0]))
        and grid[rr][cc] == 0
        and abs(rr - r) + abs(cc - c) >= 3
    ]
    rr, cc = candidates[0]
    grid[rr][cc] = 2
    assert gen.self_check(grid)
    output = gen.rule_mirror(grid)
    assert output[rr][cc] == 2
    assert any(
        0 <= rr + dr < len(grid)
        and 0 <= cc + dc < len(grid[0])
        and output[rr + dr][cc + dc] == 1
        for dr, dc in gen._CARDINALS
    )


def test_deterministic_fresh_returns_global_rng_and_reentrant_aba():
    random.seed(20260727)
    state = random.getstate()
    a = gen.generate(44, 9, difficulty="hard")
    b = gen.generate(45, 10, difficulty="easy")
    assert random.getstate() == state

    a_again = gen.generate(44, 9, difficulty="hard")
    assert a == a_again
    assert a is not a_again
    assert all(row is not other for row, other in zip(a, a_again))

    a_before = copy.deepcopy(a)
    b_before = copy.deepcopy(b)
    first = gen.rule_mirror(a)
    gen.rule_mirror(b)
    assert gen.rule_mirror(a) == first
    assert a == a_before
    assert b == b_before
