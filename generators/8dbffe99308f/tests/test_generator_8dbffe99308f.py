from __future__ import annotations

import copy
import importlib
import random

import pytest

from reviewer_support import canonical_pairs, find_root


gen = importlib.import_module(
    "puzzle_generators.per_puzzle.8dbffe99308f.generator"
)
ROOT = find_root(__file__)


def _canonical_pairs():
    return canonical_pairs(gen.TASK_ID, root=ROOT)


def _pair(grid):
    return {"input": grid, "output": gen.rule_mirror(grid)}


def _anti_mirror(size, r, c):
    return size - 1 - c, size - 1 - r


def _occupied_pairs(grid):
    size = len(grid)
    occupied = {
        (r, c): value
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    }
    return [
        ((r, c), _anti_mirror(size, r, c))
        for r, c in occupied
        if (r, c) < _anti_mirror(size, r, c)
        and _anti_mirror(size, r, c) in occupied
    ]


def test_rule_hash_and_all_canonical_pairs_match_python_oracle():
    pairs = _canonical_pairs()
    assert len(pairs) == 5
    assert gen.RULE_HASH == "e248d283a2c2"
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_occupied_anti_diagonal_pair_swaps_from_immutable_snapshot():
    grid = [[0] * 6 for _ in range(6)]
    grid[0][1] = 2
    grid[4][5] = 7  # anti-diagonal partner of (0, 1)
    grid[0][0] = 3
    grid[1][1] = 4
    grid[1][2] = 5
    grid[2][0] = 6

    out = gen.rule_mirror(grid)
    assert out[0][1] == 7
    assert out[4][5] == 2
    assert out[0][0] == 3
    assert out[5][5] == 3
    assert grid[0][1] == 2 and grid[4][5] == 7


def test_exact_axes_round_trip_in_every_band_and_bad_controls_reject():
    for band in (None, "easy", "medium", "hard"):
        for size, markers in ((6, 4), (10, 10), (8, 7)):
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
    with pytest.raises(ValueError):
        gen.generate(1, 1, size=5)
    with pytest.raises(ValueError):
        gen.generate(1, 1, markers=11)


def test_self_check_rejects_malformed_and_semantically_weak_inputs():
    assert gen.self_check(None)
    assert gen.self_check([])
    assert gen.self_check([[]])
    assert gen.self_check([[0, 1], [0]])
    assert gen.self_check([[0, 12], [0, 0]])
    assert gen.self_check([[0, True], [0, 0]])
    assert gen.self_check([[0] * 6 for _ in range(6)])

    diagonal_only = [[0] * 6 for _ in range(6)]
    for r, color in enumerate((1, 2, 3, 4)):
        diagonal_only[r][5 - r] = color
    assert any("off the anti-diagonal" in reason for reason in gen.self_check(diagonal_only))

    equal_pair = [[0] * 6 for _ in range(6)]
    for (r, c), color in {
        (0, 1): 2,
        (4, 5): 2,
        (0, 0): 3,
        (1, 1): 4,
        (1, 2): 5,
        (2, 0): 6,
    }.items():
        equal_pair[r][c] = color
    assert any("unequal colors" in reason for reason in gen.self_check(equal_pair))

    two_pairs = copy.deepcopy(equal_pair)
    two_pairs[0][1], two_pairs[4][5] = 2, 7
    two_pairs[0][2], two_pairs[3][5] = 3, 8
    assert any("more than one" in reason for reason in gen.self_check(two_pairs))


def test_schedule_profiles_cover_rule_and_every_three_demo_window_is_identifiable():
    assert len(gen.SCHEDULE_PROFILES) == 6
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


def test_every_four_pair_lesson_is_identifiable_under_any_query_rotation():
    for band in ("easy", "medium", "hard"):
        for start in range(len(gen.SCHEDULE_PROFILES) * 2):
            grids = [
                gen.generate(25_000 + start, start + offset, difficulty=band)
                for offset in range(4)
            ]
            assert sum(
                gen.SEMANTIC_WITNESSES["unequal_conflict"](grid)
                for grid in grids
            ) >= 2
            pairs = [_pair(grid) for grid in grids]
            for query_index in range(4):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                assert gen.lesson_identifiable(demos, pairs[query_index]) == []


def test_canonical_shortcuts_fit_public_pairs_but_generated_witnesses_refute_them():
    pairs = _canonical_pairs()
    for pair in pairs:
        assert gen._rival_above_only(pair["input"]) == pair["output"]
        assert gen._rival_fill_empty_only(pair["input"]) == pair["output"]

    for band in ("easy", "medium", "hard"):
        witness_hits = {name: 0 for name in gen.SEMANTIC_WITNESSES}
        for sample_index in range(12):
            grid = gen.generate(30_000, sample_index, difficulty=band)
            expected = gen.rule_mirror(grid)
            for name, predicate in gen.SEMANTIC_WITNESSES.items():
                if predicate(grid):
                    witness_hits[name] += 1
                    for rival_name in gen.WITNESS_RIVALS[name]:
                        assert gen.SEMANTIC_RIVALS[rival_name](grid) != expected
        assert all(count > 0 for count in witness_hits.values()), (band, witness_hits)


def test_conflict_orbit_varies_instead_of_teaching_one_special_coordinate():
    for band in ("easy", "medium", "hard"):
        locations = set()
        for seed in range(24):
            for sample_index in (1, 3, 5):
                grid = gen.generate(50_000 + seed, sample_index, difficulty=band)
                pairs = _occupied_pairs(grid)
                assert len(pairs) == 1
                locations.add(pairs[0][0])
        assert len(locations) >= 6, (band, locations)
        assert locations != {(0, 1)}


def test_generated_profiles_are_strict_nonidentity_and_canonical_scaled():
    canonical_profiles = {
        (
            len(pair["input"]),
            len(pair["input"][0]),
            len({value for row in pair["input"] for value in row}),
        )
        for pair in _canonical_pairs()
    }
    for band in ("easy", "medium", "hard"):
        exact_profiles = set()
        witness_hits = {name: 0 for name in gen.SEMANTIC_WITNESSES}
        for sample_index in range(24):
            grid = gen.generate(40_000 + sample_index, sample_index, difficulty=band)
            assert gen.self_check(grid, difficulty=band) == []
            assert gen.strict_canonical_like(grid) == []
            assert gen.rule_mirror(grid) != grid
            exact_profiles.add(
                (len(grid), len(grid[0]), len({value for row in grid for value in row}))
            )
            for name, predicate in gen.SEMANTIC_WITNESSES.items():
                witness_hits[name] += int(predicate(grid))
        assert exact_profiles & canonical_profiles
        assert all(count > 0 for count in witness_hits.values()), (band, witness_hits)


def test_replay_is_deterministic_fresh_and_global_rng_pure():
    random.seed(8675309)
    state = random.getstate()
    first = gen.generate(31415, 8, difficulty="hard", size=10, markers=10)
    assert random.getstate() == state
    second = gen.generate(31415, 8, difficulty="hard", size=10, markers=10)
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = (first[0][0] + 1) % 10
    assert second == gen.generate(31415, 8, difficulty="hard", size=10, markers=10)


def test_workspace_schedule_probe_exhausts_cyclic_starts_and_rotations():
    probe_path = (
        ROOT
        / "generators"
        / gen.TASK_ID
        / "workspace"
        / "schedule_probe.py"
    )
    spec = importlib.util.spec_from_file_location("schedule_probe", probe_path)
    assert spec is not None and spec.loader is not None
    probe_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe_module)

    report = probe_module.probe_generator(
        gen,
        bands=("easy", "medium", "hard"),
        seeds=(61_001, 61_002),
        cycles=2,
    )
    assert report["ambiguous_rotation_count"] == 0
    assert report["checked_lessons"] == 3 * 2 * 12
    assert report["checked_rotations"] == 3 * 2 * 12 * 4
    assert report["minimum_conflicts_per_lesson"] >= 2
    assert report["generator_sha256"]
