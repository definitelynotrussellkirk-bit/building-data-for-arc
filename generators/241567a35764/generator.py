"""Generator for arc_additional_puzzle_bank_volume21:H146.

Rule: a rotated and optionally flipped blue template is repeatedly
stamped in maroon along the marker-vector path.

Combinatorial axes (8): grid_h/w, palette_kind, rotation_control,
palette_size, position_bias, n_distinct_colors, repeat_path, texture.
Degenerates: no_template, no_rot_control, no_marker_pair.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "241567a35764"
VERSION = "2.2.0"  # Marker placement now guarantees two fully in-bounds transformed-template stamps; self_check verifies the output-dependent invariant.
TASK_ID = "241567a35764"
SUMMARY = (
    "0-bg grid (h~11-15, w~"
    "13-18) with: (a) ONE "
    "COLOR-1 (blue) "
    "TEMPLATE drawn from 6 "
    "asymmetric tetromino "
    "shapes at top-left "
    "position; (b) ONE "
    "ROTATION CONTROL cell "
    "in COLOR ∈ {2, 3, 4} "
    "on the BOTTOM BORDER "
    "encoding rotation; "
    "(c) optionally ONE "
    "COLOR-6 FLIP CONTROL "
    "adjacent (±2 cols) to "
    "the rotation control; "
    "(d) MARKER PAIR — "
    "COLOR-7 cell at (r7, "
    "c7) and COLOR-8 cell "
    "at (r8, c8) (interior, "
    "≥2-cell vector between "
    "them, allowing ≥2 in-"
    "bounds stamps). Rule "
    "(STAMP ROTATED+FLIPPED "
    "TEMPLATE IN MAROON "
    "ALONG 7→8 VECTOR): "
    "READ rotation control "
    "(determines k = 0/1/2 "
    "CW rotations or D4 "
    "code). READ optional "
    "FLIP-6 (toggle "
    "horizontal flip). "
    "APPLY transform to the "
    "BLUE TEMPLATE. COMPUTE "
    "delta = (r8 - r7, "
    "c8 - c7). STAMP the "
    "transformed template "
    "in COLOR-9 (maroon) "
    "at the 7-marker "
    "position, then at "
    "successive offsets "
    "(+delta) until off-"
    "grid. Net: blue "
    "template + rotation "
    "control → maroon "
    "stamps repeated along "
    "the 7→8 vector path."
)

# Rivals: 'no transform (verbatim stamp)' refuted by ≥2 demos where
# rotation control changes orientation. 'stamp once' refuted by ≥1
# demo with multiple stamps along the vector. 'use template color
# (1) for stamps' refuted by any demo (stamps are 9). 'stamp at
# template position' refuted by ≥1 demo (stamps along vector path).
# 4 demos with varied vectors + rotations cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "one blue template is present",
    "one rotation control is 2, 3, or 4",
    "optional color-6 flip control may appear",
    "markers 7 and 8 define a repeat vector with multiple in-bounds stamps",
]

PALETTE_KINDS = ("default", "rot_2", "rot_3", "rot_4")
DEGENERATE_TEXTURES = ("no_template", "no_rot_control", "no_marker_pair")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 11..15", "valid": "9..24"},
    "grid_w":         {"type": "int", "default": "rng 13..18", "valid": "11..24"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "rotation_control": {"type": "int", "default": "rng 2|3|4",
                         "valid": "2|3|4"},
    "palette_size":   {"type": "int", "default": "4", "valid": "4..5"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "n_distinct_colors": {"type": "int", "default": "4", "valid": "4..5"},
    "repeat_path":    {"type": "str", "default": "diagonal",
                       "valid": "diagonal"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _normalize_cells(cells):
    cells = list(cells)
    if not cells:
        return []
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return sorted((r - r0, c - c0) for r, c in cells)


def _rotate_cells_cw(cells):
    return _normalize_cells((c, -r) for r, c in _normalize_cells(cells))


def _flip_columns(cells):
    cells = _normalize_cells(cells)
    cmax = max(c for _, c in cells)
    return _normalize_cells((r, cmax - c) for r, c in cells)


def _transformed_offsets(cells, control, flip):
    result = _normalize_cells(cells)
    for _ in range({2: 0, 3: 1, 4: 2}[control]):
        result = _rotate_cells_cw(result)
    return _flip_columns(result) if flip else result


def _grid_transformed_offsets(grid):
    template = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 1
    ]
    controls = [
        color
        for color in (2, 3, 4)
        if any(value == color for row in grid for value in row)
    ]
    control = controls[0] if controls else 2
    flip = any(value == 6 for row in grid for value in row)
    return _transformed_offsets(template, control, flip)


def _fits(shape, anchor, h, w):
    ar, ac = anchor
    return all(0 <= ar + r < h and 0 <= ac + c < w for r, c in shape)


def _forward_stamp_count(grid):
    h, w = len(grid), len(grid[0])
    sevens = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 7]
    eights = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 8]
    if len(sevens) != 1 or len(eights) != 1:
        return 0
    shape = _grid_transformed_offsets(grid)
    if not shape:
        return 0
    (ar, ac), (r8, c8) = sevens[0], eights[0]
    dr, dc = r8 - ar, c8 - ac
    count = 0
    while _fits(shape, (ar, ac), h, w):
        count += 1
        ar += dr
        ac += dc
    return count


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 10, 12)
        w = ctx.draw_int("grid_w", 12, 14)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 16, 22)
        w = ctx.draw_int("grid_w", 18, 24)
    else:
        h = ctx.draw_int("grid_h", 12, 16)
        w = ctx.draw_int("grid_w", 14, 18)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    # Random template shape (3-5 cells), placed in top-left area.
    templates = [
        [(0, 0), (1, 0), (1, 1), (1, 2)],          # J-tet
        [(0, 0), (0, 1), (1, 0)],                  # L-tro
        [(0, 0), (0, 1), (0, 2), (1, 1)],          # T
        [(0, 0), (1, 0), (1, 1), (2, 1)],          # S
        [(0, 0), (0, 1), (1, 1), (1, 2)],          # Z
        [(0, 0), (0, 1), (0, 2), (1, 0)],          # J
    ]
    tmpl = rng.choice(templates)
    rs = [r for r, _ in tmpl]; cs = [c for _, c in tmpl]
    sh = max(rs) - min(rs) + 1; sw = max(cs) - min(cs) + 1
    # Place template at random top-left position in top half
    tr = rng.randint(0, max(0, h // 2 - sh))
    tc = rng.randint(0, max(0, w - sw - 1))
    paint_at(g, tr, tc, tmpl, 1)
    # Rotation control: place at random cell on bottom border
    rc_col = rng.randint(0, w - 1)
    g[h - 1][rc_col] = rng.choice([2, 3, 4])
    # Optional flip(6) control: place adjacent (within ±2 cols)
    if rng.choice([True, False]):
        for _ in range(20):
            fc_col = rc_col + rng.randint(-2, 2)
            if 0 <= fc_col < w and fc_col != rc_col and g[h - 1][fc_col] == 0:
                g[h - 1][fc_col] = 6
                break
    # Marker pair (7, 8) defining the repeat vector. The canonical rule
    # stamps the *transformed* template at 7 and then at 8, so marker validity
    # depends on the control-selected footprint, not only vector length.
    control = next(value for value in (2, 3, 4) if value in g[h - 1])
    flip = 6 in g[h - 1]
    shape = _transformed_offsets(tmpl, control, flip)
    anchors = [
        (r, c)
        for r in range(2, h - 2)
        for c in range(w)
        if g[r][c] == 0 and _fits(shape, (r, c), h, w)
    ]
    rng.shuffle(anchors)
    pair = None
    for r7, c7 in anchors:
        for r8, c8 in anchors:
            if (r7, c7) == (r8, c8):
                continue
            if abs(r8 - r7) < 2 and abs(c8 - c7) < 2:
                continue
            pair = ((r7, c7), (r8, c8))
            break
        if pair is not None:
            break
    if pair is None:
        raise ValueError("could not place a 7/8 pair supporting two transformed stamps")
    (r7, c7), (r8, c8) = pair
    g[r7][c7] = 7
    g[r8][c8] = 8
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the controls and at least two realizable canonical stamps."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    h = len(grid)
    msgs = []
    flat = [value for row in grid for value in row]
    if 1 not in flat:
        msgs.append("no blue(1) template")
    controls = [color for color in (2, 3, 4) if color in flat]
    if len(controls) != 1:
        msgs.append(f"need exactly one rotation-control color, got {controls}")
    elif sum(value in (2, 3, 4) for value in grid[h - 1]) != 1:
        msgs.append("rotation control must occur exactly once on the bottom row")
    if flat.count(6) > 1 or (6 in flat and 6 not in grid[h - 1]):
        msgs.append("optional flip control must occur at most once on the bottom row")
    sevens = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 7]
    eights = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 8]
    if len(sevens) != 1 or len(eights) != 1:
        msgs.append(f"need exactly one 7 and one 8, got {len(sevens)}/{len(eights)}")
    else:
        (r7, c7), (r8, c8) = sevens[0], eights[0]
        if abs(r8 - r7) < 2 and abs(c8 - c7) < 2:
            msgs.append("7->8 vector too short (<2) for repeated stamps")
        elif 1 in flat and len(controls) == 1 and _forward_stamp_count(grid) < 2:
            msgs.append("7->8 path must support at least two fully in-bounds transformed-template stamps")
    return msgs


def _draw_from_degenerate(name, rng):
    h, w = 13, 15
    g = full_grid(h, w, 0)
    if name == "no_template":
        # rotation control + markers but no blue template to stamp
        g[h - 1][0] = 3
        g[4][1] = 7
        g[6][4] = 8
        return g
    if name == "no_rot_control":
        # template + markers but no rotation selector
        paint_at(g, 0, 1, [(0, 0), (1, 0), (1, 1), (1, 2)], 1)
        g[4][1] = 7
        g[6][4] = 8
        return g
    if name == "no_marker_pair":
        # template + control but only one of {7, 8} → no vector defined
        paint_at(g, 0, 1, [(0, 0), (1, 0), (1, 1), (1, 2)], 1)
        g[h - 1][0] = 4
        g[4][1] = 7
        return g
    return g
