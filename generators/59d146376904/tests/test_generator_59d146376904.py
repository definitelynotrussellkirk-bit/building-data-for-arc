from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root

ROOT = find_root(__file__)
SOURCE = ROOT / "generators/59d146376904/generator.py"
SPEC = importlib.util.spec_from_file_location("_gen_59d146376904", SOURCE)
assert SPEC and SPEC.loader
gen = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gen)


def canonical_pairs():
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == gen.TASK_ID:
            return [*row["train"], *row["test"]]
    raise AssertionError(gen.TASK_ID)


def test_canonical_pairs_match_reference_summary():
    pairs = canonical_pairs()
    assert len(pairs) == 5
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert gen.rule_summary(pair["input"]) == pair["output"]
        assert pair["input"] == before
        assert gen.self_check(pair["input"]) == []


def test_exact_dimension_overrides_are_observed_and_strict():
    grid = gen.generate(11, 0, difficulty="easy", grid_h=4, grid_w=10)
    assert (len(grid), len(grid[0])) == (4, 10)
    assert gen.self_check(grid) == []

    same = gen.generate(11, 0, qh=2, qw=5)
    assert same == grid
    assert gen.generate(11, 0, grid_h=4, qh=2, grid_w=10, qw=5) == grid

    with pytest.raises(ValueError, match="even"):
        gen.generate(0, 0, grid_h=5)
    with pytest.raises(ValueError, match="incompatible"):
        gen.generate(0, 0, grid_h=6, qh=2)
    for bad in (True, 6.0, "6"):
        with pytest.raises(TypeError, match="exact integer"):
            gen.generate(0, 0, grid_h=bad)


def test_ordinary_domain_is_deterministic_valid_and_exercises_counts():
    seen_shapes = set()
    for difficulty in (None, "easy", "medium", "hard"):
        for seed in range(8):
            grid = gen.generate(seed, seed % 6, difficulty=difficulty)
            assert grid == gen.generate(seed, seed % 6, difficulty=difficulty)
            assert gen.self_check(grid) == []
            seen_shapes.add((len(grid), len(grid[0])))
            facts = gen.quadrant_analysis(grid)
            assert len({item["majority_color"] for item in facts}) == 4
            assert all(item["majority_count"] > item["runner_up_count"] for item in facts)
            assert all(item["minority_nonzero_count"] >= 1 for item in facts)
    assert len(seen_shapes) >= 4


def test_validator_rejects_ties_bad_cells_ragged_and_empty_quadrants():
    tied = gen.generate(0, 0, texture="tied_majority")
    errors = gen.self_check(tied)
    assert any("unique nonzero majority" in error for error in errors)

    valid = gen.generate(9, 1)
    bad_bool = copy.deepcopy(valid)
    bad_bool[0][0] = True
    assert any("exact integer" in error for error in gen.self_check(bad_bool))
    assert gen.self_check([row[:-1] if index == 1 else row[:] for index, row in enumerate(valid)])
    assert gen.self_check([[0] * 6 for _ in range(6)])


def test_semantic_lesson_rejects_plausible_base_shortcuts():
    demos = []
    for index in range(3):
        grid = gen.generate(440, index, difficulty="medium")
        demos.append({"input": grid, "output": gen.rule_summary(grid)})
    query = {"input": gen.generate(440, 5, difficulty="hard")}
    assert gen.lesson_identifiable(demos, query) == []
