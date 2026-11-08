"""Generator for b10d1b6eb339.

Rule: two-column key rows map source colors to fill colors around
their source-cell bounding boxes.

Combinatorial axes (8): grid_h/w, mapping_count, palette_kind,
anchor_corner, asymmetry_force, palette_size, position_bias,
shape_variant.
Degenerates: no_keys, no_shapes, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b10d1b6eb339"
VERSION = "1.5.0"  # 1.5.0: source bodies may be disconnected bbox patterns, matching canonical
TASK_ID = "b10d1b6eb339"
SUMMARY = "Key rows map source colors to fill colors around each source color bbox."

INVARIANTS = [
    "key rows have nonzero source and fill colors in columns 0 and 1",
    "source-color cells outside the key define expanded bounding boxes",
    "each source color has one nonempty body set outside the key area",
    "source bodies may be disconnected, but their expanded bboxes do not overlap",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_keys", "no_shapes", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

SHAPES = [
    [(0, 0), (1, 0), (1, 1)],
    [(0, 1), (1, 0), (1, 1), (2, 1)],
    [(0, 0), (0, 1), (1, 1)],
]

AXES = {
    "grid_h":         {"type": "int", "default": "rng 11..22", "valid": "11..22"},
    "grid_w":         {"type": "int", "default": "rng 12..22", "valid": "12..22"},
    "mapping_count":  {"type": "int", "default": "rng 2..3", "valid": "1..4"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "rng 4..6", "valid": "2..8"},
    "position_bias":  {"type": "str", "default": "body_clear_of_key", "valid": "body_clear_of_key"},
    "shape_variant":  {"type": "str", "default": "rng", "valid": "rng"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    # Rule: legend rows (col0=source, col1=fill) -> for each, draw a fill-colored
    # halo around the source shape's bbox. v1.x hardcoded a 13x14 grid + fixed
    # anchors -> shape-locked in+out. The rule is size-agnostic; now vary grid
    # size and place each source shape (random polyomino) at a random body
    # position (cols >= 3 so it never creates a spurious col0&col1 legend row).
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 11, 14); w = ctx.draw_int("grid_w", 12, 15); mc = 2
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 16, 22); w = ctx.draw_int("grid_w", 16, 22); mc = 3
    else:
        h = ctx.draw_int("grid_h", 13, 20); w = ctx.draw_int("grid_w", 13, 20); mc = rng.randint(2, 3)
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 2 * mc)  # all distinct

    # Placement is the invariant, not a best-effort decoration.  Build on a fresh
    # key-only grid for each retry so one unlucky large polyomino cannot consume
    # all remaining halo-safe room and leave a later key with no source body.
    for attempt in range(18):
        g = full_grid(h, w, 0)
        for i in range(mc):
            g[i][0] = colors[2 * i]
            g[i][1] = colors[2 * i + 1]
        placed = []      # (r1, c1, r2, c2) shape bboxes, with halo margin
        ok = True
        for i in range(mc):
            source = colors[2 * i]
            if attempt >= 12:
                shape = SHAPES[0]
            else:
                shape = _body_pattern(rng, difficulty)
            sh = max(r for r, _ in shape) + 1
            body_top_min = min(h - sh, mc + 1)
            if not _place_body_shape(g, rng, shape, source, body_top_min, placed):
                if not _place_body_shape(g, rng, SHAPES[0], source, mc + 1, placed):
                    ok = False
                    break
        if ok:
            return g
    raise RuntimeError("could not place a source body for every legend key")


def _body_pattern(rng, difficulty):
    """Return cells for one source color body.

    The canonical examples often use repeated separated cells/stripes whose
    combined bbox is the signal; a single compact polyomino hides that by
    making connectedness look causal. Mix compact bodies with disconnected
    bbox-spanning patterns so the rule must attend to all cells of a source
    color, not to one component.
    """
    if rng.random() < 0.10:
        return _poly(rng, rng.randint(3, 6))
    if difficulty == "easy":
        bh, bw = rng.randint(4, 6), rng.randint(4, 6)
    elif difficulty == "hard":
        bh, bw = rng.randint(5, 8), rng.randint(5, 9)
    else:
        bh, bw = rng.randint(4, 7), rng.randint(4, 8)
    kind = rng.choice(["checker", "checker", "corners", "speckles"])
    cells = set()
    if kind == "checker":
        parity = rng.randint(0, 1)
        for r in range(bh):
            for c in range(bw):
                if (r + c) % 2 == parity:
                    cells.add((r, c))
    elif kind == "v_stripes":
        for c in range(0, bw, 2):
            for r in range(bh):
                cells.add((r, c))
    elif kind == "h_stripes":
        for r in range(0, bh, 2):
            for c in range(bw):
                cells.add((r, c))
    elif kind == "speckles":
        for r in range(bh):
            for c in range(bw):
                if rng.random() < 0.32:
                    cells.add((r, c))
    else:  # corners + a few interior witnesses
        cells.update({(0, 0), (0, bw - 1), (bh - 1, 0), (bh - 1, bw - 1)})
        for _ in range(rng.randint(1, max(2, (bh * bw) // 5))):
            cells.add((rng.randrange(bh), rng.randrange(bw)))
    cells.update({(0, 0), (bh - 1, bw - 1)})  # force full bbox span
    return sorted(cells)


def _place_body_shape(g, rng, shape, color, body_top_min, placed):
    h, w = len(g), len(g[0])
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    max_r0 = h - sh
    max_c0 = w - sw
    if max_r0 < body_top_min or max_c0 < 3:
        return False
    positions = [(r0, c0) for r0 in range(body_top_min, max_r0 + 1)
                 for c0 in range(3, max_c0 + 1)]
    rng.shuffle(positions)
    for r0, c0 in positions:
        r1, c1, r2, c2 = r0 - 1, c0 - 1, r0 + sh, c0 + sw   # incl halo
        if any(r1 <= p2 and p0 <= r2 and c1 <= p3 and p1 <= c2
               for p0, p1, p2, p3 in placed):
            continue
        if any(g[r0 + dr][c0 + dc] != 0 for dr, dc in shape):
            continue
        for dr, dc in shape:
            g[r0 + dr][c0 + dc] = color
        placed.append((r1, c1, r2, c2))
        return True
    return False


def _poly(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for r, c in cells]


def _build_palette(kind, rng):
    if kind == "warm":
        pool = [2, 3, 4, 6, 9]
    elif kind == "cool":
        pool = [1, 5, 7, 8]
    elif kind == "primary":
        pool = [1, 2, 3, 4]
    else:
        pool = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    pool = [c for c in pool if c != 0]
    rng.shuffle(pool)
    return pool


def _draw_from_degenerate(name, rng):
    g = full_grid(13, 14, 0)
    if name == "no_keys":
        for dr, dc in SHAPES[0]:
            g[4 + dr][5 + dc] = 2
        return g
    if name == "no_shapes":
        g[0][0] = 2; g[0][1] = 3
        g[1][0] = 4; g[1][1] = 5
        return g
    if name == "full_grid":
        for r in range(13):
            for c in range(14):
                g[r][c] = 2
        return g
    return g


def _same_color_components(grid, color, *, exclude_key_rows=0):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(exclude_key_rows, h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (exclude_key_rows <= nr < h and 0 <= nc < w
                            and (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(cells)
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors: list[str] = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    if any(v not in range(10) for row in grid for v in row):
        errors.append("grid values must be digits 0..9")
    key_rows = []
    for r, row in enumerate(grid):
        if row[0] != 0 and row[1] != 0:
            key_rows.append((r, row[0], row[1]))
        else:
            break
    expected = (2,) if difficulty == "easy" else ((3,) if difficulty == "hard" else (2, 3))
    if len(key_rows) not in expected:
        errors.append(f"expected {expected} consecutive legend rows, found {len(key_rows)}")
    key_colors = [v for _r, src, fill in key_rows for v in (src, fill)]
    if len(key_colors) != len(set(key_colors)):
        errors.append("legend source/fill colors must be distinct")
    body_min_row = len(key_rows) + 1
    halo_boxes = []
    for _r, src, _fill in key_rows:
        body_cells = [(r, c) for r in range(body_min_row, h) for c in range(3, w)
                      if grid[r][c] == src]
        stray = [(r, c) for r in range(len(key_rows), h) for c in range(w)
                 if grid[r][c] == src and (r < body_min_row or c < 3)]
        if stray:
            errors.append(f"source color {src} appears outside the body region")
        if not body_cells:
            errors.append(f"source color {src} must have at least one body cell")
            continue
        if len(body_cells) < 2:
            errors.append(f"source color {src} body is too small to teach bbox fill")
        rs = [r for r, _c in body_cells]; cs = [c for _r, c in body_cells]
        if min(rs) == max(rs) and min(cs) == max(cs):
            errors.append(f"source color {src} body bbox collapsed to one cell")
        halo_boxes.append((min(rs) - 1, min(cs) - 1, max(rs) + 1, max(cs) + 1))
    for i, a in enumerate(halo_boxes):
        for b in halo_boxes[i + 1:]:
            if a[0] <= b[2] and b[0] <= a[2] and a[1] <= b[3] and b[1] <= a[3]:
                errors.append("source body halo boxes must not overlap")
                return errors
    return errors
