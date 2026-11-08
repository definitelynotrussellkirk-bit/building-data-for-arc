"""Generator for 7a0930447310.

Rule: non-default center colors appearing in row- or column-aligned tile
centers are connected by painting the zero gutter cells between them.

The canonical task is a lattice of many small framed tiles, not one large
frame.  Normal instances therefore build repeated framed tiles with a
frequent frame color, a frequent default center color, and two or three
special center colors whose repeated objects share rows/columns.
Degenerates: no_frame, no_specials, full_grid.
"""
from __future__ import annotations

from collections import Counter, deque

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "7a0930447310"
VERSION = "2.1.0"  # canonical tiled lattice; fixes one-frame low-object-count drift
TASK_ID = "7a0930447310"
SUMMARY = (
    "0-bg lattice of many same-size framed tiles. A frame color is the most "
    "frequent nonzero color; default centers are the most frequent non-frame "
    "color. Two or three special center colors appear in multiple tile centers "
    "sharing a row or column; the rule paints zero gutter cells connecting "
    "each same-color aligned pair."
)

INVARIANTS = [
    "background is 0",
    "many disconnected framed tiles share one most-frequent frame color",
    "one default center color is the most frequent non-frame color",
    "each special center color has at least two row- or column-aligned objects",
]

SPECIAL_KINDS = ("s2", "s3")
DEGENERATE_TEXTURES = ("no_frame", "no_specials", "full_grid")
HELPFUL_TEXTURES = SPECIAL_KINDS

AXES = {
    "tile_size":      {"type": "int", "default": "rng 3|4", "valid": "3|4"},
    "gap":            {"type": "int", "default": "rng 1..3", "valid": "1..3"},
    "tile_rows":      {"type": "int", "default": "rng 4..5", "valid": "3..6"},
    "tile_cols":      {"type": "int", "default": "rng 4..6", "valid": "3..7"},
    "special_count":  {"type": "choice", "default": "rng helpful", "valid": "2|3"},
    "palette_size":   {"type": "int", "default": "5", "valid": "5"},
    "position_bias":  {"type": "str", "default": "lattice", "valid": "lattice"},
    "n_distinct_colors": {"type": "int", "default": "5", "valid": "5"},
    "texture":        {"type": "str", "default": "alias for special_count",
                       "valid": "s2|s3|no_frame|no_specials|full_grid"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    tx = overrides.get("texture")
    if tx in SPECIAL_KINDS:
        special_count = int(tx[1])
    elif difficulty == "easy":
        special_count = 2
    elif difficulty == "hard":
        special_count = 3
    else:
        special_count = ctx.draw_choice("special_count", [2, 3])

    tile, gap, tile_rows, tile_cols = _choose_lattice(ctx, rng, difficulty)
    frame, default, s1, s2, s3 = ctx.draw_distinct_colors("colors", n=5, exclude={0})
    specials = [s1, s2, s3][:special_count]

    margin = 1
    h = 2 * margin + tile_rows * tile + (tile_rows - 1) * gap
    w = 2 * margin + tile_cols * tile + (tile_cols - 1) * gap
    g = full_grid(h, w, 0)

    for tr in range(tile_rows):
        for tc in range(tile_cols):
            _paint_tile(g, tr, tc, tile, gap, margin, frame, default)

    used_slots: set[tuple[int, int]] = set()
    for idx, color in enumerate(specials):
        prefer_horizontal = None
        if idx == 0:
            prefer_horizontal = True
        elif idx == 1:
            prefer_horizontal = False
        slots = _choose_aligned_slots(rng, tile_rows, tile_cols, used_slots,
                                      prefer_horizontal=prefer_horizontal)
        used_slots.update(slots)
        for tr, tc in slots:
            _paint_tile_center(g, tr, tc, tile, gap, margin, color)
    return g


def _choose_lattice(ctx, rng, difficulty):
    if difficulty == "easy":
        tile = ctx.draw_choice("tile_size", [3])
        gap = ctx.draw_int("gap", 1, 2)
        row_range, col_range = (4, 4), (4, 5)
    elif difficulty == "hard":
        tile = ctx.draw_choice("tile_size", [3, 4])
        gap = ctx.draw_int("gap", 1, 2 if tile == 4 else 3)
        row_range, col_range = (5, 6), (5, 6)
    else:
        tile = ctx.draw_choice("tile_size", [3, 4])
        gap = ctx.draw_int("gap", 1, 2 if tile == 4 else 3)
        row_range, col_range = (4, 5), (4, 6)

    candidates = []
    for rows in range(row_range[0], row_range[1] + 1):
        for cols in range(col_range[0], col_range[1] + 1):
            h = 2 + rows * tile + (rows - 1) * gap
            w = 2 + cols * tile + (cols - 1) * gap
            if h <= 30 and w <= 30:
                candidates.append((rows, cols))
    rows, cols = rng.choice(candidates)

    # Optional overrides are accepted only when the resulting lattice remains ARC-sized.
    if overrides_rows := ctx.overrides.get("tile_rows"):
        rows = int(overrides_rows)
    if overrides_cols := ctx.overrides.get("tile_cols"):
        cols = int(overrides_cols)
    h = 2 + rows * tile + (rows - 1) * gap
    w = 2 + cols * tile + (cols - 1) * gap
    if rows < 3 or cols < 3 or h > 30 or w > 30:
        raise ValueError(f"lattice {rows}x{cols} of {tile}-tiles/gap {gap} does not fit")
    return tile, gap, rows, cols


def _tile_origin(tr, tc, tile, gap, margin):
    top = margin + tr * (tile + gap)
    left = margin + tc * (tile + gap)
    return top, left


def _paint_tile(g, tr, tc, tile, gap, margin, frame, center):
    top, left = _tile_origin(tr, tc, tile, gap, margin)
    draw_frame(g, top, left, top + tile - 1, left + tile - 1, frame)
    _paint_tile_center(g, tr, tc, tile, gap, margin, center)


def _paint_tile_center(g, tr, tc, tile, gap, margin, color):
    top, left = _tile_origin(tr, tc, tile, gap, margin)
    for r in range(top + 1, top + tile - 1):
        for c in range(left + 1, left + tile - 1):
            g[r][c] = color


def _choose_aligned_slots(rng, tile_rows, tile_cols, used, *, prefer_horizontal=None):
    for _ in range(200):
        horizontal = rng.random() < 0.5 if prefer_horizontal is None else prefer_horizontal
        count = 3 if rng.random() < 0.35 else 2
        if horizontal and tile_cols >= 2:
            tr = rng.randrange(tile_rows)
            cols = sorted(rng.sample(range(tile_cols), min(count, tile_cols)))
            slots = [(tr, tc) for tc in cols]
        elif tile_rows >= 2:
            tc = rng.randrange(tile_cols)
            rows = sorted(rng.sample(range(tile_rows), min(count, tile_rows)))
            slots = [(tr, tc) for tr in rows]
        else:
            continue
        if len(slots) >= 2 and all(slot not in used for slot in slots):
            return slots

    for tr in range(tile_rows):
        free = [(tr, tc) for tc in range(tile_cols) if (tr, tc) not in used]
        if len(free) >= 2:
            return free[:2]
    for tc in range(tile_cols):
        free = [(tr, tc) for tr in range(tile_rows) if (tr, tc) not in used]
        if len(free) >= 2:
            return free[:2]
    raise ValueError("could not choose aligned special tile centers")


def _draw_from_degenerate(name, rng):
    g = full_grid(13, 13, 0)
    if name == "no_frame":
        g[3][3] = 4
        return g
    if name == "no_specials":
        draw_frame(g, 1, 1, 11, 11, 3)
        return g
    if name == "full_grid":
        for r in range(13):
            for c in range(13):
                g[r][c] = 3
        return g
    return g


def _components4(grid, color):
    h, w = len(grid), len(grid[0]) if grid else 0
    seen = [[False] * w for _ in range(h)]
    comps = []
    for r in range(h):
        for c in range(w):
            if seen[r][c] or grid[r][c] != color:
                continue
            seen[r][c] = True
            q = deque([(r, c)])
            cells = []
            while q:
                cr, cc = q.popleft()
                cells.append((cr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = cr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and not seen[nr][nc] and grid[nr][nc] == color:
                        seen[nr][nc] = True
                        q.append((nr, nc))
            comps.append(cells)
    return comps


def _bbox(cells):
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    return min(rs), min(cs), max(rs), max(cs)


def self_check(grid, *, difficulty=None, meta=None):
    """Executable default-instance invariants for the canonical tiled lattice."""
    errs = []
    if not grid or not isinstance(grid, list) or not all(isinstance(row, list) for row in grid):
        return ["grid is not a nonempty list-of-lists"]
    h, w = len(grid), len(grid[0])
    if not (1 <= h <= 30 and 1 <= w <= 30) or any(len(row) != w for row in grid):
        return [f"grid is not rectangular ARC-sized ({h}x{w})"]
    bad_vals = sorted({v for row in grid for v in row if not isinstance(v, int) or not (0 <= v <= 9)})
    if bad_vals:
        errs.append(f"non-ARC color values: {bad_vals}")
    if not any(v == 0 for row in grid for v in row):
        errs.append("no zero background/gutters found")

    nonzero = [v for row in grid for v in row if v != 0]
    if len(set(nonzero)) < 4:
        errs.append("expected frame/default plus at least two special colors")
        return errs
    counts = Counter(nonzero)
    frame = counts.most_common(1)[0][0]
    frame_comps = _components4(grid, frame)
    if len(frame_comps) < 12:
        errs.append(f"expected many disconnected frame objects, found {len(frame_comps)}")
    frame_sizes = Counter((max(r for r, _ in comp) - min(r for r, _ in comp) + 1,
                           max(c for _, c in comp) - min(c for _, c in comp) + 1)
                          for comp in frame_comps)
    if frame_sizes:
        (fh, fw), n = frame_sizes.most_common(1)[0]
        if (fh, fw) not in ((3, 3), (4, 4)) or n * 2 < len(frame_comps):
            errs.append(f"frame components are not mostly 3x3/4x4 tile frames: {dict(frame_sizes)}")

    center_counts = Counter(v for row in grid for v in row if v not in (0, frame))
    if not center_counts:
        errs.append("no non-frame center colors found")
        return errs
    default = center_counts.most_common(1)[0][0]
    specials = [c for c in center_counts if c != default]
    if len(specials) < 2:
        errs.append(f"expected at least two special colors, found {specials}")

    aligned_specials = 0
    for color in specials:
        comps = _components4(grid, color)
        bboxes = [_bbox(comp) for comp in comps]
        has_aligned_pair = False
        for i, b1 in enumerate(bboxes):
            for b2 in bboxes[i + 1:]:
                same_rows = b1[0] == b2[0] and b1[2] == b2[2]
                same_cols = b1[1] == b2[1] and b1[3] == b2[3]
                if same_rows or same_cols:
                    has_aligned_pair = True
        if has_aligned_pair:
            aligned_specials += 1
        else:
            errs.append(f"special color {color} has no row/column-aligned pair")
    if aligned_specials < len(specials):
        errs.append(f"only {aligned_specials}/{len(specials)} special colors are aligned")
    return errs
