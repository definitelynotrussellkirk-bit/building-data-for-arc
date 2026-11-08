from __future__ import annotations

import copy
import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash


gen = importlib.import_module("puzzle_generators.per_puzzle.7fc997c58be3.generator")


BANDS = ("easy", "medium", "hard")


def _pair(grid):
    return {"input": copy.deepcopy(grid), "output": gen.rule_mirror(grid)}


def test_rule_hash_and_all_canonical_pairs_are_exact() -> None:
    assert gen.RULE_HASH == canonical_rule_hash(gen.TASK_ID) == "10ffeef3b427"
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 4
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        source_before = copy.deepcopy(source)
        assert gen.self_check(source) == []
        assert gen.strict_canonical_like(source) == []
        assert gen.rule_mirror(source) == pair["output"]
        assert source == source_before


def test_default_draws_are_valid_exact_observable_and_cover_schedule() -> None:
    for band in BANDS:
        profiles: set[str] = set()
        layouts: set[str] = set()
        strict = 0
        for sample_index in range(50):
            grid = gen.generate(5003, sample_index, difficulty=band)
            assert gen.self_check(grid) == []
            observed = gen.observe_overrides(grid)
            assert 10 <= observed["grid_h"] <= 18
            assert 10 <= observed["grid_w"] <= 18
            assert 1 <= observed["target_color"] <= 9
            assert 3 <= observed["n_target_copies"] <= 8
            assert 5 <= observed["palette_size"] <= 10
            assert 20 <= observed["decoy_count"] <= 48
            layouts.add(observed["target_layout"])
            profiles.add(gen.schedule_profile(5003, sample_index, band))
            strict += gen.strict_canonical_like(grid) == []
        assert profiles == set(gen.SCHEDULE_PROFILES)
        assert layouts == set(gen.TARGET_LAYOUTS)
        assert strict >= 18


def test_all_boundary_override_combinations_are_exact_in_every_band() -> None:
    boundary_sets = (
        {
            "grid_h": 10,
            "grid_w": 10,
            "target_color": 1,
            "n_target_copies": 3,
            "palette_size": 5,
            "decoy_count": 20,
        },
        {
            "grid_h": 18,
            "grid_w": 18,
            "target_color": 9,
            "n_target_copies": 8,
            "palette_size": 10,
            "decoy_count": 48,
        },
    )
    for band in BANDS:
        for layout in gen.TARGET_LAYOUTS:
            for boundary in boundary_sets:
                overrides = {**boundary, "target_layout": layout}
                grid = gen.generate(991, 17, difficulty=band, **overrides)
                assert gen.self_check(grid) == []
                assert gen.observe_overrides(grid) == overrides


def test_unknown_override_and_invalid_values_fail_loudly() -> None:
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, imaginary_axis=3)
    with pytest.raises(ValueError, match="outside"):
        gen.generate(1, 0, grid_h=9)
    with pytest.raises(ValueError, match="not in options"):
        gen.generate(1, 0, target_layout="corners")
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(1, 0, difficulty="expert")


def test_replay_fresh_returns_and_global_rng_purity() -> None:
    random.seed(8675309)
    before = random.getstate()
    first = gen.generate(77, 8, difficulty="hard")
    after = random.getstate()
    second = gen.generate(77, 8, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(row_a is not row_b for row_a, row_b in zip(first, second))
    first[0][0] = (first[0][0] + 1) % 10
    assert gen.generate(77, 8, difficulty="hard") == second


def test_every_witness_fires_and_verified_rival_disagrees() -> None:
    seen = {name: False for name in gen.SEMANTIC_WITNESSES}
    for band in BANDS:
        for sample_index in range(30):
            grid = gen.generate(1201, sample_index, difficulty=band)
            answer = gen.rule_mirror(grid)
            for name, predicate in gen.SEMANTIC_WITNESSES.items():
                if not predicate(grid):
                    continue
                seen[name] = True
                named = gen.WITNESS_RIVALS[name]
                assert named
                assert any(gen.SEMANTIC_RIVALS[rival](grid) != answer for rival in named)
    assert all(seen.values())


def test_every_sliding_lesson_window_is_identifiable() -> None:
    for band in BANDS:
        for start in range(25):
            pairs = [
                _pair(gen.generate(8128, start + offset, difficulty=band))
                for offset in range(gen.EXAMPLES_NEEDED + 1)
            ]
            assert gen.lesson_identifiable(pairs[:-1], pairs[-1]) == []


def test_negative_recombination_names_surviving_canonical_shortcut() -> None:
    canonical = canonical_pairs(gen.TASK_ID)
    demos = copy.deepcopy(canonical[:3])
    query = _pair(
        gen.generate(
            48,
            7,
            difficulty="medium",
            target_layout="cluster",
            target_color=6,
        )
    )
    reasons = gen.lesson_identifiable(demos, query)
    assert any("erase_only_isolated_targets" in reason for reason in reasons)


def test_task_specific_mutation_fixtures_are_rejected() -> None:
    fixtures = gen.mutation_fixtures()
    assert len(fixtures) >= 4
    names = set()
    for name, grid in fixtures:
        names.add(name)
        assert gen.self_check(grid), name
    assert len(names) == len(fixtures)


def test_meta_observability_detects_mismatch() -> None:
    grid = gen.generate(15, 2, difficulty="easy")
    observed = gen.observe_overrides(grid)
    wrong = dict(observed)
    wrong["target_color"] = 1 + observed["target_color"] % 9
    assert gen.self_check(grid, meta={"overrides": wrong})
