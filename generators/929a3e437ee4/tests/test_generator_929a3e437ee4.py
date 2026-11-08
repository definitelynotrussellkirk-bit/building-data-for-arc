"""Focused regression tests for generator 929a3e437ee4.

Covers the baseline findings (missing RULE_HASH, canonical self-check rejection,
and override failures) plus the repaired rule-linked teaching distribution.
"""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "929a3e437ee4"
GEN = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)


def _canonical_row():
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError("canonical row missing")


def _components(grid, color):
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    }
    count = 0
    while remaining:
        count += 1
        stack = [remaining.pop()]
        while stack:
            r, c = stack.pop()
            for nb in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if nb in remaining:
                    remaining.remove(nb)
                    stack.append(nb)
    return count


def _python_output(grid):
    facts = GEN.semantic_observables(grid)
    return [list(facts["winners"]) for _ in range(facts["max_count"])]


def test_rule_hash_matches_canonical_program():
    normalized = " ".join(_canonical_row()["program_solution"].split())
    assert hashlib.sha256(normalized.encode()).hexdigest()[:12] == GEN.RULE_HASH


def test_regression_canonical_single_winner_inputs_are_accepted():
    row = _canonical_row()
    # These were the two exact baseline failures recorded by generator_selfcheck.
    for train_index in (0, 2):
        assert GEN.self_check(row["train"][train_index]["input"]) == []
    for split in ("train", "test"):
        for pair in row[split]:
            assert GEN.self_check(pair["input"]) == []
            assert _python_output(pair["input"]) == pair["output"]


def test_lesson_schedule_covers_rule_branches_in_every_band():
    expected = [
        (3, 1, True),
        (2, 2, False),
        (4, 3, True),
        (3, 1, True),
        (5, 4, True),
    ]
    for band in ("easy", "medium", "hard"):
        facts = [
            GEN.semantic_observables(GEN.generate(41, index, difficulty=band))
            for index in range(5)
        ]
        assert [
            (item["palette_size"], item["n_winners"], item["has_distractor"])
            for item in facts
        ] == expected
        assert any(item["winner_order_not_numeric"] for item in facts)
        assert len({item["max_count"] for item in facts[:4]}) >= 3


def test_generated_colors_are_exact_connected_objects():
    for band in ("easy", "medium", "hard"):
        for seed in range(10):
            grid = GEN.generate(seed, seed * 7 + 2, difficulty=band)
            assert GEN.self_check(grid) == []
            facts = GEN.semantic_observables(grid)
            counts = Counter(value for row in grid for value in row if value)
            assert counts == Counter(facts["counts"])
            assert all(_components(grid, color) == 1 for color in counts)
            winner_counts = {counts[color] for color in facts["winners"]}
            assert winner_counts == {facts["max_count"]}
            assert all(
                count < facts["max_count"]
                for color, count in counts.items()
                if color not in facts["winners"]
            )


def test_boundary_overrides_are_exact_and_observable():
    cases = (
        {"grid_h": 8},
        {"grid_h": 14},
        {"grid_w": 8},
        {"grid_w": 14},
        {"palette_size": 2},
        {"palette_size": 5},
        {"n_winners": 1},
        {"n_winners": 4},
        {"max_count": 3},
        {"max_count": 9},
        {"anchor_edge": False},
        {"anchor_edge": True},
        {"palette_size": 5, "n_winners": 4, "max_count": 9},
        {"grid_h": 8, "max_count": 9, "n_winners": 4},
    )
    for case in cases:
        grid = GEN.generate(73, 13, difficulty="easy", **case)
        observed = GEN.observe_overrides(grid)
        for key, value in case.items():
            if key in observed:
                assert observed[key] == value, (case, observed)
        assert GEN.self_check(grid) == []


def test_incompatible_overrides_reject_loudly():
    for case in (
        {"palette_size": 2, "n_winners": 4},
        {
            "grid_h": 8,
            "grid_w": 8,
            "palette_size": 5,
            "max_count": 9,
            "anchor_edge": False,
        },
        {"palette_kind": "bogus"},
        {"shape_style": "bogus"},
        {"unknown_axis": 1},
    ):
        with pytest.raises(ValueError):
            GEN.generate(3, 3, difficulty="medium", **case)


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(981723)
    before = random.getstate()
    first = GEN.generate(91, 17, difficulty="hard")
    after = random.getstate()
    second = GEN.generate(91, 17, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert first[0] is not second[0]
    snapshot = copy.deepcopy(first)
    second[0][0] = (second[0][0] + 1) % 10
    assert first == snapshot


def test_declared_mutation_fixtures_are_rejected():
    fixtures = dict(GEN.mutation_fixtures())
    assert len(fixtures) >= 4
    for name, grid in fixtures.items():
        assert GEN.self_check(grid), name


def test_four_demo_window_identifies_scheduled_query():
    for band in ("easy", "medium", "hard"):
        for seed in (5, 19, 101):
            pairs = []
            for index in range(5):
                grid = GEN.generate(seed, index, difficulty=band)
                pairs.append({"input": grid, "output": _python_output(grid)})
            assert GEN.lesson_identifiable(pairs[:4], pairs[4]) == []
