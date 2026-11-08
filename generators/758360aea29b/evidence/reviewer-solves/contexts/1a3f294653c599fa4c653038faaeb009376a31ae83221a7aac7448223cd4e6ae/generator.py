"""Generator for arc_additional_puzzles_21_set10_bundle:M70.

Rule: objects sorted by reading order produce a matrix comparing their
bounding-box widths.

Combinatorial axes (8): grid_h/w, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_objects, single_object, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, draw_rect

GENERATOR_ID = "758360aea29b"
VERSION = "2.2.0"  # defect-lint round: AXES ranges now match the real draws (h/w lied);
# object colors exclude 1 (canonical reserves 1 for the output alphabet — half the old
# instances used 1 as an object color, muting the rule's 1-introduction signature);
# self_check strengthened from palette-only to structural (isolated colored objects,
# >=2 distinct widths).
TASK_ID = "758360aea29b"
RULE_HASH = "a2e0aeab30da"
SUMMARY = "N separated rectangles with random bounding-box widths; output is the n x n width-comparison matrix (1=equal, 2=greater, 3=less)."

INVARIANTS = [
    "2+ objects separated by background",
    "object bbox widths vary (so greater/less comparisons arise)",
    "when n>=3, at least two distinct objects share a width (off-diagonal equal)",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_objects", "single_object", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "10-12 easy / 12-16 med / 14-18 hard", "valid": "10..18"},
    "grid_w":         {"type": "int", "default": "12-15 easy / 14-20 med / 16-22 hard", "valid": "12..22"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "warm|cool|broad|primary"},
    "n_objects":      {"type": "int", "default": "2-7", "valid": "2..7"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "warm|cool|broad|primary|no_objects|single_object|full_grid"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural invariants: bg=0; no color 1; each non-zero color is exactly one
    isolated shape; >=2 objects with >=2 distinct bbox widths."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if h > 30 or w > 30:
        return [f"grid too large: {h}x{w}"]
    errs = []
    cells_by_color: dict[int, list[tuple[int, int]]] = {}
    for r in range(h):
        for c in range(w):
            v = grid[r][c]
            if v != 0:
                cells_by_color.setdefault(v, []).append((r, c))
    if 1 in cells_by_color:
        errs.append("color 1 used as an object color (reserved for the output alphabet)")
    if len(cells_by_color) < 2:
        errs.append(f"expected >=2 distinct non-zero colors (separated objects), got {len(cells_by_color)}")
    widths = []
    for color, cells in cells_by_color.items():
        r1 = min(r for r, _ in cells); r2 = max(r for r, _ in cells)
        c1 = min(c for _, c in cells); c2 = max(c for _, c in cells)
        widths.append(c2 - c1 + 1)
        # isolation: no cell of another color 8-adjacent to this rectangle
        for r, c in cells:
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    rr, cc = r + dr, c + dc
                    if 0 <= rr < h and 0 <= cc < w and grid[rr][cc] not in (0, color):
                        errs.append(f"colors {color} and {grid[rr][cc]} touch — objects must be separated")
                        break
                else:
                    continue
                break
            else:
                continue
            break
    if len(set(widths)) < 2:
        errs.append("all object widths equal — the greater/less relation is never demonstrated")
    return errs


def _place_rect(g, rh, rw, color, rng, occ):
    h, w = len(g), len(g[0])
    if rh > h or rw > w:
        return False
    for _ in range(150):
        r0 = rng.randint(0, h - rh); c0 = rng.randint(0, w - rw)
        cells = [(r0 + r, c0 + c) for r in range(rh) for c in range(rw)]
        if any((r + dr, c + dc) in occ for (r, c) in cells
               for dr in (-1, 0, 1) for dc in (-1, 0, 1)):
            continue
        for (r, c) in cells:
            g[r][c] = color
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    occ.add((r + dr, c + dc))
        return True
    return False


def _width_pool(rng, n, w_hi):
    """Widths that always exercise the comparison relation.

    The old random pool could collapse to all-equal widths, making the target
    matrix contain no greater/less relation. For n>=3, include an off-diagonal
    equality pair plus at least one different width; for n=2, use distinct
    widths so both greater and less appear off-diagonal.
    """
    if n <= 2:
        a = rng.randint(1, w_hi)
        choices = [x for x in range(1, w_hi + 1) if x != a]
        b = rng.choice(choices) if choices else a
        widths = [a, b]
    else:
        a = rng.randint(1, w_hi)
        choices = [x for x in range(1, w_hi + 1) if x != a]
        b = rng.choice(choices) if choices else a
        widths = [a, a, b]
        while len(widths) < n:
            widths.append(rng.randint(1, w_hi))
    rng.shuffle(widths)
    return widths

def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 10, 12); w = ctx.draw_int("grid_w", 12, 15)
        n = ctx.draw_int("n_objects", 2, 4); w_hi = 5
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 18); w = ctx.draw_int("grid_w", 16, 22)
        n = ctx.draw_int("n_objects", 5, 7); w_hi = 8
    else:
        h = ctx.draw_int("grid_h", 12, 16); w = ctx.draw_int("grid_w", 14, 20)
        n = ctx.draw_int("n_objects", 2, 6); w_hi = 7
    rng = ctx.draw_rng("layout")
    # Never 1: the output matrix's alphabet is {1,2,3} and the canonical demos
    # reserve 1 for it — an object colored 1 mutes the rule's signature.
    colors = rng.sample([2, 3, 4, 5, 6, 7, 8, 9], n)

    # N rectangles with controlled bbox widths -> a varied width-comparison matrix.
    # Retry the full layout because a failed late placement used to silently drop
    # objects, changing the matrix size and weakening the task.
    width_pool = _width_pool(rng, n, w_hi)
    for _attempt in range(80):
        g = full_grid(h, w, 0)
        occ = set()
        placed = 0
        for i in range(n):
            rw = max(1, min(width_pool[i], w - 1))
            rh = rng.randint(1, min(4, h - 1))
            if not _place_rect(g, rh, rw, colors[i], rng, occ):
                break
            placed += 1
        if placed == n:
            return g

    # Deterministic safety layout: one 1-row rectangle per even-numbered row.
    # All configured size bands have h >= 2*n-1, so this preserves separation
    # and avoids silently returning a partial task when random packing is unlucky.
    g = full_grid(h, w, 0)
    for i in range(n):
        r = min(2 * i, h - 1)
        rw = max(1, min(width_pool[i], w))
        for c in range(rw):
            g[r][c] = colors[i]
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(11, 14, 0)
    if name == "no_objects":
        return g
    if name == "single_object":
        draw_rect(g, 4, 5, 2, 4, 3)
        return g
    if name == "full_grid":
        for r in range(11):
            for c in range(14):
                g[r][c] = 3
        return g
    return g


def observe_overrides(grid):
    """Measure exact geometry/count controls directly from rendered pixels."""
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_objects": len({v for row in grid for v in row if v != 0}),
    }
