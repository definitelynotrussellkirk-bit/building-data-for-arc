from __future__ import annotations

import copy
import random

import pytest

from puzzle_generators import base
from scripts.canonical_profile_gate import canonical_pairs

import importlib

gen = importlib.import_module("puzzle_generators.per_puzzle.17018eeb34da.generator")


def _pair(seed: int, sample_index: int, band: str) -> dict:
    grid = gen.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_rule_hash_and_all_canonical_pairs_are_exact_and_input_pure():
    assert gen.RULE_HASH == "0ce6913875ad"
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 3
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


def test_default_draws_are_lawful_and_exact_provenance_is_observable():
    for band in ("easy", "medium", "hard"):
        for sample_index in range(18):
            captured = []
            base.set_ctx_observer(captured.append)
            try:
                grid = gen.generate(4100 + sample_index, sample_index, difficulty=band)
            finally:
                base.set_ctx_observer(None)
            assert gen.self_check(grid) == []
            recorded_axes = {
                key: value
                for key, value in captured[-1].recorded_draws().items()
                if key in gen.AXES
            }
            assert recorded_axes == gen.observe_overrides(grid)


def test_every_three_demo_sliding_window_refutes_every_named_competitor():
    for band in ("easy", "medium", "hard"):
        for start in range(12):
            pairs = [_pair(7000 + start, start + offset, band) for offset in range(4)]
            demos, query = pairs[: gen.EXAMPLES_NEEDED], pairs[gen.EXAMPLES_NEEDED]
            assert gen.lesson_identifiable(demos, query) == []
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(rival(pair["input"]) != pair["output"] for pair in demos), name


def test_six_slot_schedule_has_all_profiles_in_each_cycle():
    expected = set(gen.SCHEDULE_PROFILES)
    for start in range(6):
        observed = {gen.schedule_profile(0, start + offset) for offset in range(6)}
        assert observed == expected


def test_exact_override_cross_product_round_trips_or_rejects_declared_conflict():
    for band in ("easy", "medium", "hard"):
        for grid_h in (7, 10):
            for grid_w in (7, 10):
                for n_pairs in (2, 4):
                    for source_uses in (2, 3):
                        for unchanged_targets in (0, 1):
                            for legend_layout in gen.LEGEND_LAYOUTS:
                                for mapping_overlap in gen.MAPPING_OVERLAPS:
                                    requested = {
                                        "grid_h": grid_h,
                                        "grid_w": grid_w,
                                        "n_pairs": n_pairs,
                                        "source_uses": source_uses,
                                        "unchanged_targets": unchanged_targets,
                                        "legend_layout": legend_layout,
                                        "mapping_overlap": mapping_overlap,
                                    }
                                    if legend_layout == "shifted_even" and n_pairs == 4 and grid_w == 7:
                                        with pytest.raises(ValueError, match="shifted-even"):
                                            gen.generate(99, 17, difficulty=band, **requested)
                                        continue
                                    grid = gen.generate(99, 17, difficulty=band, **requested)
                                    assert gen.self_check(grid) == []
                                    assert gen.observe_overrides(grid) == requested


def test_unknown_override_fails_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(0, 0, typo_palette="warm")


def test_self_check_rejects_targeted_structural_impostors():
    valid = gen.generate(1234, 3, difficulty="medium")
    columns, sources, destinations = gen._legend(valid)

    no_legend = copy.deepcopy(valid)
    no_legend[0] = [0] * len(no_legend[0])
    no_legend[1] = [0] * len(no_legend[1])

    half_pair = copy.deepcopy(valid)
    half_pair[1][columns[0]] = 0

    duplicate_source = copy.deepcopy(valid)
    duplicate_source[0][columns[1]] = duplicate_source[0][columns[0]]

    identity_pair = copy.deepcopy(valid)
    identity_pair[1][columns[0]] = identity_pair[0][columns[0]]

    unknown_body = copy.deepcopy(valid)
    allowed = set(sources) | set(destinations) | {0}
    foreign = next(color for color in range(1, 10) if color not in allowed)
    unknown_body[2][0] = foreign

    missing_source = copy.deepcopy(valid)
    missing = sources[0]
    for r in range(2, len(missing_source)):
        for c, value in enumerate(missing_source[r]):
            if value == missing:
                missing_source[r][c] = 0

    fixtures = [no_legend, half_pair, duplicate_source, identity_pair, unknown_body, missing_source]
    for fixture in fixtures:
        assert gen.self_check(fixture), fixture


def test_deterministic_fresh_returns_global_rng_and_reentrant_aba():
    random.seed(20260726)
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
    assert gen.rule_mirror(a) == gen.rule_mirror(a)
    gen.rule_mirror(b)
    assert gen.rule_mirror(a) == gen.rule_mirror(a_again)
    assert a == a_before
    assert b == b_before
