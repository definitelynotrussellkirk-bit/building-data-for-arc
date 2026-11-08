"""Focused regression tests for the 21ada29469bf generator repair."""
from __future__ import annotations

import copy
import importlib
import random

import pytest

from puzzle_generators import base as gen_base
from puzzle_generators.runner import _apply_rule, _load_bundle, _open_bridge_with_rule
from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash


GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.21ada29469bf.generator"
)
TASK_ID = "21ada29469bf"
BANDS = ("easy", "medium", "hard")


def _pair(grid):
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def _bridge():
    bundle = _load_bundle(TASK_ID)
    return _open_bridge_with_rule(bundle.rule_callable_text)


def test_rule_pin_all_canonical_pairs_and_racket_are_exact():
    assert GEN.GENERATOR_ID == TASK_ID
    assert GEN.TASK_ID == TASK_ID
    assert GEN.VERSION == "4.0.0"
    assert GEN.RULE_HASH == canonical_rule_hash(TASK_ID) == "32d07d8a907c"

    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 3
    bridge, fn_name = _bridge()
    try:
        for pair in pairs:
            source = copy.deepcopy(pair["input"])
            before = copy.deepcopy(source)
            assert GEN.self_check(source) == []
            assert GEN.strict_canonical_like(source) == []
            expected = GEN.rule_mirror(source)
            actual = _apply_rule(bridge, fn_name, source)
            assert actual == expected == pair["output"]
            assert source == before
    finally:
        bridge.shutdown()


def test_every_exact_override_value_and_composition_is_observable():
    case_index = 0
    for band in BANDS:
        for n in (3, 4, 5):
            for row_perm in GEN.PERM_KINDS:
                for col_perm in GEN.PERM_KINDS:
                    if row_perm == col_perm == "identity":
                        continue
                    requested = {
                        "n": n,
                        "row_perm": row_perm,
                        "col_perm": col_perm,
                    }
                    grid = GEN.generate(
                        100_000 + case_index,
                        case_index,
                        difficulty=band,
                        **requested,
                    )
                    assert GEN.self_check(
                        grid,
                        difficulty=band,
                        meta={"overrides": requested},
                    ) == []
                    assert GEN.observe_overrides(grid) == requested
                    case_index += 1

    # A single pinned identity remains usable even when its scheduled partner
    # would otherwise also be identity; only an explicit double identity is
    # forbidden as a no-op lesson.
    row_only = GEN.generate(7, 3, row_perm="identity")
    assert GEN.observe_overrides(row_only)["row_perm"] == "identity"
    assert GEN.observe_overrides(row_only)["col_perm"] != "identity"
    col_only = GEN.generate(7, 2, col_perm="identity")
    assert GEN.observe_overrides(col_only)["col_perm"] == "identity"
    assert GEN.observe_overrides(col_only)["row_perm"] != "identity"


@pytest.mark.parametrize("band", BANDS)
def test_ordinary_draws_round_trip_every_genctx_axis(band):
    for sample_index in range(24):
        contexts = []
        gen_base.set_ctx_observer(contexts.append)
        try:
            grid = GEN.generate(310_000 + sample_index, sample_index, difficulty=band)
        finally:
            gen_base.set_ctx_observer(None)
        assert contexts
        keyed = contexts[-1].recorded_draws()
        assert {name: keyed[name] for name in GEN.AXES} == GEN.observe_overrides(grid)


def test_invalid_overrides_and_unknown_difficulty_reject_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, typo_axis=True)
    with pytest.raises(ValueError):
        GEN.generate(1, 0, n=2)
    with pytest.raises(ValueError):
        GEN.generate(1, 0, n=6)
    with pytest.raises(ValueError):
        GEN.generate(1, 0, row_perm="diagonal")
    with pytest.raises(ValueError):
        GEN.generate(1, 0, col_perm="diagonal")
    with pytest.raises(ValueError, match="incompatible overrides"):
        GEN.generate(1, 0, row_perm="identity", col_perm="identity")
    with pytest.raises(ValueError, match="unknown difficulty"):
        GEN.generate(1, 0, difficulty="nightmare")


@pytest.mark.parametrize("band", BANDS)
def test_every_schedule_residue_window_identifies_the_rule(band):
    period = len(GEN.SCHEDULE_PROFILES)
    assert period == GEN.EXAMPLES_NEEDED == 4
    for start in range(period):
        demos = [
            _pair(GEN.generate(420_000, start + offset, difficulty=band))
            for offset in range(GEN.EXAMPLES_NEEDED)
        ]
        query = _pair(
            GEN.generate(420_000, start + GEN.EXAMPLES_NEEDED, difficulty=band)
        )
        assert GEN.lesson_identifiable(demos, query) == []
        for rival_name, rival in GEN.SEMANTIC_RIVALS.items():
            assert any(rival(item["input"]) != item["output"] for item in demos), (
                band,
                start,
                rival_name,
            )


def test_each_named_witness_fires_and_kills_its_declared_rivals():
    grids = [GEN.generate(530_000, index, difficulty="medium") for index in range(8)]
    for witness_name, rival_names in GEN.WITNESS_RIVALS.items():
        witness = GEN.SEMANTIC_WITNESSES[witness_name]
        firing = next(grid for grid in grids if witness(grid))
        expected = GEN.rule_mirror(firing)
        for rival_name in rival_names:
            assert GEN.SEMANTIC_RIVALS[rival_name](firing) != expected


def test_targeted_mutation_fixtures_are_rejected():
    fixtures = GEN.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, malformed in fixtures:
        assert GEN.self_check(malformed), name


def test_negative_link_recombination_is_not_teaching_data_but_oracle_executes():
    pairs = canonical_pairs(TASK_ID)
    recombined = copy.deepcopy(pairs[0]["input"])
    recombined[0][1:] = copy.deepcopy(pairs[1]["input"][0][1:])

    assert GEN.self_check(recombined) == []
    assert GEN.strict_canonical_like(recombined)

    bridge, fn_name = _bridge()
    try:
        output = _apply_rule(bridge, fn_name, recombined)
    finally:
        bridge.shutdown()
    assert output == GEN.rule_mirror(recombined)
    assert len(output) == 3 and all(len(row) == 3 for row in output)


def test_replay_is_deterministic_fresh_and_global_rng_pure():
    random.seed(20260816)
    before = random.getstate()
    first = GEN.generate(640_000, 11, difficulty="hard")
    middle = random.getstate()
    second = GEN.generate(640_000, 11, difficulty="hard")
    after = random.getstate()

    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    assert before == middle == after
    first[0][0] = 9
    assert second[0][0] == 0
