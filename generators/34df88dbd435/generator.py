"""Generator for puzzle b4dc03b8.

Rule: for each non-bg object: bbox h > w → 2 (tall); w > h → 8 (wide);
h == w → 4 (square).

Combinatorial axes (8): grid_h/w, n_tall, n_wide, n_square,
shape_kind (rect/L/cross/blob/line), aspect_ratio_strength,
input_palette_mode, placement.
Degenerates: all_tall, all_wide, all_square.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob, bbox_of

GENERATOR_ID = "34df88dbd435"
VERSION = "2.0.0"
TASK_ID = "34df88dbd435"
SUMMARY = (
    "0-bg grid with several connected objects of varied aspect ratios. "
    "At least one TALL (bbox h > w), one WIDE (bbox w > h), and one "
    "SQUARE (bbox h == w). Objects in any non-{0, 2, 4, 8} color "
    "(avoid output colors). Objects separated by ≥1-cell buffer. "
    "Rule: for each object, compute bbox h and w. If h > w → recolor "
    "to 2 (tall). If w > h → recolor to 8 (wide). If h == w → "
    "recolor to 4 (square). Output preserves grid shape."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "≥1 tall object (bbox h > w)",
    "≥1 wide object (bbox w > h)",
    "≥1 square object (bbox h == w)",
    "objects don't touch (≥1-cell buffer)",
    "object colors are NOT in {0, 2, 4, 8} (avoid output colors)",
]

SHAPE_KINDS = ("rect", "L_shape", "cross", "blob", "line")
PALETTE_MODES = ("same_color", "all_distinct", "per_aspect")
PLACEMENTS = ("random", "corners", "row", "column", "grid")
DEGENERATE_TEXTURES = ("all_tall", "all_wide", "all_square")
HELPFUL_TEXTURES = SHAPE_KINDS

AXES = {
    "grid_h":             {"type": "int", "default": "rng 8..14", "valid": "6..18"},
    "grid_w":             {"type": "int", "default": "rng 8..14", "valid": "6..18"},
    "n_tall":             {"type": "int", "default": "rng 1..2", "valid": "0..4"},
    "n_wide":             {"type": "int", "default": "rng 1..2", "valid": "0..4"},
    "n_square":           {"type": "int", "default": "rng 1..2", "valid": "0..4"},
    "shape_kind":         {"type": "str", "default": "rng helpful",
                           "valid": "|".join(SHAPE_KINDS)},
    "input_palette_mode": {"type": "str", "default": "rng helpful",
                           "valid": "|".join(PALETTE_MODES)},
    "placement":          {"type": "str", "default": "rng helpful",
                           "valid": "|".join(PLACEMENTS)},
    "texture":            {"type": "str", "default": "alias for shape_kind",
                           "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi, n_lo, n_hi = 8, 11, 1, 1
    elif difficulty == "hard":
        h_lo, h_hi, n_lo, n_hi = 13, 18, 2, 2
    else:
        h_lo, h_hi, n_lo, n_hi = 8, 18, 1, 2
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    n_t = int(overrides.get("n_tall", ctx.draw_int("n_tall", n_lo, n_hi)))
    n_w = int(overrides.get("n_wide", ctx.draw_int("n_wide", n_lo, n_hi)))
    n_s = int(overrides.get("n_square", ctx.draw_int("n_square", n_lo, n_hi)))
    palette_mode = overrides.get("input_palette_mode",
                                 ctx.draw_choice("input_palette_mode", list(PALETTE_MODES)))
    palette = list(ctx.draw_distinct_colors("palette", n=6, exclude={0, 2, 4, 8}))
    g = full_grid(h, w, 0)
    used: set = set(); bboxes: list = []
    plan = ([("tall", n_t)] + [("wide", n_w)] + [("square", n_s)])
    color_idx = 0
    for orient, count in plan:
        for _ in range(count):
            for _try in range(15):
                size = rng.randint(3, 7)
                blob = _make_oriented(rng, h, w, used, size, orient)
                if blob is None: continue
                bb = bbox_of(blob)
                if any(_bbox_close(bb, ob) for ob in bboxes): continue
                if palette_mode == "same_color":
                    color = palette[0]
                elif palette_mode == "per_aspect":
                    color = palette[{"tall": 0, "wide": 1, "square": 2}.get(orient, 0)
                                    % len(palette)]
                else:
                    color = palette[color_idx % len(palette)]; color_idx += 1
                used |= blob; bboxes.append(bb)
                for r, c in blob:
                    g[r][c] = color
                break
    present = set(_aspect_from_bbox(bb) for bb in bboxes)
    fallback_shapes = {
        "tall": [(0, 0), (1, 0), (2, 0)],
        "wide": [(0, 0), (0, 1), (0, 2)],
        "square": [(0, 0), (0, 1), (1, 0), (1, 1)],
    }
    for orient in ("tall", "wide", "square"):
        if orient in present:
            continue
        color = palette[color_idx % len(palette)]
        color_idx += 1
        placed = _place_shape_with_buffer(g, fallback_shapes[orient], color, rng, bboxes)
        if placed is not None:
            bboxes.append(placed)
            present.add(orient)
    if present != {"tall", "wide", "square"}:
        # Last-resort rare small-grid fallback: the task is about aspect-ratio
        # classification, so a clean three-object curriculum instance is better
        # than a default sample that silently omits one branch.
        g = full_grid(h, w, 0)
        layouts = [
            ([(0, 0), (1, 0), (2, 0)], 1, 1, palette[0]),
            ([(0, 0), (0, 1), (0, 2)], 1, max(4, w - 4), palette[1 % len(palette)]),
            ([(0, 0), (0, 1), (1, 0), (1, 1)], max(5, h - 3), max(2, w // 2 - 1), palette[2 % len(palette)]),
        ]
        for cells, r0, c0, color in layouts:
            for dr, dc in cells:
                r = min(h - 1, r0 + dr)
                c = min(w - 1, c0 + dc)
                g[r][c] = color
    return g


def _aspect_from_bbox(bb):
    bh = bb[2] - bb[0] + 1
    bw = bb[3] - bb[1] + 1
    return "tall" if bh > bw else "wide" if bw > bh else "square"


def _place_shape_with_buffer(g, cells, color, rng, bboxes):
    h, w = len(g), len(g[0])
    sh = max(r for r, _ in cells) + 1
    sw = max(c for _, c in cells) + 1
    for _ in range(250):
        r0 = rng.randint(1, max(1, h - sh - 1))
        c0 = rng.randint(1, max(1, w - sw - 1))
        abs_cells = [(r0 + r, c0 + c) for r, c in cells]
        if any(g[r][c] != 0 for r, c in abs_cells):
            continue
        bb = (r0, c0, r0 + sh - 1, c0 + sw - 1)
        if any(_bbox_close(bb, ob) for ob in bboxes):
            continue
        # Check the actual cell moat too because non-rectangular blobs can sit
        # near an expanded bbox without occupying the bbox corners.
        ok = True
        aset = set(abs_cells)
        for r, c in abs_cells:
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    nr, nc = r + dr, c + dc
                    if ((nr, nc) not in aset and 0 <= nr < h and 0 <= nc < w and
                            g[nr][nc] != 0):
                        ok = False
                        break
                if not ok:
                    break
            if not ok:
                break
        if not ok:
            continue
        for r, c in abs_cells:
            g[r][c] = color
        return bb
    return None


def _bbox_close(a, b, pad=1):
    """True if inclusive bboxes overlap after expanding by `pad`.

    The public invariant promises a one-cell buffer between objects. The blob
    helper prevents 4-neighbour contact, but diagonal contact can still leak
    through unless accepted bboxes are separated by a full Chebyshev moat.
    """
    r1a, c1a, r2a, c2a = a
    r1b, c1b, r2b, c2b = b
    return not (r2a + pad < r1b or r2b + pad < r1a or
                c2a + pad < c1b or c2b + pad < c1a)


def _components_nonzero(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and
                            (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append((color, cells))
    return comps


def self_check(grid, *, difficulty=None, meta=None):
    errs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    bad_colors = sorted({v for row in grid for v in row if v in {2, 4, 8}})
    if bad_colors:
        errs.append(f"input objects must avoid output colors {{2,4,8}}, got {bad_colors}")
    comps = _components_nonzero(grid)
    aspects = []
    bboxes = []
    for _color, cells in comps:
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        bb = (min(rs), min(cs), max(rs), max(cs))
        bboxes.append(bb)
        bh = bb[2] - bb[0] + 1
        bw = bb[3] - bb[1] + 1
        aspects.append("tall" if bh > bw else "wide" if bw > bh else "square")
    for need in ("tall", "wide", "square"):
        if need not in aspects:
            errs.append(f"missing {need} object; aspects={aspects}")
    for i, bb in enumerate(bboxes):
        for ob in bboxes[i + 1:]:
            if _bbox_close(bb, ob):
                errs.append("objects lack the declared one-cell bbox buffer")
                return errs
    return errs


def _make_oriented(rng, h, w, used, target_size, orient):
    for _ in range(15):
        blob = grow_blob(rng, h, w, used, target_size)
        if blob is None: return None
        bb = bbox_of(blob)
        bh = bb[2] - bb[0] + 1; bw = bb[3] - bb[1] + 1
        if orient == "tall" and bh > bw: return blob
        if orient == "wide" and bw > bh: return blob
        if orient == "square" and bh == bw: return blob
    return None


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    color = rng.choice([1, 3, 5, 6, 7, 9])
    if name == "all_tall":
        # 3 tall objects.
        for i, c0 in enumerate([2, w // 2, w - 4]):
            for r in range(2, 6):
                if 0 <= c0 < w:
                    g[r][c0] = color
        return g
    if name == "all_wide":
        for i, r0 in enumerate([2, h // 2, h - 3]):
            for c in range(2, 7):
                if 0 <= r0 < h and c < w:
                    g[r0][c] = color
        return g
    if name == "all_square":
        for r0, c0 in [(2, 2), (2, w - 5), (h - 5, 2)]:
            for r in range(r0, r0 + 3):
                for c in range(c0, c0 + 3):
                    if 0 <= r < h and 0 <= c < w:
                        g[r][c] = color
        return g
    return g
