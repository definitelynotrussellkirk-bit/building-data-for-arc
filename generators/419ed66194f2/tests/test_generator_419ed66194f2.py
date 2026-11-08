"""Focused semantic and override regressions for generator 419ed66194f2."""
from __future__ import annotations

from collections import Counter
import copy
import hashlib
import importlib
import json
from pathlib import Path
import random

import pytest

from puzzle_generators import base


TASK_ID = "419ed66194f2"
ROOT = Path(__file__).resolve().parents[1]
MODULE = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)


def _canonical_row():
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"missing canonical task {TASK_ID}")


def _canonical_pairs():
    row = _canonical_row()
    test = row["test"]
    tests = test if isinstance(test, list) else [test]
    return [*row["train"], *tests]


def _normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _frozen(grid):
    return tuple(tuple(row) for row in grid)


def test_rule_hash_canonical_inventory_and_exact_outputs():
    row = _canonical_row()
    pairs = _canonical_pairs()
    assert len(row["train"]) == 2
    assert len(pairs) == 3
    assert MODULE.RULE_HASH == "80ec33fe7d6c"
    assert MODULE.RULE_HASH == _normalized_hash(row["program_solution"])

    for pair in pairs:
        source = [[int(value) for value in row] for row in pair["input"]]
        expected = [[int(value) for value in row] for row in pair["output"]]
        before = copy.deepcopy(source)
        assert MODULE.self_check(source) == []
        assert MODULE.rule_mirror(source) == expected
        assert source == before


def test_declared_axes_are_exact_observable_and_full_boundaries_work():
    assert set(MODULE.AXES) == {
        "grid_h",
        "grid_w",
        "n_colors",
        "palette_profile",
        "layout_profile",
    }
    cases = [
        {"grid_h": 8},
        {"grid_h": 18},
        {"grid_w": 10},
        {"grid_w": 20},
        {"n_colors": 2},
        {"n_colors": 5},
        *({"palette_profile": value} for value in MODULE.PALETTE_PROFILES),
        *({"layout_profile": value} for value in MODULE.LAYOUT_PROFILES),
        {
            "grid_h": 8,
            "grid_w": 10,
            "n_colors": 5,
            "palette_profile": "high",
            "layout_profile": "reversed",
        },
        {
            "grid_h": 18,
            "grid_w": 20,
            "n_colors": 2,
            "palette_profile": "low",
            "layout_profile": "aligned",
        },
    ]
    for band in ("easy", "medium", "hard"):
        for index, overrides in enumerate(cases):
            grid = MODULE.generate(
                700 + index,
                31 * index + 5,
                difficulty=band,
                **overrides,
            )
            observed = MODULE.observe_overrides(grid)
            assert MODULE.self_check(
                grid,
                difficulty=band,
                meta={"overrides": overrides},
            ) == []
            assert all(observed[key] == value for key, value in overrides.items())

    for bad in (
        {"grid_h": 7},
        {"grid_h": 19},
        {"grid_w": 9},
        {"grid_w": 21},
        {"n_colors": 1},
        {"n_colors": 6},
        {"palette_profile": "warm"},
        {"layout_profile": "permuted"},
        {"palette_size": 5},
    ):
        with pytest.raises(ValueError):
            MODULE.generate(1, 2, difficulty="easy", **bad)


def test_ordinary_keyed_axis_values_match_returned_grid():
    for band in ("easy", "medium", "hard"):
        for seed in range(80):
            captured = []
            base.set_ctx_observer(captured.append)
            try:
                grid = MODULE.generate(seed + 1300, seed * 37 + 7, difficulty=band)
            finally:
                base.set_ctx_observer(None)
            assert len(captured) == 1
            observed = MODULE.observe_overrides(grid)
            assert set(captured[0]._drawn) >= set(MODULE.AXES)
            for axis in MODULE.AXES:
                assert captured[0]._drawn[axis] == observed[axis]


def test_linked_semantic_census_has_full_profiles_and_band_separation():
    expected_n_support = {
        "easy": {2, 3},
        "medium": {3, 4},
        "hard": {4, 5},
    }
    expected_size_bounds = {
        "easy": (3, 4),
        "medium": (3, 5),
        "hard": (4, 7),
    }
    for band in ("easy", "medium", "hard"):
        inputs = set()
        outputs = set()
        n_counts = Counter()
        palettes = Counter()
        layouts = Counter()
        size_counts = Counter()
        matches = 0
        for seed in range(200):
            grid = MODULE.generate(seed + 5000, seed * 41 + 11, difficulty=band)
            output = MODULE.rule_mirror(grid)
            observed = MODULE.semantic_observables(grid)
            linked = (
                MODULE.self_check(grid) == []
                and output != grid
                and observed["targets_nonoverlapping"]
                and observed["all_anchors_above_sources"]
                and observed["target_cell_count"] == sum(observed["object_sizes"])
                and set(value for row in output for value in row if value)
                == set(value for row in grid for value in row if value)
            )
            matches += int(linked)
            n_counts[observed["n_colors"]] += 1
            palettes[observed["palette_profile"]] += 1
            layouts[observed["layout_profile"]] += 1
            size_counts.update(observed["object_sizes"])
            inputs.add(_frozen(grid))
            outputs.add(_frozen(output))

        assert matches == 200
        assert set(n_counts) == expected_n_support[band]
        assert set(palettes) == set(MODULE.PALETTE_PROFILES)
        assert set(layouts) == set(MODULE.LAYOUT_PROFILES)
        lo, hi = expected_size_bounds[band]
        assert min(size_counts) >= lo
        assert max(size_counts) <= hi
        assert len(inputs) >= 198
        assert len(outputs) >= 198


def test_self_check_rejects_targeted_structural_impostors():
    grid = MODULE.generate(
        2201,
        17,
        difficulty="medium",
        grid_h=12,
        grid_w=15,
        n_colors=3,
        palette_profile="canonical",
        layout_profile="reversed",
    )
    analysis = MODULE._analysis(grid)
    color = sorted(analysis["colors"])[0]
    facts = analysis["colors"][color]
    anchor = facts["anchor"]
    source = facts["source"]

    missing_anchor = copy.deepcopy(grid)
    missing_anchor[anchor[0]][anchor[1]] = 0

    duplicate_anchor = copy.deepcopy(grid)
    candidate = next(
        (row, col)
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if duplicate_anchor[row][col] == 0
        and all(
            not (0 <= row + dr < len(grid) and 0 <= col + dc < len(grid[0]))
            or duplicate_anchor[row + dr][col + dc] != color
            for dr, dc in MODULE._DIRECTIONS
        )
    )
    duplicate_anchor[candidate[0]][candidate[1]] = color

    merged_anchor = copy.deepcopy(grid)
    merged_anchor[anchor[0]][anchor[1]] = 0
    neighbor = next(
        (row + dr, col + dc)
        for row, col in source
        for dr, dc in MODULE._DIRECTIONS
        if 0 <= row + dr < len(grid)
        and 0 <= col + dc < len(grid[0])
        and merged_anchor[row + dr][col + dc] == 0
    )
    merged_anchor[neighbor[0]][neighbor[1]] = color

    clipped_target = copy.deepcopy(grid)
    clipped_target[anchor[0]][anchor[1]] = 0
    clipped_target[-1][-1] = color

    for name, impostor in (
        ("missing_anchor", missing_anchor),
        ("duplicate_anchor", duplicate_anchor),
        ("merged_anchor", merged_anchor),
        ("clipped_target", clipped_target),
    ):
        assert MODULE.self_check(impostor), name


def test_negative_recombination_is_distribution_invalid():
    grid = MODULE.generate(3301, 19, difficulty="hard")
    analysis = MODULE._analysis(grid)
    color = sorted(analysis["colors"])[0]
    replacement = next(value for value in range(1, 10) if value not in analysis["colors"])
    mutated = copy.deepcopy(grid)
    for row, col in analysis["colors"][color]["source"]:
        mutated[row][col] = replacement
    assert MODULE.self_check(mutated)


def test_replay_returns_fresh_objects_and_preserves_global_rng():
    random.seed(20260724)
    state = random.getstate()
    first = MODULE.generate(97, 103, difficulty="hard")
    assert random.getstate() == state
    second = MODULE.generate(97, 103, difficulty="hard")
    assert random.getstate() == state
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))

    before = copy.deepcopy(second)
    output = MODULE.rule_mirror(second)
    assert second == before
    assert output is not second
    first[0][0] = 9 if first[0][0] != 9 else 7
    assert first != second
