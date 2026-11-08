"""Independent BFS regressions for the known tie and eligibility competitors.

Frozen lesson labels are copied from the public Racket-labeled v3.0.1 census,
source SHA-256 2557381fbf829ee6c0fc0cdf7a27c1b5451708485fd47f0c09567ccba5b75f6e.
The first easy production lesson is seed1753406524/start0, held-out pair3.
"""
from __future__ import annotations
from collections import deque
from copy import deepcopy
import importlib.util
import json
import pytest
from reviewer_support import canonical_pairs, find_root

TASK = "c7070676c606"
ROOT = find_root(__file__)
SOURCE = ROOT / "generators" / TASK / "generator.py"
if not SOURCE.is_file():
    SOURCE = ROOT / "puzzle_generators" / "per_puzzle" / TASK / "generator.py"
SPEC = importlib.util.spec_from_file_location("tie_teaching_generator", SOURCE)
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)
EXTRA_NAMES = {"reverse_ties", "bbox_ties", "dense_ranks", "all_tied",
               "include_top_row", "clip_top_row", "all_nonbackground"}
_ENCODED = json.loads('[{"input":["110000000000","000000000000","000000000000","000000003300","000000003000","000000330000","000000000000","000000000000","003300000000","003300000000","000000000010","000000000000"],"output":["110000000000","000000000000","000000000000","000000002200","000000002000","000000330000","000000000000","000000000000","003300000000","003300000000","000000000010","000000000000"]},{"input":["1010100000000","0000000000000","0000000003000","0000000003000","0000000003000","0000000000000","0000000000000","0000000000000","0300000000000","0330000000000","0330000003000","3300000003300","3000000003330"],"output":["1010100000000","0000000000000","0000000002000","0000000002000","0000000002000","0000000000000","0000000000000","0000000000000","0300000000000","0330000000000","0330000003000","3300000003300","3000000003330"]},{"input":["011000000000","000000000000","003300000000","000300000000","000033000000","000000000000","030000000000","000000003300","000030003300","010000000000","000000000000","000000000000"],"output":["011000000000","000000000000","002200000000","000200000000","000033000000","000000000000","030000000000","000000003300","000030003300","010000000000","000000000000","000000000000"]},{"input":["010000000000000000000000","000000000003000000000000","000000000033000000000000","000000000030000000000000","000000000033000000000000","000000000030000000000000","000000000000000000003000","000000000000000000000000","000000000000000330000000","000000000000003333000000","000000000000000300000000","000000000000000000000000","000000000000000000000000","000000000000000000000000","000000000000000000000000","000300000000000000000000","003300000000000000000000","000300000000000000000000","003300000000000000000000","000300000000000000000000","000000000000000000000000","000000000000000000000000"],"output":["010000000000000000000000","000000000002000000000000","000000000022000000000000","000000000020000000000000","000000000022000000000000","000000000020000000000000","000000000000000000003000","000000000000000000000000","000000000000000330000000","000000000000003333000000","000000000000000300000000","000000000000000000000000","000000000000000000000000","000000000000000000000000","000000000000000000000000","000300000000000000000000","003300000000000000000000","000300000000000000000000","003300000000000000000000","000300000000000000000000","000000000000000000000000","000000000000000000000000"]}]')
FROZEN = [{key: [[int(v) for v in row] for row in pair[key]]
           for key in ('input', 'output')} for pair in _ENCODED]


def components(grid, *, all_colors=False, include=False, clip=False):
    """Test-only independent same-color BFS with explicit row-zero handling."""
    unseen = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
              if r >= int(clip) and (value != 0 if all_colors else value == 3)}
    result = []
    while unseen:
        first = min(unseen)
        unseen.remove(first)
        color = grid[first[0]][first[1]]
        pending = deque([first])
        cells = {first}
        while pending:
            r, c = pending.popleft()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in unseen and grid[point[0]][point[1]] == color:
                    unseen.remove(point)
                    pending.append(point)
                    cells.add(point)
        if include or min(r for r, c in cells) > 0:
            result.append(cells)
    return result


def independent_prediction(grid, rival="intended"):
    out = deepcopy(grid)
    if not grid or not grid[0]:
        return out
    groups = components(grid, all_colors=rival == "all_nonbackground",
                        include=rival == "include_top_row", clip=rival == "clip_top_row")
    k = grid[0].count(1)
    if not 1 <= k <= len(groups):
        return out
    def key(cells):
        first = min(cells)
        if rival == "reverse_ties":
            first = (-first[0], -first[1])
        elif rival == "bbox_ties":
            first = (min(r for r, c in cells), min(c for r, c in cells))
        return (-len(cells), first)
    ranked = sorted(groups, key=key)
    selected = [ranked[k - 1]]
    if rival == "dense_ranks":
        sizes = sorted({len(cells) for cells in groups}, reverse=True)
        if k > len(sizes):
            return out
        selected = [next(cells for cells in ranked if len(cells) == sizes[k - 1])]
    elif rival == "all_tied":
        selected = [cells for cells in groups if len(cells) == len(ranked[k - 1])]
    for cells in selected:
        for r, c in cells:
            out[r][c] = 2
    return out


def test_frozen_actual_racket_lesson_has_tie_ambiguity_and_hook_reports_it():
    assert [len(cells) for cells in sorted(components(FROZEN[3]["input"]), key=lambda cells: -len(cells))] == [7, 7, 7, 1]
    for pair in FROZEN:
        assert independent_prediction(pair["input"]) == pair["output"]
        assert GEN.self_check(pair["input"]) == []
    for name in ("reverse_ties", "all_tied"):
        assert all(independent_prediction(pair["input"], name) == pair["output"] for pair in FROZEN[:3])
        assert independent_prediction(FROZEN[3]["input"], name) != FROZEN[3]["output"]
    reasons = GEN.lesson_identifiable(FROZEN[:3], FROZEN[3])
    assert any("reverse_ties" in reason for reason in reasons)
    assert any("all_tied" in reason for reason in reasons)


@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
@pytest.mark.parametrize("seed", (0, 17, 91))
@pytest.mark.parametrize("index", range(1, 20, 2))
def test_default_odd_shapes_have_distinct_sizes(band, seed, index):
    grid = GEN.generate(seed, index, difficulty=band)
    sizes = [len(cells) for cells in components(grid)]
    assert len(sizes) == len(set(sizes)), (band, seed, index, sizes)
    assert GEN.self_check(grid) == []


@pytest.mark.parametrize("name", sorted(EXTRA_NAMES))
def test_extra_competitors_are_lesson_only_match_independent_semantics_and_are_pure(name):
    solve = GEN.LESSON_COMPETITORS.get(name)
    assert callable(solve)
    assert name not in GEN.CANONICAL_SHORTCUTS and name not in GEN.SEMANTIC_RIVALS
    # Include a row-zero-crossing green component and an eligible other-color
    # component so inclusion/clipping/color rivals have nontrivial behavior.
    grids = [pair["input"] for pair in FROZEN]
    grids += [[[3, 1, 0, 0], [3, 0, 0, 4], [0, 0, 3, 4]],
              [[1, 1, 1, 0], [3, 0, 3, 0], [0, 0, 0, 0]], []]
    for grid in grids:
        before = deepcopy(grid)
        assert solve(grid) == independent_prediction(grid, name)
        assert grid == before
    for pair in canonical_pairs(TASK, root=ROOT, labeled_only=True):
        assert solve(pair["input"]) == pair["output"]


def test_explicit_overrides_retain_lawful_ties_without_a_curriculum_promise():
    tied = False
    for seed in range(30):
        grid = GEN.generate(seed, 3, grid_h=10, grid_w=11, n_shapes=5, k_select=1)
        sizes = [len(cells) for cells in components(grid)]
        assert GEN.self_check(grid) == []
        tied |= len(sizes) != len(set(sizes))
    assert tied
