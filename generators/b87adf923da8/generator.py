"""Generator for arc_puzzle_bank_eleventh21:M76 — stamp prototype at every target.

Rule: 8 + 3-blob is the prototype (8 = anchor of prototype, 3 = shape
cells). 1-cells are targets. Output: empty grid + prototype's 3-cells
stamped at each target (target = where 8 lands).

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_prototype, no_targets, target_oob.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "b87adf923da8"
# 2.1.0: randomize the prototype (random connected polyomino + varied colors +
# varied anchor offset) instead of a fixed green tromino -> stamped shape varies
VERSION = "2.1.1"
TASK_ID = "b87adf923da8"
SUMMARY = (
    "0-bg grid (h~8-11, w~9-12) with: (a) one PROTOTYPE — one "
    "color-8 (cyan) ANCHOR cell adjacent to (or inside) a small "
    "RANDOM CONNECTED POLYOMINO (2-7 cells) painted in 1-3 "
    "varied non-{0,1,8} colors; (b) 1-4 single color-1 (blue) "
    "TARGET cells scattered apart from the prototype, each "
    "with room around them for a full stamp. Rule: find the "
    "anchor (the 8 cell). Targets = all color-1 cells. "
    "Offsets = for every non-{0, 1, 8} cell in the input, "
    "compute (r - anchor_r, c - anchor_c, value). For each "
    "target, stamp those offsets at the target's position "
    "(target becomes new 'anchor'), each cell painted with the "
    "original value. Output: a fresh empty grid with all "
    "stamped cells. The original prototype, anchor, and "
    "target markers all DISAPPEAR in the output."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "exactly one 8-cell anchored to a small random polyomino (prototype)",
    "1-4 single 1-cells with room around to stamp the prototype",
    "target stamps stay fully in-bounds",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_prototype", "no_targets", "target_oob")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 9..12", "valid": "8..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "prototype_top_left_targets_scattered",
                       "valid": "prototype_top_left_targets_scattered"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_prototype|no_targets|target_oob"},
}


def _build_prototype(rng, size):
    """Random connected polyomino (the shape cells) + an anchor offset.

    Returns (offsets, anchor) where offsets is a list of (dr, dc, color)
    relative to the anchor (color != 0/1/8), and anchor is the (0,0)-based
    reference cell. The anchor is one of the shape's orthogonal neighbours
    (mirrors the demos where 8 sits next to / inside the blob)."""
    cells = {(0, 0)}
    frontier = [(0, 0)]
    while len(cells) < size and frontier:
        r, c = rng.choice(frontier)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nb = (r + dr, c + dc)
        if nb not in cells:
            cells.add(nb)
            frontier.append(nb)
    # Anchor must remain a visible 8-cell.  Earlier versions sometimes chose a
    # shape cell as the anchor, then overwrote the 8 while painting offsets; that
    # produced no-anchor inputs and all-background stamp outputs.
    neigh = []
    for (r, c) in cells:
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nb = (r + dr, c + dc)
            if nb not in cells:
                neigh.append(nb)
    anchor = rng.choice(neigh) if neigh else (0, 1)
    palette_pool = [2, 3, 4, 5, 6, 7, 9]
    rng.shuffle(palette_pool)
    n_colors = rng.randint(1, min(3, len(palette_pool)))
    colors = palette_pool[:n_colors]
    offsets = []
    for (r, c) in sorted(cells):
        offsets.append((r - anchor[0], c - anchor[1], rng.choice(colors)))
    return offsets, anchor, cells


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify prototype/target structure yields a non-empty stamp output."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs: list[str] = []
    cells_8 = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 8]
    if len(cells_8) != 1:
        errs.append(f"found {len(cells_8)} color-8 cells, expected exactly one anchor")
        return errs
    targets = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 1]
    if not targets:
        errs.append("no color-1 target cells; canonical output would be all background")
    ar, ac = cells_8[0]
    offsets = []
    for r in range(h):
        for c in range(w):
            v = grid[r][c]
            if v not in (0, 1, 8):
                offsets.append((r - ar, c - ac, v))
    if not offsets:
        errs.append("prototype has no stamp cells outside {0,1,8}")
    for tr, tc in targets:
        for dr, dc, _v in offsets:
            rr, cc = tr + dr, tc + dc
            if not (0 <= rr < h and 0 <= cc < w):
                errs.append(f"target {(tr, tc)} would stamp out of bounds at {(rr, cc)}")
                break
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 9, 10)
        sz_lo, sz_hi = 2, 4
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 13)
        w = ctx.draw_int("grid_w", 12, 14)
        sz_lo, sz_hi = 3, 7
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 9, 12)
        sz_lo, sz_hi = 2, 6
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)

    # Build a random prototype. offsets are (dr,dc,color) relative to anchor;
    # the rule reads exactly these (all non-{0,1,8} cells) as the stamp.
    offsets, anchor, cells = _build_prototype(rng, rng.randint(sz_lo, sz_hi))
    # normalise so the whole prototype (shape + anchor) starts near top-left
    all_r = [anchor[0]] + [anchor[0] + o[0] for o in offsets]
    all_c = [anchor[1]] + [anchor[1] + o[1] for o in offsets]
    base_r = 1 - min(all_r); base_c = 1 - min(all_c)
    ar, ac = anchor[0] + base_r, anchor[1] + base_c
    if not (0 <= ar < h and 0 <= ac < w):
        ar, ac = 1, 1
    g[ar][ac] = 8
    used = {(ar, ac)}
    for dr, dc, color in offsets:
        rr, cc = ar + dr, ac + dc
        if (rr, cc) == (ar, ac):
            continue
        if 0 <= rr < h and 0 <= cc < w:
            g[rr][cc] = color
            used.add((rr, cc))

    # stamp extent so targets stay in-bounds
    min_dr = min((o[0] for o in offsets), default=0)
    max_dr = max((o[0] for o in offsets), default=0)
    min_dc = min((o[1] for o in offsets), default=0)
    max_dc = max((o[1] for o in offsets), default=0)

    n_targets = rng.randint(1, 4)
    candidates = []
    for r in range(max(0, -min_dr), h - max(0, max_dr)):
        for c in range(max(0, -min_dc), w - max(0, max_dc)):
            stamp = {(r, c)} | {(r + dr, c + dc) for dr, dc, _col in offsets}
            if all(0 <= rr < h and 0 <= cc < w for rr, cc in stamp) and all(g[rr][cc] == 0 for rr, cc in stamp):
                candidates.append((r, c, stamp))
    rng.shuffle(candidates)
    placed_targets = 0
    blocked = set(used)
    for r, c, stamp in candidates:
        if placed_targets >= n_targets:
            break
        if stamp & blocked:
            continue
        g[r][c] = 1
        blocked |= stamp
        placed_targets += 1
    if placed_targets == 0 and candidates:
        r, c, _stamp = candidates[0]
        g[r][c] = 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "no_prototype":
        # 1-targets but no 8/3 prototype — rule has no shape to stamp.
        g[5][3] = 1; g[6][7] = 1
        return g
    if name == "no_targets":
        # Prototype but no 1-targets — rule has no positions to stamp at.
        g[1][1] = 8
        for r, c in [(1, 2), (2, 1), (2, 2)]: g[r][c] = 3
        return g
    if name == "target_oob":
        # Prototype + a 1-target placed near the corner so the
        # full stamp would extend off-grid — rule's stamp region
        # is undefined.
        g[1][1] = 8
        for r, c in [(1, 2), (2, 1), (2, 2)]: g[r][c] = 3
        g[h - 1][w - 1] = 1
        return g
    return g
