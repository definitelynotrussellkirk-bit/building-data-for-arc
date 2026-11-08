from __future__ import annotations

import copy
import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash


gen = importlib.import_module(
    "puzzle_generators.per_puzzle.9536d5aef3f6.generator"
)


def _pair(grid):
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_rule_hash_and_all_canonical_pairs_match_python_mirror():
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 5
    assert gen.RULE_HASH == canonical_rule_hash(gen.TASK_ID)
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_exact_axes_round_trip_in_every_band_and_bad_controls_reject():
    for band in ("easy", "medium", "hard"):
        for size, markers in ((5, 3), (10, 8), (7, 5)):
            grid = gen.generate(
                1000 + size * 10 + markers,
                size + markers,
                difficulty=band,
                size=size,
                markers=markers,
            )
            assert gen.observe_overrides(grid) == {
                "size": size,
                "markers": markers,
            }
            assert gen.self_check(grid, difficulty=band) == []

    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 1, typo_axis=7)
    with pytest.raises(ValueError, match="unknown difficulty"):
        gen.generate(1, 1, difficulty="expert")
    with pytest.raises(ValueError, match="size must be an integer"):
        gen.generate(1, 1, size=True)
    with pytest.raises(ValueError, match="markers must be an integer"):
        gen.generate(1, 1, markers=4.5)


def test_self_check_rejects_malformed_and_semantically_weak_inputs():
    assert gen.self_check([[0, 1], [0]])
    assert gen.self_check([[0, 12], [0, 0]])
    assert gen.self_check([[0, True], [0, 0]])
    assert gen.self_check([[0] * 5 for _ in range(5)])

    paired = [[0] * 5 for _ in range(5)]
    paired[0][1] = 2
    paired[1][0] = 2
    paired[0][2] = 3
    assert any("transpose pair" in reason for reason in gen.self_check(paired))

    diagonal_only = [[0] * 5 for _ in range(5)]
    for i, color in enumerate((2, 3, 4)):
        diagonal_only[i][i] = color
    assert any("off-diagonal" in reason for reason in gen.self_check(diagonal_only))


def test_schedule_profiles_cover_the_rule_and_every_three_demo_window_is_identifiable():
    assert len(gen.SCHEDULE_PROFILES) >= 4
    for band in ("easy", "medium", "hard"):
        seen_profiles = set()
        for start in range(len(gen.SCHEDULE_PROFILES) * 2):
            grids = [
                gen.generate(20_000 + start, start + offset, difficulty=band)
                for offset in range(4)
            ]
            seen_profiles.add(gen.schedule_profile(20_000 + start, start, band))
            demos = [_pair(grid) for grid in grids[:3]]
            query = _pair(grids[3])
            assert gen.lesson_identifiable(demos, query) == []
        assert seen_profiles == set(gen.SCHEDULE_PROFILES)


def test_public_upper_only_shortcut_is_killed_by_generated_lower_source():
    for pair in canonical_pairs(gen.TASK_ID):
        assert gen._rival_upper_only(pair["input"]) == pair["output"]

    for band in ("easy", "medium", "hard"):
        found = False
        for sample_index in range(len(gen.SCHEDULE_PROFILES) * 2):
            grid = gen.generate(30_000, sample_index, difficulty=band)
            if gen.SEMANTIC_WITNESSES["lower_source"](grid):
                assert gen._rival_upper_only(grid) != gen.rule_mirror(grid)
                found = True
                break
        assert found, band


def test_fill_empty_only_shortcut_fits_public_pairs_but_is_wrong_on_conflicts():
    for pair in canonical_pairs(gen.TASK_ID):
        assert gen._rival_fill_empty_only(pair["input"]) == pair["output"]

    conflict = [[0] * 5 for _ in range(5)]
    conflict[0][1] = 2
    conflict[1][0] = 3
    conflict[0][2] = 4
    assert gen.self_check(conflict) == []
    assert gen.rule_mirror(conflict)[0][1] == 3
    assert gen.rule_mirror(conflict)[1][0] == 2
    assert gen._rival_fill_empty_only(conflict) != gen.rule_mirror(conflict)


def test_every_three_demo_window_contains_an_unequal_conflict_witness():
    for band in ("easy", "medium", "hard"):
        for start in range(len(gen.SCHEDULE_PROFILES) * 2):
            demos = [
                gen.generate(35_000 + start, start + offset, difficulty=band)
                for offset in range(3)
            ]
            assert any(gen.SEMANTIC_WITNESSES["unequal_conflict"](grid) for grid in demos)
            assert any(
                gen._rival_fill_empty_only(grid) != gen.rule_mirror(grid)
                for grid in demos
            )


def test_conflict_orbit_varies_instead_of_teaching_one_special_coordinate():
    for band in ("easy", "medium", "hard"):
        locations = set()
        for seed in range(24):
            for sample_index in (2, 5):
                grid = gen.generate(50_000 + seed, sample_index, difficulty=band)
                occupied = {
                    (r, c): value
                    for r, row in enumerate(grid)
                    for c, value in enumerate(row)
                    if value != 0
                }
                pairs = [
                    (r, c)
                    for r, c in occupied
                    if r < c and (c, r) in occupied
                ]
                assert len(pairs) == 1
                locations.add(pairs[0])
        assert len(locations) >= 6, (band, locations)
        assert locations != {(0, 1)}


def test_generated_profiles_are_strict_nonidentity_and_canonical_scaled():
    canonical_profiles = {(5, 4), (6, 5), (7, 5), (8, 5)}
    for band in ("easy", "medium", "hard"):
        exact_profiles = set()
        witness_hits = {name: 0 for name in gen.SEMANTIC_WITNESSES}
        for sample_index in range(24):
            grid = gen.generate(40_000 + sample_index, sample_index, difficulty=band)
            assert gen.self_check(grid, difficulty=band) == []
            assert gen.strict_canonical_like(grid) == []
            assert gen.rule_mirror(grid) != grid
            palette_size = len({value for row in grid for value in row})
            exact_profiles.add((len(grid), palette_size))
            for name, predicate in gen.SEMANTIC_WITNESSES.items():
                witness_hits[name] += int(predicate(grid))
        assert exact_profiles & canonical_profiles
        assert all(count > 0 for count in witness_hits.values()), (band, witness_hits)


def test_replay_is_deterministic_fresh_and_global_rng_pure():
    random.seed(8675309)
    state = random.getstate()
    first = gen.generate(31415, 8, difficulty="hard", size=10, markers=8)
    assert random.getstate() == state
    second = gen.generate(31415, 8, difficulty="hard", size=10, markers=8)
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = (first[0][0] + 1) % 10
    assert second == gen.generate(31415, 8, difficulty="hard", size=10, markers=8)
