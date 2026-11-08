"""Task-local regression tests for generator 0162460030af.

These tests intentionally use an independent Python oracle for the ARC rule.
They protect the canonical examples, the advertised override contract, and the
three-example lesson schedule that feeds downstream training.
"""
from __future__ import annotations

import importlib.util
import os
from copy import deepcopy
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root


HOME = Path(__file__).resolve().parents[1]


def _load_generator():
    candidate = os.environ.get("GENERATOR_UNDER_TEST")
    path = Path(candidate) if candidate else HOME / "generator.py"
    spec = importlib.util.spec_from_file_location("generator_under_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def _pairs():
    return canonical_pairs(gen.TASK_ID, root=find_root(__file__), labeled_only=True)


def _components(grid):
    """Independent nonzero 4-connected component extractor, left-to-right."""
    height, width = len(grid), len(grid[0])
    seen = set()
    components = []
    for row in range(height):
        for column in range(width):
            if grid[row][column] == 0 or (row, column) in seen:
                continue
            stack = [(row, column)]
            seen.add((row, column))
            cells = []
            while stack:
                current = stack.pop()
                cells.append(current)
                r, c = current
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] != 0
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append(cells)
    return sorted(components, key=lambda cells: min(c for _, c in cells))


def _oracle(grid):
    """Independent mirror of the authoritative right-anchored alternation."""
    output = deepcopy(grid)
    components = _components(grid)
    count = len(components)
    for index, cells in enumerate(components):
        color = 8 if (count - index) % 2 == 1 else 2
        for row, column in cells:
            output[row][column] = color
    return output


@pytest.mark.parametrize("pair", _pairs(), ids=lambda p: f"{p['split']}-{p['pair_index']}")
def test_canonical_examples_match_independent_oracle_and_strict_profile(pair):
    assert gen.RULE_HASH == "617100877d72"
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert _oracle(pair["input"]) == pair["output"]
    assert gen._reference_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo_axis": 1},
        {"texture": "no_objects"},
        {"grid_h": 3},
        {"grid_h": 15},
        {"object_count": 1},
        {"object_count": 10},
        {"source_color": 0},
        {"source_color": 10},
        {"object_shape_kind": "diagonal"},
        {"column_spacing": 1},
        {"column_spacing": 4},
        {"mixed_shapes": 2},
        {"mixed_colors": -1},
    ],
)
def test_invalid_overrides_are_rejected(overrides):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 2, **overrides)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "expected",
    [
        {
            "grid_h": 4,
            "object_count": 9,
            "source_color": 2,
            "object_shape_kind": "L",
            "column_spacing": 2,
            "mixed_shapes": 1,
            "mixed_colors": 1,
        },
        {
            "grid_h": 14,
            "object_count": 2,
            "source_color": 8,
            "object_shape_kind": "single",
            "column_spacing": 3,
            "mixed_shapes": 0,
            "mixed_colors": 0,
        },
    ],
)
def test_exact_overrides_are_observable_in_every_band(band, expected):
    grid = gen.generate(1701, 29, difficulty=band, **expected)
    assert gen.self_check(grid, difficulty=band) == []
    assert gen.observe_overrides(grid) == expected


@pytest.mark.parametrize("shape", ["L", "vertical_2", "block_2x2", "T", "s_shape", "single"])
def test_each_declared_shape_is_constructed_and_observable(shape):
    expected = {
        "grid_h": 7,
        "object_count": 4,
        "source_color": 5,
        "object_shape_kind": shape,
        "column_spacing": 3,
        "mixed_shapes": 0,
        "mixed_colors": 0,
    }
    grid = gen.generate(77, 13, difficulty="hard", **expected)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == expected


def test_default_distribution_covers_strict_profiles_and_every_semantic_witness():
    for band in ("easy", "medium", "hard"):
        grids = [gen.generate(8000 + i, i, difficulty=band) for i in range(36)]
        assert all(gen.self_check(grid, difficulty=band) == [] for grid in grids)
        strict_count = sum(gen.strict_canonical_like(grid) == [] for grid in grids)
        assert strict_count >= 8, (band, strict_count)
        for name, predicate in gen.SEMANTIC_WITNESSES.items():
            assert any(predicate(grid) for grid in grids), (band, name)


def test_declared_canonical_shortcuts_fit_canonical_and_are_refuted_by_generation():
    pairs = _pairs()
    assert gen.CANONICAL_SHORTCUTS
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs), name
        assert any(
            rival(grid) != _oracle(grid)
            for grid in (gen.generate(9100 + i, i, difficulty="hard") for i in range(40))
        ), name


def test_every_four_pair_lesson_is_identifiable_under_all_query_rotations():
    # Materialization consumes consecutive accepted indices.  Every four-pair
    # window must retain both parity evidence and a generalized-shape/color
    # counterexample after any one pair is held out as the query.
    for band in ("easy", "medium", "hard"):
        for start in range(12):
            lesson = []
            for index in range(start, start + 4):
                grid = gen.generate(12001, index, difficulty=band)
                lesson.append({"input": grid, "output": _oracle(grid)})
            for query_index in range(4):
                query = lesson[query_index]
                demos = [pair for i, pair in enumerate(lesson) if i != query_index]
                assert gen.lesson_identifiable(demos, query) == [], (
                    band,
                    start,
                    query_index,
                )


def test_generation_is_deterministic_and_does_not_alias_returned_rows():
    overrides = {
        "grid_h": 9,
        "object_count": 7,
        "source_color": 6,
        "object_shape_kind": "T",
        "column_spacing": 2,
        "mixed_shapes": 1,
        "mixed_colors": 1,
    }
    first = gen.generate(73, 11, difficulty="medium", **overrides)
    second = gen.generate(73, 11, difficulty="medium", **overrides)
    assert first == second
    assert len({id(row) for row in first}) == len(first)
    first[0][0] = 9 if first[0][0] != 9 else 1
    assert first != second


@pytest.mark.parametrize("axis", ["mixed_shapes", "mixed_colors"])
@pytest.mark.parametrize("value", [False, True])
def test_boolean_axes_accept_literal_booleans_and_report_booleans(axis, value):
    grid = gen.generate(404, 17, difficulty="easy", **{axis: value})
    observed = gen.observe_overrides(grid)
    assert observed[axis] is value


def test_canonical_anchor_varies_across_seeds_without_changing_its_profile():
    grids = [gen.generate(seed, 0, difficulty="medium") for seed in range(20)]
    fingerprints = {tuple(tuple(row) for row in grid) for grid in grids}
    assert len(fingerprints) >= 4
    assert all(gen.strict_canonical_like(grid) == [] for grid in grids)


@pytest.mark.parametrize(
    "difficulty",
    [False, 0, 0.5, "__invalid_difficulty__"],
)
def test_generate_rejects_unsupported_difficulty_scalars(difficulty):
    """Invalid call-contract values must not silently select the medium band."""
    with pytest.raises((TypeError, ValueError)):
        gen.generate(20261020, 0, difficulty=difficulty)


@pytest.mark.parametrize("seed", [True, False, 1.0, 1.75, "1"])
def test_generate_rejects_noninteger_seed_scalars(seed):
    """Seed identity must not collapse across bool, float, or text values."""
    with pytest.raises((TypeError, ValueError)):
        gen.generate(seed, 0)


@pytest.mark.parametrize("sample_index", [True, False, 1.0, 1.75, -1])
def test_generate_rejects_invalid_sample_index_scalars(sample_index):
    """Accepted sample indices are genuine, non-negative integers."""
    with pytest.raises((TypeError, ValueError)):
        gen.generate(20261020, sample_index)
