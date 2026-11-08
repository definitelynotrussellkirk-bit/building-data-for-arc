"""Generator for arc_additional_puzzle_bank_volume20:E139 — Bbox crop of all non-zero cells.

Rule: subgrid bounded by min/max row/col of all non-bg cells.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_blobs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: empty_grid, content_fills_grid, single_cell.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "045c3641f0eb"
VERSION = "2.1.1"
TASK_ID = "045c3641f0eb"
SUMMARY = (
    "0-bg grid with 1-3 grown blobs in distinct colors at VARIED "
    "arrangements (either diagonal, horizontal/vertical pairs, or an "
    "off-center cluster), sometimes touching a border; rule crops to "
    "the bbox of all non-zero cells. (Was: always exactly TL+BR "
    "diagonal — the arrangement could be mistaken for the rule.)"
)

# Rivals: 'content is always in opposite corners' refuted by pair and
# cluster arrangements. 'crop never touches the input border' refuted
# by border_touch boards. 'one blob per corner' refuted by 1- and
# 3-blob boards. 3 demos with >=2 arrangements.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "1-3 blobs, distinct colors, bbox crop strictly smaller than the grid",
    "arrangements vary: diagonals, pairs, clusters, border-touching",
]

ARRANGEMENTS = ("diag_tlbr", "diag_trbl", "horizontal", "vertical", "cluster")
DEGENERATE_TEXTURES = ("empty_grid", "content_fills_grid", "single_cell")
HELPFUL_TEXTURES = ARRANGEMENTS + ("border_touch",)

AXES = {
    "grid_h":      {"type": "int", "default": "rng 8..10 (hard 9..13)",
                    "valid": "7..14", "doc": "Grid height."},
    "grid_w":      {"type": "int", "default": "rng 10..12 (hard 11..14)",
                    "valid": "8..14", "doc": "Grid width."},
    "n_blobs":     {"type": "int", "default": "rng 1..3", "valid": "1..3",
                    "doc": "Blob count."},
    "arrangement": {"type": "enum", "default": "rng",
                    "valid": "diag_tlbr|diag_trbl|horizontal|vertical|cluster",
                    "doc": "Where the blobs sit."},
    "texture":     {"type": "str", "default": "rng helpful",
                    "valid": "diag_tlbr|diag_trbl|horizontal|vertical|cluster|"
                             "border_touch|empty_grid|content_fills_grid|single_cell",
                    "doc": "Arrangement, border contact, or a degenerate."},
}


def _grow(rng, k):
    cells = [(0, 0)]
    seen = {(0, 0)}
    while len(cells) < k:
        r, c = cells[rng.randrange(len(cells))]
        dr, dc = ((-1, 0), (1, 0), (0, -1), (0, 1))[rng.randrange(4)]
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc))
            seen.add((r + dr, c + dc))
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice("texture", ARRANGEMENTS + ("border_touch",))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 8)
        w = ctx.draw_int("grid_w", 10, 10)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 13)
        w = ctx.draw_int("grid_w", 11, 14)
    else:
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 10, 12)
    n = int(overrides.get("n_blobs", ctx.draw_int("n_blobs", 1, 3)))
    rng = ctx.draw_rng("layout")
    arrangement = texture if texture in ARRANGEMENTS else \
        overrides.get("arrangement", rng.choice(ARRANGEMENTS))

    # region anchors per arrangement (region = quarter of the grid)
    halves = {
        "diag_tlbr": [(0, 0), (1, 1), (0, 1)],
        "diag_trbl": [(0, 1), (1, 0), (1, 1)],
        "horizontal": [(0, 0), (0, 1), (1, 0)],
        "vertical": [(0, 0), (1, 0), (0, 1)],
        "cluster": [(0, 0), (0, 0), (0, 0)],
    }[arrangement]
    pal = rng.sample([1, 2, 3, 4, 6, 7, 8, 9], n)
    for _attempt in range(60):
        g = full_grid(h, w, 0)
        lo_r = 0 if texture == "border_touch" else 1
        ok = True
        for i in range(n):
            cells = _grow(rng, rng.randint(2, 5))
            sh = max(r for r, _ in cells) + 1
            sw = max(c for _, c in cells) + 1
            qr, qc = halves[i % len(halves)]
            r_lo = lo_r + qr * (h // 2)
            r_hi = (h // 2 - sh) if qr == 0 else (h - sh - lo_r)
            c_lo = lo_r + qc * (w // 2)
            c_hi = (w // 2 - sw) if qc == 0 else (w - sw - lo_r)
            if r_hi < r_lo or c_hi < c_lo:
                ok = False
                break
            r0 = rng.randint(r_lo, r_hi)
            c0 = rng.randint(c_lo, c_hi)
            if any(g[r0 + r][c0 + c] != 0 for r, c in cells):
                ok = False
                break
            for r, c in cells:
                g[r0 + r][c0 + c] = pal[i]
        if not ok:
            continue
        # crop must shrink
        rows = [r for r in range(h) if any(g[r])]
        cols = [c for c in range(w) if any(g[r][c] for r in range(h))]
        if not rows:
            continue
        bh = max(rows) - min(rows) + 1
        bw = max(cols) - min(cols) + 1
        if (bh, bw) == (h, w):
            continue
        return g
    # fallback: one small blob with margins
    g = full_grid(h, w, 0)
    g[1][1] = pal[0]
    g[1][2] = pal[0]
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Non-bg content must exist and bbox must be strictly smaller than the grid."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    rows = [r for r in range(h) if any(grid[r][c] != 0 for c in range(w))]
    cols = [c for c in range(w) if any(grid[r][c] != 0 for r in range(h))]
    errors = []
    if not rows:
        errors.append("no non-zero content found")
    elif (max(rows) - min(rows) + 1 == h) and (max(cols) - min(cols) + 1 == w):
        errors.append("bbox fills the entire grid — crop is identity")
    return errors


def _draw_from_degenerate(name, ctx):
    """Rule-hiding inputs — rng-varied. (empty_grid is SAFE for this
    rule: it returns [[0]] explicitly when no content exists.)

    empty_grid         — rule emits a 1x1 zero grid.
    content_fills_grid — crop is the identity.
    single_cell        — 1x1 crop.
    """
    rng = ctx.draw_rng("degenerate_layout")
    h = ctx.draw_int("grid_h", 8, 11)
    w = ctx.draw_int("grid_w", 9, 12)
    g = full_grid(h, w, 0)
    if name == "empty_grid":
        return g
    if name == "content_fills_grid":
        base = rng.randint(0, 4)
        for r in range(h):
            for c in range(w):
                g[r][c] = 1 + ((r * 3 + c + base) % 5)
        return g
    g[rng.randrange(h)][rng.randrange(w)] = rng.randint(1, 9)
    return g
