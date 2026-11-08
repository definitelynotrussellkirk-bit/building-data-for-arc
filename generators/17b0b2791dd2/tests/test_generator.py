"""Portable regression tests for the exact-vertical-triple generator."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import os
from pathlib import Path
from typing import Iterable, Sequence

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "17b0b2791dd2"
HOME = Path(__file__).resolve().parents[1]
EXPECTED_AXES = {"grid_h", "grid_w", "vertical_count"}


def _load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
    spec = importlib.util.spec_from_file_location("reviewed_17b0b2791dd2", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()
PAIRS = canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)


def _components_of_one(grid: Sequence[Sequence[int]]) -> list[list[tuple[int, int]]]:
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 1 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == 1
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append(cells)
    return components


def _normalized(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    top = min(row for row, _ in cells)
    left = min(col for _, col in cells)
    return tuple(sorted((row - top, col - left) for row, col in cells))


def _shape_counts(grid: Sequence[Sequence[int]]) -> dict[str, int]:
    counts = {"vertical3": 0, "vertical4": 0, "horizontal3": 0}
    v3 = ((0, 0), (1, 0), (2, 0))
    v4 = ((0, 0), (1, 0), (2, 0), (3, 0))
    h3 = ((0, 0), (0, 1), (0, 2))
    for cells in _components_of_one(grid):
        shape = _normalized(cells)
        if shape == v3:
            counts["vertical3"] += 1
        elif shape == v4:
            counts["vertical4"] += 1
        elif shape == h3:
            counts["horizontal3"] += 1
    return counts


def _exact_rule(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Independent component oracle for the written canonical rule."""
    output = [list(row) for row in grid]
    target = ((0, 0), (1, 0), (2, 0))
    for cells in _components_of_one(grid):
        if _normalized(cells) == target:
            for row, col in cells:
                output[row][col] = 2
    return output


def _episode(grid: Sequence[Sequence[int]]) -> dict[str, list[list[int]]]:
    return {"input": [list(row) for row in grid], "output": _exact_rule(grid)}


def test_public_contract_is_pinned_minimal_and_semantic():
    assert gen.RULE_HASH == "1deed242f221"
    assert gen.VERSION == "2.0.0"
    assert gen.EXAMPLES_NEEDED == 3
    assert gen.MIN_STRICT_FRAC == 1.0
    assert set(gen.AXES) == EXPECTED_AXES
    assert tuple(gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS) == ()
    assert not hasattr(gen, "DEGENERATE_TEXTURES")
    assert callable(gen.observe_overrides)
    assert callable(gen.strict_canonical_like)
    assert set(gen.SEMANTIC_WITNESSES) == {
        "vertical_length_four_distractor",
        "horizontal_length_three_distractor",
    }
    assert set(gen.SEMANTIC_RIVALS) == {
        "recolor_every_vertical_line",
        "recolor_every_three_cell_component",
    }
    assert set(gen.CANONICAL_SHORTCUTS) == {"recolor_every_vertical_line"}
    assert set(gen.LESSON_COMPETITORS) == set(gen.SEMANTIC_RIVALS)


def test_canonical_inputs_are_accepted_and_independent_oracle_matches_labels():
    assert len(PAIRS) == 3
    for pair in PAIRS:
        original = deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert _exact_rule(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_declared_vertical_shortcut_really_fits_all_canonical_examples():
    rival = gen.CANONICAL_SHORTCUTS["recolor_every_vertical_line"]
    assert all(rival(pair["input"]) == pair["output"] for pair in PAIRS)


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": 8, "grid_w": 8, "vertical_count": 1},
        {"grid_h": 8, "grid_w": 8, "vertical_count": 3},
        {"grid_h": 14, "grid_w": 13, "vertical_count": 2},
        {"grid_h": 14, "grid_w": 14, "vertical_count": 3},
    ],
)
def test_every_advertised_override_is_exact_and_observable_in_every_band(
    difficulty, overrides
):
    grid = gen.generate(91, 7, difficulty=difficulty, **overrides)
    assert gen.self_check(grid, difficulty=difficulty) == []
    assert gen.observe_overrides(grid) == overrides
    assert _shape_counts(grid)["vertical3"] == overrides["vertical_count"]


@pytest.mark.parametrize(
    "overrides",
    [
        {"unknown_axis": 1},
        {"grid_h": 7},
        {"grid_h": 15},
        {"grid_h": True},
        {"grid_h": "8"},
        {"grid_w": 7},
        {"grid_w": 15},
        {"grid_w": 8.0},
        {"vertical_count": 0},
        {"vertical_count": 4},
        {"vertical_count": False},
    ],
)
def test_unknown_invalid_and_coercible_overrides_fail_loudly(overrides):
    with pytest.raises((KeyError, TypeError, ValueError)):
        gen.generate(1, 2, **overrides)


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_ordinary_draws_are_deterministic_lawful_and_always_teach_exactness(difficulty):
    distinct = set()
    dimensions = set()
    vertical_counts = set()
    for index in range(36):
        seed = 7000 + index
        grid = gen.generate(seed, index, difficulty=difficulty)
        assert grid == gen.generate(seed, index, difficulty=difficulty)
        assert gen.self_check(grid) == []
        counts = _shape_counts(grid)
        assert counts["vertical3"] >= 1
        assert counts["horizontal3"] >= 1
        assert counts["vertical4"] >= 1
        assert gen.SEMANTIC_WITNESSES["vertical_length_four_distractor"](grid)
        assert gen.SEMANTIC_WITNESSES["horizontal_length_three_distractor"](grid)
        observed = gen.observe_overrides(grid)
        vertical_counts.add(observed["vertical_count"])
        dimensions.add((observed["grid_h"], observed["grid_w"]))
        distinct.add(tuple(tuple(row) for row in grid))
    assert len(distinct) >= 32
    assert len(dimensions) >= 6
    assert vertical_counts == {1, 2, 3}


def test_retained_seed_one_regression_cannot_omit_the_exactness_witness():
    for sample_index in range(4):
        grid = gen.generate(1, sample_index, difficulty="medium")
        assert _shape_counts(grid)["vertical4"] >= 1
        rival = gen.SEMANTIC_RIVALS["recolor_every_vertical_line"]
        assert rival(grid) != _exact_rule(grid)


def test_declared_semantic_witnesses_refute_their_named_rivals():
    grid = gen.generate(712, 5, grid_h=10, grid_w=10, vertical_count=2)
    assert gen.SEMANTIC_WITNESSES["vertical_length_four_distractor"](grid)
    assert gen.SEMANTIC_WITNESSES["horizontal_length_three_distractor"](grid)
    assert (
        gen.SEMANTIC_RIVALS["recolor_every_vertical_line"](grid)
        != _exact_rule(grid)
    )
    assert (
        gen.SEMANTIC_RIVALS["recolor_every_three_cell_component"](grid)
        != _exact_rule(grid)
    )


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_three_demo_lessons_refute_every_declared_competitor(difficulty):
    generated = [
        gen.generate(311, index, difficulty=difficulty) for index in range(8)
    ]
    for start in range(5):
        demos = [_episode(grid) for grid in generated[start : start + 3]]
        query = _episode(generated[start + 3])
        assert gen.lesson_identifiable(demos, query) == []


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0], [0, 0]],
        [[True] * 8 for _ in range(8)],
        [[0] * 8 for _ in range(8)],
        [[2] + [0] * 7 for _ in range(8)],
    ],
)
def test_self_check_handles_malformed_or_out_of_grammar_grids_without_raising(grid):
    assert gen.self_check(grid)
