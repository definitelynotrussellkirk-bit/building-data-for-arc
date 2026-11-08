"""Task-local regression tests for the repaired periodic-tile generator."""
from __future__ import annotations

from copy import deepcopy
import itertools
import json
import os
from pathlib import Path
import random
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    RULE_HASH,
    authority_files,
    canonical_pairs,
    canonical_program,
    load_generator,
    normalized_rule_hash,
    observed,
    recover_details,
    rule_output,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def _answer(grid):
    return rule_output(deepcopy(grid))


def _top_left_tile_shortcut(grid):
    observed_axes = gen.observe_overrides(grid)
    pr = observed_axes["period_r"]
    pc = observed_axes["period_c"]
    tile = [row[:pc] for row in grid[:pr]]
    return [
        [tile[r % pr][c % pc] for c in range(len(grid[0]))]
        for r in range(len(grid))
    ]


def test_rule_pin_canonical_pairs_and_active_authorities_are_exact():
    assert gen.VERSION == "2.1.0"
    assert gen.RULE_HASH == RULE_HASH
    assert normalized_rule_hash(canonical_program()) == RULE_HASH

    pairs = canonical_pairs()
    assert len(pairs) == 3
    for pair in pairs:
        assert gen.self_check(deepcopy(pair["input"])) == []
        assert gen.strict_canonical_like(deepcopy(pair["input"])) == []
        assert rule_output(deepcopy(pair["input"])) == pair["output"]
        assert gen.rule_mirror(deepcopy(pair["input"])) == pair["output"]

    selected = canonical_program()
    for path in authority_files():
        target = json.loads(path.read_text(encoding="utf-8"))["racket_target"]
        assert target["target_code"] == selected, path
        assert target["raw_code"] != target["target_code"], path


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_every_three_consecutive_draws_cover_schedule_and_refute_shortcuts(difficulty):
    assert gen.EXAMPLES_NEEDED == 3
    assert set(gen.CANONICAL_SHORTCUTS) == {
        "square_period_only",
        "periods_at_most_three",
    }
    assert set(gen.LESSON_COMPETITORS) == {
        "square_period_only",
        "periods_at_most_three",
        "literal_top_left_tile",
    }

    for start in range(12):
        seed = 7000 + start
        grids = [
            gen.generate(seed, start + offset, difficulty=difficulty)
            for offset in range(4)
        ]
        assert {
            gen.schedule_profile(seed, start + offset, difficulty=difficulty)
            for offset in range(3)
        } == set(gen.SCHEDULE_PROFILES)
        for grid in grids:
            assert gen.self_check(grid) == []
            assert gen.rule_mirror(grid) == _answer(grid)

        demos = [{"input": grid, "output": _answer(grid)} for grid in grids[:3]]
        query = {"input": grids[3], "output": _answer(grids[3])}
        assert any(
            not gen.observe_overrides(demo["input"])["clean_anchor"]
            for demo in demos
        )
        assert any(
            _top_left_tile_shortcut(demo["input"]) != demo["output"]
            for demo in demos
        )
        assert gen.lesson_identifiable(demos, query) == []
        for name, rival in gen.LESSON_COMPETITORS.items():
            assert any(rival(demo["input"]) != demo["output"] for demo in demos), name

        for witness_name, rival_names in gen.WITNESS_RIVALS.items():
            witness = gen.SEMANTIC_WITNESSES[witness_name]
            firing = [grid for grid in grids[:3] if witness(grid)]
            assert firing, witness_name
            for grid in firing:
                assert any(
                    gen.SEMANTIC_RIVALS[name](grid) != _answer(grid)
                    for name in rival_names
                )


def test_pinned_production_lesson_teaches_noisy_anchor_recovery():
    seed = 213_974_615_879_964
    start = 66
    grids = [
        gen.generate(seed, start + offset, difficulty="easy")
        for offset in range(4)
    ]
    demos = [{"input": grid, "output": _answer(grid)} for grid in grids[:3]]
    query = {"input": grids[3], "output": _answer(grids[3])}

    assert any(
        not gen.observe_overrides(demo["input"])["clean_anchor"]
        for demo in demos
    )
    assert any(
        _top_left_tile_shortcut(demo["input"]) != demo["output"]
        for demo in demos
    )
    assert gen.lesson_identifiable(demos, query) == []


def test_declared_canonical_shortcuts_fit_every_unique_canonical_pair():
    pairs = canonical_pairs()
    for name, shortcut in gen.CANONICAL_SHORTCUTS.items():
        assert all(shortcut(deepcopy(pair["input"])) == pair["output"] for pair in pairs), name


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_full_override_boundary_cartesian_is_exact_observable_and_safe(difficulty):
    values = {
        "grid_h": (12, 16),
        "grid_w": (12, 19),
        "period_r": (2, 4),
        "period_c": (2, 4),
        "palette_size": (2, 4),
        "noise_count": (1, 64),
        "clean_anchor": (False, True),
    }
    keys = tuple(values)
    for case_index, combo in enumerate(itertools.product(*(values[key] for key in keys))):
        requested = dict(zip(keys, combo, strict=True))
        grid = gen.generate(
            seed=91000 + case_index,
            sample_index=case_index,
            difficulty=difficulty,
            **requested,
        )
        assert gen.self_check(grid) == [], requested
        assert observed(grid) == requested
        assert gen.observe_overrides(grid) == requested
        assert gen.rule_mirror(grid) == _answer(grid)
        assert sum(value == 6 for row in grid for value in row) == requested["noise_count"]


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo_axis": 1},
        {"grid_h": 11},
        {"grid_h": 17},
        {"grid_w": 11},
        {"grid_w": 20},
        {"period_r": 1},
        {"period_r": 5},
        {"period_c": 1},
        {"period_c": 5},
        {"palette_size": 1},
        {"palette_size": 5},
        {"noise_count": 0},
        {"noise_count": 65},
        {"grid_h": True},
        {"period_c": 2.0},
        {"noise_count": "23"},
        {"clean_anchor": 1},
    ],
)
def test_invalid_overrides_are_rejected_loudly(overrides):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 2, **overrides)


def test_invalid_difficulty_is_rejected_loudly():
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(1, 2, difficulty="impossible")


def test_default_schedule_matches_canonical_profiles_and_exact_periods():
    expected_period = {0: (3, 3), 1: (2, 2), 2: (4, 3)}
    expected_scale = {0: (12, 12), 1: (15, 19), 2: (16, 16)}
    for seed in (0, 1, 99, 20261003):
        for sample_index in range(12):
            grid = gen.generate(seed, sample_index, difficulty="hard")
            semantic_profile = gen.schedule_profile(
                seed, sample_index, difficulty="hard"
            )
            actual = observed(grid)
            assert semantic_profile == sample_index % 3
            assert (actual["period_r"], actual["period_c"]) == expected_period[semantic_profile]
            scale_profile = sample_index % 4
            if scale_profile in expected_scale:
                assert (actual["grid_h"], actual["grid_w"]) == expected_scale[scale_profile]
                assert actual["palette_size"] == 2
            else:
                assert actual["grid_h"] == 12
                assert actual["grid_w"] in {13, 14, 15, 17, 18}
                assert actual["palette_size"] in {2, 3, 4}
            assert 45 <= actual["noise_count"] <= 64
            details = recover_details(grid)
            assert details is not None
            _, pr, pc = details
            assert (pr, pc) == expected_period[semantic_profile]


def test_replay_is_fresh_deterministic_and_global_rng_pure():
    random.seed(20261003)
    state = random.getstate()
    first = gen.generate(123, 456, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(123, 456, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert first != second


def test_validator_rejects_structural_corruption_without_mutating_input():
    grid = gen.generate(44, 2, difficulty="medium")
    original = deepcopy(grid)
    assert gen.self_check(grid) == []
    assert grid == original

    mutations = {}
    mutations["blank"] = [[0 for _ in row] for row in grid]
    mutations["all_noise"] = [[6 for _ in row] for row in grid]
    mutations["remove_noise"] = [[0 if value == 6 else value for value in row] for row in grid]
    mutations["ragged"] = [list(row) for row in grid]
    mutations["ragged"][-1].pop()
    mutations["bad_color"] = [list(row) for row in grid]
    mutations["bad_color"][0][0] = 10
    mutations["break_period"] = [list(row) for row in grid]
    clean = _answer(grid)
    mutations["break_period"][0][0] = next(
        color for color in range(10)
        if color not in {6, clean[0][0]}
    )

    for name, mutated in mutations.items():
        assert gen.self_check(mutated), name


def test_rule_mirror_returns_zero_grid_when_no_period_is_recoverable():
    rng = random.Random(99173)
    grid = [[rng.randrange(0, 6) for _ in range(12)] for _ in range(12)]
    assert recover_details(grid) is None
    assert gen.rule_mirror(grid) == [[0] * 12 for _ in range(12)]
