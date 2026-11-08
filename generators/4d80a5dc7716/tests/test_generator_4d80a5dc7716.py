"""Focused semantic regressions for generator 4d80a5dc7716."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
from pathlib import Path
import random

import pytest


TASK_ID = "4d80a5dc7716"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
ROOT = Path(__file__).resolve().parents[1]


def _canonical_pairs():
    pairs = []
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                pairs.extend(row.get("train", []))
                test = row.get("test", [])
                pairs.extend(test if isinstance(test, list) else [test])
    return pairs


def test_canonical_inputs_and_outputs_match_rule_mirror():
    pairs = _canonical_pairs()
    assert len(pairs) == 3
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_exact_boundary_overrides_are_observable_in_every_band():
    for band in ("easy", "medium", "hard"):
        grid = GEN.generate(
            17,
            23,
            difficulty=band,
            grid_h=12,
            grid_w=8,
            orientation="diag_up",
            span=6,
        )
        assert GEN.observe_overrides(grid) == {
            "grid_h": 12,
            "grid_w": 8,
            "orientation": "diag_up",
            "span": 6,
        }
        assert GEN.self_check(grid) == []


def test_default_schedule_covers_every_orientation_and_span_per_band():
    for band in ("easy", "medium", "hard"):
        orientations = set()
        spans = set()
        distinct = set()
        for sample_index in range(48):
            grid = GEN.generate(101 + sample_index, sample_index, difficulty=band)
            observed = GEN.observe_overrides(grid)
            orientations.add(observed["orientation"])
            spans.add(observed["span"])
            distinct.add(tuple(map(tuple, grid)))
        assert orientations == set(GEN.ORIENTATIONS)
        assert spans == {3, 4, 5, 6}
        assert len(distinct) > 40


def test_materialized_lesson_schedule_is_identifiable():
    demos = []
    for sample_index in range(GEN.EXAMPLES_NEEDED):
        grid = GEN.generate(31337, sample_index)
        demos.append({"input": grid, "output": GEN.rule_mirror(grid)})
    query_grid = GEN.generate(31337, GEN.EXAMPLES_NEEDED)
    query = {"input": query_grid, "output": GEN.rule_mirror(query_grid)}
    assert GEN.lesson_identifiable(demos, query) == []

    insufficient = demos[:2]
    reasons = GEN.lesson_identifiable(insufficient, query)
    assert any("omit orientation" in reason for reason in reasons)
    assert any("spans 3,4,5,6" in reason for reason in reasons)


def test_self_check_rejects_targeted_structural_impostors():
    base = GEN.generate(41, 0)
    endpoints = GEN._analyze(base)["endpoints"]

    one_endpoint = copy.deepcopy(base)
    row, col = endpoints[0]
    one_endpoint[row][col] = 0

    third_endpoint = copy.deepcopy(base)
    third_endpoint[0][0] = 2
    if (0, 0) in endpoints:
        third_endpoint[0][1] = 2

    wrong_color = copy.deepcopy(base)
    row, col = endpoints[0]
    wrong_color[row][col] = 3

    non_aligned = [[0] * 8 for _ in range(8)]
    non_aligned[1][1] = 2
    non_aligned[5][6] = 2

    too_short = [[0] * 8 for _ in range(8)]
    too_short[2][2] = 2
    too_short[2][4] = 2

    ragged = copy.deepcopy(base)
    ragged[0].pop()

    boolean_cell = copy.deepcopy(base)
    boolean_cell[0][0] = True

    for mutation in (
        one_endpoint,
        third_endpoint,
        wrong_color,
        non_aligned,
        too_short,
        ragged,
        boolean_cell,
    ):
        assert GEN.self_check(mutation), mutation


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(20260725)
    state = random.getstate()
    first = GEN.generate(97, 103, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(97, 103, difficulty="hard")
    assert random.getstate() == state
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second, strict=True))
    first[0][0] = 9
    assert GEN.generate(97, 103, difficulty="hard") == second


def test_unknown_and_invalid_overrides_reject_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 2, texture="warm")
    with pytest.raises(ValueError):
        GEN.generate(1, 2, grid_h=7)
    with pytest.raises(ValueError):
        GEN.generate(1, 2, orientation="diagonal")
    with pytest.raises(ValueError, match="unknown difficulty"):
        GEN.generate(1, 2, difficulty="extreme")


def test_rule_hash_matches_selected_canonical_authority():
    programs = set()
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                programs.add(row["program_solution"])
    assert len(programs) == 1
    expected = hashlib.sha256(next(iter(programs)).encode()).hexdigest()[:12]
    assert GEN.RULE_HASH == expected == "89dfbab7de55"
