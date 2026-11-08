from __future__ import annotations

import copy
import importlib
import random

import pytest

from puzzle_generators import base
from scripts.canonical_profile_gate import canonical_pairs


gen = importlib.import_module(
    "puzzle_generators.per_puzzle.5d321adb3a28.generator"
)


def _pair(seed: int, sample_index: int, band: str) -> dict:
    grid = gen.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_rule_hash_and_all_canonical_pairs_are_exact_and_input_pure():
    assert gen.RULE_HASH == "980e1ed5540b"
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 4
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_draws_are_lawful_exact_and_observable(band):
    for sample_index in range(24):
        captured = []
        base.set_ctx_observer(captured.append)
        try:
            grid = gen.generate(3100 + sample_index, sample_index, difficulty=band)
        finally:
            base.set_ctx_observer(None)
        assert gen.self_check(grid) == []
        recorded = {
            key: value
            for key, value in captured[-1].recorded_draws().items()
            if key in gen.AXES
        }
        assert recorded == gen.observe_overrides(grid)
        output = gen.rule_mirror(grid)
        changed = sum(
            left != right
            for input_row, output_row in zip(grid, output)
            for left, right in zip(input_row, output_row)
        )
        assert changed == 2


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_exact_override_cross_product_round_trips(band):
    for profile in gen.SCENE_PROFILES:
        for relation in gen.TARGET_RELATIONS:
            grid = gen.generate(
                99,
                17,
                difficulty=band,
                scene_profile=profile,
                target_relation=relation,
            )
            assert gen.self_check(grid) == []
            assert gen.observe_overrides(grid) == {
                "scene_profile": profile,
                "target_relation": relation,
            }


def test_unknown_override_fails_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(0, 0, typo_palette="warm")


def test_every_three_demo_window_refutes_every_named_competitor():
    for band in ("easy", "medium", "hard"):
        for start in range(12):
            pairs = [_pair(7000 + start, start + offset, band) for offset in range(4)]
            demos = pairs[: gen.EXAMPLES_NEEDED]
            query = pairs[gen.EXAMPLES_NEEDED]
            assert gen.lesson_identifiable(demos, query) == []
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(
                    rival(pair["input"]) != pair["output"] for pair in demos
                ), name


def test_every_semantic_witness_fires_in_every_generated_draw():
    for band in ("easy", "medium", "hard"):
        for seed in range(30):
            grid = gen.generate(9000 + seed, seed, difficulty=band)
            for name, witness in gen.SEMANTIC_WITNESSES.items():
                assert witness(grid), (band, seed, name)


def test_every_task_specific_mutation_is_rejected():
    fixtures = list(gen.mutation_fixtures())
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert gen.self_check(grid), name


def test_deterministic_fresh_return_and_global_rng_purity():
    random.seed(2026)
    before_state = random.getstate()
    first = gen.generate(314159, 7, difficulty="hard")
    after_state = random.getstate()
    second = gen.generate(314159, 7, difficulty="hard")
    assert before_state == after_state
    assert first == second
    assert first is not second
    first[0][0] = 9
    assert second[0][0] != 9
