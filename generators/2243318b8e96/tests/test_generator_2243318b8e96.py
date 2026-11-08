"""Focused tests for the repaired size-parity base generator."""
from __future__ import annotations

import copy
import importlib
import random

import pytest

from puzzle_generators import base as gen_base
from reviewer_support import canonical_pairs, find_root

GEN = importlib.import_module("puzzle_generators.per_puzzle.2243318b8e96.generator")
TASK_ID = "2243318b8e96"
BANDS = ("easy", "medium", "hard")


def _pair(grid):
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def test_rule_pin_and_every_canonical_pair_match_the_python_mirror():
    assert GEN.GENERATOR_ID == GEN.TASK_ID == TASK_ID
    assert GEN.RULE_HASH == "419ce8882a3d"
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert len(pairs) == 3
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        before = copy.deepcopy(source)
        assert GEN.self_check(source) == []
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == before


def test_exact_override_boundaries_are_observable_and_lawful():
    case = 0
    for grid_h in (8, 16):
        for grid_w in (8, 16):
            for n_blobs in (3, 6):
                for n_distinct_colors in (1, 3):
                    requested = {
                        "grid_h": grid_h,
                        "grid_w": grid_w,
                        "n_blobs": n_blobs,
                        "n_distinct_colors": n_distinct_colors,
                    }
                    grid = GEN.generate(1000 + case, case, difficulty="easy", **requested)
                    assert GEN.self_check(grid, difficulty="easy", meta={"overrides": requested}) == []
                    assert GEN.observe_overrides(grid) == requested
                    case += 1


@pytest.mark.parametrize("band", BANDS)
def test_ordinary_draws_round_trip_every_declared_axis(band):
    for sample_index in range(18):
        contexts = []
        gen_base.set_ctx_observer(contexts.append)
        try:
            grid = GEN.generate(41_000 + sample_index, sample_index, difficulty=band)
        finally:
            gen_base.set_ctx_observer(None)
        assert contexts
        draws = contexts[-1].recorded_draws()
        assert {name: draws[name] for name in GEN.AXES} == GEN.observe_overrides(grid)
        assert GEN.self_check(grid, difficulty=band) == []


@pytest.mark.parametrize("name,value", [
    ("seed", True), ("seed", 1.0), ("seed", "1"),
    ("sample_index", True), ("sample_index", 1.0), ("sample_index", "1"),
])
def test_call_identity_rejects_non_exact_integers(name, value):
    kwargs = {"seed": 1, "sample_index": 0}
    kwargs[name] = value
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(**kwargs)


def test_invalid_calls_and_overrides_reject_loudly():
    with pytest.raises(ValueError, match="nonnegative"):
        GEN.generate(1, -1)
    with pytest.raises(ValueError, match="unknown difficulty"):
        GEN.generate(1, 0, difficulty="nightmare")
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, typo_axis=7)
    for axis, value in (("grid_h", True), ("grid_w", 9.0),
                        ("n_blobs", "4"), ("n_distinct_colors", False)):
        with pytest.raises((TypeError, ValueError)):
            GEN.generate(1, 0, **{axis: value})
    with pytest.raises(ValueError):
        GEN.generate(1, 0, grid_h=7)
    with pytest.raises(ValueError):
        GEN.generate(1, 0, n_blobs=7)
    with pytest.raises(ValueError):
        GEN.generate(1, 0, n_distinct_colors=4)


def test_only_the_eight_connected_rival_is_declared_canonical_ambiguous():
    assert set(GEN.CANONICAL_SHORTCUTS) == {"eight_connected_components"}
    assert set(GEN.LESSON_COMPETITORS) == set(GEN.SEMANTIC_RIVALS)


def test_every_schedule_window_refutes_every_named_competitor():
    assert GEN.EXAMPLES_NEEDED == len(GEN.SCHEDULE_PROFILES) == 3
    for start in range(len(GEN.SCHEDULE_PROFILES)):
        demos = [_pair(GEN.generate(72_001, start + offset, difficulty="medium"))
                 for offset in range(GEN.EXAMPLES_NEEDED)]
        query_grid = GEN.generate(72_001, start + GEN.EXAMPLES_NEEDED, difficulty="medium")
        assert GEN.lesson_identifiable(demos, _pair(query_grid)) == []
        for name, rival in GEN.SEMANTIC_RIVALS.items():
            assert any(rival(pair["input"]) != pair["output"] for pair in demos), name


def test_mutation_fixtures_are_rejected():
    fixtures = GEN.mutation_fixtures()
    assert len(fixtures) >= 5
    for name, malformed in fixtures:
        assert GEN.self_check(malformed), name


def test_replay_is_deterministic_fresh_and_global_rng_pure():
    random.seed(20261026)
    before = random.getstate()
    first = GEN.generate(991_337, 7, difficulty="hard")
    middle = random.getstate()
    second = GEN.generate(991_337, 7, difficulty="hard")
    after = random.getstate()
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert before == middle == after
