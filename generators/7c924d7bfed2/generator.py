"""Generator for d749d46f.

Rule: a short strip contains several same-color solid rectangles on the
mode-color background.  Read the non-background components from left to
right.  Output a 10-row gallery: the top half draws each component as
thin×long, and the bottom half draws long×thin, separated by background
gaps.

Combinatorial axes (8): grid_h/w, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_rects, bg_kind.
Degenerates: no_rects, single_rect, full_grid.
"""
from __future__ import annotations

from collections import Counter, deque

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, draw_rect

GENERATOR_ID = "7c924d7bfed2"
VERSION = "1.3.0"  # fix distribution drift: canonical-like short two-color component strips
TASK_ID = "7c924d7bfed2"
SUMMARY = (
    "Short two-color strip with 4-6 left-to-right solid rectangular "
    "foreground components.  The rule packs their thin/long dimensions into "
    "a 10-row gallery."
)

# Rivals: 'preserve input' refuted by any demo (output is gallery). 'sort by
# area' refuted by varying left-to-right order vs size. 'use just one stack'
# refuted by both top and bottom halves. 'ignore 1x1/thin components' refuted by
# the canonical-like mix of scalar, vertical, horizontal, and block components.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "exactly two colors: mode background plus one foreground color",
    "4-6 foreground components, each a solid rectangle",
    "components are separated by at least one background column",
    "short strip geometry matches the canonical task scale",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
BG_KINDS = ("black", "cyan", "gray", "colored")
DEGENERATE_TEXTURES = ("no_rects", "single_rect", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 3..6", "valid": "3..7"},
    "grid_w":         {"type": "int", "default": "rng 11..18", "valid": "8..24"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "warm|cool|broad|primary"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force": {"type": "bool", "default": "false",
                        "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "top_aligned_strip",
                       "valid": "top_aligned_strip"},
    "n_rects":        {"type": "int", "default": "rng 4..6", "valid": "2..7"},
    "bg_kind":        {"type": "str", "default": "rng",
                       "valid": "black|cyan|gray|colored"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "warm|cool|broad|primary|no_rects|single_rect|full_grid"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("placement")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    if difficulty == "easy":
        h_lo, h_hi, n_lo, n_hi = 3, 4, 4, 5
    elif difficulty == "hard":
        h_lo, h_hi, n_lo, n_hi = 5, 6, 5, 6
    else:
        h_lo, h_hi, n_lo, n_hi = 4, 6, 4, 6
    h = int(overrides.get("grid_h", ctx.draw_int("grid_h", h_lo, h_hi)))
    n_rects = int(overrides.get("n_rects", ctx.draw_int("n_rects", n_lo, n_hi)))
    n_rects = max(2, min(7, n_rects))

    palette_kind = (overrides.get("texture") or
                    overrides.get("palette_kind") or
                    ctx.draw_choice("palette_kind", list(PALETTE_KINDS)))
    bg_kind = overrides.get("bg_kind", ctx.draw_choice("bg_kind", list(BG_KINDS)))
    bg, fg = _choose_palette(palette_kind, bg_kind, rng)

    # Try several dimension sets until the strip fits the requested width.  The
    # pattern deliberately mirrors canonical inputs: top-aligned separated
    # components of one foreground color on a short background strip.
    for _outer in range(80):
        dims = []
        for i in range(n_rects):
            # Cycle through horizontal, vertical, block, and occasional 1x1
            # pieces so the gallery must use each component's thin/long dims.
            kind = (i + sample_index + seed) % 4
            if kind == 0:
                rh = 1
                rw = rng.randint(2, min(4, max(2, h + 1)))
            elif kind == 1:
                rh = rng.randint(2, h)
                rw = 1
            elif kind == 2:
                rh = rng.randint(2, min(h, 3))
                rw = rng.randint(2, 3)
            else:
                rh = 1
                rw = 1 if rng.random() < 0.55 else rng.randint(2, 3)
            dims.append((rh, rw))
        gaps = [rng.randint(1, 2) for _ in range(n_rects - 1)]
        min_w = sum(rw for _, rw in dims) + sum(gaps)
        w_lo = max(8, min_w)
        if difficulty == "easy":
            w_hi = max(w_lo, 15)
        elif difficulty == "hard":
            w_hi = max(w_lo, 22)
        else:
            w_hi = max(w_lo, 18)
        requested = overrides.get("grid_w")
        w = int(requested) if requested is not None else ctx.draw_int("grid_w", w_lo, min(24, w_hi))
        if w < min_w or w > 24:
            continue
        g = full_grid(h, w, bg)
        left_margin = rng.randint(0, w - min_w)
        c = left_margin
        for (rh, rw), gap in zip(dims, gaps + [0]):
            draw_rect(g, 0, c, rh, rw, fg)
            c += rw + gap
        return g
    raise ValueError("could not fit canonical-like component strip")


def _choose_palette(kind, bg_kind, rng):
    if kind == "warm":
        pool = [2, 3, 4, 6, 9]
    elif kind == "cool":
        pool = [1, 5, 7, 8]
    elif kind == "primary":
        pool = [1, 2, 3, 4]
    else:
        pool = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    pool = list(pool)
    rng.shuffle(pool)
    if bg_kind == "black":
        bg = 0
    elif bg_kind == "cyan":
        bg = 8
    elif bg_kind == "gray":
        bg = 5
    else:
        bg = pool[0]
    fg_candidates = [c for c in pool + [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
                     if c != bg]
    return bg, fg_candidates[0]


def _foreground_components(grid, bg):
    h, w = len(grid), len(grid[0])
    seen = [[False] * w for _ in range(h)]
    components = []
    for sr in range(h):
        for sc in range(w):
            if seen[sr][sc] or grid[sr][sc] == bg:
                continue
            col = grid[sr][sc]
            q = deque([(sr, sc)])
            seen[sr][sc] = True
            cells = []
            while q:
                r, c = q.popleft()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < h and 0 <= nc < w and not seen[nr][nc]
                            and grid[nr][nc] == col):
                        seen[nr][nc] = True
                        q.append((nr, nc))
            components.append((col, cells))
    return components


def self_check(grid, *, difficulty=None, meta=None):
    """Verify the canonical short two-color component-strip invariants."""
    errs = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    flat = [v for row in grid for v in row]
    freq = Counter(flat)
    bg = freq.most_common(1)[0][0]
    colors = set(flat)
    if len(colors) != 2:
        errs.append(f"expected exactly two colors, found {sorted(colors)}")
    components = _foreground_components(grid, bg)
    if not 2 <= len(components) <= 7:
        errs.append(f"expected 2..7 foreground rectangles, found {len(components)}")
    for color, cells in components:
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        r1, r2, c1, c2 = min(rs), max(rs), min(cs), max(cs)
        area = (r2 - r1 + 1) * (c2 - c1 + 1)
        if len(cells) != area:
            errs.append(f"color {color} component at {(r1, c1, r2, c2)} is not solid rectangular")
        if r1 != 0:
            errs.append(f"component at {(r1, c1, r2, c2)} should be top-aligned")
    if h > 7 or w > 24:
        errs.append(f"canonical strip should stay small; got {h}x{w}")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 5, 14
    g = full_grid(h, w, 0)
    if name == "no_rects":
        return g
    if name == "single_rect":
        draw_rect(g, 0, 4, 3, 4, 2)
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 2
        return g
    return g
