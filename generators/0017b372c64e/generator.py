"""Generator for arc_additional_puzzle_bank_volume14:H98 (task 0017b372c64e).

THE RULE (what a solver must learn to see):
  Two seeds — color 1 and color 2 — sit in a field whose walls are
  color 5. BFS from each seed through non-wall cells; every background
  cell whose two distances are EQUAL turns cyan (8). The output paints
  the equidistance frontier ("the watershed between two springs").

WHAT MAKES AN INPUT TEACH THIS RULE (helpful textures):
  - default        a few interior wall segments: the frontier BENDS
                   around obstacles — pure-bisector explanations fail
  - wide_chamber   no interior walls: the frontier is the clean
                   perpendicular bisector (the easy read)
  - tight_corridor dense walls forming corridors: distances are path
                   distances, not straight-line — the maze case
  - off_center_seeds  seeds at different rows/heights: the frontier is
                   a bent curve, killing "middle column" shortcuts

GEOMETRY CONSTRAINT (enforced): the grid graph is bipartite, so equal
integer distances exist only when the seeds' Manhattan separation is
EVEN; seeds must also be mutually reachable and the tie set non-empty
(checked by a feasibility BFS used for rejection ONLY — the Racket
rule remains the single source of output truth).

WHAT HIDES IT (degenerate textures, reachable via texture=...):
  - seeds_collide  adjacent seeds (odd parity): no cell can tie
  - no_walls       open field, not even a border
  - no_seeds       walls but nothing to measure from
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0017b372c64e"
VERSION = "2.0.1"
TASK_ID = "0017b372c64e"
SUMMARY = (
    "Bordered (and optionally interior-) walled field of 5s with one "
    "color-1 seed and one color-2 seed at even Manhattan separation; "
    "rule paints every background cell equidistant (BFS through "
    "non-wall cells) from both seeds cyan. Interior walls bend the "
    "frontier; seed geometry varies freely across rows and columns."
)

INVARIANTS = [
    "background is 0; walls are 5; seeds are exactly one 1 and one 2",
    "full border wall is present (helpful path)",
    "seeds sit on background, never on walls",
    "seeds' Manhattan separation is even (bipartite grid: ties exist)",
    "both seeds are mutually reachable and at least one background cell ties",
]

PALETTE_KINDS = ("default", "tight_corridor", "wide_chamber", "off_center_seeds")
DEGENERATE_TEXTURES = ("seeds_collide", "no_walls", "no_seeds")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":        {"type": "int", "default": "rng 8..13 (easy 8..10, hard 12..18)",
                      "valid": "7..24", "doc": "Grid height incl. border walls."},
    "grid_w":        {"type": "int", "default": "rng 9..15 (easy 9..11, hard 14..20)",
                      "valid": "7..24", "doc": "Grid width incl. border walls."},
    "palette_kind":  {"type": "enum", "default": "rng helpful",
                      "valid": "default|tight_corridor|wide_chamber|off_center_seeds",
                      "doc": "Interior-wall regime + seed geometry style."},
    "seed_distance": {"type": "int", "default": "rng even 2..10",
                      "valid": "2..16", "doc": "Manhattan separation of the seeds "
                                               "(odd values are bumped to even)."},
    "anchor_row":    {"type": "enum", "default": "rng",
                      "valid": "top|middle|bottom",
                      "doc": "Vertical band where seed 1 is placed."},
    "n_wall_segments": {"type": "int", "default": "rng per palette_kind",
                        "valid": "0..12", "doc": "Interior wall segments dropped in."},
    "texture":       {"type": "enum", "default": "helpful",
                      "valid": "default|tight_corridor|wide_chamber|off_center_seeds|"
                               "seeds_collide|no_walls|no_seeds",
                      "doc": "Set to a degenerate name to build a rule-hiding input."},
}

_BANDS = ("top", "middle", "bottom")


def _dims(ctx, difficulty):
    if difficulty == "easy":
        return ctx.draw_int("grid_h", 8, 10), ctx.draw_int("grid_w", 9, 11)
    if difficulty == "hard":
        return ctx.draw_int("grid_h", 12, 18), ctx.draw_int("grid_w", 14, 20)
    return ctx.draw_int("grid_h", 8, 13), ctx.draw_int("grid_w", 9, 15)


def _bordered(h, w):
    g = full_grid(h, w, 0)
    for r in range(h):
        g[r][0] = 5
        g[r][w - 1] = 5
    for c in range(w):
        g[0][c] = 5
        g[h - 1][c] = 5
    return g


def _drop_wall_segments(g, rng, n_segments):
    """Interior walls: short horizontal/vertical segments. They bend the
    equidistance frontier — the whole point of the maze framing."""
    h = len(g)
    w = len(g[0])
    for _ in range(n_segments):
        horizontal = rng.random() < 0.5
        length = rng.randint(2, max(2, (w if horizontal else h) // 3))
        r = rng.randint(1, h - 2)
        c = rng.randint(1, w - 2)
        for k in range(length):
            rr = r if horizontal else min(h - 2, r + k)
            cc = min(w - 2, c + k) if horizontal else c
            g[rr][cc] = 5


def _open_cells(g):
    return [(r, c) for r in range(len(g)) for c in range(len(g[0])) if g[r][c] == 0]


def _bfs(g, start):
    """Feasibility mirror of the rule's BFS (rejection only)."""
    h = len(g)
    w = len(g[0])
    dist = {start: 0}
    queue = [start]
    head = 0
    while head < len(queue):
        r, c = queue[head]
        head += 1
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w and g[nr][nc] != 5 and (nr, nc) not in dist:
                dist[(nr, nc)] = dist[(r, c)] + 1
                queue.append((nr, nc))
    return dist


def _tie_exists(g, a, b):
    da = _bfs(g, a)
    if b not in da:
        return False  # seeds walled apart: no common cells at all
    db = _bfs(g, b)
    return any(
        g[r][c] == 0 and (r, c) in da and (r, c) in db and da[(r, c)] == db[(r, c)]
        for r, c in _open_cells(g)
    )


def _band_rows(band, h):
    if band == "top":
        return range(1, max(2, h // 3))
    if band == "bottom":
        return range(min(h - 2, (2 * h) // 3), h - 1)
    return range(max(1, h // 3), min(h - 1, (2 * h) // 3 + 1))


def _place_seeds(g, rng, band, target_distance, same_row):
    """Pick seed cells on background with EVEN Manhattan separation near
    the target distance. Returns (a, b) or None."""
    h = len(g)
    candidates_a = [(r, c) for (r, c) in _open_cells(g) if r in _band_rows(band, h)]
    if not candidates_a:
        candidates_a = _open_cells(g)
    rng.shuffle(candidates_a)
    for a in candidates_a[:24]:
        options = []
        for b in _open_cells(g):
            if b == a:
                continue
            if same_row and b[0] != a[0]:
                continue
            manhattan = abs(a[0] - b[0]) + abs(a[1] - b[1])
            if manhattan % 2 == 0 and abs(manhattan - target_distance) <= 2:
                options.append(b)
        if options:
            return a, options[rng.randrange(len(options))]
    return None


def _degenerate(ctx, name, difficulty):
    """Rule-hiding inputs, still diverse in size and layout."""
    h, w = _dims(ctx, difficulty)
    rng = ctx.draw_rng("degenerate_layout")
    if name == "no_walls":
        g = full_grid(h, w, 0)
        r = rng.randint(0, h - 1)
        c = rng.randint(0, w - 3)
        g[r][c] = 1
        g[r][min(w - 1, c + 1)] = 2  # adjacent: odd parity, no tie either
        return g
    g = _bordered(h, w)
    if name == "no_seeds":
        _drop_wall_segments(g, rng, rng.randint(0, 3))
        return g
    # seeds_collide: adjacent seeds (odd Manhattan parity -> no tie cell)
    r = rng.randint(1, h - 2)
    c = rng.randint(1, w - 3)
    g[r][c] = 1
    g[r][c + 1] = 2
    return g


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)

    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _degenerate(ctx, texture, difficulty)

    h, w = _dims(ctx, difficulty)
    kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    band = ctx.draw_choice("anchor_row", _BANDS)
    distance = ctx.draw_int("seed_distance", 2, 10)
    distance += distance % 2  # bipartite grid: ties need even separation
    if kind == "tight_corridor":
        n_segments = ctx.draw_int("n_wall_segments", 5, 9)
    elif kind == "wide_chamber":
        n_segments = ctx.draw_int("n_wall_segments", 0, 0)
    else:
        n_segments = ctx.draw_int("n_wall_segments", 1, 4)
    same_row = kind != "off_center_seeds"

    rng = ctx.draw_rng("layout")
    # rejection-sample layouts until the rule is VISIBLE: seeds mutually
    # reachable and at least one background cell ties
    for _attempt in range(40):
        g = _bordered(h, w)
        _drop_wall_segments(g, rng, n_segments)
        placed = _place_seeds(g, rng, band, distance, same_row)
        if placed is None:
            continue
        a, b = placed
        g[a[0]][a[1]] = 1
        g[b[0]][b[1]] = 2
        if _tie_exists(g, a, b):
            return g
    # guaranteed fallback: open chamber, horizontally aligned seeds
    g = _bordered(h, w)
    r = rng.randint(1, h - 2)
    mid = w // 2
    g[r][max(1, mid - 2)] = 1
    g[r][min(w - 2, mid + 2)] = 2
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Exactly one color-1 seed and one color-2 seed; border is all 5s;
    seeds not on walls; seeds' Manhattan distance is even (bipartite grid)."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errors = []
    ones = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 1]
    twos = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    if len(ones) != 1:
        errors.append(f"expected exactly 1 color-1 seed, found {len(ones)}")
    if len(twos) != 1:
        errors.append(f"expected exactly 1 color-2 seed, found {len(twos)}")
    # border must be all 5s
    border_ok = (all(grid[0][c] == 5 for c in range(w)) and
                 all(grid[h - 1][c] == 5 for c in range(w)) and
                 all(grid[r][0] == 5 for r in range(h)) and
                 all(grid[r][w - 1] == 5 for r in range(h)))
    if not border_ok:
        errors.append("border is not fully color-5 walls")
    if len(ones) == 1 and len(twos) == 1:
        a, b = ones[0], twos[0]
        manhattan = abs(a[0] - b[0]) + abs(a[1] - b[1])
        if manhattan % 2 != 0:
            errors.append(f"seeds' Manhattan distance {manhattan} is odd (no equidistant cell possible)")
    return errors
