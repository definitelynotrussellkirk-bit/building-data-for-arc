from __future__ import annotations

import copy
import random

import pytest

from puzzle_generators.per_puzzle.bfa4f83b9dbd import generator as gen
from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash

TASK_ID = "bfa4f83b9dbd"


def _pair(seed: int, sample_index: int, band: str):
    grid = gen.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": gen._expected_output(grid)}


def test_rule_hash_matches_selected_canonical_rule():
    assert gen.RULE_HASH == canonical_rule_hash(TASK_ID) == "45804b5cdffe"


def test_every_canonical_input_is_owned_by_structural_and_strict_contract():
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(copy.deepcopy(pair["input"])) == []
        assert gen.strict_canonical_like(copy.deepcopy(pair["input"])) == []


def test_all_declared_override_boundaries_are_exact_and_unknown_keys_reject():
    for band in ("easy", "medium", "hard"):
        for h in range(7, 10):
            for w in range(8, 12):
                for n_markers in (2, 3):
                    grid = gen.generate(
                        1000 + h * 100 + w * 10 + n_markers,
                        h + w + n_markers,
                        difficulty=band,
                        grid_h=h,
                        grid_w=w,
                        n_markers=n_markers,
                    )
                    assert gen.observe_overrides(grid) == {
                        "grid_h": h,
                        "grid_w": w,
                        "n_markers": n_markers,
                    }
                    assert gen.self_check(grid) == []
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, difficulty="easy", misspelled_axis=1)


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    random.seed(123456)
    before = random.getstate()
    first = gen.generate(77, 9, difficulty="hard")
    middle = random.getstate()
    second = gen.generate(77, 9, difficulty="hard")
    after = random.getstate()
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert before == middle == after


def test_self_check_rejects_targeted_structural_impostors():
    blank = [[0] * 9 for _ in range(7)]
    assert gen.self_check(blank)

    one = copy.deepcopy(blank)
    one[3][4] = 2
    assert gen.self_check(one)

    border = copy.deepcopy(blank)
    border[0][3] = 2
    border[4][6] = 7
    assert gen.self_check(border)

    adjacent = copy.deepcopy(blank)
    adjacent[2][2] = 2
    adjacent[2][3] = 7
    assert gen.self_check(adjacent)

    overlapping_pluses = copy.deepcopy(blank)
    overlapping_pluses[2][2] = 2
    overlapping_pluses[3][3] = 7
    assert any("overlapping plus footprints" in item for item in gen.self_check(overlapping_pluses))

    bad_cell = copy.deepcopy(blank)
    bad_cell[2][2] = 12
    bad_cell[4][6] = 7
    assert gen.self_check(bad_cell)


def test_semantic_witnesses_fire_and_named_rivals_disagree():
    for band, seed in (("easy", 2201), ("medium", 2202), ("hard", 2203)):
        grid = gen.generate(seed, 17, difficulty=band)
        expected = gen._expected_output(grid)
        assert gen.strict_canonical_like(grid) == []
        assert all(predicate(grid) for predicate in gen.SEMANTIC_WITNESSES.values())
        for rival in gen.SEMANTIC_RIVALS.values():
            assert rival(grid) != expected


def test_two_demo_sliding_lessons_are_identifiable():
    for band, seed in (("easy", 3001), ("medium", 3002), ("hard", 3003)):
        pairs = [_pair(seed, index, band) for index in range(7)]
        for start in range(5):
            assert gen.lesson_identifiable(pairs[start:start + 2], pairs[start + 2]) == []


def test_strict_semantic_census_200_per_band_and_observable_axes():
    for band_index, band in enumerate(("easy", "medium", "hard")):
        strict_hits = 0
        distinct_inputs = set()
        marker_counts = set()
        for index in range(200):
            grid = gen.generate(500_000 + band_index * 10_000 + index, index * 13 + 7, difficulty=band)
            strict_hits += int(gen.strict_canonical_like(grid) == [])
            observed = gen.observe_overrides(grid)
            marker_counts.add(observed["n_markers"])
            distinct_inputs.add(tuple(tuple(row) for row in grid))
        assert strict_hits == 200
        assert len(distinct_inputs) >= 190
        assert marker_counts == {2, 3}
