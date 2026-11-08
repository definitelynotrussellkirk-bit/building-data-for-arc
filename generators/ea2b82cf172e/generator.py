"""Generator for puzzle d0f5fe59.

Rule: `(rule! (lambda (g) (let ((n (length (objects g 0)))) (build-grid n n (r c) (if (= r c) 8 0)))))`.
Count 4-connected non-bg components → output an n × n grid with cyan(8)
on the diagonal, zeros elsewhere.

Combinatorial axes:
  * grid_h / grid_w     — outer canvas size
  * n_objects           — how many distinct objects (1..9 — output dim)
  * object_kind         — shape: rect / cross / L / blob / hollow_ring /
                          line_h / line_v / single_pixel
  * object_size_dist    — small / medium / mixed
  * object_palette_mode — same_color / all_distinct / alternating
  * placement           — random / corners / row / column / grid
  * caller-opt-in degenerates: single_object (output is 1 × 1 cyan dot),
                               touching_objects (rule sees fewer
                               components than visually intended),
                               max_objects (n=9 — output 9 × 9)
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ea2b82cf172e"
VERSION = "1.3.0"  # guarantees target components are 1..9 separated objects and adds executable self_check
TASK_ID = "ea2b82cf172e"
SUMMARY = "Several non-overlapping objects on a 0 bg; rule outputs n × n cyan-diagonal where n = object count."

INVARIANTS = [
    "background is 0",
    "1..9 distinct non-overlapping objects (so output dim is 1..9)",
    "objects are 4-disconnected (each is its own component)",
]

OBJECT_KINDS = (
    "rect", "cross", "L_shape", "random_blob",
    "hollow_ring", "line_h", "line_v", "single_pixel",
)
SIZE_DISTRIBUTIONS = ("small", "medium", "mixed")
PALETTE_MODES = ("same_color", "all_distinct", "alternating")
PLACEMENTS = ("random", "corners", "row", "column", "grid")
DEGENERATE_TEXTURES = ("single_object", "touching_objects", "max_objects")
HELPFUL_TEXTURES = OBJECT_KINDS

AXES = {
    "grid_h":             {"type": "int", "default": "rng 12..20", "valid": "10..25"},
    "grid_w":             {"type": "int", "default": "rng 12..20", "valid": "10..25"},
    "n_objects":          {"type": "int", "default": "rng 2..7",   "valid": "1..9"},
    "object_kind":        {"type": "str", "default": "rng helpful",
                           "valid": "rect|cross|L_shape|random_blob|hollow_ring|line_h|line_v|single_pixel"},
    "object_size_dist":   {"type": "str", "default": "rng small|medium|mixed",
                           "valid": "small|medium|mixed"},
    "object_palette_mode": {"type": "str", "default": "rng same_color|all_distinct|alternating",
                            "valid": "same_color|all_distinct|alternating"},
    "placement":          {"type": "str", "default": "rng helpful",
                           "valid": "random|corners|row|column|grid"},
    "texture":            {"type": "str", "default": "alias for object_kind",
                           "valid": "rect|cross|L_shape|random_blob|hollow_ring|line_h|line_v|single_pixel|single_object|touching_objects|max_objects"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)

    if difficulty == "easy":
        h_lo, h_hi, n_lo, n_hi = 12, 14, 1, 3
    elif difficulty == "hard":
        h_lo, h_hi, n_lo, n_hi = 17, 22, 6, 9
    else:
        h_lo, h_hi, n_lo, n_hi = 12, 20, 2, 7

    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    rng = ctx.draw_rng("placement")

    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, ctx, rng)

    n_obj = int(overrides.get("n_objects",
                              ctx.draw_int("n_objects", n_lo, n_hi)))
    n_obj = max(1, min(9, n_obj))
    kind = (overrides.get("texture")
            or overrides.get("object_kind")
            or ctx.draw_choice("object_kind", list(OBJECT_KINDS)))
    size_dist = overrides.get(
        "object_size_dist",
        ctx.draw_choice("object_size_dist", list(SIZE_DISTRIBUTIONS)))
    palette_mode = overrides.get(
        "object_palette_mode",
        ctx.draw_choice("object_palette_mode", list(PALETTE_MODES)))
    placement = overrides.get(
        "placement",
        ctx.draw_choice("placement", list(PLACEMENTS)))

    palette = list(ctx.draw_distinct_colors("palette", n=max(2, n_obj), exclude={0}))
    obj_colors = _colors_for_mode(palette_mode, palette, n_obj, rng)

    g = full_grid(h, w, 0)
    anchors = _anchors(placement, h, w, n_obj, rng)
    placed = 0
    for i, color in enumerate(obj_colors):
        ar, ac = anchors[i] if i < len(anchors) else _random_anchor(h, w, rng)
        placed_this = False
        for attempt in range(80):
            sh, sw = _shape_dims(size_dist, h, w, rng)
            if attempt:
                ar, ac = _random_anchor(h, w, rng)
            if 0 <= ar < h - sh - 1 and 0 <= ac < w - sw - 1:
                if _check_clear(g, ar, ac, sh, sw):
                    _paint_kind(g, kind, ar, ac, sh, sw, color, rng)
                    placed += 1
                    placed_this = True
                    break
        if not placed_this and _place_singleton_fallback(g, color, rng):
            placed += 1
    if placed == 0:
        return [[0]]
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate default samples for the count-objects-to-diagonal task."""
    errs: list[str] = []
    if not grid or not isinstance(grid, list) or not isinstance(grid[0], list):
        return ["empty or non-grid input"]
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        return ["ragged grid"]
    if h > 30 or w > 30:
        errs.append(f"grid exceeds ARC bounds: {h}x{w}")
    vals = [v for row in grid for v in row]
    if any(not isinstance(v, int) or v < 0 or v > 9 for v in vals):
        errs.append("grid contains non-ARC color values")
    if 0 not in set(vals):
        errs.append("expected visible zero background")
    comps = _nonzero_components(grid)
    if not (1 <= len(comps) <= 9):
        errs.append(f"expected 1..9 nonzero objects, found {len(comps)}")
    min_objects = 6 if difficulty == "hard" else 1 if difficulty == "easy" else 2
    if len(comps) < min_objects:
        errs.append(f"expected at least {min_objects} objects at difficulty={difficulty!r}, found {len(comps)}")
    for i, comp in enumerate(comps):
        colors = {grid[r][c] for r, c in comp}
        if len(colors) != 1:
            errs.append(f"object component {i} contains multiple colors {sorted(colors)}")
    return errs


def _nonzero_components(grid):
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    comps: list[list[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            comp: list[tuple[int, int]] = []
            while stack:
                cr, cc = stack.pop()
                comp.append((cr, cc))
                for nr, nc in ((cr - 1, cc), (cr + 1, cc), (cr, cc - 1), (cr, cc + 1)):
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] != 0 and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(comp)
    return comps


def _shape_dims(size_dist, h, w, rng):
    if size_dist == "small":
        return rng.randint(2, 3), rng.randint(2, 3)
    if size_dist == "medium":
        return rng.randint(3, 5), rng.randint(3, 5)
    return rng.randint(2, max(2, h // 5)), rng.randint(2, max(2, w // 5))


def _colors_for_mode(mode, palette, n, rng):
    if mode == "same_color":
        return [palette[0]] * n
    if mode == "all_distinct":
        if len(palette) >= n:
            return list(palette[:n])
        return list(palette) + [palette[0]] * (n - len(palette))
    a = palette[0]; b = palette[1] if len(palette) > 1 else palette[0]
    return [a if i % 2 == 0 else b for i in range(n)]


def _anchors(placement, h, w, n, rng):
    margin = 2
    if placement == "corners":
        cands = [(margin, margin), (margin, w - margin - 5),
                 (h - margin - 5, margin), (h - margin - 5, w - margin - 5)]
        while len(cands) < n:
            cands.append(_random_anchor(h, w, rng))
        return cands[:n]
    if placement == "row":
        gap = max(1, (w - 2 * margin) // max(1, n))
        return [(rng.randint(margin, h // 2), margin + i * gap) for i in range(n)]
    if placement == "column":
        gap = max(1, (h - 2 * margin) // max(1, n))
        return [(margin + i * gap, rng.randint(margin, w // 2)) for i in range(n)]
    if placement == "grid":
        cols = 3 if n > 4 else 2
        rows = (n + cols - 1) // cols
        return [(margin + (i // cols) * max(3, h // (rows + 1)),
                 margin + (i % cols) * max(3, w // (cols + 1))) for i in range(n)]
    return [(rng.randint(margin, max(margin, h - 6)),
             rng.randint(margin, max(margin, w - 6))) for _ in range(n)]


def _random_anchor(h, w, rng):
    return rng.randint(1, max(1, h - 6)), rng.randint(1, max(1, w - 6))


def _place_singleton_fallback(g, color, rng):
    """Last-resort placement that preserves the object-count rule.

    The hard band may request up to nine objects; large randomly chosen shapes
    can exhaust an unlucky layout. A separated singleton is still a valid object
    for this task and is better than silently under-counting the episode.
    """
    h, w = len(g), len(g[0])
    cells = [(r, c) for r in range(1, max(1, h - 1)) for c in range(1, max(1, w - 1))]
    rng.shuffle(cells)
    for r, c in cells:
        if _check_clear(g, r, c, 1, 1):
            g[r][c] = color
            return True
    return False


def _check_clear(g, rr, rc, sh, sw):
    for r in range(max(0, rr - 1), min(len(g), rr + sh + 1)):
        for c in range(max(0, rc - 1), min(len(g[0]), rc + sw + 1)):
            if g[r][c] != 0:
                return False
    return True


def _paint_kind(g, kind, rr, rc, sh, sw, color, rng):
    if kind == "rect":
        for dr in range(sh):
            for dc in range(sw):
                g[rr + dr][rc + dc] = color
    elif kind == "cross":
        mr, mc = sh // 2, sw // 2
        for dc in range(sw):
            g[rr + mr][rc + dc] = color
        for dr in range(sh):
            g[rr + dr][rc + mc] = color
    elif kind == "L_shape":
        for dr in range(sh):
            g[rr + dr][rc] = color
        for dc in range(sw):
            g[rr + sh - 1][rc + dc] = color
    elif kind == "random_blob":
        for dr in range(sh):
            for dc in range(sw):
                if rng.random() < 0.6:
                    g[rr + dr][rc + dc] = color
        # Connectivity hack: pin a cross through the bbox center, then clear
        # stray cells that were randomly painted but not connected to it.
        mr, mc = sh // 2, sw // 2
        for dc in range(sw):
            g[rr + mr][rc + dc] = color
        for dr in range(sh):
            g[rr + dr][rc + mc] = color
        _clear_disconnected_blob_cells(g, rr, rc, sh, sw, color)
    elif kind == "hollow_ring":
        for dc in range(sw):
            g[rr][rc + dc] = color
            g[rr + sh - 1][rc + dc] = color
        for dr in range(sh):
            g[rr + dr][rc] = color
            g[rr + dr][rc + sw - 1] = color
    elif kind == "line_h":
        for dc in range(sw):
            g[rr][rc + dc] = color
    elif kind == "line_v":
        for dr in range(sh):
            g[rr + dr][rc] = color
    else:  # single_pixel
        g[rr][rc] = color


def _clear_disconnected_blob_cells(g, rr, rc, sh, sw, color):
    start = (rr + sh // 2, rc + sw // 2)
    stack = [start]
    seen = {start}
    while stack:
        cr, cc = stack.pop()
        for nr, nc in ((cr - 1, cc), (cr + 1, cc), (cr, cc - 1), (cr, cc + 1)):
            if rr <= nr < rr + sh and rc <= nc < rc + sw and (nr, nc) not in seen and g[nr][nc] == color:
                seen.add((nr, nc))
                stack.append((nr, nc))
    for r in range(rr, rr + sh):
        for c in range(rc, rc + sw):
            if g[r][c] == color and (r, c) not in seen:
                g[r][c] = 0


def _draw_from_degenerate(name, h, w, ctx, rng):
    """Edge-case where the count-objects signal collapses.

    single_object     — only one object → output is 1 × 1 cyan dot.
    touching_objects  — multiple objects placed adjacently so 4-conn
                         BFS merges them; rule sees fewer components.
    max_objects       — n=9 objects → output is 9 × 9.
    """
    palette = ctx.draw_distinct_colors("palette", n=9, exclude={0})
    g = full_grid(h, w, 0)
    if name == "single_object":
        for r in range(2, 5):
            for c in range(2, 5):
                g[r][c] = palette[0]
        return g
    if name == "touching_objects":
        # Two 3×3 rects sharing an edge — 4-connectivity merges them.
        for r in range(2, 5):
            for c in range(2, 5):
                g[r][c] = palette[0]
        for r in range(2, 5):
            for c in range(5, 8):
                g[r][c] = palette[1]
        return g
    if name == "max_objects":
        # 9 single-cell objects on a 3×3 layout pattern with gaps.
        anchors = [(2 + 3 * i, 2 + 3 * j) for i in range(3) for j in range(3)]
        for i, (r, c) in enumerate(anchors):
            if 0 <= r < h and 0 <= c < w:
                g[r][c] = palette[i % len(palette)]
        return g
    return g
