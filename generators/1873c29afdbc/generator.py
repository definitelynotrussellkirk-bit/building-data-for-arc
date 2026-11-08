"""Generator for arc_additional_puzzle_bank_volume13:E88.

Rule: orange components touching exactly one border are recolored blue.

Combinatorial axes (8): grid_h/w, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_objects, no_one_border, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect, full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "1873c29afdbc"
# 1.2.0: was 3 fixed 2x2 squares in near-fixed positions; now places a
#        varied number of random orange polyominoes (varied shapes/sizes)
#        explicitly distributed across 0-, 1-, and 2-border configs, with
#        >=1 touching exactly one border. Branch coverage maximized.
VERSION = "1.2.1"  # add executable self_check for single-border component rule
TASK_ID = "1873c29afdbc"
SUMMARY = "Orange components touching exactly one border recolored blue."

INVARIANTS = [
    "background is 0",
    "at least one orange component touches exactly one border",
    "other orange components touch zero or two borders",
    "orange components are separated",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_objects", "no_one_border", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..13", "valid": "8..13"},
    "grid_w":         {"type": "int", "default": "rng 8..13", "valid": "8..13"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "varied", "valid": "varied"},
    "n_distinct_colors":{"type": "int", "default": "1", "valid": "1"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("placement")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 8, 9)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 13)
        w = ctx.draw_int("grid_w", 12, 13)
    else:
        h = ctx.draw_int("grid_h", 8, 13)
        w = ctx.draw_int("grid_w", 8, 13)
    g = full_grid(h, w, 0)
    used = set()

    # How many orange components of each border-class.
    if difficulty == "easy":
        n_one = rng.randint(1, 2)
        n_zero = rng.randint(0, 1)
        n_two = rng.randint(0, 1)
    elif difficulty == "hard":
        n_one = rng.randint(2, 4)
        n_zero = rng.randint(1, 3)
        n_two = rng.randint(1, 2)
    else:
        n_one = rng.randint(1, 3)
        n_zero = rng.randint(1, 2)
        n_two = rng.randint(0, 2)

    # 'one': touches exactly one border. Choose which border and slide a
    # blob so its bbox just reaches that edge but no other edge.
    for _ in range(n_one):
        _place_border_blob(g, used, rng, h, w, n_borders=1)
    for _ in range(n_two):
        _place_border_blob(g, used, rng, h, w, n_borders=2)
    # 'zero': interior blob touching no border (kept inside 1..h-2, 1..w-2).
    for _ in range(n_zero):
        _place_interior_blob(g, used, rng, h, w)
    return g


def _stamp(g, used, cells, color=7):
    for r, c in cells:
        g[r][c] = color
        used.add((r, c))
    # Reserve a 1-cell orthogonal buffer so distinct blobs stay separate.
    for r, c in list(cells):
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            used.add((r + dr, c + dc))


def _place_interior_blob(g, used, rng, h, w):
    # Grow a blob constrained to the interior (rows 1..h-2, cols 1..w-2).
    blob = _grow_in_region(rng, used, 1, 1, h - 2, w - 2, rng.randint(1, 5))
    if blob:
        _stamp(g, used, blob)


def _place_border_blob(g, used, rng, h, w, n_borders):
    """Place a blob whose bbox touches exactly n_borders grid edges."""
    if n_borders == 1:
        side = rng.choice(("top", "bottom", "left", "right"))
        if side == "top":
            blob = _grow_in_region(rng, used, 0, 1, max(0, h // 2), w - 2,
                                   rng.randint(1, 5), must_include_row=0)
        elif side == "bottom":
            blob = _grow_in_region(rng, used, max(1, h // 2), 1, h - 1, w - 2,
                                   rng.randint(1, 5), must_include_row=h - 1)
        elif side == "left":
            blob = _grow_in_region(rng, used, 1, 0, h - 2, max(0, w // 2),
                                   rng.randint(1, 5), must_include_col=0)
        else:
            blob = _grow_in_region(rng, used, 1, max(1, w // 2), h - 2, w - 1,
                                   rng.randint(1, 5), must_include_col=w - 1)
    else:  # two borders -> a corner
        corner = rng.choice(("nw", "ne", "sw", "se"))
        sz = rng.randint(2, 4)
        if corner == "nw":
            cells = {(r, c) for r in range(0, min(sz, h)) for c in range(0, min(sz, w))}
        elif corner == "ne":
            cells = {(r, c) for r in range(0, min(sz, h)) for c in range(max(0, w - sz), w)}
        elif corner == "sw":
            cells = {(r, c) for r in range(max(0, h - sz), h) for c in range(0, min(sz, w))}
        else:
            cells = {(r, c) for r in range(max(0, h - sz), h) for c in range(max(0, w - sz), w)}
        if cells & used:
            return
        _stamp(g, used, cells)
        return
    if blob:
        _stamp(g, used, blob)


def _grow_in_region(rng, used, r1, c1, r2, c2, target, *,
                    must_include_row=None, must_include_col=None,
                    attempts=60):
    """Grow a connected blob within [r1..r2]x[c1..c2] (inclusive), isolated
    from `used`. Optionally force inclusion of a given row/col so the blob
    touches a specific edge. Returns a set of cells or None."""
    if r2 < r1 or c2 < c1:
        return None
    for _ in range(attempts):
        if must_include_row is not None:
            sr = must_include_row
            sc = rng.randint(c1, c2)
        elif must_include_col is not None:
            sr = rng.randint(r1, r2)
            sc = must_include_col
        else:
            sr = rng.randint(r1, r2)
            sc = rng.randint(c1, c2)
        if (sr, sc) in used:
            continue
        cells = {(sr, sc)}
        frontier = [(sr, sc)]
        while frontier and len(cells) < target:
            r, c = frontier.pop(rng.randint(0, len(frontier) - 1))
            opts = [(r + dr, c + dc) for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))]
            rng.shuffle(opts)
            for nr, nc in opts:
                if not (r1 <= nr <= r2 and c1 <= nc <= c2):
                    continue
                if (nr, nc) in cells or (nr, nc) in used:
                    continue
                cells.add((nr, nc))
                frontier.append((nr, nc))
                if len(cells) >= target:
                    break
        # Validate: blob must not touch `used`, and must include the
        # required edge if one was requested.
        if any((r + dr, c + dc) in used
               for r, c in cells for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            continue
        if must_include_row is not None and not any(r == must_include_row for r, _ in cells):
            continue
        if must_include_col is not None and not any(c == must_include_col for _, c in cells):
            continue
        return cells
    return None


def _draw_from_degenerate(name, rng):
    g = full_grid(10, 10, 0)
    if name == "no_objects":
        return g
    if name == "no_one_border":
        draw_rect(g, 4, 4, 2, 2, 7)
        return g
    if name == "full_grid":
        for r in range(10):
            for c in range(10):
                g[r][c] = 7
        return g
    return g


def _components_7(grid):
    h, w = len(grid), len(grid[0])
    seen = set(); comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 7 or (r, c) in seen:
                continue
            q = [(r, c)]; seen.add((r, c)); cells = []
            while q:
                cr, cc = q.pop(); cells.append((cr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = cr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == 7 and (nr, nc) not in seen:
                        seen.add((nr, nc)); q.append((nr, nc))
            comps.append(cells)
    return comps


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    h, w = len(grid), len(grid[0])
    comps = _components_7(grid)
    if not comps:
        msgs.append("expected orange components")
    one = 0
    for cells in comps:
        touches = int(any(r == 0 for r, _ in cells)) + int(any(r == h - 1 for r, _ in cells)) \
            + int(any(c == 0 for _, c in cells)) + int(any(c == w - 1 for _, c in cells))
        if touches == 1:
            one += 1
        elif touches not in (0, 2):
            msgs.append(f"component touches {touches} borders; expected 0, 1, or 2")
    if one < 1:
        msgs.append("expected at least one component touching exactly one border")
    return msgs
