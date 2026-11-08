from __future__ import annotations

import copy
import json
import random
from pathlib import Path

from puzzle_generators.per_puzzle.be743fd05a59 import generator as gen


def _canonical_inputs():
    path = Path(__file__).resolve().parents[1] / "data/canonical/puzzles.jsonl"
    for line in path.open():
        row = json.loads(line)
        if row.get("task_id") == gen.TASK_ID:
            return [pair["input"] for pair in row["train"]] + [row["test"]["input"]]
    raise AssertionError("canonical task missing")


def test_canonical_inputs_pass_structural_self_check():
    for grid in _canonical_inputs():
        assert gen.self_check(grid) == []


def test_rule_mirror_matches_canonical_outputs():
    path = Path(__file__).resolve().parents[1] / "data/canonical/puzzles.jsonl"
    row = next(
        json.loads(line)
        for line in path.open()
        if json.loads(line).get("task_id") == gen.TASK_ID
    )
    pairs = row["train"] + [row["test"]]
    for pair in pairs:
        assert gen.rule_mirror(pair["input"]) == [list(map(int, r)) for r in pair["output"]]


def test_override_axes_are_realized_and_observable():
    cases = [
        dict(grid_h=8, grid_w=9, source_count=2, blocked_source_count=0,
             boundary_source_count=0, distractor_color=1, distractor_style="domino"),
        dict(grid_h=12, grid_w=14, source_count=6, blocked_source_count=2,
             boundary_source_count=2, distractor_color=4, distractor_style="block"),
        dict(source_count=4, blocked_source_count=1, boundary_source_count=1,
             distractor_color=3, distractor_style="bar"),
    ]
    for index, case in enumerate(cases):
        grid = gen.generate(700 + index, 11, difficulty="easy", **case)
        observed = gen.observe_overrides(grid)
        for key, value in case.items():
            assert observed[key] == value
        assert gen.self_check(grid) == []


def test_deterministic_fresh_returns_and_global_rng_purity():
    random.seed(918273)
    before = random.getstate()
    first = gen.generate(91, 7, difficulty="hard")
    middle = random.getstate()
    second = gen.generate(91, 7, difficulty="hard")
    after = random.getstate()
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert before == middle == after
    first[0][0] = 8
    assert second[0][0] != 8


def test_self_check_rejects_targeted_impostors():
    lawful = gen.generate(123, 4, difficulty="medium",
                          source_count=4, blocked_source_count=1,
                          boundary_source_count=1, distractor_style="bar")

    no_sources = copy.deepcopy(lawful)
    for row in no_sources:
        for c, value in enumerate(row):
            if value == 9:
                row[c] = 0
    assert any("2..6 maroon" in e for e in gen.self_check(no_sources))

    clustered = copy.deepcopy(lawful)
    sources = [(r, c) for r, row in enumerate(clustered) for c, v in enumerate(row) if v == 9]
    r, c = sources[0]
    target = (r, c + 1) if c + 1 < len(clustered[0]) else (r, c - 1)
    clustered[target[0]][target[1]] = 9
    assert any("Manhattan-separated" in e for e in gen.self_check(clustered))

    no_decoration = copy.deepcopy(lawful)
    color = gen.observe_overrides(lawful)["distractor_color"]
    source_targets = {
        (r + 1, c - 1)
        for r, row in enumerate(lawful)
        for c, value in enumerate(row)
        if value == 9 and 0 <= r + 1 < len(lawful) and 0 <= c - 1 < len(lawful[0])
    }
    for r, row in enumerate(no_decoration):
        for c, value in enumerate(row):
            if value == color and (r, c) not in source_targets:
                row[c] = 0
    assert any("non-singleton distractor" in e for e in gen.self_check(no_decoration))

    all_blocked = gen.generate(456, 8, source_count=3,
                               blocked_source_count=2,
                               boundary_source_count=0)
    active = [
        (r + 1, c - 1)
        for r, row in enumerate(all_blocked)
        for c, value in enumerate(row)
        if value == 9
        and 0 <= r + 1 < len(all_blocked)
        and 0 <= c - 1 < len(all_blocked[0])
        and all_blocked[r + 1][c - 1] == 0
    ]
    assert len(active) == 1
    rr, cc = active[0]
    all_blocked[rr][cc] = gen.observe_overrides(all_blocked)["distractor_color"]
    assert any("at least one source" in e for e in gen.self_check(all_blocked))


def test_lesson_schedule_covers_plain_blocked_boundary_and_combined_witnesses():
    observed = []
    for sample_index in range(8):
        grid = gen.generate(314159, sample_index, difficulty="medium")
        axes = gen.observe_overrides(grid)
        observed.append((axes["blocked_source_count"], axes["boundary_source_count"]))
    assert set(gen._BRANCH_SCHEDULE) <= set(observed)
