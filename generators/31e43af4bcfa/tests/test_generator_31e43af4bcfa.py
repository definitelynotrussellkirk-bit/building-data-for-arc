"""Focused regression tests for generator 31e43af4bcfa."""

from __future__ import annotations

import copy
import importlib.util
import random

import pytest

from reviewer_support import canonical_pairs, find_root


ROOT = find_root(__file__)
SOURCE = next(path for path in (
    ROOT / "generators/31e43af4bcfa/generator.py",
    ROOT / "puzzle_generators/per_puzzle/31e43af4bcfa/generator.py",
) if path.is_file())
SPEC = importlib.util.spec_from_file_location("inventory_existing_test", SOURCE)
gen = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gen)


def test_all_canonical_inputs_are_accepted_and_mirror_matches_outputs():
    pairs = canonical_pairs(gen.TASK_ID, root=ROOT)
    assert len(pairs) == 3
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


def test_unknown_override_and_invalid_difficulty_are_rejected():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, typo_axis=7)
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(1, 0, difficulty="extreme")


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_exact_override_boundaries_are_observable_in_every_band(band):
    cases = (
        {"K": 2, "grid_h": 5, "grid_w": 7},
        {"K": 4, "grid_h": 9, "grid_w": 13},
        {"K": 4, "grid_h": 5, "grid_w": 7},
    )
    for index, overrides in enumerate(cases):
        grid = gen.generate(1000 + index, index, difficulty=band, **overrides)
        assert gen.self_check(grid) == []
        assert gen.observe_overrides(grid) == overrides


def test_three_profile_schedule_is_witnessed_in_every_sliding_window():
    for start in range(12):
        seen = set()
        demos = []
        for index in range(start, start + gen.EXAMPLES_NEEDED):
            grid = gen.generate(77, index, difficulty="medium")
            profile = gen.schedule_profile(77, index, "medium")
            assert gen.SEMANTIC_WITNESSES[profile](grid)
            seen.add(profile)
            demos.append({"input": grid, "output": gen.rule_mirror(grid)})
        assert seen == set(gen.SCHEDULE_PROFILES)
        query_grid = gen.generate(77, start + gen.EXAMPLES_NEEDED, difficulty="medium")
        query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
        assert gen.lesson_identifiable(demos, query) == []


def test_each_scheduled_witness_kills_its_named_rival():
    for index, profile in enumerate(gen.SCHEDULE_PROFILES):
        grid = gen.generate(91, index, difficulty="hard")
        official = gen.rule_mirror(grid)
        assert gen.SEMANTIC_WITNESSES[profile](grid)
        for rival_name in gen.WITNESS_RIVALS[profile]:
            assert gen.SEMANTIC_RIVALS[rival_name](grid) != official


def test_structural_mutations_are_rejected():
    base = gen.generate(31, 1, difficulty="medium")

    hole = copy.deepcopy(base)
    hole[0][1] = 0
    assert any("contiguous" in error for error in gen.self_check(hole))

    duplicate_palette = copy.deepcopy(base)
    duplicate_palette[0][1] = duplicate_palette[0][0]
    assert any("distinct" in error for error in gen.self_check(duplicate_palette))

    foreign_body_color = copy.deepcopy(base)
    target = next(
        (r, c)
        for r in range(1, len(base))
        for c in range(len(base[0]))
        if base[r][c] == 0
    )
    foreign_body_color[target[0]][target[1]] = 9
    assert any("body" in error for error in gen.self_check(foreign_body_color))

    missing_component = copy.deepcopy(base)
    component = gen._components_ones(missing_component)[0]
    for r, c in component:
        missing_component[r][c] = 0
    assert any("body components" in error for error in gen.self_check(missing_component))

    invalid_color = copy.deepcopy(base)
    invalid_color[0][0] = 10
    assert any("invalid ARC colors" in error for error in gen.self_check(invalid_color))


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(123456)
    before = random.getstate()
    first = gen.generate(222, 8, difficulty="easy")
    after = random.getstate()
    second = gen.generate(222, 8, difficulty="easy")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert before == after
