"""Focused regression tests for generator c56657e663d9."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parents[1]
DEFAULT_GENERATOR = REPO / "puzzle_generators/per_puzzle/c56657e663d9/generator.py"
GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", DEFAULT_GENERATOR))


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        f"generator_c56657e663d9_{abs(hash(str(GENERATOR_PATH)))}", GENERATOR_PATH
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_row():
    path = REPO / "data/canonical/puzzles.jsonl"
    for line in path.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == "c56657e663d9":
            return row
    raise AssertionError("canonical row c56657e663d9 not found")


def test_rule_hash_and_canonical_inputs_are_accepted():
    gen = _load_generator()
    assert gen.RULE_HASH == "38eb4ea53ac4"
    row = _canonical_row()
    for split in ("train", "test"):
        for pair in row[split]:
            assert gen.self_check(pair["input"]) == []
            assert gen.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_normal_draws_expose_all_decisive_branches(band):
    gen = _load_generator()
    for seed in range(20):
        grid = gen.generate(seed, 1000 + seed, difficulty=band)
        profile = gen._pair_profile(grid)
        assert profile["upper_only"] >= 1
        assert profile["lower_only"] >= 1
        assert profile["conflict_diff"] >= 1
        assert gen.self_check(grid) == []
        assert gen._fill_blanks_only(grid) != gen.rule_mirror(grid)


def test_boundary_overrides_are_exact_and_observable():
    gen = _load_generator()
    cases = [
        {
            "size": 6,
            "conflict_pairs": 1,
            "one_sided_pairs": 2,
            "diagonal_cells": 0,
            "palette_size": 2,
        },
        {
            "size": 10,
            "conflict_pairs": 2,
            "one_sided_pairs": 3,
            "diagonal_cells": 1,
            "palette_size": 4,
        },
    ]
    for index, overrides in enumerate(cases):
        grid = gen.generate(31, index, difficulty="easy", **overrides)
        assert gen.observe_overrides(grid) == overrides
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 0, __override_contract_unknown_axis__=1)


def test_declared_mutation_fixtures_are_rejected():
    gen = _load_generator()
    fixtures = list(gen.mutation_fixtures())
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert gen.self_check(grid), name
