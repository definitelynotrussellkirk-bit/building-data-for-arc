from __future__ import annotations

import copy
import importlib.util
import os
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root

TASK_ID = "d185ceed5cc1"
HOME = Path(__file__).resolve().parents[1]


def _load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
    spec = importlib.util.spec_from_file_location("reviewed_generator", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


gen = _load_generator()
CANONICAL_PROFILES = {(6, 10, 10), (5, 11, 10), (4, 13, 10), (5, 12, 10)}


def _profile(grid):
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def test_rule_pin_axes_and_canonical_oracle_contract():
    assert gen.RULE_HASH == "a1ebff603893"
    assert set(gen.AXES) == {
        "grid_h",
        "grid_w",
        "walls_per_row",
        "pebbles_per_row",
    }
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert len(pairs) == 5
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        {"grid_h": 4, "grid_w": 10, "walls_per_row": 4, "pebbles_per_row": 2},
        {"grid_h": 5, "grid_w": 12, "walls_per_row": 3, "pebbles_per_row": 3},
        {"grid_h": 6, "grid_w": 13, "walls_per_row": 2, "pebbles_per_row": 4},
    ],
)
def test_exact_override_boundaries_are_observable(difficulty, options):
    grid = gen.generate(701, 19, difficulty=difficulty, **options)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == options
    assert _profile(grid)[2] == 10
    assert gen.rule_mirror(grid) != grid


@pytest.mark.parametrize(
    "case",
    [
        {"typo_axis": 1},
        {"grid_h": 3},
        {"grid_h": 7},
        {"grid_h": True},
        {"grid_w": 9},
        {"grid_w": 14},
        {"walls_per_row": 1},
        {"walls_per_row": 5},
        {"pebbles_per_row": 1},
        {"pebbles_per_row": 5},
        {"pebbles_per_row": 2.0},
    ],
)
def test_invalid_or_unknown_overrides_fail_loudly(case):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **case)


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_default_distribution_is_canonical_profiled_and_teaches_all_branches(difficulty):
    profiles = set()
    shapes = set()
    for index in range(48):
        grid = gen.generate(20_000 + index, index * 17 + 3, difficulty=difficulty)
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        assert set(value for row in grid for value in row) == set(range(10))
        assert len({tuple(c for c, value in enumerate(row) if value == 8) for row in grid}) >= 2
        assert gen.rule_mirror(grid) != grid
        for witness in gen.SEMANTIC_WITNESSES.values():
            assert witness(grid)
        profiles.add(_profile(grid))
        shapes.add((len(grid), len(grid[0])))
    assert profiles & CANONICAL_PROFILES
    assert len(shapes) >= 3


def test_semantic_witnesses_refute_named_rivals():
    expected = {
        "segment_locality": "ignore_walls",
        "order_preservation": "sort_then_pack",
        "edge_segments": "bounded_segments_only",
    }
    assert set(gen.SEMANTIC_WITNESSES) == set(expected)
    for witness, rival in expected.items():
        assert gen.WITNESS_RIVALS[witness] == [rival]
    for index in range(24):
        grid = gen.generate(30_000 + index, index, difficulty="medium")
        correct = gen.rule_mirror(grid)
        for witness, rival in expected.items():
            assert gen.SEMANTIC_WITNESSES[witness](grid)
            assert gen.SEMANTIC_RIVALS[rival](grid) != correct


def test_self_check_rejects_uninformative_or_malformed_impostors():
    valid = gen.generate(44, 1, difficulty="medium")
    assert gen.self_check(valid) == []

    no_pebbles = [[8 if value == 8 else 0 for value in row] for row in valid]
    one_wall_signature = copy.deepcopy(valid)
    signature = [value == 8 for value in one_wall_signature[0]]
    for row in one_wall_signature:
        for c, is_wall in enumerate(signature):
            if is_wall:
                row[c] = 8
            elif row[c] == 8:
                row[c] = 0
    missing_color = copy.deepcopy(valid)
    removed = next(color for color in range(1, 10) if color != 8)
    for row in missing_color:
        for c, value in enumerate(row):
            if value == removed:
                row[c] = 0

    cases = [
        None,
        [],
        [[]],
        [[0] * 10 for _ in range(4)],
        [[0] * 10, [0] * 9],
        [[False] * 10 for _ in range(4)],
        no_pebbles,
        one_wall_signature,
        missing_color,
    ]
    for grid in cases:
        assert gen.self_check(grid), grid


def test_generation_is_deterministic_and_returns_fresh_grids():
    options = {"grid_h": 5, "grid_w": 11, "walls_per_row": 3, "pebbles_per_row": 3}
    first = gen.generate(81, 13, difficulty="hard", **options)
    second = gen.generate(81, 13, difficulty="hard", **options)
    assert first == second
    assert first is not second
    first[0][0] = 9 if first[0][0] != 9 else 7
    assert gen.generate(81, 13, difficulty="hard", **options) == second


@pytest.mark.parametrize(
    "seed,sample_index,difficulty",
    [
        (True, 0, None),
        (1.0, 0, None),
        ("1", 0, None),
        (1, True, None),
        (1, 1.0, None),
        (1, -1, None),
        (1, 0, True),
        (1, 0, 0),
        (1, 0, "__invalid_difficulty__"),
    ],
)
def test_invalid_control_scalars_fail_loudly(seed, sample_index, difficulty):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(seed, sample_index, difficulty=difficulty)
