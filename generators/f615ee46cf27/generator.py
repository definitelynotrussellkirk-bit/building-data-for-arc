"""Generator for arc_puzzle_bank_21_set21_s:S21_H2 — paint articulation rooms.

Rule (decoded from canonical Racket): cells of {1,7,9} are WALLS; every connected
4-region of non-wall cells is a ROOM. Color-7 cells are DOORS: each door adds an
edge between the rooms on its two sides, forming a room-adjacency GRAPH. The rule
finds the graph's ARTICULATION POINTS (rooms whose removal disconnects the graph)
and paints those rooms color 8; walls and doors stay; non-articulation rooms stay 0.

PRIOR POISON (severe): the old generator emitted random scattered colored MOTIFS
(its docstring even said "vertical pack") — totally unrelated to this rule. The
rule then just erased non-wall colors, producing garbage outputs with no maze
structure. This is a full rewrite that builds a real room maze: a grid of rooms
separated by color-1 walls, connected by color-7 doors along a random spanning
TREE — guaranteeing the graph has BOTH articulation rooms (internal tree nodes,
painted) AND non-articulation rooms (leaves, left 0).

Rule-safe diversity: room-grid shape, room sizes, spanning-tree shape (chain /
star / branching), door positions.
Degenerates: no_doors, single_room, all_connected_cycle.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f615ee46cf27"
VERSION = "2.0.0"  # FULL REWRITE: was random motifs (poison, unrelated to rule); now real room maze + spanning-tree doors
TASK_ID = "f615ee46cf27"

SUMMARY = (
    "A room MAZE: a grid of rectangular rooms (0 interiors) separated by color-1 "
    "WALLS, connected by color-7 DOORS placed along a random spanning TREE so the "
    "room-adjacency graph is a tree. Rule: build the room graph from the doors, "
    "find its articulation-point rooms (whose removal disconnects the graph) and "
    "paint them color 8; leaf rooms stay 0; walls and doors stay. Net: the "
    "'cut-vertex' rooms light up. A tree guarantees both painted (internal) and "
    "unpainted (leaf) rooms. (Was: random scattered motifs unrelated to the rule.)"
)

INVARIANTS = [
    "walls are color 1, doors color 7, room interiors 0 (matches canonical {0,1,7})",
    ">=3 rooms so a tree has both internal (articulation) and leaf rooms",
    "doors form a spanning TREE over the rooms (graph connected, has cut vertices)",
    "each door is cardinally adjacent to exactly the two rooms it connects",
]

DEGENERATE_TEXTURES = ("no_doors", "single_room", "all_connected_cycle")

AXES = {
    "room_rows":  {"type": "int", "default": "1-2 easy / 1-3 med / 2-3 hard", "valid": "1..4"},
    "room_cols":  {"type": "int", "default": "3-4 easy / 3-4 med / 3-4 hard", "valid": "2..5"},
    "rh":         {"type": "int", "default": "room interior height 2-4", "valid": "1..5"},
    "rw":         {"type": "int", "default": "room interior width 2-4", "valid": "1..5"},
    "n_distinct_colors": {"type": "int", "default": "3 (0/1/7) + 8 out", "valid": "3..3"},
    "density":    {"type": "str", "default": "maze", "valid": "maze"},
    "texture":    {"type": "str", "default": "maze",
                   "valid": "maze|no_doors|single_room|all_connected_cycle"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify the generated input is a wall/door room tree with cut rooms."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errors = []
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    palette = {v for row in grid for v in row}
    if not palette <= {0, 1, 7}:
        errors.append(f"input palette must be {{0,1,7}}, got {sorted(palette)}")
    if 7 not in palette:
        errors.append("maze has no doors (color 7)")
    if 0 not in palette:
        errors.append("maze has no room interior cells (color 0)")
    if 1 not in palette:
        errors.append("maze has no walls (color 1)")

    labels = [[-1] * w for _ in range(h)]
    rooms = []
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] != 0 or labels[sr][sc] != -1:
                continue
            idx = len(rooms)
            q = [(sr, sc)]; labels[sr][sc] = idx; cells = []
            while q:
                r, c = q.pop(); cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == 0 and labels[nr][nc] == -1:
                        labels[nr][nc] = idx; q.append((nr, nc))
            rooms.append(cells)
    if len(rooms) < 3:
        errors.append(f"expected at least three rooms, found {len(rooms)}")

    edges = set()
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 7:
                continue
            adj = []
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w and labels[nr][nc] != -1:
                    adj.append((dr, dc, labels[nr][nc]))
            labs = sorted({lab for _, _, lab in adj})
            if len(labs) != 2:
                errors.append(f"door at {(r,c)} touches {len(labs)} rooms, expected 2")
                continue
            # The two room contacts must be across one wall segment, not a corner-like fork.
            dirs = {(dr, dc) for dr, dc, _ in adj}
            if not ({(-1, 0), (1, 0)} <= dirs or {(0, -1), (0, 1)} <= dirs):
                errors.append(f"door at {(r,c)} does not bridge opposite rooms")
            edges.add(tuple(labs))

    if rooms:
        parent = list(range(len(rooms)))
        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]; x = parent[x]
            return x
        for a, b in edges:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[rb] = ra
        comps = {find(i) for i in range(len(rooms))}
        if len(comps) != 1:
            errors.append(f"room graph is not connected ({len(comps)} components)")
        if len(edges) != len(rooms) - 1:
            errors.append(f"room graph should be a tree: rooms={len(rooms)} edges={len(edges)}")
        deg = [0] * len(rooms)
        for a, b in edges:
            deg[a] += 1; deg[b] += 1
        if len(rooms) >= 3 and not any(d >= 2 for d in deg):
            errors.append("room tree has no internal/articulation room")
    return errors


def _spanning_tree(rng, nr, nc):
    """Randomized-DFS spanning tree over the nr x nc room grid -> list of edges."""
    start = (rng.randrange(nr), rng.randrange(nc))
    visited = {start}; stack = [start]; edges = []
    while stack:
        i, j = stack[-1]
        unv = [(ni, nj) for ni, nj in ((i-1, j), (i+1, j), (i, j-1), (i, j+1))
               if 0 <= ni < nr and 0 <= nj < nc and (ni, nj) not in visited]
        if unv:
            nxt = rng.choice(unv)
            edges.append(((i, j), nxt)); visited.add(nxt); stack.append(nxt)
        else:
            stack.pop()
    return edges


def _build_maze(rng, nr, nc, rh, rw):
    H = 1 + nr * (rh + 1)
    W = 1 + nc * (rw + 1)
    g = full_grid(H, W, 1)                      # everything wall to start

    def room_rows(i):
        top = 1 + i * (rh + 1); return range(top, top + rh)

    def room_cols(j):
        left = 1 + j * (rw + 1); return range(left, left + rw)

    for i in range(nr):
        for j in range(nc):
            for r in room_rows(i):
                for c in room_cols(j):
                    g[r][c] = 0
    for (a, b) in _spanning_tree(rng, nr, nc):
        (ai, aj), (bi, bj) = a, b
        if ai == bi:                            # horizontal neighbors -> vertical wall door
            wc = 1 + min(aj, bj) * (rw + 1) + rw
            dr = rng.choice(list(room_rows(ai)))
            g[dr][wc] = 7
        else:                                   # vertical neighbors -> horizontal wall door
            wr = 1 + min(ai, bi) * (rh + 1) + rh
            dc = rng.choice(list(room_cols(aj)))
            g[wr][dc] = 7
    return g


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        nr = rng.randint(1, 2); nc = rng.randint(3, 4); rh = rng.randint(2, 3); rw = rng.randint(2, 3)
    elif difficulty == "hard":
        nr = rng.randint(2, 3); nc = rng.randint(3, 5); rh = rng.randint(2, 4); rw = rng.randint(2, 4)
    else:
        nr = rng.randint(1, 3); nc = rng.randint(3, 4); rh = rng.randint(2, 4); rw = rng.randint(2, 4)
    if nr * nc < 3:                              # need >=3 rooms for articulation + leaves
        nc = 3
    return _build_maze(rng, nr, nc, rh, rw)


def _draw_from_degenerate(name, rng):
    if name == "no_doors":
        # rooms but no doors -> no edges -> no articulation points (output = walls only)
        return _build_maze(rng, 1, 3, 2, 2) if False else _rooms_no_doors(1, 3, 2, 2)
    if name == "single_room":
        g = full_grid(5, 5, 1)
        for r in range(1, 4):
            for c in range(1, 4):
                g[r][c] = 0
        return g
    # all_connected_cycle: 3 rooms in a triangle-ish cycle -> no articulation point
    g = full_grid(5, 11, 1)
    for j in range(3):
        for r in range(1, 4):
            for c in range(1 + j * 3, 3 + j * 3):
                g[r][c] = 0
    g[2][3] = 7; g[2][6] = 7
    return g


def _rooms_no_doors(nr, nc, rh, rw):
    H = 1 + nr * (rh + 1); W = 1 + nc * (rw + 1)
    g = full_grid(H, W, 1)
    for i in range(nr):
        for j in range(nc):
            for r in range(1 + i * (rh + 1), 1 + i * (rh + 1) + rh):
                for c in range(1 + j * (rw + 1), 1 + j * (rw + 1) + rw):
                    g[r][c] = 0
    return g
