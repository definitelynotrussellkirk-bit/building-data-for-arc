"""Independent public-rule and lesson-identifiability regressions.

The transform below normalizes and rotates coordinates without calling the
generator's rotation helper or rule mirror. It checks the public canonical
pairs and compares every declared canonical-fitting rival with generated
lessons. Run alongside test_review_regressions.py in either supported layout.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
import sys

import pytest


# Official task tests use pytest's importlib mode, which does not add the
# sibling test directory to sys.path. Load support from this file's own tree.
SUPPORT_PATH = Path(__file__).resolve().with_name("test_review_regressions.py")
SUPPORT_SPEC = importlib.util.spec_from_file_location(
    "review_regressions_support_531e65dffc0a", SUPPORT_PATH)
assert SUPPORT_SPEC is not None and SUPPORT_SPEC.loader is not None
support = importlib.util.module_from_spec(SUPPORT_SPEC)
sys.modules[SUPPORT_SPEC.name] = support
SUPPORT_SPEC.loader.exec_module(support)
ANCHOR_CODES, PAIRS = support.ANCHOR_CODES, support.PAIRS
assert_scene, gen = support.assert_scene, support.gen


def normalize(cells):
    min_r = min(r for r, c in cells)
    min_c = min(c for r, c in cells)
    return {(r - min_r, c - min_c) for r, c in cells}


def independent_transform(grid):
    cells = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row)
             if v not in ({0} | ANCHOR_CODES)}
    color = grid[next(iter(cells))[0]][next(iter(cells))[1]]
    shape = normalize(cells)
    height, width = len(grid), len(grid[0])
    output = [[0] * width for _ in range(height)]
    for r, row in enumerate(grid):
        for c, code in enumerate(row):
            if code not in ANCHOR_CODES:
                continue
            rotated = shape
            for _ in range(code - 2):
                rotated = normalize({(dc, -dr) for dr, dc in rotated})
            for dr, dc in rotated:
                if 0 <= r + dr < height and 0 <= c + dc < width:
                    output[r + dr][c + dc] = color
    return output


def canonical_shortcuts():
    shortcuts = getattr(gen, "CANONICAL_SHORTCUTS", None)
    assert isinstance(shortcuts, dict) and shortcuts, "declare executable canonical-fitting rivals"
    assert all(isinstance(name, str) and callable(rival)
               for name, rival in shortcuts.items())
    return shortcuts


def mapping_rivals():
    """All twelve single-code substitutions, independent of generator hooks."""
    rivals = {}
    for original in sorted(ANCHOR_CODES):
        for replacement in sorted(ANCHOR_CODES - {original}):
            def predict(grid, original=original, replacement=replacement):
                recoded = [[replacement if v == original else v for v in row]
                           for row in grid]
                return independent_transform(recoded)
            rivals[f"code_{original}_uses_{replacement}"] = predict
    return rivals


def lesson_rivals():
    return {**canonical_shortcuts(), **mapping_rivals()}


@pytest.mark.parametrize("pair", PAIRS)
def test_independent_transform_reproduces_every_public_pair(pair):
    before = deepcopy(pair["input"])
    assert independent_transform(pair["input"]) == pair["output"]
    assert pair["input"] == before


def test_declared_canonical_shortcuts_really_fit_all_public_pairs():
    for name, rival in canonical_shortcuts().items():
        for pair in PAIRS:
            grid = deepcopy(pair["input"])
            assert rival(grid) == pair["output"], (name, pair["split"], pair["pair_index"])
            assert grid == pair["input"], name


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_default_teaching_scenes_refute_each_canonical_fitting_rival(difficulty):
    # The declared even-index teaching schedule is a curriculum contract.
    # Exact overrides use the broad sampler and are intentionally absent here.
    shortcuts = canonical_shortcuts()
    for index in range(0, 24, 2):
        grid = gen.generate(74001 + index, index, difficulty=difficulty)
        assert_scene(grid)
        expected = independent_transform(grid)
        for name, rival in shortcuts.items():
            before = deepcopy(grid)
            assert rival(grid) != expected, (difficulty, index, name)
            assert grid == before, name


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_default_teaching_scenes_refute_all_twelve_code_mapping_rivals(difficulty):
    for index in range(0, 24, 2):
        grid = gen.generate(74001 + index, index, difficulty=difficulty)
        assert_scene(grid)
        expected = independent_transform(grid)
        for name, rival in mapping_rivals().items():
            before = deepcopy(grid)
            assert rival(grid) != expected, (difficulty, index, name)
            assert grid == before, name


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_every_four_position_lesson_window_identifies_the_query(difficulty):
    shortcuts = lesson_rivals()
    for seed in (93001, 93017, 93101):
        for start in range(4):
            pairs = []
            for offset in range(4):
                grid = gen.generate(seed, start + offset, difficulty=difficulty)
                assert_scene(grid)
                pairs.append({"input": grid, "output": independent_transform(grid)})
            for query_index in range(4):
                demos = [pair for i, pair in enumerate(pairs) if i != query_index]
                query = pairs[query_index]
                for name, rival in shortcuts.items():
                    fits_demos = all(rival(p["input"]) == p["output"] for p in demos)
                    assert not fits_demos or rival(query["input"]) == query["output"], (
                        difficulty, seed, start, query_index, name)
                if hasattr(gen, "lesson_identifiable"):
                    assert gen.lesson_identifiable(demos, query) == []
