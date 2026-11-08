"""Focused regression tests for the c18b572dbe0d ring-replication repair."""
from __future__ import annotations

import copy
import random
import pytest

from puzzle_generators.per_puzzle.c18b572dbe0d import generator as gen
from scripts.canonical_profile_gate import canonical_pairs


def test_canonical_inputs_owned_and_outputs_exact():
    for pair in canonical_pairs("c18b572dbe0d"):
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_regression_full_ring_was_accepted_and_is_now_rejected():
    valid = gen.generate(7001, 2, difficulty="medium", n_cells=4, corner_crossing=False)
    analysis = gen._analyze(valid)
    full_ring = [[8 for _ in row] for row in valid]
    for r, c in analysis["ring"]:
        full_ring[r][c] = analysis["color"]
    errors = gen.self_check(full_ring)
    assert errors
    assert any("segment" in reason or "length" in reason for reason in errors)


def test_mutation_fixtures_all_rejected():
    fixtures = gen.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert gen.self_check(grid), name


def test_exact_overrides_and_unknown_keys():
    grid = gen.generate(
        12345,
        17,
        difficulty="hard",
        grid_h=9,
        grid_w=14,
        n_cells=5,
        color=7,
        corner_crossing=True,
    )
    assert gen.observe_overrides(grid) == {
        "grid_h": 9,
        "grid_w": 14,
        "n_cells": 5,
        "color": 7,
        "corner_crossing": True,
    }
    with pytest.raises(TypeError, match="unknown override"):
        gen.generate(1, 0, typo_axis=3)


def test_canonical_n3_shortcut_is_killed():
    pairs = canonical_pairs("c18b572dbe0d")
    train, query = pairs[:3], pairs[3]
    assert all(gen._rival_skip_unseen_length_three(p["input"]) == p["output"] for p in train)
    assert gen.observe_overrides(query["input"])["n_cells"] == 3
    assert gen._rival_skip_unseen_length_three(query["input"]) != query["output"]


def test_deterministic_fresh_and_global_rng_pure():
    state = random.getstate()
    a = gen.generate(98765, 13, difficulty="medium")
    b = gen.generate(98765, 13, difficulty="medium")
    assert a == b
    assert a is not b and all(ra is not rb for ra, rb in zip(a, b))
    expected = copy.deepcopy(b)
    a[0][0] = (a[0][0] + 1) % 10
    assert gen.generate(98765, 13, difficulty="medium") == expected
    assert random.getstate() == state


def test_every_sliding_four_demo_window_identifies_rule():
    for band_i, band in enumerate(("easy", "medium", "hard")):
        for start in range(4):
            seed = 910000 + 100 * band_i + start
            demos = []
            for offset in range(4):
                grid = gen.generate(seed, start + offset, difficulty=band)
                demos.append({"input": grid, "output": gen.rule_mirror(grid)})
            q = gen.generate(seed, start + 4, difficulty=band)
            assert gen.lesson_identifiable(demos, {"input": q, "output": gen.rule_mirror(q)}) == []
