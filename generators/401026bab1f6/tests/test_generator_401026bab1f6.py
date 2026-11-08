from __future__ import annotations

import copy
import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs


TASK_ID = "401026bab1f6"
gen = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")


def _pair(grid):
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_rule_hash_and_all_canonical_pairs():
    assert gen.RULE_HASH == "5539aa3ad4f4"
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 4
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


def test_exact_override_boundaries_and_unknown_keys():
    cases = (
        {"grid_h": 10},
        {"grid_h": 24},
        {"grid_w": 10},
        {"grid_w": 26},
        {"n_frames": 1},
        {"n_frames": 3},
        {"pattern_mode": "top_only"},
        {"pattern_mode": "bottom_only"},
        {"pattern_mode": "mixed"},
        {"pattern_mode": "blocked"},
        {"grid_h": 10, "grid_w": 10, "n_frames": 3, "pattern_mode": "blocked"},
        {"grid_h": 24, "grid_w": 26, "n_frames": 3, "pattern_mode": "mixed"},
    )
    for index, overrides in enumerate(cases):
        grid = gen.generate(700 + index, index, difficulty="hard", **overrides)
        observed = gen.observe_overrides(grid)
        for key, value in overrides.items():
            assert observed[key] == value
        assert gen.self_check(grid) == []

    with pytest.raises(ValueError, match="unknown override key"):
        gen.generate(1, 0, bogus_axis=3)


def test_every_four_example_window_identifies_the_rule():
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for start in range(16):
            demos = [
                _pair(gen.generate(10000 + band_index * 100 + start, sample_index, difficulty=band))
                for sample_index in range(start, start + gen.EXAMPLES_NEEDED)
            ]
            query = _pair(
                gen.generate(
                    20000 + band_index * 100 + start,
                    start + gen.EXAMPLES_NEEDED,
                    difficulty=band,
                )
            )
            assert gen.lesson_identifiable(demos, query) == []
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(
                    rival(pair["input"]) != pair["output"] for pair in demos
                ), f"{band=} {start=} failed to refute {name}"


def test_declared_witnesses_have_concrete_counterexamples():
    grids = [gen.generate(900, index, difficulty="medium") for index in range(8)]
    for witness_name, witness in gen.SEMANTIC_WITNESSES.items():
        assert any(witness(grid) for grid in grids), witness_name


def test_mutation_fixtures_are_rejected():
    fixtures = gen.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert gen.self_check(grid), name


def test_replay_returns_fresh_objects_and_preserves_global_rng():
    random.seed(24680)
    expected = [random.random() for _ in range(4)]
    random.seed(24680)
    first = gen.generate(123, 7, difficulty="hard")
    observed = [random.random() for _ in range(4)]
    assert observed == expected

    second = gen.generate(123, 7, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(row1 is not row2 for row1, row2 in zip(first, second))
    first[0][0] = 9
    assert second[0][0] != 9


def test_all_ordinary_draws_fire_and_report_exact_axes():
    for band in ("easy", "medium", "hard"):
        for sample_index in range(24):
            grid = gen.generate(3000 + sample_index, sample_index, difficulty=band)
            assert gen.self_check(grid) == []
            assert gen.rule_mirror(grid) != grid
            observed = gen.observe_overrides(grid)
            assert observed["grid_h"] == len(grid)
            assert observed["grid_w"] == len(grid[0])
            assert observed["n_frames"] in (1, 2, 3)
            assert observed["pattern_mode"] in {
                "top_only",
                "bottom_only",
                "mixed",
                "blocked",
            }
