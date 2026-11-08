"""Generator for arc_puzzle_bank_21_set9_s:S9_H6 — nearest-marker maze coloring.

Rule (canonical): the walkable maze is every cell of color {7, 2, 3}. One cell
is the 2-start, one is the 3-goal. For each walkable cell the rule BFS-measures
its distance to the 2-start (a) and to the 3-goal (b) THROUGH the maze, then
colors it: a==b -> 8; a<b and a odd -> 2; b<a and b odd -> 3; otherwise 0. The
2 and 3 cells keep their colors.

The previous generator emitted random multicolor 'motifs' (a WRONG-TASK rewrite)
that had no connected 7-maze and no 2/3 markers, so the rule produced an all-0
output. This version emits the correct structure: a single CONNECTED region of
7-corridors (with optional interior holes) holding exactly one 2 and one 3.

Combinatorial axes: grid_h, grid_w, hole_density.
Degenerates: no_maze, no_markers, disconnected.
"""
from __future__ import annotations

from collections import deque

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a4addbf26818"
VERSION = "2.1.0"  # ensure the equidistant -> 8 branch is visible in default samples.
TASK_ID = "a4addbf26818"

SUMMARY = ("A single CONNECTED region of color-7 corridors (interior of a 0-bg grid, "
           "with a few interior holes) holding exactly one color-2 start and one "
           "color-3 goal. The rule colors each maze cell by which marker is nearer "
           "(with a parity rule); equidistant cells become 8.")

INVARIANTS = [
    "background is 0",
    "the walkable cells (colors {7,2,3}) form ONE 4-connected region",
    "exactly one color-2 start and one color-3 goal, both inside the maze",
    "at least one non-marker maze cell is equidistant from start and goal (8-branch visible)",
]

DEGENERATE_TEXTURES = ("no_maze", "no_markers", "disconnected")
HELPFUL_TEXTURES = ("dense", "holey")

AXES = {'grid_h': {'type': 'int', 'default': 'rng 8..10', 'valid': '6..14'},
 'grid_w': {'type': 'int', 'default': 'rng 10..13', 'valid': '8..16'},
 'hole_density': {'type': 'float', 'default': 'rng 0.0..0.35', 'valid': '0..0.5'},
 'texture': {'type': 'str',
             'default': 'alias for fill style',
             'valid': 'dense|holey|no_maze|no_markers|disconnected'}}


def _connected(cells):
    """True if the set of (r,c) cells is one 4-connected region."""
    if not cells:
        return False
    start = next(iter(cells))
    seen = {start}; q = deque([start])
    while q:
        r, c = q.popleft()
        for nr, nc in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
            if (nr, nc) in cells and (nr, nc) not in seen:
                seen.add((nr, nc)); q.append((nr, nc))
    return len(seen) == len(cells)




def _distances(cells, start):
    dist = {start: 0}
    q = deque([start])
    while q:
        r, c = q.popleft()
        for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if (nr, nc) in cells and (nr, nc) not in dist:
                dist[(nr, nc)] = dist[(r, c)] + 1
                q.append((nr, nc))
    return dist


def _has_equidistant_branch(cells, start, goal):
    d_start = _distances(cells, start)
    d_goal = _distances(cells, goal)
    for cell in cells:
        if cell in (start, goal):
            continue
        if d_start.get(cell) == d_goal.get(cell):
            return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        hr, wr, hd_hi = (8, 9), (10, 11), 0.15
    elif difficulty == "hard":
        hr, wr, hd_hi = (10, 13), (13, 16), 0.40
    else:
        hr, wr, hd_hi = (8, 10), (10, 13), 0.35
    rng = ctx.draw_rng("layout")
    hole_density = float(overrides.get("hole_density", rng.uniform(0.0, hd_hi)))

    for _attempt in range(60):
        h = rng.randint(*hr); w = rng.randint(*wr)
        g = full_grid(h, w, 0)
        # interior corridor region, fully 7 to start
        region = {(r, c) for r in range(1, h - 1) for c in range(1, w - 1)}
        # punch holes one at a time, keeping the region connected
        candidates = list(region)
        rng.shuffle(candidates)
        n_holes = int(len(region) * hole_density)
        for cell in candidates[:n_holes]:
            trial = region - {cell}
            if _connected(trial):
                region = trial
        if len(region) < 8 or not _connected(region):
            continue
        for r, c in region:
            g[r][c] = 7
        # place the 2-start and 3-goal at two distinct maze cells, ideally apart
        rcells = list(region)
        rng.shuffle(rcells)
        s2 = rcells[0]
        # pick a goal a few steps away for a more interesting coloring
        far = sorted(rcells[1:], key=lambda p: -(abs(p[0]-s2[0]) + abs(p[1]-s2[1])))
        s3 = far[rng.randint(0, min(2, len(far) - 1))] if far else rcells[1]
        if not _has_equidistant_branch(region, s2, s3):
            continue
        g[s2[0]][s2[1]] = 2
        g[s3[0]][s3[1]] = 3
        return g
    raise ValueError("could not realize a connected 7-maze")


def _draw_from_degenerate(name, rng):
    h, w = 9, 12
    g = full_grid(h, w, 0)
    if name == "no_maze":
        # markers but no 7-corridors -> tiny isolated allowed set
        g[2][2] = 2; g[6][9] = 3
        return g
    if name == "no_markers":
        # a 7-maze but no 2/3 markers -> the rule has no start/goal
        for r in range(1, h - 1):
            for c in range(1, w - 1):
                g[r][c] = 7
        return g
    if name == "disconnected":
        # two separate 7-blobs, markers in different ones -> BFS can't connect
        for r in range(1, 4):
            for c in range(1, 4):
                g[r][c] = 7
        for r in range(5, 8):
            for c in range(8, 11):
                g[r][c] = 7
        g[2][2] = 2; g[6][9] = 3
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs = []
    h = len(grid); w = len(grid[0]) if h else 0
    twos = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    threes = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 3]
    if len(twos) != 1:
        errs.append(f"expected exactly one color-2 start, got {len(twos)}")
    if len(threes) != 1:
        errs.append(f"expected exactly one color-3 goal, got {len(threes)}")
    walkable = {(r, c) for r in range(h) for c in range(w) if grid[r][c] in (7, 2, 3)}
    if len(walkable) < 4:
        errs.append("walkable maze is too small")
    elif not _connected(walkable):
        errs.append("walkable region {7,2,3} is not 4-connected (BFS can't reach all)")
    elif len(twos) == 1 and len(threes) == 1 and not _has_equidistant_branch(walkable, twos[0], threes[0]):
        errs.append("no non-marker maze cell is equidistant from start and goal; 8-branch hidden")
    return errs
