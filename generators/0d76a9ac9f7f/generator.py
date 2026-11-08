"""Generator for arc_puzzle_bank_tenth21:H69 — color-map a query panel by an A->B key.

Rule: THREE panels separated by full color-9 columns: A, B, query. A and B
define a per-cell color mapping (a[r][c] -> b[r][c] for non-bg a-cells).
The query panel is recolored cell-by-cell through that mapping (unmapped
colors stay). Output is the recolored query (panel-sized).

This generator draws a consistent A->B color key (each source color maps
to one target) and a query panel using the source colors.

Combinatorial axes: panel size, the color mapping (which source colors,
which targets), and the query cell layout.
Degenerates: no_dividers, empty_query, identity_map.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0d76a9ac9f7f"
VERSION = "3.0.1"  # 2.1.0->3.0.0: WRONG-TASK rewrite. Old gen made 5-7 random-motif panels; rule reads exactly 3 panels (A,B=color key, query) and color-maps the query
TASK_ID = "0d76a9ac9f7f"

SUMMARY = (
    "Three panels separated by full-height color-9 columns: A and B form a "
    "per-cell color KEY (a->b at matching positions), and a QUERY panel uses "
    "the source colors. Rule recolors the query through the A->B map."
)

INVARIANTS = [
    "background is 0",
    "exactly three panels separated by single full-height color-9 columns",
    "A and B define a consistent source->target color map at matching cells",
    "the query panel uses only the mapped source colors",
]

DEGENERATE_TEXTURES = ("no_dividers", "empty_query", "identity_map")

AXES = {
    "panel_h":        {"type": "int", "default": "rng 4..6", "valid": "3..8"},
    "panel_w":        {"type": "int", "default": "rng 4..6", "valid": "3..8"},
    "n_map":          {"type": "int", "default": "rng 2..4", "valid": "1..6"},
    "texture":        {"type": "str", "default": "n/a (degenerates only)",
                       "valid": "|".join(DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Exactly 2 full-height color-9 dividers; non-zero cells in panel A and panel B."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    nine_cols = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    errors = []
    if len(nine_cols) != 2:
        errors.append(f"expected exactly 2 full-height color-9 dividers, found {len(nine_cols)}")
        return errors
    lo, hi = nine_cols[0], nine_cols[1]
    a_nz = any(grid[r][c] != 0 for r in range(h) for c in range(lo))
    b_nz = any(grid[r][c] != 0 for r in range(h) for c in range(lo + 1, hi))
    if not a_nz:
        errors.append("panel A (left of first divider) has no non-zero cells")
    if not b_nz:
        errors.append("panel B (between dividers) has no non-zero cells")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        ph = ctx.draw_int("panel_h", 4, 4); pw = ctx.draw_int("panel_w", 4, 4)
        n_map = rng.randint(2, 3)
    elif difficulty == "hard":
        ph = ctx.draw_int("panel_h", 6, 8); pw = ctx.draw_int("panel_w", 6, 8)
        n_map = rng.randint(3, 5)
    else:
        ph = ctx.draw_int("panel_h", 4, 6); pw = ctx.draw_int("panel_w", 4, 6)
        n_map = rng.randint(2, 4)

    # source colors and a distinct-target mapping (avoid 9 = divider)
    pool = [c for c in range(1, 10) if c != 9]
    n_map = min(n_map, len(pool) // 2)
    rng.shuffle(pool)
    srcs = pool[:n_map]
    tgts = pool[n_map:2 * n_map]
    cmap = dict(zip(srcs, tgts))

    # build the three panels
    A = [[0] * pw for _ in range(ph)]
    B = [[0] * pw for _ in range(ph)]
    Q = [[0] * pw for _ in range(ph)]
    positions = [(r, c) for r in range(ph) for c in range(pw)]
    rng.shuffle(positions)
    # place each source->target pair at a distinct cell in A and B
    for i, s in enumerate(srcs):
        r, c = positions[i]
        A[r][c] = s
        B[r][c] = cmap[s]
    # query: scatter source-colored cells (so they map to targets)
    n_q = rng.randint(max(1, n_map), min(len(positions), n_map + 4))
    for (r, c) in positions[:n_q]:
        Q[r][c] = rng.choice(srcs)

    # assemble A | 9-col | B | 9-col | Q
    h = ph
    w = pw * 3 + 2
    g = full_grid(h, w, 0)
    for r in range(h):
        for c in range(pw):
            g[r][c] = A[r][c]
            g[r][pw + 1 + c] = B[r][c]
            g[r][2 * pw + 2 + c] = Q[r][c]
        g[r][pw] = 9
        g[r][2 * pw + 1] = 9
    return g


def _draw_from_degenerate(name, rng):
    ph, pw = 4, 4
    h = ph; w = pw * 3 + 2
    g = full_grid(h, w, 0)
    if name == "no_dividers":
        g[1][1] = 4; g[1][5] = 6; g[1][9] = 4
        return g
    # base: a small A->B key + dividers
    for r in range(h):
        g[r][pw] = 9
        g[r][2 * pw + 1] = 9
    g[0][0] = 3; g[0][pw + 1] = 7      # 3 -> 7
    g[1][1] = 2; g[1][pw + 2] = 5      # 2 -> 5
    if name == "empty_query":
        return g                       # query empty -> output empty
    if name == "identity_map":
        # A==B so every color maps to itself; query unchanged
        g[0][pw + 1] = 3; g[1][pw + 2] = 2
        g[0][2 * pw + 2] = 3; g[1][2 * pw + 3] = 2
        return g
    return g
