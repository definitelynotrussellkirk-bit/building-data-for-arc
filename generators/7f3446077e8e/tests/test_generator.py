"""Focused contract tests for task 7f3446077e8e."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import os
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "7f3446077e8e"
TASK_HOME = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get("GENERATOR_UNDER_TEST", TASK_HOME / "generator.py"))


def _load_generator(path: Path):
    spec = importlib.util.spec_from_file_location(f"generator_{TASK_ID}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator(SOURCE)


def intended_output(grid):
    out = deepcopy(grid)
    h, w = len(grid), len(grid[0])
    cells2 = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    p8 = next((r, c) for r in range(h) for c in range(w) if grid[r][c] == 8)
    p9 = next((r, c) for r in range(h) for c in range(w) if grid[r][c] == 9)
    dr, dc = p9[0] - p8[0], p9[1] - p8[1]
    for r, c in cells2:
        rr, cc = r + dr, c + dc
        if 0 <= rr < h and 0 <= cc < w:
            out[rr][cc] = 3
    return out


def vector(grid):
    h, w = len(grid), len(grid[0])
    p8 = next((r, c) for r in range(h) for c in range(w) if grid[r][c] == 8)
    p9 = next((r, c) for r in range(h) for c in range(w) if grid[r][c] == 9)
    return p9[0] - p8[0], p9[1] - p8[1]


def palette_size(grid):
    return len({value for row in grid for value in row})


def test_canonical_inputs_are_owned_and_rule_mirror_matches_labels():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert intended_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("visibility", ["full", "clipped"])
def test_exact_overrides_are_observable_in_every_band(band, visibility):
    options = {
        "grid_h": 11,
        "grid_w": 12,
        "shape_size": 7,
        "decoration_size": 2,
        "copy_visibility": visibility,
    }
    grid = gen.generate(19, 6, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert gen.strict_canonical_like(grid) == []
    assert gen.observe_overrides(grid) == options
    assert grid == gen.generate(19, 6, difficulty=band, **options)


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 8),
        ("grid_w", 13),
        ("shape_size", 2),
        ("shape_size", 10),
        ("decoration_size", 0),
        ("decoration_size", 3),
        ("copy_visibility", "unknown"),
        ("grid_h", True),
        ("shape_size", 4.0),
    ],
)
def test_invalid_overrides_are_rejected(key, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{key: value})


def test_default_distribution_covers_profiles_clipping_and_both_vector_modes():
    canonical_profiles = {(9, 11, 5), (10, 10, 5), (10, 12, 5), (11, 12, 5), (12, 12, 5)}
    exact_profiles = set()
    visibilities = set()
    modes = []
    for index in range(120):
        grid = gen.generate(700 + index, index, difficulty=("easy", "medium", "hard")[index % 3])
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        assert palette_size(grid) == 5
        exact_profiles.add((len(grid), len(grid[0]), palette_size(grid)))
        visibilities.add(gen.observe_overrides(grid)["copy_visibility"])
        dr, dc = vector(grid)
        modes.append("axial" if (dr == 0) ^ (dc == 0) else "diagonal")
    assert canonical_profiles & exact_profiles
    assert visibilities == {"full", "clipped"}
    assert {"axial", "diagonal"} <= set(modes)
    for start in range(len(modes) - 3):
        assert modes[start : start + 4].count("axial") == 2


def test_diagonal_only_shortcut_fits_canonical_but_generated_axial_case_refutes_it():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    rival = gen.CANONICAL_SHORTCUTS["diagonal_only"]
    assert all(rival(pair["input"]) == pair["output"] for pair in pairs)

    witness = gen.generate(31, 0, copy_visibility="full")
    dr, dc = vector(witness)
    assert (dr == 0) ^ (dc == 0)
    assert gen.SEMANTIC_WITNESSES["axial_vector"](witness)
    assert rival(witness) != intended_output(witness)


def test_lesson_contract_refutes_shortcut_for_production_and_rotated_queries():
    pairs = []
    for index in range(4):
        grid = gen.generate(91, index)
        pairs.append({"input": grid, "output": intended_output(grid)})
    for query_index in range(4):
        demos = [pair for i, pair in enumerate(pairs) if i != query_index]
        assert gen.lesson_identifiable(demos, pairs[query_index]) == []


def test_difficulty_bands_enter_layout_randomness_without_changing_contract():
    grids = [gen.generate(314159, 5, difficulty=band)
             for band in ("easy", "medium", "hard")]
    assert all(gen.self_check(grid) == [] for grid in grids)
    assert len({tuple(tuple(row) for row in grid) for grid in grids}) >= 2
