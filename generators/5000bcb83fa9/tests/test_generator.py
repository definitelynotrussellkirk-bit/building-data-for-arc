"""Focused regressions for the odd-horizontal-run center curriculum."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import os
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "5000bcb83fa9"
HOME = Path(__file__).resolve().parents[1]


def _load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
    spec = importlib.util.spec_from_file_location(f"review_{TASK_ID}_generator", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def _runs(grid):
    """Return (row, start, end-exclusive, color) for maximal nonzero row runs."""
    found = []
    for row_index, row in enumerate(grid):
        column = 0
        while column < len(row):
            if row[column] == 0:
                column += 1
                continue
            start = column
            color = row[column]
            while column < len(row) and row[column] == color:
                column += 1
            found.append((row_index, start, column, color))
    return found


def _rule_output(grid):
    output = [[0 for _ in row] for row in grid]
    for row, start, end, color in _runs(grid):
        length = end - start
        if length % 2:
            output[row][start + length // 2] = color
    return output


def _observed(grid):
    runs = _runs(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "run_count": len(runs),
        "singleton_count": sum(end - start == 1 for _, start, end, _ in runs),
    }


def test_rule_pin_and_every_canonical_pair():
    assert gen.RULE_HASH == "2b45ada2fe3e"
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert len(pairs) == 4
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert _rule_output(pair["input"]) == pair["output"]


def test_historical_override_and_validator_counterexamples_are_closed():
    grid = gen.generate(0, 0, difficulty="easy", run_count=5)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid)["run_count"] == 5

    malformed = [
        [2, 2, 0, 3, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ]
    findings = gen.self_check(malformed)
    assert findings
    assert any("even" in finding or "odd" in finding for finding in findings)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        {"grid_h": 5, "grid_w": 9, "run_count": 3, "singleton_count": 0},
        {"grid_h": 5, "grid_w": 13, "run_count": 5, "singleton_count": 2},
        {"grid_h": 9, "grid_w": 9, "run_count": 5, "singleton_count": 0},
        {"grid_h": 9, "grid_w": 13, "run_count": 3, "singleton_count": 2},
    ],
)
def test_exact_controls_are_constructive_and_observable_in_every_band(band, options):
    grid = gen.generate(71, 19, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert _observed(grid) == options
    assert gen.observe_overrides(grid) == options
    assert _rule_output(grid) != grid


@pytest.mark.parametrize(
    "options",
    [
        {"typo": 1},
        {"texture": "no_runs"},
        {"grid_h": 4},
        {"grid_h": 10},
        {"grid_w": 8},
        {"grid_w": 14},
        {"run_count": 2},
        {"run_count": 6},
        {"singleton_count": -1},
        {"singleton_count": 3},
        {"run_count": True},
        {"singleton_count": 1.5},
        {"grid_w": "10"},
    ],
)
def test_invalid_or_unknown_overrides_are_loud(options):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **options)


def test_default_distribution_is_canonical_profiled_nonidentity_and_deterministic():
    canonical_profiles = {(5, 11, 5), (6, 10, 5), (7, 9, 5)}
    profiles = set()
    starts = set()
    colors = set()
    lengths_by_band = {}
    for band in ("easy", "medium", "hard"):
        lengths = set()
        for index in range(48):
            grid = gen.generate(3100 + index, index, difficulty=band)
            assert grid == gen.generate(3100 + index, index, difficulty=band)
            assert gen.self_check(grid) == []
            assert _rule_output(grid) != grid
            assert gen.strict_canonical_like(grid) == []
            obs = gen.observe_overrides(grid)
            assert obs["run_count"] == 4
            assert obs["singleton_count"] == 1
            profiles.add((len(grid), len(grid[0]), len({v for row in grid for v in row})))
            for _, start, end, color in _runs(grid):
                starts.add(start)
                colors.add(color)
                lengths.add(end - start)
        lengths_by_band[band] = lengths
    assert profiles == canonical_profiles
    assert len(starts) >= 5
    assert len(colors) >= 8
    assert {1, 3} <= lengths_by_band["easy"]
    assert {1, 3, 5} <= lengths_by_band["medium"]
    assert {1, 5} <= lengths_by_band["hard"]


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True] * 9 for _ in range(5)],
        [[0] * 9 for _ in range(5)],
        [[1, 1, 1] + [0] * 6] + [[0] * 9 for _ in range(4)],
        [
            [1, 1, 1, 0, 1, 1, 1, 0, 0],
            [0, 2, 2, 2, 0, 0, 0, 0, 0],
            [0, 0, 3, 3, 3, 0, 0, 0, 0],
            [0] * 9,
            [0] * 9,
        ],
        [
            [1, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 2, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 3, 0, 0, 0, 0, 0, 0],
            [0] * 9,
            [0] * 9,
        ],
    ],
)
def test_self_check_rejects_malformed_and_out_of_manifold_inputs(grid):
    assert gen.self_check(deepcopy(grid))


def test_semantic_witness_refutes_every_declared_rival():
    for band in ("easy", "medium", "hard"):
        for index in range(12):
            grid = gen.generate(811 + index, index, difficulty=band)
            expected = _rule_output(grid)
            assert gen.SEMANTIC_WITNESSES["nontrivial_odd_run"](grid)
            for name in gen.WITNESS_RIVALS["nontrivial_odd_run"]:
                assert gen.SEMANTIC_RIVALS[name](deepcopy(grid)) != expected


def test_lessons_refute_all_competitors_without_order_dependence():
    for band in ("easy", "medium", "hard"):
        pairs = []
        for index in range(4):
            grid = gen.generate(901, index, difficulty=band)
            pairs.append({"input": grid, "output": _rule_output(grid)})
        for query_index in range(4):
            query = deepcopy(pairs[query_index])
            demos = deepcopy([pair for i, pair in enumerate(pairs) if i != query_index])
            assert gen.lesson_identifiable(demos, query) == []
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(rival(deepcopy(d["input"])) != d["output"] for d in demos), name
