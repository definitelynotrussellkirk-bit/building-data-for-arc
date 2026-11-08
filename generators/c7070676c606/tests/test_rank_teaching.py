"""Independent BFS regressions for marker-dependent rank teaching.

Diagnostic constant-rank predictions do not label generated material. Actual
Racket before-repair ambiguity is retained separately in the review evidence.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
import importlib.util

import pytest
from reviewer_support import find_root


TASK = "c7070676c606"
ROOT = find_root(__file__)
SOURCE = ROOT / "generators" / TASK / "generator.py"
if not SOURCE.is_file():
    SOURCE = ROOT / "puzzle_generators" / "per_puzzle" / TASK / "generator.py"
SPEC = importlib.util.spec_from_file_location("rank_teaching_generator", SOURCE)
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)
BASE_NAMES = {"top_to_bottom", "bbox_area", "bbox_width", "bbox_height",
              "perimeter", "eight_connected", "global_blue_count", "blue_runs"}
CONSTANT_NAMES = {f"constant_rank_{rank}" for rank in range(1, 6)}
ASCENDING_NAMES = {f"constant_smallest_rank_{rank}" for rank in range(1, 6)}
EXTRA_NAMES = {"reverse_ties", "bbox_ties", "dense_ranks", "all_tied",
               "include_top_row", "clip_top_row", "all_nonbackground",
               "global_blue_components"}


def constant_rank_prediction(grid, rank):
    """Independent same-color BFS; undefined fixed ranks leave input unchanged."""
    output = deepcopy(grid)
    unseen = {(r, c) for r, row in enumerate(grid)
              for c, color in enumerate(row) if color == 3}
    components = []
    while unseen:
        first = min(unseen)
        unseen.remove(first)
        pending = deque([first])
        cells = {first}
        while pending:
            r, c = pending.popleft()
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    pending.append(neighbor)
                    cells.add(neighbor)
        if min(r for r, c in cells) > 0:
            components.append(cells)
    components.sort(key=lambda cells: (-len(cells), min(cells)))
    if 1 <= rank <= len(components):
        for r, c in components[rank - 1]:
            output[r][c] = 2
    return output


@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
@pytest.mark.parametrize("seed", (0, 17, 91))
@pytest.mark.parametrize("start", range(10))
def test_default_three_demo_windows_teach_rank_variation(band, seed, start):
    grids = [GEN.generate(seed, index, difficulty=band)
             for index in range(start, start + 5)]
    ranks = [grid[0].count(1) for grid in grids]
    assert len(set(ranks[:3])) >= 2, (band, seed, start, ranks)
    for index, rank in zip(range(start, start + 5), ranks):
        assert (rank == 2) == (index % 2 == 0), (index, ranks)
        if index % 10 == 1:
            assert rank == 3
    # The first four also support every query rotation; two witnesses ensure
    # one refuter remains among demos when any single pair becomes the query.
    assert len({str(grid) for grid in grids[:4]}) == 4
    for rank in range(1, 6):
        refutes = [constant_rank_prediction(grid, rank)
                   != constant_rank_prediction(grid, grid[0].count(1))
                   for grid in grids[:4]]
        assert sum(refutes) >= 2, (band, seed, start, rank, refutes)


def test_constant_rank_rivals_are_lesson_only_and_all_twenty_six_are_declared():
    assert set(GEN.LESSON_COMPETITORS) == BASE_NAMES | CONSTANT_NAMES | EXTRA_NAMES | ASCENDING_NAMES
    assert set(GEN.CANONICAL_SHORTCUTS) == BASE_NAMES
    assert set(GEN.SEMANTIC_RIVALS) == BASE_NAMES
    assert GEN.VERSION == "3.0.4"


@pytest.mark.parametrize("rank", range(1, 6))
def test_constant_rank_rivals_match_independent_oracle_and_are_pure(rank):
    solve = GEN.LESSON_COMPETITORS.get(f"constant_rank_{rank}")
    assert callable(solve)
    grids = [GEN.generate(17, index, difficulty="hard") for index in range(10)]
    grids += [[], [[1, 0], [0, 3]], [[3, 1], [3, 0]]]
    for grid in grids:
        before = deepcopy(grid)
        assert solve(grid) == constant_rank_prediction(grid, rank)
        assert grid == before


@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
@pytest.mark.parametrize("index", (0, 1, 3))
def test_explicit_rank_two_remains_a_lawful_exact_override(band, index):
    grid = GEN.generate(17, index, difficulty=band, k_select=2)
    assert grid[0].count(1) == 2
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid)["k_select"] == 2
