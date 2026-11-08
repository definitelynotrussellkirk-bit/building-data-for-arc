from __future__ import annotations

import copy
import random

import pytest

import importlib

gen = importlib.import_module("puzzle_generators.per_puzzle.3f4b5ff68c93.generator")
from scripts.canonical_profile_gate import canonical_pairs


def _pair(seed: int, sample_index: int, band: str = "medium") -> dict:
    grid = gen.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_canonical_pairs_are_owned_and_transposed_exactly() -> None:
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(copy.deepcopy(pair["input"])) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_exact_axes_are_observable_and_unknown_keys_reject() -> None:
    for n in range(5, 9):
        for count in (4, 5):
            for palette in (4, 5):
                for pattern in gen.POSITION_PATTERNS:
                    overrides = {
                        "grid_size": n,
                        "cell_count": count,
                        "palette_size": palette,
                        "position_pattern": pattern,
                    }
                    if palette > count:
                        with pytest.raises(ValueError):
                            gen.generate(41, 7, difficulty="medium", **overrides)
                        continue
                    grid = gen.generate(41, 7, difficulty="medium", **overrides)
                    assert gen.observe_overrides(grid) == overrides
                    assert gen.self_check(grid) == []
    with pytest.raises(TypeError):
        gen.generate(1, 0, mystery_axis="not allowed")


def test_replay_freshness_and_global_rng_purity() -> None:
    before = random.getstate()
    first = gen.generate(20260728, 11, difficulty="hard")
    middle = gen.generate(9, 3, difficulty="easy")
    second = gen.generate(20260728, 11, difficulty="hard")
    after = random.getstate()
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert middle != first
    assert before == after


def test_mutation_fixtures_are_rejected() -> None:
    fixtures = gen.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert gen.self_check(grid), name


def test_every_four_demo_window_identifies_all_scheduled_branches() -> None:
    for band in ("easy", "medium", "hard"):
        for start in range(8):
            demos = [_pair(7000 + start, start + offset, band) for offset in range(4)]
            query = _pair(8000 + start, start + 4, band)
            assert gen.lesson_identifiable(demos, query) == []
            assert {
                gen.observe_overrides(pair["input"])["position_pattern"]
                for pair in demos
            } == set(gen.POSITION_PATTERNS)
