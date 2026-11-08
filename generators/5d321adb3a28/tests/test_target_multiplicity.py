"""Regression tests for canonical target-count coverage."""
from __future__ import annotations

from collections import Counter
import importlib.util
import os
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root


TASK_DIR = Path(__file__).resolve().parents[1]
GENERATOR_PATH = Path(
    os.environ.get("GENERATOR_UNDER_TEST", TASK_DIR / "generator.py")
)


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        "generator_5d321adb3a28_target_multiplicity", GENERATOR_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _changed_cells(gen, grid) -> int:
    output = gen.rule_mirror(grid)
    return sum(
        before != after
        for input_row, output_row in zip(grid, output)
        for before, after in zip(input_row, output_row)
    )


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_draws_match_canonical_three_target_profiles(band):
    gen = _load_generator()
    profiles = Counter()

    for sample_index in range(80):
        grid = gen.generate(7301 + sample_index, sample_index, difficulty=band)
        analysis = gen._analyze_grid(grid)
        horizontal = analysis["counts"][gen._H_TARGET]
        vertical = analysis["counts"][gen._V_TARGET]
        profiles[f"{horizontal}h{vertical}v"] += 1

        assert _changed_cells(gen, grid) == 3
        assert (horizontal, vertical) in {(2, 1), (1, 2)}
        assert gen.self_check(grid) == []

    assert set(profiles) == {"2h1v", "1h2v"}


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_two_change_cap_competitor_is_refuted_by_every_default_draw(band):
    gen = _load_generator()
    rival = gen.LESSON_COMPETITORS["two_change_cap"]
    witness = gen.SEMANTIC_WITNESSES["canonical_target_multiplicity"]

    for sample_index in range(40):
        grid = gen.generate(8101 + sample_index, sample_index, difficulty=band)
        assert witness(grid)
        assert rival(grid) != gen.rule_mirror(grid)


def _max_nonzero_component_size(grid) -> int:
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    biggest = 0
    for row in range(height):
        for column in range(width):
            if grid[row][column] == 0 or (row, column) in seen:
                continue
            color = grid[row][column]
            stack = [(row, column)]
            seen.add((row, column))
            size = 0
            while stack:
                current_row, current_column = stack.pop()
                size += 1
                for drow, dcolumn in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    next_row = current_row + drow
                    next_column = current_column + dcolumn
                    if not (0 <= next_row < height and 0 <= next_column < width):
                        continue
                    cell = (next_row, next_column)
                    if cell in seen or grid[next_row][next_column] != color:
                        continue
                    seen.add(cell)
                    stack.append(cell)
            biggest = max(biggest, size)
    return biggest


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_distribution_reaches_canonical_scale_components(band):
    gen = _load_generator()
    observed = []

    for sample_index in range(80):
        grid = gen.generate(9201 + sample_index, sample_index, difficulty=band)
        observed.append(_max_nonzero_component_size(grid))

    assert min(observed) <= 2, observed


def test_every_declared_canonical_shortcut_fits_every_canonical_pair():
    gen = _load_generator()
    root = find_root(__file__)
    pairs = canonical_pairs(gen.TASK_ID, root=root)

    assert pairs
    assert gen.CANONICAL_SHORTCUTS
    for name, shortcut in gen.CANONICAL_SHORTCUTS.items():
        for pair in pairs:
            assert shortcut(pair["input"]) == pair["output"], (
                name,
                pair["variant"],
                pair["split"],
                pair["pair_index"],
            )
