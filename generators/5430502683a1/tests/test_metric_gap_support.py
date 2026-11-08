"""Independent regressions for adjacent-gap shortcuts in endpoint selection.

The v4.0.0 candidate made every winning axis exactly one cell longer than its
longest diagonal competitor. A conditional rule could therefore match its
whole distribution while rejecting other lawful axis winners. These checks
observe rendered spans, not schedule labels or private placement helpers.
Canonical labels anchor the local geometric interpretation; retained Racket
receipts independently exercise the labels and counterexample inputs.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import importlib.util
from math import gcd
from pathlib import Path
import sys

import pytest


for _ancestor in Path(__file__).resolve().parents:
    _found = False
    for _candidate in (_ancestor, _ancestor / "shared" / "runtime"):
        if (_candidate / "reviewer_support.py").is_file():
            sys.path.insert(0, str(_candidate))
            _found = True
            break
    if _found:
        break
else:
    raise ImportError("No local reviewer_support runtime for gap regressions")

from reviewer_support import canonical_pairs, find_root

ROOT = find_root(__file__)
TASK = "5430502683a1"
GENERATOR_PATH = next(path for path in (
    ROOT / "generators" / TASK / "generator.py",
    ROOT / "puzzle_generators" / "per_puzzle" / TASK / "generator.py",
) if path.is_file())
_spec = importlib.util.spec_from_file_location("endpoint_gap_regression_generator", GENERATOR_PATH)
generator = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = generator
_spec.loader.exec_module(generator)


def _observed_pairs(grid):
    occupied = defaultdict(list)
    for row, values in enumerate(grid):
        for col, color in enumerate(values):
            if color:
                occupied[color].append((row, col))
    pairs = []
    for color, endpoints in sorted(occupied.items()):
        assert len(endpoints) == 2
        a, b = endpoints
        dr, dc = b[0] - a[0], b[1] - a[1]
        assert dr == 0 or dc == 0 or abs(dr) == abs(dc)
        steps = gcd(abs(dr), abs(dc))
        assert steps > 0
        cells = [(a[0] + i * dr // steps, a[1] + i * dc // steps) for i in range(steps + 1)]
        pairs.append({"color": color, "cells": cells, "length": len(cells),
                      "diagonal": bool(dr and dc), "euclidean_squared": dr * dr + dc * dc})
    return pairs


def _paint(grid, pair):
    out = [[0] * len(grid[0]) for _ in grid]
    if pair is not None:
        for row, col in pair["cells"]:
            out[row][col] = 8
    return out


def _longest(pairs):
    return max(pairs, key=lambda pair: pair["length"]) if pairs else None


def _correct(grid):
    pairs = _observed_pairs(grid)
    assert Counter(pair["length"] for pair in pairs)[max(pair["length"] for pair in pairs)] == 1
    return _paint(grid, _longest(pairs))


def _axis_only_for_gap(grid, gap_kind):
    """Wrong rule: choose an axis only for one allowed gap class."""
    pairs = _observed_pairs(grid)
    axis = _longest([pair for pair in pairs if not pair["diagonal"]])
    diagonal = _longest([pair for pair in pairs if pair["diagonal"]])
    if axis is None or diagonal is None:
        return _paint(grid, _longest(pairs))
    gap = axis["length"] - diagonal["length"]
    allowed = gap == 1 if gap_kind == "one" else gap >= 2
    return _paint(grid, axis if allowed else diagonal)


def _ignore_color(grid, color):
    """Wrong color semantics: connect the longest pair of every other color."""
    return _paint(grid, _longest([pair for pair in _observed_pairs(grid) if pair["color"] != color]))


def _shape_kind(grid):
    pairs = _observed_pairs(grid)
    winner = _longest(pairs)
    if winner["diagonal"]:
        return "diagonal", 0, winner["length"]
    diagonal = _longest([pair for pair in pairs if pair["diagonal"]])
    if diagonal is None or diagonal["euclidean_squared"] <= winner["euclidean_squared"]:
        return "free_axis", 0, winner["length"]
    gap = winner["length"] - diagonal["length"]
    assert gap > 0
    return "gap_one" if gap == 1 else "gap_many", gap, winner["length"]


def test_both_conditional_gap_rivals_fit_the_canonical_labels():
    pairs = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    assert pairs
    for pair in pairs:
        assert _correct(pair["input"]) == pair["output"]
        for gap_kind in ("one", "many"):
            assert _axis_only_for_gap(pair["input"], gap_kind) == pair["output"]


@pytest.mark.parametrize("difficulty", ("easy", "medium", "hard"))
def test_default_distribution_has_a_substantial_floor_for_both_gap_classes(difficulty):
    kinds, lengths, gaps = Counter(), defaultdict(set), defaultdict(set)
    draws = 48 * 8
    for seed in range(48):
        for index in range(8):
            kind, gap, length = _shape_kind(generator.generate(seed, index, difficulty=difficulty))
            kinds[kind] += 1
            lengths[kind].add(length)
            gaps[kind].add(gap)
    for kind in ("gap_one", "gap_many", "diagonal"):
        assert kinds[kind] >= draws // 6, f"{difficulty}: only {kinds[kind]}/{draws} {kind} examples"
    assert min(lengths["gap_one"]) <= 7, "adding a large-gap branch must retain short axis witnesses"
    assert min(gaps["gap_many"]) >= 2
    if difficulty == "hard":
        assert len(gaps["gap_many"]) >= 2, "large gaps must vary beyond one fixed replacement gap"


@pytest.mark.parametrize("difficulty", ("easy", "medium", "hard"))
@pytest.mark.parametrize("pair_count", (2, 3, 4))
@pytest.mark.parametrize("start", range(8))
def test_each_query_holdout_retains_counterexamples_to_gap_and_ignored_color_shortcuts(difficulty, pair_count, start):
    for seed in (0, 29):
        grids = [generator.generate(seed, start + offset, difficulty=difficulty, pair_count=pair_count)
                 for offset in range(8)]
        labels = [_correct(grid) for grid in grids]
        palette = {pair["color"] for pair in _observed_pairs(grids[0])}
        assert all({pair["color"] for pair in _observed_pairs(grid)} == palette for grid in grids)
        winning_colors = Counter(_longest(_observed_pairs(grid))["color"] for grid in grids)
        assert set(winning_colors) == palette
        assert all(winning_colors[color] >= 2 for color in palette), winning_colors
        for gap_kind in ("one", "many"):
            disagreements = [_axis_only_for_gap(grid, gap_kind) != label for grid, label in zip(grids, labels)]
            assert sum(disagreements) >= 2, f"{seed=}, {start=}, {gap_kind=}: an isolated witness is not rotation-safe"
            for query_index in range(8):
                assert any(disagrees for index, disagrees in enumerate(disagreements) if index != query_index)
        for color in palette:
            disagreements = [_ignore_color(grid, color) != label for grid, label in zip(grids, labels)]
            for query_index in range(8):
                assert any(disagrees for index, disagrees in enumerate(disagreements) if index != query_index), (
                    f"{seed=}, {start=}, {color=}: ignore-color rival survives the remaining seven demonstrations"
                )


@pytest.mark.parametrize("height,width", ((8, 9), (8, 18), (16, 9), (16, 18)))
@pytest.mark.parametrize("pair_count", (2, 3, 4))
def test_metric_gap_contrast_survives_joint_exact_axis_extremes(height, width, pair_count):
    for seed in (3, 41):
        grids = [generator.generate(seed, index, difficulty="hard",
                                    grid_h=height, grid_w=width, pair_count=pair_count)
                 for index in range(8)]
        kinds = Counter(_shape_kind(grid)[0] for grid in grids)
        assert all(kinds[kind] >= 2 for kind in ("gap_one", "gap_many", "diagonal")), kinds
        assert all((len(grid), len(grid[0])) == (height, width) for grid in grids)
