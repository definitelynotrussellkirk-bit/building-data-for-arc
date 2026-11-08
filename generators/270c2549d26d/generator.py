"""Generator for a834deea.

Rule: every 4-connected region of 0-cells (a solid rectangle of 0 on
the color-8 background) has its INTERIOR (bbox minus the outer ring)
filled by a 9-zone COMPASS ROSE. Each interior cell is mapped to one of
a 3x3 grid of zones by its fractional position within the interior bbox
(top/mid/bot x left/mid/right); the 8 surrounding zones get the fixed
compass colors (TL=1 T=7 TR=6 L=4 R=5 BL=2 B=9 BR=3) and the centre
stays 0. The rule runs PER 0-region, so several rectangles each get
their own rose.

Combinatorial axes: grid size, the number of rectangles (1-3), and each
rectangle's size and position.
Degenerates: no_region, full_grid, no_bg.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "270c2549d26d"
VERSION = "3.0.1"  # diversity: multiple rectangles, random size+position+grid (was 1 fixed-offset rect ~13)
TASK_ID = "270c2549d26d"
SUMMARY = (
    "Color-8 (cyan) background grid (size varies). 1-3 solid RECTANGLES "
    "of 0-cells (each rh x rw, rh/rw in [5..9]), placed apart so each is a "
    "separate 4-connected 0-region fully enclosed by the cyan background. "
    "Rule: for each rectangle, fill its INTERIOR (bbox minus outer ring) "
    "with a 9-zone COMPASS ROSE keyed by fractional position within the "
    "interior (corners/edges/centre get distinct fixed colors; centre "
    "stays 0); the outer ring stays 0 and the cyan background is "
    "unchanged. The grid size, rectangle count, and each rectangle's "
    "size/position all vary freely (was one fixed-offset rectangle, ~13 "
    "distinct)."
)

INVARIANTS = [
    "background is color 8",
    "1-3 solid 0-rectangles, each fully enclosed by the background",
    "rectangles are pairwise separated (each a distinct 4-connected region)",
    "each rectangle is >=5 in both dims so it has a non-trivial interior",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_region", "full_grid", "no_bg")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "10..26"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "12..28"},
    "region_h":       {"type": "int", "default": "varies", "valid": "5..9"},
    "region_w":       {"type": "int", "default": "varies", "valid": "5..9"},
    "n_rects":        {"type": "int", "default": "varies", "valid": "1..3"},
    "palette_kind":   {"type": "str", "default": "fixed", "valid": "fixed"},
    "anchor_corner":  {"type": "bool", "default": "false", "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false", "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "rects_apart", "valid": "rects_apart"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "warm|cool|broad|primary|no_region|full_grid|no_bg"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: background is color-8; at least one solid 0-rectangle ≥5×5 enclosed by background."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    # Majority value should be 8 (the background)
    count_8 = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 8)
    if count_8 < (h * w) // 2:
        return errors  # degenerate no_bg — allowed
    # Find connected regions of 0-cells; at least one ≥5×5 bbox
    visited = [[False] * w for _ in range(h)]
    found_rect = False
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] == 0 and not visited[sr][sc]:
                # BFS to find connected 0-region
                queue = [(sr, sc)]
                region = []
                visited[sr][sc] = True
                while queue:
                    r, c = queue.pop()
                    region.append((r, c))
                    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == 0 and not visited[nr][nc]:
                            visited[nr][nc] = True
                            queue.append((nr, nc))
                if region:
                    rmin = min(r for r, c in region); rmax = max(r for r, c in region)
                    cmin = min(c for r, c in region); cmax = max(c for r, c in region)
                    if rmax - rmin + 1 >= 5 and cmax - cmin + 1 >= 5:
                        found_rect = True
    if not found_rect:
        errors.append("no 0-rectangle ≥5×5 found on color-8 background")
    return errors


def _reserve(occ, top, left, bh, bw, h, w, margin=1):
    """Reserve the rectangle bbox plus a `margin` ring (keeps rects apart)."""
    for r in range(top - margin, top + bh + margin):
        for c in range(left - margin, left + bw + margin):
            if 0 <= r < h and 0 <= c < w and occ[r][c]:
                return False
    for r in range(top, top + bh):
        for c in range(left, left + bw):
            occ[r][c] = True
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    if difficulty == "easy":
        hr, wr, rr, nr = (10, 13), (12, 15), (5, 7), (1, 1)
    elif difficulty == "hard":
        hr, wr, rr, nr = (18, 26), (20, 28), (5, 9), (2, 3)
    else:
        hr, wr, rr, nr = (13, 19), (15, 22), (5, 8), (1, 2)

    for _attempt in range(40):
        h = rng.randint(*hr); w = rng.randint(*wr)
        g = full_grid(h, w, 8)
        occ = [[False] * w for _ in range(h)]
        want = rng.randint(*nr)
        placed = 0
        for _ in range(want):
            rh = rng.randint(*rr); rw = rng.randint(*rr)
            if rh + 2 > h or rw + 2 > w:
                continue
            for _t in range(40):
                top = rng.randint(1, h - rh - 1)   # >=1 cell bg margin all sides
                left = rng.randint(1, w - rw - 1)
                if not _reserve(occ, top, left, rh, rw, h, w, margin=1):
                    continue
                for r in range(top, top + rh):
                    for c in range(left, left + rw):
                        g[r][c] = 0
                placed += 1
                break
        if placed >= 1:
            return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    g = full_grid(11, 11, 8)
    if name == "no_region":
        return g
    if name == "no_bg":
        return full_grid(11, 11, 0)
    if name == "full_grid":
        for r in range(11):
            for c in range(11):
                g[r][c] = 8
        return g
    return g
