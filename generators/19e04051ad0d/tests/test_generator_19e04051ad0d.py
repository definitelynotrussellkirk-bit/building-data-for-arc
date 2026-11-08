from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import random

import pytest

from reviewer_support import canonical_pairs, find_root
from arcpuzzles import Catalog

ROOT = find_root(__file__)
SOURCE = ROOT / "generators/19e04051ad0d/generator.py"
if not SOURCE.is_file():
    SOURCE = ROOT / "puzzle_generators/per_puzzle/19e04051ad0d/generator.py"
SPEC = importlib.util.spec_from_file_location("cyclic_region_original_regressions", SOURCE)
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def _pair(grid):
    return {"input": copy.deepcopy(grid), "output": GEN.rule_mirror(grid)}


def test_rule_hash_and_all_canonical_pairs():
    assert GEN.RULE_HASH == Catalog(ROOT).describe(GEN.TASK_ID)["rule_hash"]
    pairs = canonical_pairs(GEN.TASK_ID, root=ROOT)
    assert len(pairs) == 6
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_declared_overrides_round_trip_at_boundaries_and_canonical_layout():
    cases = [
        {"grid_h": 8, "layout": "222", "bg_color": 0},
        {"grid_h": 12, "layout": "232", "bg_color": 9},
        {"grid_h": 10, "layout": "312", "bg_color": 4},
    ]
    for i, overrides in enumerate(cases):
        grid = GEN.generate(7000 + i, i, difficulty="hard", **overrides)
        assert GEN.observe_overrides(grid) == overrides
        assert GEN.self_check(grid) == []


def test_unknown_override_is_rejected_loudly():
    with pytest.raises(ValueError, match="unknown override key"):
        GEN.generate(1, 2, unknown_axis=3)


def test_ordinary_draws_are_strict_and_complete_lessons_kill_all_named_rivals():
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(8):
            grids = [GEN.generate(10000 + seed, index, difficulty=difficulty)
                     for index in range(4)]
            for grid in grids:
                expected = GEN.rule_mirror(grid)
                assert GEN.strict_canonical_like(grid) == []
                assert GEN.observe_overrides(grid)["layout"] != "222"
                # A witness need not fire on every input, but any firing must
                # refute its declared rival on that exact input.
                for name, predicate in GEN.SEMANTIC_WITNESSES.items():
                    if predicate(grid):
                        assert any(GEN.SEMANTIC_RIVALS[rival](grid) != expected
                                   for rival in GEN.WITNESS_RIVALS[name]), name
            for name, rival in GEN.LESSON_COMPETITORS.items():
                assert any(rival(g) != GEN.rule_mirror(g) for g in grids[:3]), name


def test_lessons_are_identifiable_without_schedule_aliasing():
    grids = [GEN.generate(22001, i, difficulty="medium") for i in range(4)]
    pairs = [_pair(grid) for grid in grids]
    assert GEN.lesson_identifiable(pairs[:3], pairs[3]) == []


def test_targeted_mutation_fixtures_are_rejected():
    fixtures = GEN.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert GEN.self_check(grid), name


def test_determinism_fresh_return_and_process_global_rng_purity():
    random.seed(8675309)
    before = random.getstate()
    a = GEN.generate(314159, 7, difficulty="medium")
    middle = random.getstate()
    b = GEN.generate(314159, 7, difficulty="medium")
    after = random.getstate()
    assert a == b
    assert a is not b
    assert all(row_a is not row_b for row_a, row_b in zip(a, b))
    assert before == middle == after

    a[0][0] = (a[0][0] + 1) % 10
    c = GEN.generate(314159, 7, difficulty="medium")
    assert c == b
