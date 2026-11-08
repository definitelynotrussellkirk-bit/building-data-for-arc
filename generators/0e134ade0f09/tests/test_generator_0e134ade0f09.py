"""Focused semantic and regression tests for generator 0e134ade0f09."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest

gen = importlib.import_module("puzzle_generators.per_puzzle.0e134ade0f09.generator")
from src.core.canonical_pairs import iter_task_rows, load_task_pairs


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "0e134ade0f09"
AUTHORITY_PATHS = (
    ROOT / "data/base/solutions/training/5b37cb25__0e134ade0f09.json",
    ROOT / "data/base/solutions/augmented/5b37cb25__a4de4b1e52a5.json",
)


def _canonical_rows() -> list[dict]:
    return list(iter_task_rows(TASK_ID))


def test_rule_hash_and_selected_task_local_authorities_are_canonical():
    rows = _canonical_rows()
    assert len(rows) == 2
    programs = {row["program_solution"] for row in rows}
    assert len(programs) == 1
    canonical = programs.pop()
    normalized_hash = hashlib.sha256(" ".join(canonical.split()).encode()).hexdigest()[:12]
    assert normalized_hash == gen.RULE_HASH == "71fca8698886"

    for path in AUTHORITY_PATHS:
        data = json.loads(path.read_text())
        target = data["racket_target"]
        assert target["target_code"] == canonical
        assert target["target_code_role"] == "selected_task_rule"
        assert target["raw_code_role"] == "archival_executable_source"
        assert target["raw_code"]
        assert target["canonicalization_status"] == "selected_canonical_with_preserved_archival_raw"


def test_all_six_canonical_inputs_are_accepted_and_mirrored_exactly():
    pairs = load_task_pairs(TASK_ID)
    assert len(pairs) == 6
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == source


def test_every_axis_boundary_is_exact_observable_and_composable_in_every_band():
    cases = []
    for difficulty in ("easy", "medium", "hard"):
        for grid_h in (24, 30):
            for grid_w in (24, 30):
                for n_notches in (4, 8):
                    cases.append((difficulty, grid_h, grid_w, n_notches))

    for index, (difficulty, grid_h, grid_w, n_notches) in enumerate(cases):
        grid = gen.generate(
            810_000 + index,
            index,
            difficulty=difficulty,
            grid_h=grid_h,
            grid_w=grid_w,
            n_notches=n_notches,
        )
        assert gen.self_check(grid) == []
        assert gen.observe_overrides(grid) == {
            "grid_h": grid_h,
            "grid_w": grid_w,
            "n_notches": n_notches,
        }
        analysis, errors = gen._analyze_grid(grid)
        assert errors == []
        assert set(analysis["side_counts"]) == set(gen.SIDES)
        matches = sum(
            marker["side"] == marker["nearest_side"] for marker in analysis["markers"]
        )
        assert 0 < matches < n_notches


def test_unknown_override_is_rejected_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, __typo_axis=3)


def test_default_generation_is_deterministic_fresh_and_global_rng_pure():
    random.seed(9051)
    before = random.getstate()
    first = gen.generate(123456, 9, difficulty="hard")
    middle = random.getstate()
    second = gen.generate(123456, 9, difficulty="hard")
    after = random.getstate()
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert before == middle == after


def test_every_default_grid_refutes_named_shortcuts_and_identifies_from_one_demo():
    for difficulty in ("easy", "medium", "hard"):
        for index in range(24):
            demo_grid = gen.generate(91_000 + index, index, difficulty=difficulty)
            query_grid = gen.generate(92_000 + index, index + 1, difficulty=difficulty)
            demo = {"input": demo_grid, "output": gen.rule_mirror(demo_grid)}
            query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
            assert gen.lesson_identifiable([demo], query) == []
            for name, competitor in gen.LESSON_COMPETITORS.items():
                assert competitor(demo_grid) != demo["output"], name


def test_structural_mutation_fixtures_are_rejected():
    fixtures = gen.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        errors = gen.self_check(grid)
        assert errors, name


def test_output_changes_exactly_each_marker_cross_without_mutating_input():
    grid = gen.generate(777, 4, grid_h=26, grid_w=27, n_notches=8)
    snapshot = copy.deepcopy(grid)
    analysis, errors = gen._analyze_grid(grid)
    assert errors == []
    output = gen.rule_mirror(grid)
    assert grid == snapshot
    changed = [
        (r, c)
        for r in range(len(grid))
        for c in range(len(grid[0]))
        if grid[r][c] != output[r][c]
    ]
    assert len(changed) == 5 * analysis["n_notches"]
    expected = {
        (int(marker["row"]) + dr, int(marker["col"]) + dc)
        for marker in analysis["markers"]
        for dr, dc in gen.CROSS
    }
    assert set(changed) == expected
