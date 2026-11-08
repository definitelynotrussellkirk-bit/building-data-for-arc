"""Focused regression tests for generator 7deedd72e091."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest

from puzzle_generators import base as generator_base

REPO_ROOT = Path(__file__).resolve().parents[3]
gen = importlib.import_module("puzzle_generators.per_puzzle.7deedd72e091.generator")


def _canonical_row():
    with (REPO_ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                return row
    raise AssertionError("canonical task row missing")


def _assemble(tiles, colors):
    s = len(tiles[0])
    grid = [[0 for _ in range(len(tiles) * s + len(tiles) - 1)] for _ in range(s)]
    for index, (mask, color) in enumerate(zip(tiles, colors)):
        left = index * (s + 1)
        for row in range(s):
            for column in range(s):
                if mask[row][column]:
                    grid[row][left + column] = color
        if index + 1 < len(tiles):
            for row in range(s):
                grid[row][left + s] = 9
    return grid


A = ((1, 0, 0), (1, 0, 0), (1, 1, 0))
AR = ((1, 1, 1), (1, 0, 0), (0, 0, 0))
B = ((1, 1, 1), (0, 1, 0), (0, 0, 0))
C = ((1, 0, 0), (0, 1, 0), (0, 0, 1))


def test_rule_hash_and_all_canonical_pairs():
    row = _canonical_row()
    actual = hashlib.sha256(" ".join(row["program_solution"].split()).encode()).hexdigest()[:12]
    assert gen.RULE_HASH == actual
    for pair in list(row["train"]) + [row["test"]]:
        grid = copy.deepcopy(pair["input"])
        assert gen.self_check(grid) == []
        assert gen.rule_mirror(grid) == pair["output"]


def test_exact_axis_boundaries_and_observation():
    for band in ("easy", "medium", "hard"):
        for index, match_pair in enumerate(gen.MATCH_PAIRS):
            grid = gen.generate(
                1000 + index,
                2000 + index,
                difficulty=band,
                match_pair=match_pair,
            )
            assert gen.self_check(grid) == []
            assert gen.observe_overrides(grid) == {"match_pair": match_pair}
    with pytest.raises(ValueError):
        gen.generate(1, 1, match_pair="diagonal")


def test_every_ordinary_lesson_rebuts_shortcuts():
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for seed in range(40):
            grid = gen.generate(30000 + band_index * 1000 + seed, 40000 + seed, difficulty=band)
            info = gen._analyze(grid)
            assert info["errors"] == []
            assert gen.self_check(grid) == []
            features = info["lesson_features"]
            assert features["has_positive_relation"]
            assert features["has_negative_relation"]
            assert features["nontrivial_rotation"]
            assert features["count_shortcut_rebuttal"]
            assert features["congruent_different_colors"]
            assert features["noncongruent_same_color"]
            assert len(set(info["occupied_counts"])) == 1




def test_sequential_lesson_schedule_covers_all_pair_positions():
    for start in range(12):
        observed = {
            gen.observe_overrides(gen.generate(71, start + offset, difficulty="medium"))["match_pair"]
            for offset in range(4)
        }
        assert observed == set(gen.MATCH_PAIRS)

def test_default_keyed_axis_matches_returned_observation():
    captured = []
    generator_base.set_ctx_observer(captured.append)
    try:
        observed_pairs = set()
        observed_counts = set()
        for band_index, band in enumerate(("easy", "medium", "hard")):
            for seed in range(60):
                grid = gen.generate(50_000 + band_index * 1_000 + seed, seed * 23 + 11, difficulty=band)
                ctx = captured[-1]
                expected = {axis: ctx._drawn[axis] for axis in gen.AXES}
                actual = gen.observe_overrides(grid)
                assert actual == expected
                observed_pairs.add(actual["match_pair"])
                observed_counts.add(gen._analyze(grid)["occupied_counts"][0])
        assert observed_pairs == set(gen.MATCH_PAIRS)
        assert observed_counts == {3, 4, 5}
    finally:
        generator_base.set_ctx_observer(None)

def test_determinism_fresh_returns_and_global_rng():
    random.seed(701091)
    state = random.getstate()
    first = gen.generate(17, 9, difficulty="medium")
    assert random.getstate() == state
    second = gen.generate(17, 9, difficulty="medium")
    assert first == second
    assert first is not second and first[0] is not second[0]
    first[0][0] = 9 if first[0][0] != 9 else 0
    assert first != second
    assert second != gen.generate(18, 9, difficulty="medium")
    assert second != gen.generate(17, 10, difficulty="medium")


def test_targeted_impostors_are_rejected_but_oracle_remains_general():
    valid = _assemble([A, AR, B], [1, 2, 1])
    assert gen.self_check(valid) == []

    broken_divider = copy.deepcopy(valid)
    broken_divider[1][3] = 0

    all_congruent = _assemble([A, AR, A], [1, 2, 1])
    all_distinct = _assemble([A, B, C], [1, 2, 1])
    identity_hidden = _assemble([A, A, B], [1, 2, 1])

    multicolor = copy.deepcopy(valid)
    multicolor[0][0] = 4
    multicolor[1][0] = 5

    for impostor in (broken_divider, all_congruent, all_distinct, identity_hidden, multicolor):
        assert gen.self_check(impostor)

    # Negative recombination: the replacement C is absent from every remaining
    # tile.  The lesson grammar rejects the now-all-distinct strip, while the
    # task oracle still executes it and returns a valid diagonal relation matrix.
    recombined = _assemble([A, B, C], [1, 2, 1])
    assert gen.self_check(recombined)
    assert gen.rule_mirror(recombined) == [[8, 0, 0], [0, 8, 0], [0, 0, 8]]


def test_invalid_calls_reject_loudly():
    with pytest.raises(ValueError):
        gen.generate(1, 1, difficulty="extreme")
    with pytest.raises(ValueError):
        gen.generate(1, 1, match_pair="diagonal")
    with pytest.raises(ValueError):
        gen.generate(1, 1, tile_s=3)
    with pytest.raises(ValueError):
        gen.generate(1, 1, texture="warm")
