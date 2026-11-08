"""Independent BFS tests for the observed global blue-component shortcut.

The exact solver hypothesis counts same-color four-connected blue components
anywhere and ranks all green components, including those touching row zero.
This diagnostic is not the selected Racket label authority.
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
SPEC = importlib.util.spec_from_file_location("blue_component_generator", SOURCE)
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def components(grid, color):
    unseen = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
              if value == color}
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
        result.append(cells)
    return result


def observed_shortcut(grid):
    out = deepcopy(grid)
    rank = len(components(grid, 1))
    greens = sorted(components(grid, 3), key=lambda cells: (-len(cells), min(cells)))
    if 1 <= rank <= len(greens):
        for r, c in greens[rank - 1]:
            out[r][c] = 2
    return out


@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
@pytest.mark.parametrize("seed", (0, 17, 91))
@pytest.mark.parametrize("index", range(0, 20, 2))
def test_default_rich_inputs_distinguish_cells_runs_global_cells_and_components(band, seed, index):
    grid = GEN.generate(seed, index, difficulty=band)
    assert len(components(grid, 1)) == 3
    assert grid[0].count(1) == 2
    assert sum(row.count(1) for row in grid) == 4
    assert sum(value == 1 and (c == 0 or grid[0][c - 1] != 1)
               for c, value in enumerate(grid[0])) == 1
    assert GEN.self_check(grid) == []
    assert observed_shortcut(grid) != GEN._prediction(grid)


def test_global_blue_component_rival_is_lesson_only_and_matches_exact_observed_rule():
    assert "global_blue_components" in GEN.LESSON_COMPETITORS
    assert "global_blue_components" not in GEN.CANONICAL_SHORTCUTS
    assert "global_blue_components" not in GEN.SEMANTIC_RIVALS
    solve = GEN.LESSON_COMPETITORS["global_blue_components"]
    grids = [GEN.generate(17, index) for index in range(10)]
    # The first crafted input exercises inclusion of row-zero green components.
    grids += [[[3, 1, 0], [3, 0, 0], [0, 0, 3]], [], [[0]],
              [[1, 0], [0, 0]], [[1, 0, 1], [3, 0, 0]]]
    for grid in grids:
        before = deepcopy(grid)
        assert solve(grid) == observed_shortcut(grid)
        assert grid == before

# Frozen source3233... public Racket labels, {'band': 'easy', 'index': 0, 'seed': 1753406524, 'sample_index': 0}
_FROZEN_ENCODED = json.loads('[{"input":["1100000000000","0000000000000","0000000000000","0000000000000","0033330000000","0000030000000","0000003300000","0000000000000","0300000000000","0000000033300","0000300033300","0100000000000","0000000000000"],"output":["1100000000000","0000000000000","0000000000000","0000000000000","0022220000000","0000020000000","0000003300000","0000000000000","0300000000000","0000000033300","0000300033300","0100000000000","0000000000000"]},{"input":["1010100000000","0000000000000","3333000000000","0030000000000","0330000000000","0000000000003","0000000000033","0000000000000","0000000000000","0033000000000","0033330000300","0000000000300","0000000000333"],"output":["1010100000000","0000000000000","3333000000000","0030000000000","0330000000000","0000000000003","0000000000033","0000000000000","0000000000000","0033000000000","0033330000200","0000000000200","0000000000222"]},{"input":["011000000000","000000000000","000000000000","000000333300","000000300000","000033000000","000000000000","000000000030","033300000000","033300030000","000000000010","000000000000"],"output":["011000000000","000000000000","000000000000","000000222200","000000200000","000033000000","000000000000","000000000030","033300000000","033300030000","000000000010","000000000000"]},{"input":["0111000000000000","0000000000000000","0000000000000000","3333000000000000","0300000000000000","0000000000033000","0000000003333000","0000000000030000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","0330000000000000","0030000000000000","0000000000000000"],"output":["0111000000000000","0000000000000000","0000000000000000","3333000000000000","0300000000000000","0000000000033000","0000000003333000","0000000000030000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","0220000000000000","0020000000000000","0000000000000000"]}]')
FROZEN = [{key: [[int(value) for value in row] for row in pair[key]]
           for key in ("input", "output")} for pair in _FROZEN_ENCODED]


def test_frozen_actual_blue_component_ambiguity_is_recognized():
    demos, query = FROZEN[:-1], FROZEN[-1]
    assert all(observed_shortcut(pair["input"]) == pair["output"] for pair in demos)
    assert observed_shortcut(query["input"]) != query["output"]
    for pair in FROZEN:
        assert GEN._prediction(pair["input"]) == pair["output"]
    assert any("global_blue_components" in reason
               for reason in GEN.lesson_identifiable(demos, query))
