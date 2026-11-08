"""Generator for arc_additional_puzzle_bank_volume23:M160 (task 00cccdad1b37).

THE RULE (what a solver must learn to see):
  BFS over 4-connected non-wall (color-5) cells from the red (2) start
  and green (3) goal. A background cell is marked cyan (8) only if it
  lies on EVERY shortest path: dist_s + dist_g == best AND
  ways_s * ways_g == total_ways. Cells on some-but-not-all shortest
  paths stay 0. No path -> grid unchanged.

WHAT MAKES AN INPUT TEACH THIS RULE (helpful scenarios):
  - straight     s,t on one clear row: the unique path is marked whole
  - bottleneck   a wall barrier with ONE gap between s and t: every
                 path funnels through the gap — the gap cells are
                 marked even though the region is wide open elsewhere
  - snake        two staggered barriers: the corridor zig-zags and the
                 forced segments are marked
  The old generator ONLY produced 'straight' (s,t same row, walls
  always off-row decor) — the ways-counting half of the rule (partial
  overlap -> NOT marked) was never exercised.
  A Python mirror verifies: path exists, >=1 cell marked, and for
  bottleneck/snake boards >=1 equidistant cell is NOT marked (so the
  "on SOME shortest path" rival is refuted by the data).

WHAT HIDES IT (degenerate textures, reachable via texture=...):
  - blocked_corridor  walls separate s from t: output unchanged
  - no_forced_cell    open diagonal placement: many shortest paths,
                      no cell on all of them: output unchanged
  - adjacent_pair     s,t adjacent: no 0-cell between them
  (no_start / no_goal are NOT offered: the rule crashes on them —
  (first (find-color g 2)) on an empty list)
"""
from __future__ import annotations

from collections import deque

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "00cccdad1b37"
VERSION = "3.1.1"  # add executable self_check for marked-background snake boards
TASK_ID = "00cccdad1b37"
SUMMARY = (
    "0-bg grid with one red(2) start, one green(3) goal, color-5 "
    "walls forming straight / single-gap / staggered-double-gap "
    "layouts; rule marks cyan(8) exactly the bg cells lying on EVERY "
    "shortest 4-connected path (verified non-empty, with partially- "
    "shared cells present and unmarked on pinch boards)."
)

# Rivals: 'mark cells on SOME shortest path' refuted by pinch boards
# carrying equidistant cells that stay 0. 'draw straight line red->
# green' refuted by bottleneck/snake demos where the marked set bends
# through gaps. 'walls are decor' refuted likewise. 4 demos: >=1
# straight, >=2 pinch layouts.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0; exactly one 2-cell and one 3-cell; walls are 5",
    "a 4-connected non-wall path from start to goal exists",
    ">=1 background cell is on every shortest path (output non-trivial)",
    "bottleneck/snake boards also carry >=1 equidistant cell NOT on all paths",
]

SCENARIOS = ("straight", "bottleneck", "snake")
DEGENERATE_TEXTURES = ("blocked_corridor", "no_forced_cell", "adjacent_pair")
HELPFUL_TEXTURES = SCENARIOS

AXES = {
    "grid_h":      {"type": "int", "default": "rng 8..11 (easy 6..8, hard 12..16)",
                    "valid": "5..18", "doc": "Grid height."},
    "grid_w":      {"type": "int", "default": "rng 10..14 (easy 7..10, hard 14..18)",
                    "valid": "6..20", "doc": "Grid width."},
    "scenario":    {"type": "enum", "default": "rng over straight|bottleneck|snake",
                    "valid": "straight|bottleneck|snake",
                    "doc": "Wall layout class; pinch layouts exercise the "
                           "ways-counting half of the rule."},
    "decor_walls": {"type": "int", "default": "rng 0..4", "valid": "0..8",
                    "doc": "Extra wall cells that do not change the marked set."},
    "texture":     {"type": "str", "default": "rng helpful",
                    "valid": "straight|bottleneck|snake|blocked_corridor|"
                             "no_forced_cell|adjacent_pair",
                    "doc": "Set to a degenerate name to build a rule-hiding input."},
}


# ----------------------------------------------------- rule mirror
def _bfs(g, start):
    h, w = len(g), len(g[0])
    dist = {start: 0}
    ways = {start: 1}
    q = deque([start])
    while q:
        r, c = q.popleft()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if not (0 <= nr < h and 0 <= nc < w) or g[nr][nc] == 5:
                continue
            nd = dist[(r, c)] + 1
            if (nr, nc) not in dist:
                dist[(nr, nc)] = nd
                ways[(nr, nc)] = ways[(r, c)]
                q.append((nr, nc))
            elif dist[(nr, nc)] == nd:
                ways[(nr, nc)] += ways[(r, c)]
    return dist, ways


def _analyze(g):
    """Returns (marked, partial): cells on ALL shortest paths vs cells on
    some-but-not-all. Both restricted to bg cells. None if no path."""
    s = next((r, c) for r, row in enumerate(g) for c, v in enumerate(row) if v == 2)
    t = next((r, c) for r, row in enumerate(g) for c, v in enumerate(row) if v == 3)
    ds, ws = _bfs(g, s)
    if t not in ds:
        return None
    dt, wt = _bfs(g, t)
    best, total = ds[t], ws[t]
    marked, partial = set(), set()
    for p in ds:
        if g[p[0]][p[1]] != 0 or p not in dt or ds[p] + dt[p] != best:
            continue
        if ws[p] * wt[p] == total:
            marked.add(p)
        else:
            partial.add(p)
    return marked, partial


# ------------------------------------------------------- builders
def _place_decor(g, rng, n, baseline):
    """Add up to n wall cells that leave the marked set unchanged."""
    h, w = len(g), len(g[0])
    placed = 0
    for _ in range(40):
        if placed >= n:
            break
        r, c = rng.randrange(h), rng.randrange(w)
        if g[r][c] != 0:
            continue
        g[r][c] = 5
        res = _analyze(g)
        if res is None or res[0] != baseline:
            g[r][c] = 0
            continue
        placed += 1


def _build(scenario, h, w, rng):
    g = full_grid(h, w, 0)
    if scenario == "straight":
        r = rng.randint(0, h - 1)
        c1 = rng.randint(0, w - 5)
        c2 = rng.randint(c1 + 3, w - 1)
        g[r][c1] = 2
        g[r][c2] = 3
        return g
    if scenario == "bottleneck":
        # vertical barrier with one gap; s left, t right at OTHER rows
        bc = rng.randint(3, w - 4)
        gap_r = rng.randint(1, h - 2)
        for r in range(h):
            if r != gap_r:
                g[r][bc] = 5
        r1 = rng.choice([r for r in range(h) if r != gap_r])
        r2 = rng.choice([r for r in range(h) if r != gap_r])
        g[r1][rng.randint(0, bc - 2)] = 2
        g[r2][rng.randint(bc + 2, w - 1)] = 3
        return g
    # snake: two staggered barriers with gaps at far rows. The second barrier
    # must satisfy b1+2 <= b2 <= w-3, so b1 is only feasible up to w-5. Drawing
    # b1 from [2, w//2] let it exceed that on narrow easy grids (w=8,b1=4 →
    # randint(6,5)=randrange(6,6); w=7,b1=3 → randrange(5,5)). Cap b1's hi at the
    # feasible min(w//2, w-5) (>=2 for easy w>=7; no-op for w>=10 where w//2<=w-5).
    b1 = rng.randint(2, min(w // 2, w - 5))
    b2 = rng.randint(b1 + 2, w - 3)
    gap1, gap2 = 0, h - 1
    if rng.random() < 0.5:
        gap1, gap2 = gap2, gap1
    for r in range(h):
        if r != gap1:
            g[r][b1] = 5
        if r != gap2:
            g[r][b2] = 5
    g[rng.randint(0, h - 1)][rng.randint(0, b1 - 1)] = 2
    g[rng.randint(0, h - 1)][rng.randint(b2 + 1, w - 1)] = 3
    return g


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)

    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 8)
        w = ctx.draw_int("grid_w", 7, 10)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 16)
        w = ctx.draw_int("grid_w", 14, 18)
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 10, 14)
    scenario = texture if texture in SCENARIOS else \
        ctx.draw_choice("scenario", SCENARIOS)
    n_decor = int(overrides.get("decor_walls", ctx.draw_int("decor_walls", 0, 4)))
    rng = ctx.draw_rng("placement")

    for _attempt in range(60):
        g = _build(scenario, h, w, rng)
        res = _analyze(g)
        if res is None:
            continue
        marked, partial = res
        if not marked:
            continue
        # pinch boards must also show NOT-marked equidistant cells, so
        # "on some shortest path" is refuted by the training pair itself
        if scenario in ("bottleneck", "snake") and not partial:
            continue
        _place_decor(g, rng, n_decor, marked)
        return g
    raise ValueError(f"could not realize scenario={scenario} {h}x{w}")


def _draw_from_degenerate(name, ctx):
    """Rule-hiding inputs — rule-safe (s and t always exist), rng-varied.

    blocked_corridor — a full barrier with NO gap: no path, unchanged.
    no_forced_cell   — open diagonal: every cell sits on only some
                       shortest paths, nothing is marked.
    adjacent_pair    — s,t adjacent: no bg cell between them.
    """
    h = ctx.draw_int("grid_h", 7, 10)
    w = ctx.draw_int("grid_w", 8, 12)
    rng = ctx.draw_rng("degenerate_placement")
    g = full_grid(h, w, 0)
    if name == "blocked_corridor":
        bc = rng.randint(2, w - 3)
        for r in range(h):
            g[r][bc] = 5
        g[rng.randrange(h)][rng.randint(0, bc - 1)] = 2
        g[rng.randrange(h)][rng.randint(bc + 1, w - 1)] = 3
        return g
    if name == "no_forced_cell":
        for _ in range(40):
            g = full_grid(h, w, 0)
            r1, c1 = rng.randint(0, h - 3), rng.randint(0, w - 3)
            r2 = rng.randint(r1 + 2, h - 1)
            c2 = rng.randint(c1 + 2, w - 1)
            g[r1][c1] = 2
            g[r2][c2] = 3
            res = _analyze(g)
            if res and not res[0]:
                return g
        return g
    # adjacent_pair
    r = rng.randint(0, h - 1)
    c = rng.randint(0, w - 2)
    g[r][c] = 2
    g[r][c + 1] = 3
    return g


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    vals = [v for row in grid for v in row]
    if vals.count(2) != 1:
        msgs.append("expected exactly one start color 2")
    if vals.count(3) != 1:
        msgs.append("expected exactly one goal color 3")
    if any(v not in (0, 2, 3, 5) for v in vals):
        msgs.append("unexpected color outside {0,2,3,5}")
    if vals.count(2) == 1 and vals.count(3) == 1:
        res = _analyze(grid)
        if res is None:
            msgs.append("no non-wall path from start to goal")
        elif not res[0]:
            msgs.append("expected at least one background cell on every shortest path")
    return msgs
