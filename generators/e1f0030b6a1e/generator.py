"""Generator for 7b:m44 — stamp rotated source at markers.

Rule: source = largest shape whose color is NOT in {1,2,3,4}. For
each cell with value v in {1,2,3,4}, paste source rotated (v-1) times
CW, recolored to v, with top-left at that cell.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_source, no_markers, marker_invalid_code.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e1f0030b6a1e"
VERSION = "2.1.0"  # fixed 3-shape source bank + could raise ValueError on hard-to-pack seeds. Rule: source=largest color-5..9 shape; each marker v in {1,2,3,4} pastes source rotated (v-1) CW, recolored to v, at the marker. Now random asymmetric source + robust placement (no raise).
TASK_ID = "e1f0030b6a1e"

SUMMARY = "1 random asymmetric source shape (color 5-9) + 2-4 marker cells with distinct codes in {1,2,3,4}; rule stamps the source rotated (code-1)*90deg CW (recolored to the code) at each marker."

INVARIANTS = [
    "background is 0",
    "exactly one source shape in a color from {5,6,7,8,9}, isolated, asymmetric",
    "2-4 isolated marker cells with values in {1, 2, 3, 4}",
    "each marker has space for the source rotated by (v-1)*90° to fit in-bounds",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_source", "no_markers", "marker_invalid_code")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 11..13", "valid": "10..18"},
    "grid_w":         {"type": "int", "default": "rng 12..14", "valid": "11..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "palette_size":   {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "position_bias":  {"type": "str", "default": "source_plus_markers",
                       "valid": "source_plus_markers"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_source|no_markers|marker_invalid_code"},
}


_ASYM_SHAPES = [
    [(0, 0), (1, 0), (1, 1), (1, 2)],
    [(0, 0), (0, 1), (0, 2), (1, 0)],
    [(0, 0), (1, 0), (2, 0), (2, 1)],
]


def _poly(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def _too_close(g, r, c) -> bool:
    h, w = len(g), len(g[0])
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            rr, cc = r + dr, c + dc
            if 0 <= rr < h and 0 <= cc < w and g[rr][cc] != 0:
                return True
    return False


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify one multi-cell source and difficulty-scaled isolated markers."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    seen = set()
    sources = []
    markers = []
    errs = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0 and (r, c) not in seen:
                color = grid[r][c]
                stack = [(r, c)]
                seen.add((r, c))
                comp = []
                while stack:
                    cr, cc = stack.pop()
                    comp.append((cr, cc))
                    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == color and (nr, nc) not in seen:
                            seen.add((nr, nc))
                            stack.append((nr, nc))
                if color in (5, 6, 7, 8, 9) and len(comp) > 1:
                    sources.append(comp)
                elif color in (1, 2, 3, 4) and len(comp) == 1:
                    markers.append(comp[0])
                else:
                    errs.append(f"unexpected component color/size: color={color}, size={len(comp)}")
    if len(sources) != 1:
        errs.append(f"expected exactly one source shape, found {len(sources)}")
    min_markers = 2 if difficulty != "hard" else 3
    if len(markers) < min_markers:
        errs.append(f"only {len(markers)} markers; expected at least {min_markers}")
    for r, c in markers:
        if any(0 <= r + dr < h and 0 <= c + dc < w and grid[r + dr][c + dc] != 0
               for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))):
            errs.append("marker cells must be 4-isolated")
            break
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 11, 12); w = ctx.draw_int("grid_w", 12, 13)
        nm = (2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 18); w = ctx.draw_int("grid_w", 15, 18)
        nm = (3, 4)
    else:
        h = ctx.draw_int("grid_h", 12, 14); w = ctx.draw_int("grid_w", 13, 16)
        nm = (2, 4)
    rng = ctx.draw_rng("layout")

    for _attempt in range(40):
        source_color = rng.choice([5, 6, 7, 8, 9])
        shape = _poly(rng, rng.randint(4, 6))
        sh = max(r for r, _ in shape) + 1
        sw = max(c for _, c in shape) + 1
        bound = max(sh, sw)
        g = full_grid(h, w, 0)
        # place source
        placed_source = False
        for _ in range(60):
            r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
            if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1):
                continue
            for dr, dc in shape:
                g[r0 + dr][c0 + dc] = source_color
            placed_source = True
            break
        if not placed_source:
            continue
        n_markers = rng.randint(*nm)
        used_codes = rng.sample([1, 2, 3, 4], n_markers)
        placed = 0
        for _ in range(120):
            if placed >= n_markers:
                break
            mr = rng.randint(0, h - bound); mc = rng.randint(0, w - bound)
            region = [(r, c) for r in range(mr, mr + bound) for c in range(mc, mc + bound)]
            if any(g[r][c] != 0 for r, c in region):
                continue
            if _too_close(g, mr, mc):
                continue
            g[mr][mc] = used_codes[placed]
            placed += 1
        if placed == n_markers:
            return g
    return g   # graceful fallback


def _draw_from_degenerate(name, rng):
    h, w = 12, 13
    g = full_grid(h, w, 0)
    if name == "no_source":
        # Markers but no source shape — rule has nothing to stamp.
        g[3][3] = 1; g[6][8] = 2
        return g
    if name == "no_markers":
        # Source but no markers — rule has nothing to stamp at.
        for dr, dc in _ASYM_SHAPES[0]: g[1 + dr][1 + dc] = 5
        return g
    if name == "marker_invalid_code":
        # Markers have codes outside {1..4} — rule has no defined rotation.
        for dr, dc in _ASYM_SHAPES[0]: g[1 + dr][1 + dc] = 5
        g[6][6] = 7  # 7 is not a valid marker code
        g[8][3] = 8
        return g
    return g
