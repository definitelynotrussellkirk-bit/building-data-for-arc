"""Focused regression and semantic-teaching tests for a8a99930c51a."""
from __future__ import annotations

from collections import deque
import importlib.util
import os
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "a8a99930c51a"
HOME = Path(__file__).resolve().parents[1]
GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
SPEC = importlib.util.spec_from_file_location("reviewed_a8a99930c51a", GENERATOR_PATH)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)
CANONICAL = canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)


def strip_codes(grid):
    return [value for value in grid[0] if value != 0]


def strip_oracle(grid):
    codes = strip_codes(grid)
    mapping = {value: codes[(i + 1) % len(codes)] for i, value in enumerate(codes)}
    return [
        row[:] if r == 0 else [mapping.get(value, value) for value in row]
        for r, row in enumerate(grid)
    ]


def numeric_successor(grid):
    codes = sorted(strip_codes(grid))
    mapping = {value: codes[(i + 1) % len(codes)] for i, value in enumerate(codes)}
    return [
        row[:] if r == 0 else [mapping.get(value, value) for value in row]
        for r, row in enumerate(grid)
    ]


def body_first_successor(grid):
    code_set = set(strip_codes(grid))
    order = []
    for row in grid[1:]:
        for value in row:
            if value in code_set and value not in order:
                order.append(value)
    mapping = {value: order[(i + 1) % len(order)] for i, value in enumerate(order)}
    return [
        row[:] if r == 0 else [mapping.get(value, value) for value in row]
        for r, row in enumerate(grid)
    ]


def body_positions(grid, color):
    return {(r, c) for r, row in enumerate(grid[1:], 1) for c, value in enumerate(row) if value == color}


def connected(points):
    if not points:
        return False
    seen = {next(iter(points))}
    todo = deque(seen)
    while todo:
        r, c = todo.popleft()
        for nxt in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if nxt in points and nxt not in seen:
                seen.add(nxt)
                todo.append(nxt)
    return seen == points


def observed(grid):
    codes = strip_codes(grid)
    counts = [len(body_positions(grid, color)) for color in codes]
    assert len(set(counts)) == 1
    code_set = set(codes)
    distractors = sum(value != 0 and value not in code_set for row in grid[1:] for value in row)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_codes": len(codes),
        "cells_per_code": counts[0],
        "n_distractors": distractors,
    }


def test_rule_pin_and_exact_axis_surface():
    assert GEN.RULE_HASH == "e5c43869717c"
    assert set(GEN.AXES) == {"grid_h", "grid_w", "n_codes", "cells_per_code", "n_distractors"}
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []


@pytest.mark.parametrize("pair", CANONICAL, ids=lambda pair: pair.get("split", "canonical"))
def test_canonical_pairs_match_independent_oracle(pair):
    assert GEN.self_check(pair["input"]) == []
    assert strip_oracle(pair["input"]) == pair["output"]


def test_declared_canonical_shortcuts_really_fit_every_labeled_pair():
    for pair in CANONICAL:
        assert numeric_successor(pair["input"]) == pair["output"]
        assert body_first_successor(pair["input"]) == pair["output"]
        assert GEN.CANONICAL_SHORTCUTS["numeric_successor"](pair["input"]) == pair["output"]
        assert GEN.CANONICAL_SHORTCUTS["body_first_successor"](pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_exact_override_is_honored_in_every_band(band):
    wanted = {
        "grid_h": 7,
        "grid_w": 9,
        "n_codes": 6,
        "cells_per_code": 5,
        "n_distractors": 4,
    }
    grid = GEN.generate(17, 0, difficulty=band, **wanted)
    assert GEN.self_check(grid) == []
    assert observed(grid) == wanted
    assert GEN.observe_overrides(grid) == wanted


@pytest.mark.parametrize(
    "kwargs",
    [
        {"typo": 1},
        {"grid_h": 6},
        {"grid_h": 15},
        {"grid_h": True},
        {"grid_w": "9"},
        {"n_codes": 2},
        {"n_codes": 7},
        {"cells_per_code": 2},
        {"cells_per_code": 6},
        {"n_distractors": -1},
        {"n_distractors": 5},
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(kwargs):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **kwargs)


@pytest.mark.parametrize(
    "seed,index,difficulty",
    [
        (True, 0, None),
        (-1, 0, None),
        (0, True, None),
        (0, -1, None),
        (0, 0, 0),
        (0, 0, "__invalid_difficulty__"),
    ],
)
def test_invalid_call_scalars_are_rejected(seed, index, difficulty):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(seed, index, difficulty=difficulty)


def test_profile_gate_sha256_seed_is_supported():
    # canonical_profile_gate._pinned_seed uses 12 hex digits (a 48-bit value).
    seed = int("fedcba987654", 16)
    grid = GEN.generate(seed, seed % 7919, difficulty="hard")
    assert GEN.self_check(grid) == []


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_schedule_hits_a_canonical_profile_in_each_band(band):
    grids = [GEN.generate(991, index, difficulty=band) for index in range(20)]
    assert any(
        len(grid) == 7
        and len(grid[0]) in {9, 10, 11}
        and len({value for row in grid for value in row}) == 4
        for grid in grids
    )


def test_profile_gate_pinned_census_has_at_least_25_percent_envelope_support():
    import hashlib

    hits = 0
    total = 0
    for band in ("easy", "medium", "hard"):
        for index in range(20):
            digest = hashlib.sha256(
                f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
            ).hexdigest()
            seed = int(digest[:12], 16)
            grid = GEN.generate(seed, seed % 7919 + index, difficulty=band)
            total += 1
            hits += (
                len(grid) == 7
                and len(grid[0]) in {9, 10, 11}
                and len({value for row in grid for value in row}) == 4
            )
    assert hits / total >= 0.25


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_generated_inputs_are_lawful_connected_and_refute_both_shortcuts(band):
    for index in range(24):
        grid = GEN.generate(2100 + index, index, difficulty=band)
        assert GEN.self_check(grid) == []
        assert grid == GEN.generate(2100 + index, index, difficulty=band)
        assert all(value == 0 for value in grid[1])
        for color in strip_codes(grid):
            points = body_positions(grid, color)
            assert 3 <= len(points) <= 5
            assert connected(points)
        intended = strip_oracle(grid)
        assert numeric_successor(grid) != intended
        assert body_first_successor(grid) != intended
        assert GEN.SEMANTIC_WITNESSES["non_numeric_strip_cycle"](grid)
        assert GEN.SEMANTIC_WITNESSES["body_order_disagrees"](grid)


@pytest.mark.parametrize(
    "grid",
    [
        [[0] * 9 for _ in range(7)],
        [[1, 0, 2, 0, 3, 0, 0, 0, 0]] + [[0] * 9 for _ in range(6)],
        [[1, 0, 2, 0, 3, 0, 0, 0, 0], [0] * 9, [1, 1, 1, 0, 2, 2, 2, 0, 0]] + [[0] * 9 for _ in range(4)],
        [[1, 0, 2, 0, 3, 0, 0, 0, 0], [0] * 9, [1, 0, 1, 0, 2, 2, 2, 3, 3], [0] * 6 + [3, 0, 0]] + [[0] * 9 for _ in range(3)],
    ],
)
def test_self_check_rejects_minimal_or_semantically_broken_impostors(grid):
    assert GEN.self_check(grid)


def test_lesson_identifiability_flags_a_surviving_shortcut():
    pair = CANONICAL[0]
    query_grid = GEN.generate(53, 1)
    query = {"input": query_grid, "output": strip_oracle(query_grid)}
    reasons = GEN.lesson_identifiable([pair], query)
    assert any("numeric_successor" in reason for reason in reasons)
    assert any("body_first_successor" in reason for reason in reasons)


def test_one_generated_demo_refutes_declared_shortcuts_for_a_generated_query():
    demo_grid = GEN.generate(71, 2)
    query_grid = GEN.generate(72, 3)
    demo = {"input": demo_grid, "output": strip_oracle(demo_grid)}
    query = {"input": query_grid, "output": strip_oracle(query_grid)}
    assert GEN.lesson_identifiable([demo], query) == []


def test_retained_shortcut_counterexample_is_source_bound_and_racket_checked():
    import hashlib
    import json

    path = HOME / "counterexamples" / "shortcut_seed71_index2.json"
    case = json.loads(path.read_text(encoding="utf-8"))
    current_sha = hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest()
    assert case["generator_sha256"] == current_sha
    assert case["racket_authority"]["executed_rule_hash"] == GEN.RULE_HASH
    assert case["racket_authority"]["rule_hash_matches_catalog"] is True
    assert case["racket_authority"]["valid_output"] is True

    grid = case["input"]
    assert GEN.generate(case["seed"], case["sample_index"]) == grid
    assert GEN.self_check(grid) == []
    intended = case["racket_authority"]["output"]
    assert strip_oracle(grid) == intended
    assert numeric_successor(grid) == case["rival_outputs"]["numeric_successor"]
    assert body_first_successor(grid) == case["rival_outputs"]["body_first_successor"]
    assert numeric_successor(grid) != intended
    assert body_first_successor(grid) != intended
