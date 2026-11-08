"""Focused contract tests for f2e717c7c250."""
from __future__ import annotations

import copy
import hashlib
import json
import random
from pathlib import Path

import pytest
from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "f2e717c7c250"
ROOT = find_root(__file__)
CANONICAL = canonical_path(ROOT)
GEN, _, _ = load_selected_generator(TASK_ID, root=ROOT)


def _canonical_row() -> dict:
    for line in CANONICAL.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError("canonical row missing")


def test_rule_hash_and_canonical_inputs_are_pinned_and_accepted():
    row = _canonical_row()
    canonical = row["program_solution"]
    expected = hashlib.sha256(" ".join(canonical.split()).encode()).hexdigest()[:12]
    assert GEN.RULE_HASH == expected
    for split in ("train", "test"):
        pairs = row[split] if isinstance(row[split], list) else [row[split]]
        for pair in pairs:
            original = copy.deepcopy(pair["input"])
            assert GEN.self_check(pair["input"]) == []
            assert pair["input"] == original


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_generation_is_deterministic_valid_and_global_rng_pure(difficulty):
    random.seed(9137)
    before = random.getstate()
    first = GEN.generate(17, 3, difficulty=difficulty)
    after = random.getstate()
    second = GEN.generate(17, 3, difficulty=difficulty)
    assert before == after
    assert first == second
    assert first is not second and first[0] is not second[0]
    assert GEN.self_check(first) == []


def test_exact_two_key_contract_and_unknown_override_rejection():
    assert GEN.AXES["n_keys"]["valid"] == "2"
    grid = GEN.generate(23, 0, difficulty="medium", n_keys=2)
    assert sum(value != 0 for value in grid[0]) == 2
    for invalid in (1, 3, True, 2.0, "2"):
        with pytest.raises((TypeError, ValueError)):
            GEN.generate(23, 0, difficulty="medium", n_keys=invalid)
    with pytest.raises(ValueError):
        GEN.generate(23, 0, difficulty="medium", unknown_axis=1)


def test_grid_overrides_are_strict_and_observable():
    for height, width in ((7, 8), (15, 17), (10, 13)):
        grid = GEN.generate(31, 1, difficulty="medium", grid_h=height, grid_w=width)
        assert (len(grid), len(grid[0])) == (height, width)
        assert GEN.self_check(grid) == []
    for bad in (True, 10.5, "10"):
        with pytest.raises((TypeError, ValueError)):
            GEN.generate(31, 1, difficulty="medium", grid_h=bad)
