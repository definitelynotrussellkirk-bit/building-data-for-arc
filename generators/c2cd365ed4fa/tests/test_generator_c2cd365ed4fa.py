from __future__ import annotations

import copy
import hashlib
import json
import random
from pathlib import Path

import pytest

from puzzle_generators.per_puzzle.c2cd365ed4fa import generator as gen
from puzzle_generators.runner import _apply_rule, _load_bundle, _open_bridge_with_rule
from src.core.canonical_pairs import iter_task_rows, load_task_pairs

TASK_ID = "c2cd365ed4fa"
ROOT = Path(__file__).resolve().parents[1]
AUTHORITY_PATHS = (
    ROOT / "data/base/solutions/training/aaecdb9a__c2cd365ed4fa.json",
    ROOT / "data/base/solutions/augmented/aaecdb9a__cef804fa6ca7.json",
)
COLUMN_COLORS = (5, 2, 8, 9, 6)


def _norm_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _components8(grid, color):
    todo = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    }
    out = []
    while todo:
        start = todo.pop()
        component = {start}
        stack = [start]
        while stack:
            row, col = stack.pop()
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if (dr, dc) == (0, 0):
                        continue
                    point = (row + dr, col + dc)
                    if point in todo:
                        todo.remove(point)
                        component.add(point)
                        stack.append(point)
        out.append(component)
    return out


def _expected_histogram(grid):
    counts = {
        color: len(_components8(grid, color))
        for color in COLUMN_COLORS
        if any(color in row for row in grid)
    }
    height = max(counts.values())
    return [
        [
            color if color in counts and row >= height - counts[color] else 7
            for color in COLUMN_COLORS
        ]
        for row in range(height)
    ]


def _grid_with_points(points):
    grid = [[7 for _ in range(10)] for _ in range(10)]
    for row, col, color in points:
        grid[row][col] = color
    return grid


def test_metadata_and_all_racket_authorities_are_pinned():
    assert gen.TASK_ID == TASK_ID
    assert gen.GENERATOR_ID == TASK_ID
    assert gen.VERSION == "3.0.0"
    assert gen.RULE_HASH == "281335890ae5"
    for path in AUTHORITY_PATHS:
        record = json.loads(path.read_text())
        for field in ("raw_code", "target_code"):
            assert _norm_hash(record["racket_target"][field]) == gen.RULE_HASH


def test_all_canonical_occurrences_outputs_and_self_check():
    rows = list(iter_task_rows(TASK_ID))
    assert [row["source"] for row in rows] == ["training", "augmented"]
    pairs = load_task_pairs(TASK_ID)
    assert len(pairs) == 8
    unique_inputs = {tuple(map(tuple, pair["input"])) for pair in pairs}
    assert len(unique_inputs) == 4
    for pair in pairs:
        assert pair["output"] is not None
        assert _expected_histogram(pair["input"]) == pair["output"]
        assert gen.self_check(pair["input"]) == []


def test_racket_exactness_input_purity_and_a_b_a_repeat():
    pairs = load_task_pairs(TASK_ID)
    bundle = _load_bundle(TASK_ID)
    bridge, fn_name = _open_bridge_with_rule(bundle.rule_callable_text)
    try:
        for pair in pairs:
            source = copy.deepcopy(pair["input"])
            before = copy.deepcopy(source)
            assert _apply_rule(bridge, fn_name, source) == pair["output"]
            assert source == before

        grid_a = gen.generate(901, 11, difficulty="easy", diagonal_merge=True)
        grid_b = gen.generate(902, 12, difficulty="hard", diagonal_merge=False)
        out_a1 = _apply_rule(bridge, fn_name, grid_a)
        out_b = _apply_rule(bridge, fn_name, grid_b)
        out_a2 = _apply_rule(bridge, fn_name, grid_a)
        assert out_a1 == _expected_histogram(grid_a)
        assert out_b == _expected_histogram(grid_b)
        assert out_a2 == out_a1
    finally:
        bridge.shutdown()


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_declared_axes_are_exact_on_default_draws(difficulty):
    for seed in range(40):
        grid = gen.generate(seed, seed * 17 + 3, difficulty=difficulty)
        observed = gen.observe_overrides(grid)
        assert gen.self_check(grid, difficulty=difficulty) == []
        assert 10 <= observed["grid_h"] <= 22
        assert 10 <= observed["grid_w"] <= 22
        assert 3 <= observed["n_colors"] <= 5
        assert 2 <= observed["peak_count"] <= 6
        assert 6 <= observed["largest_component_size"] <= 16
        assert isinstance(observed["diagonal_merge"], bool)


@pytest.mark.parametrize("diagonal_merge", [False, True])
def test_full_boundary_override_combination_is_observable(diagonal_merge):
    for peak_count in (2, 6):
        for largest_size in (6, 16):
            grid = gen.generate(
                1201 + peak_count,
                73 + largest_size,
                difficulty="hard",
                grid_h=10,
                grid_w=10,
                n_colors=5,
                peak_count=peak_count,
                largest_component_size=largest_size,
                diagonal_merge=diagonal_merge,
            )
            assert gen.observe_overrides(grid) == {
                "grid_h": 10,
                "grid_w": 10,
                "n_colors": 5,
                "peak_count": peak_count,
                "largest_component_size": largest_size,
                "diagonal_merge": diagonal_merge,
            }


def test_determinism_fresh_returns_and_process_global_rng():
    state = random.getstate()
    first = gen.generate(444, 19, difficulty="medium")
    assert random.getstate() == state
    second = gen.generate(444, 19, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 0
    assert gen.generate(444, 19, difficulty="medium") == second


@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": 9},
        {"grid_w": 23},
        {"n_colors": 2},
        {"peak_count": 7},
        {"largest_component_size": 17},
        {"diagonal_merge": "yes"},
        {"texture": "scattered"},
    ],
)
def test_invalid_or_unknown_overrides_fail_loudly(overrides):
    with pytest.raises(ValueError):
        gen.generate(1, 1, **overrides)


def test_self_check_rejects_targeted_semantic_impostors():
    # 1. A replacement color absent everywhere else is outside the fixed map.
    unknown_color = gen.generate(21, 7, n_colors=3)
    replaced = False
    for row, values in enumerate(unknown_color):
        for col, value in enumerate(values):
            if value != 7:
                unknown_color[row][col] = 3
                replaced = True
                break
        if replaced:
            break
    assert any("unexpected colors" in error for error in gen.self_check(unknown_color))

    # 2. Two colors cannot demonstrate the canonical three-to-five role range.
    two_colors = _grid_with_points(
        [(1, 1, 5), (1, 4, 5), (4, 1, 2), (4, 4, 2), (7, 7, 2)]
    )
    assert any("three to five" in error for error in gen.self_check(two_colors))

    # 3. One component per color hides the counting transformation.
    one_each = [[7 for _ in range(10)] for _ in range(10)]
    for offset, color in enumerate((5, 2, 8)):
        for col in range(2):
            one_each[2 + offset * 3][2 + col] = color
    assert any("at least one color must repeat" in error for error in gen.self_check(one_each))

    # 4. Equal component counts across colors erase the comparative histogram.
    equal_counts = _grid_with_points(
        [
            (1, 1, 5), (1, 4, 5),
            (4, 1, 2), (4, 4, 2),
            (7, 1, 8), (7, 4, 8),
        ]
    )
    assert any("counts must differ" in error for error in gen.self_check(equal_counts))

    # 5. Seven isolated components exceed the canonical/output-height envelope.
    too_many = _grid_with_points(
        [
            (0, 0, 5), (0, 3, 5), (0, 6, 5), (3, 0, 5),
            (3, 3, 5), (3, 6, 5), (6, 0, 5),
            (7, 3, 2), (7, 6, 2), (9, 3, 8),
        ]
    )
    assert any("one to six" in error for error in gen.self_check(too_many))
