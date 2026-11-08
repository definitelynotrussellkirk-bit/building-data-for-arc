from __future__ import annotations

import copy
import hashlib
import json
import random
from pathlib import Path

import pytest

from puzzle_generators.per_puzzle.b636461d71b8 import generator as gen

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "b636461d71b8"


def _canonical_row():
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"missing canonical row for {TASK_ID}")


def _grid(rows):
    return [[int(value) for value in row] for row in rows]


def _pair(grid):
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_rule_hash_and_all_canonical_pairs():
    row = _canonical_row()
    actual_hash = hashlib.sha256(
        " ".join(row["program_solution"].split()).encode()
    ).hexdigest()[:12]
    assert gen.RULE_HASH == actual_hash == "753f48cab523"

    pairs = list(row["train"]) + [row["test"]]
    assert len(pairs) == 5
    for pair in pairs:
        input_grid = _grid(pair["input"])
        expected = _grid(pair["output"])
        before = copy.deepcopy(input_grid)
        assert gen.self_check(input_grid) == []
        assert gen.strict_canonical_like(input_grid) == []
        assert gen.rule_mirror(input_grid) == expected
        assert input_grid == before


def test_default_lesson_schedule_is_identifiable_and_branch_complete():
    seed = 7391
    grids = [gen.generate(seed, index) for index in range(5)]
    patterns = [gen.observe_overrides(grid)["match_pattern"] for grid in grids]
    assert patterns[:4] == ["single_tl", "single_br", "cross", "top_row"]
    assert patterns[4] == gen._QUERY_PATTERN_PAIRS[seed % len(gen._QUERY_PATTERN_PAIRS)][0]

    demos = [_pair(grid) for grid in grids[:4]]
    query = _pair(grids[4])
    assert gen.lesson_identifiable(demos, query) == []

    positive_support = set()
    for demo in demos:
        pattern = gen.semantic_observables(demo["input"])["pattern"]
        positive_support.update(index for index, value in enumerate(pattern) if value)
    assert positive_support == {0, 1, 2, 3}
    assert gen.semantic_observables(grids[1])["reflection_only_positive"]
    assert gen.semantic_observables(grids[3])["offset_only_positive"]


def test_all_declared_overrides_are_exact_deterministic_and_fresh():
    global_state = random.getstate()
    for pattern_name in gen._MATCH_PATTERNS:
        for palette_kind in gen.PALETTE_KINDS:
            first = gen.generate(
                941,
                17,
                difficulty="hard",
                grid_h=7,
                grid_w=9,
                match_pattern=pattern_name,
                palette_kind=palette_kind,
            )
            second = gen.generate(
                941,
                17,
                difficulty="hard",
                grid_h=7,
                grid_w=9,
                match_pattern=pattern_name,
                palette_kind=palette_kind,
            )
            assert first == second
            assert first is not second
            assert all(a is not b for a, b in zip(first, second))
            assert gen.self_check(first) == []
            observed = gen.observe_overrides(first)
            assert observed == {
                "grid_h": 7,
                "grid_w": 9,
                "match_pattern": pattern_name,
                "palette_kind": palette_kind,
            }
            expected = gen._MATCH_PATTERNS[pattern_name]
            actual = tuple(value == 8 for row in gen.rule_mirror(first) for value in row)
            assert actual == tuple(bool(value) for value in expected)
    assert random.getstate() == global_state


def test_self_check_rejects_structural_and_semantic_mutations():
    grid = gen.generate(101, 0)

    mutation = copy.deepcopy(grid)
    mutation[3][0] = 1
    assert any("non-panel" in message for message in gen.self_check(mutation))

    mutation = copy.deepcopy(grid)
    panel_color = next(value for value in mutation[0][:3] if value)
    replacement = next(color for color in range(1, 10) if color != panel_color)
    location = next(
        (r, c) for r in range(3) for c in range(3) if mutation[r][c] == panel_color
    )
    mutation[location[0]][location[1]] = replacement
    assert any("nonzero colors" in message for message in gen.self_check(mutation))

    mutation = copy.deepcopy(grid)
    location = next(
        (r, c) for r in range(3) for c in range(3) if mutation[r][c] != 0
    )
    mutation[location[0]][location[1]] = 0
    assert any("expected 5" in message for message in gen.self_check(mutation))

    mutation = copy.deepcopy(grid)
    mutation[0][0] = True
    assert any("invalid ARC color" in message for message in gen.self_check(mutation))

    assert gen.self_check(grid[:-1])
    assert gen.self_check([row[:-1] for row in grid])
    assert gen.self_check([row[:] for row in grid] + [[0]])


def test_lesson_hook_rejects_ambiguous_single_example_bundle():
    seed = 557
    demo_grid = gen.generate(seed, 0)
    query_grid = gen.generate(seed, 4)
    reasons = gen.lesson_identifiable([_pair(demo_grid)], _pair(query_grid))
    assert reasons
    assert any("cover matrix positions" in reason for reason in reasons)
    assert any("multi-match" in reason for reason in reasons)


def test_bad_calls_are_loud():
    with pytest.raises(TypeError):
        gen.generate(0, 0, unknown_axis=1)
    with pytest.raises(ValueError):
        gen.generate(0, 0, difficulty="impossible")
    with pytest.raises(ValueError):
        gen.generate(0, 0, grid_h=8)
    with pytest.raises(ValueError):
        gen.generate(0, 0, match_pattern="not-a-pattern")
