"""Focused contract, semantic, and regression tests for 07ab476607b3."""
from __future__ import annotations

import copy
import importlib.util
import json
import random
import sys
from collections import Counter
from pathlib import Path

import pytest


TASK_ID = "07ab476607b3"
HOME = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "shared" / "runtime"))

SPEC = importlib.util.spec_from_file_location(f"reviewed_{TASK_ID}", HOME / "generator.py")
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)

AUTHORITY = (
    REPO_ROOT
    / "shared/data/base/solutions/banks/54d03287ae93/H42__07ab476607b3.json"
)


def _canonical_row() -> dict:
    with (REPO_ROOT / "shared/data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"missing canonical row for {TASK_ID}")


def _canonical_pairs() -> list[dict]:
    row = _canonical_row()
    return [pair for split in ("train", "test") for pair in row[split]]


def test_rule_pin_canonical_pairs_and_selected_authority_are_exact() -> None:
    row = _canonical_row()
    target = json.loads(AUTHORITY.read_text(encoding="utf-8"))["racket_target"]

    assert GEN.VERSION == "4.0.0"
    assert GEN.RULE_HASH == "11cea0a09738"
    assert target["target_code"] == row["program_solution"]
    assert target["raw_code"] == row["program_solution"]

    for pair in _canonical_pairs():
        original = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_unknown_overrides_reject_and_every_declared_axis_is_exact() -> None:
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 2, misspelled_axis=3)
    with pytest.raises(ValueError, match="unknown texture"):
        GEN.generate(1, 2, texture="not_a_texture")

    cases = [
        {"grid_h": 10},
        {"grid_h": 13},
        {"grid_w": 11},
        {"grid_w": 15},
        {"a_size": 4},
        {"a_size": 7},
        {"texture": "plain"},
        {"texture": "disjoint_b"},
        {"texture": "clip"},
        {"texture": "empty_diff"},
        {
            "grid_h": 13,
            "grid_w": 15,
            "a_size": 7,
            "texture": "disjoint_b",
        },
    ]
    for difficulty in ("easy", "medium", "hard"):
        for index, requested in enumerate(cases):
            grid = GEN.generate(9000 + index, index, difficulty=difficulty, **requested)
            assert GEN.self_check(grid) == []
            observed = GEN.observe_overrides(grid)
            for key, value in requested.items():
                assert observed[key] == value


def test_texture_branches_have_distinct_guaranteed_semantics() -> None:
    expected = {
        "plain": (True, False, False),
        "disjoint_b": (False, False, False),
        "clip": (True, True, False),
        "empty_diff": (True, False, True),
    }
    for index, (texture, (has_overlap, clipped, empty)) in enumerate(expected.items()):
        grid = GEN.generate(3100 + index, index, difficulty="hard", texture=texture)
        analysis = GEN.analyze(grid)
        assert analysis["errors"] == []
        assert GEN.observe_overrides(grid)["texture"] == texture
        assert bool(analysis["normalized_overlap"]) is has_overlap
        assert analysis["clipped"] is clipped
        assert (len(analysis["diff"]) == 0) is empty
        assert GEN.rule_mirror(grid) == analysis["output"]

    # Input objects are physically separated, yet normalized subtraction must
    # remove cells. This is the decisive counterexample to positional erasure.
    plain = GEN.generate(2718, 0, texture="plain")
    analysis = GEN.analyze(plain)
    assert not (set(analysis["a_cells"]) & set(analysis["b_cells"]))
    assert analysis["normalized_overlap"]
    assert len(analysis["output_cells"]) < len(analysis["a_cells"])


def test_default_schedule_teaches_all_branches_in_every_band() -> None:
    canonical_profiles = {(10, 11), (10, 12), (11, 11), (11, 12)}
    for difficulty in ("easy", "medium", "hard"):
        grids = [GEN.generate(1776, index, difficulty=difficulty) for index in range(20)]
        observed = [GEN.observe_overrides(grid) for grid in grids]
        assert all(GEN.self_check(grid) == [] for grid in grids)
        assert all(GEN.strict_canonical_like(grid) == [] for grid in grids)
        assert canonical_profiles <= {(len(grid), len(grid[0])) for grid in grids}
        assert {item["texture"] for item in observed} >= {"plain", "disjoint_b", "clip"}
        counts = Counter(
            name
            for grid in grids
            for name, predicate in GEN.SEMANTIC_WITNESSES.items()
            if predicate(grid)
        )
        assert set(counts) == set(GEN.SEMANTIC_WITNESSES)

    lesson = [GEN.generate(2026, index, difficulty="medium") for index in range(4)]
    demos = [{"input": grid, "output": GEN.rule_mirror(grid)} for grid in lesson[:3]]
    query = {"input": lesson[3], "output": GEN.rule_mirror(lesson[3])}
    assert GEN.lesson_identifiable(demos, query) == []

    for witness_name, rival_names in GEN.WITNESS_RIVALS.items():
        grid = next(
            candidate
            for candidate in lesson
            if GEN.SEMANTIC_WITNESSES[witness_name](candidate)
        )
        answer = GEN.rule_mirror(grid)
        for rival_name in rival_names:
            assert GEN.SEMANTIC_RIVALS[rival_name](grid) != answer


def test_deterministic_fresh_and_global_rng_pure() -> None:
    random.seed(20260928)
    state = random.getstate()
    first = GEN.generate(12345, 67, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(12345, 67, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert first != second


def test_declared_no_anchor_degenerate_is_constructible_but_rejected_as_lawful() -> None:
    grid = GEN.generate(404, 7, difficulty="medium", texture="no_anchor")
    assert sum(value == 9 for row in grid for value in row) == 0
    assert any("anchor" in reason for reason in GEN.self_check(grid))
