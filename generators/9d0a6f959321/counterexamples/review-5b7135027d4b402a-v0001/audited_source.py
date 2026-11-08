"""Generator for arc_additional_puzzle_bank_volume16:E112.

Rule: orange components that touch the grid border are recolored green.

Combinatorial axes (8): grid_h/w, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_objects, all_interior, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect, full_grid

GENERATOR_ID = "9d0a6f959321"
VERSION = "2.0.2"  # distinct 102 / under-distributed: only 2 fixed 2x2 orange rects, no distractors. Rule recolors EVERY border-touching orange(7) to 3; canonical has multiple orange components + non-7 distractor objects. Place 2-5 varied orange polyominoes (mix border/interior) + 0-2 distractor-color objects (rule ignores them)."
TASK_ID = "9d0a6f959321"
SUMMARY = "Orange(7) components touching the grid border are recolored green(3); interior orange stays 7. Multiple varied orange components (mix of border-touching and interior) plus non-7 distractor objects that the rule ignores."

INVARIANTS = [
    "background is 0",
    "at least one orange component touches an outer border",
    "at least one orange component is fully interior",
    "orange components are separated by background",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_objects", "all_interior", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..13", "valid": "8..16"},
    "grid_w":         {"type": "int", "default": "rng 8..13", "valid": "8..16"},
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


def _poly(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for r, c in cells]


def _free(g, cells, h, w):
    cset = set(cells)
    for (r, c) in cells:
        if not (0 <= r < h and 0 <= c < w):
            return False
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = r + dr, c + dc
                if 0 <= rr < h and 0 <= cc < w and g[rr][cc] != 0 and (rr, cc) not in cset:
                    return False
    return True


def _touches_border(cells, h, w):
    return any(r == 0 or r == h - 1 or c == 0 or c == w - 1 for r, c in cells)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("placement")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9); w = ctx.draw_int("grid_w", 8, 9)
        n7, ndec = 2, rng.randint(0, 1)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 16); w = ctx.draw_int("grid_w", 12, 16)
        n7, ndec = rng.randint(3, 5), rng.randint(1, 3)
    else:
        h = ctx.draw_int("grid_h", 8, 13); w = ctx.draw_int("grid_w", 8, 13)
        n7, ndec = rng.randint(2, 4), rng.randint(0, 2)
    for _outer in range(80):
        g = full_grid(h, w, 0)
        ok = True
        # Orange(7) components: guarantee >=1 border-touching (recolored to 3) AND
        # >=1 interior (stays 7); the rest random.  Previously an unplaced required
        # component was silently skipped, so rare normal boards contained only the
        # border or only the interior branch.
        for i in range(n7):
            want_border = (i == 0) or (i >= 2 and rng.random() < 0.5)
            if i == 1:
                want_border = False
            placed = False
            for _ in range(100):
                shape = _poly(rng, rng.randint(2, 5))
                sh = max(r for r, _ in shape) + 1; sw = max(c for _, c in shape) + 1
                if sh >= h or sw >= w:
                    continue
                if want_border:
                    edge = rng.choice(["top", "bottom", "left", "right"])
                    if edge == "top":
                        r0, c0 = 0, rng.randint(0, w - sw)
                    elif edge == "bottom":
                        r0, c0 = h - sh, rng.randint(0, w - sw)
                    elif edge == "left":
                        r0, c0 = rng.randint(0, h - sh), 0
                    else:
                        r0, c0 = rng.randint(0, h - sh), w - sw
                else:
                    if h - sh - 1 < 1 or w - sw - 1 < 1:
                        continue
                    r0 = rng.randint(1, h - sh - 1); c0 = rng.randint(1, w - sw - 1)
                cells = [(r0 + dr, c0 + dc) for dr, dc in shape]
                if _touches_border(cells, h, w) != want_border:
                    continue
                if _free(g, cells, h, w):
                    for (r, c) in cells:
                        g[r][c] = 7
                    placed = True
                    break
            if not placed:
                ok = False
                break
        if not ok:
            continue
        # Distractor objects in non-{0,3,7} colors — the rule ignores them (canonical
        # carries such decoys; they stay unchanged in the output).  Distractors are
        # optional; failed placements are skipped rather than invalidating the board.
        dec_pool = [1, 2, 4, 5, 6, 8, 9]
        rng.shuffle(dec_pool)
        for col in dec_pool[:ndec]:
            for _ in range(40):
                shape = _poly(rng, rng.randint(1, 3))
                sh = max(r for r, _ in shape) + 1; sw = max(c for _, c in shape) + 1
                if sh >= h or sw >= w:
                    continue
                r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
                cells = [(r0 + dr, c0 + dc) for dr, dc in shape]
                if _free(g, cells, h, w):
                    for (r, c) in cells:
                        g[r][c] = col
                    break
        if not self_check(g, difficulty=difficulty):
            return g
    raise ValueError("could not place both border-touching and interior orange components")

def _draw_from_degenerate(name, rng):
    g = full_grid(10, 10, 0)
    if name == "no_objects":
        return g
    if name == "all_interior":
        draw_rect(g, 4, 4, 2, 2, 7)
        return g
    if name == "full_grid":
        for r in range(10):
            for c in range(10):
                g[r][c] = 7
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Verify: bg=0; at least one color-7 blob touching border; at least one fully interior."""
    msgs = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    seen = set()
    border_found = False
    interior_found = False
    for r0 in range(h):
        for c0 in range(w):
            if (r0, c0) not in seen and grid[r0][c0] == 7:
                stack = [(r0, c0)]; seen.add((r0, c0)); cells = [(r0, c0)]
                while stack:
                    r, c = stack.pop()
                    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == 7:
                            seen.add((nr, nc)); stack.append((nr, nc)); cells.append((nr, nc))
                touches = any(r == 0 or r == h - 1 or c == 0 or c == w - 1 for r, c in cells)
                if touches:
                    border_found = True
                else:
                    interior_found = True
    if not border_found:
        msgs.append("no color-7 blob touches the grid border")
    if not interior_found:
        msgs.append("no fully interior color-7 blob found")
    return msgs
