"""Independent BFS checks for both finite fixed-rank orientations.

Frozen labels come from the public Racket-labeled v3.0.3 census. Fixed ascending
rules are diagnostic competitors and do not supply generation labels.
"""
from __future__ import annotations
from collections import deque
from copy import deepcopy
import importlib.util
import json

import pytest
from reviewer_support import find_root

TASK = "c7070676c606"
ROOT = find_root(__file__)
SOURCE = ROOT / "generators" / TASK / "generator.py"
if not SOURCE.is_file():
    SOURCE = ROOT / "puzzle_generators" / "per_puzzle" / TASK / "generator.py"
SPEC = importlib.util.spec_from_file_location("ascending_teaching_generator", SOURCE)
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def components(grid):
    unseen = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
              if value == 3}
    result = []
    while unseen:
        first = min(unseen)
        unseen.remove(first)
        pending = deque([first])
        cells = {first}
        while pending:
            r, c = pending.popleft()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in unseen:
                    unseen.remove(point)
                    pending.append(point)
                    cells.add(point)
        if min(r for r, c in cells) > 0:
            result.append(cells)
    return result


def prediction(grid, rank, *, ascending):
    out = deepcopy(grid)
    ranked = sorted(components(grid),
                    key=lambda cells: (len(cells) if ascending else -len(cells), min(cells)))
    if 1 <= rank <= len(ranked):
        for r, c in ranked[rank - 1]:
            out[r][c] = 2
    return out


@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
@pytest.mark.parametrize("seed", (0, 17, 91))
@pytest.mark.parametrize("start", range(10))
def test_every_default_window_refutes_each_fixed_rank_in_both_orientations(band, seed, start):
    grids = [GEN.generate(seed, index, difficulty=band) for index in range(start, start + 4)]
    for index, grid in zip(range(start, start + 4), grids):
        n, k = len(components(grid)), grid[0].count(1)
        if index % 2 == 0:
            assert 4 <= n <= 5 and k == 2
        else:
            assert k != 2 and n - k + 1 <= 2, (index, n, k)
        assert GEN.self_check(grid) == []
    for ascending in (False, True):
        for rank in range(1, 6):
            refutes = [prediction(grid, rank, ascending=ascending)
                       != prediction(grid, grid[0].count(1), ascending=False) for grid in grids]
            assert sum(refutes) >= 2, (seed, band, start, ascending, rank, refutes)


@pytest.mark.parametrize("rank", range(1, 6))
def test_ascending_family_is_lesson_only_pure_and_matches_independent_oracle(rank):
    name = f"constant_smallest_rank_{rank}"
    solve = GEN.LESSON_COMPETITORS.get(name)
    assert callable(solve)
    assert name not in GEN.CANONICAL_SHORTCUTS and name not in GEN.SEMANTIC_RIVALS
    grids = [GEN.generate(17, index) for index in range(10)]
    grids += [[], [[3, 1, 0], [3, 0, 3], [0, 0, 0]],
              [[1, 1, 0, 0], [3, 0, 3, 0], [0, 0, 0, 0]]]
    for grid in grids:
        before = deepcopy(grid)
        assert solve(grid) == prediction(grid, rank, ascending=True)
        assert grid == before


@pytest.mark.parametrize("rank", range(1, 6))
def test_exact_overrides_keep_every_legal_rank(rank):
    grid = GEN.generate(17, 1, n_shapes=5, k_select=rank)
    assert len(components(grid)) == 5 and grid[0].count(1) == rank
    assert GEN.self_check(grid) == []


def test_explicit_three_candidate_second_rank_remains_allowed():
    grid = GEN.generate(17, 0, n_shapes=3, k_select=2)
    assert len(components(grid)) == 3 and grid[0].count(1) == 2
    assert GEN.self_check(grid) == []

# Frozen source9269... medium seed2940377972/start11/querysample14.
_FROZEN_ENCODED = json.loads('[{"input":["00000101010","00000003000","33300003303","33000033333","03000033333","00000000000","33000000330","03300000333","00300000000","00330000000"],"output":["00000101010","00000003000","22200003303","22000033333","02000033333","00000000000","33000000330","03300000333","00300000000","00330000000"]},{"input":["000000110000","000000000000","000000000000","000000000000","000000003330","000000003000","000000330000","000000000000","000000000000","003330000000","003330000000","000000000101"],"output":["000000110000","000000000000","000000000000","000000000000","000000002220","000000002000","000000330000","000000000000","000000000000","003330000000","003330000000","000000000101"]},{"input":["0000001000000000","0003300000000000","0003000000000000","0003300000000000","0003000000000000","0003000000000000","0003000000000000","0000000000000000","0000000000000000","0000000000000000","0000030000000000","0000333000000000","0033300000000000","0003330000000000","0000033300000000","0000000000000000","0000000000000000"],"output":["0000001000000000","0003300000000000","0003000000000000","0003300000000000","0003000000000000","0003000000000000","0003000000000000","0000000000000000","0000000000000000","0000000000000000","0000020000000000","0000222000000000","0022200000000000","0002220000000000","0000022200000000","0000000000000000","0000000000000000"]},{"input":["000000011000","000000000000","000000000000","000000003330","000000003000","000000330000","000000000000","000000000003","003330000000","003330000000","000000000101","000000000000"],"output":["000000011000","000000000000","000000000000","000000002220","000000002000","000000330000","000000000000","000000000003","003330000000","003330000000","000000000101","000000000000"]}]')
FROZEN = [{key: [[int(value) for value in row] for row in pair[key]]
           for key in ("input", "output")} for pair in _FROZEN_ENCODED]


def test_frozen_second_smallest_ambiguity_is_recognized():
    demos, query = FROZEN[:-1], FROZEN[-1]
    assert sorted(len(cells) for cells in components(query["input"])) == [1, 2, 4, 6]
    assert all(prediction(pair["input"], 2, ascending=True) == pair["output"] for pair in demos)
    assert prediction(query["input"], 2, ascending=True) != query["output"]
    for pair in FROZEN:
        assert prediction(pair["input"], pair["input"][0].count(1), ascending=False) == pair["output"]
        assert GEN.self_check(pair["input"]) == []
    assert any("constant_smallest_rank_2" in reason
               for reason in GEN.lesson_identifiable(demos, query))
