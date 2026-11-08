"""Generator for arc_additional_puzzles_21_set6:M41 — stamp 2/4-blob template at each 6-9 anchor.

Rule: find largest connected blob of {2,4}-colored cells. Normalize
its cell-shape. Each cell with color in {6,7,8,9} is an anchor;
output stamps the shape at the anchor (using anchor's color).

Combinatorial axes: grid_h, grid_w, n_anchors, tpl_size, texture
(plain|decoy_blob|anchor_pair|clip).
Degenerates: no_anchors (output = BLANK grid, the template vanishes).
no_template / single_cell_template were dropped — both leave the
{2,4}-component list empty after the >1-cell filter, so the rule does
(map ... #f) and CRASHES.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "05b5a82ace36"
VERSION = "3.1.0"
TASK_ID = "05b5a82ace36"
SUMMARY = (
    "Largest {2,4}-colored blob is the template; every cell colored "
    "6-9 is an anchor. Output is a BLANK grid with the normalized "
    "template stamped at each anchor cell (bbox top-left on the "
    "anchor) in the anchor's color; out-of-bounds stamp cells clip. "
    "(Was: 5 fixed 3-4 cell templates always in the top-left corner, "
    "largest-blob selection never contested, no clipping, and two "
    "degenerates that CRASH the rule.)"
)

# Rivals: 'any 2/4 cells form the template' refuted by a strictly
# smaller {2,4} decoy blob the rule ignores. 'one stamp per anchor
# OBJECT' refuted by anchor_pair: a domino anchor is TWO cells, so
# two offset overlapping stamps. 'stamps always fit' refuted by clip
# boards. 'template survives' refuted by every demo (blank canvas).
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "the template is the unique LARGEST {2,4} component (>1 cell); any decoy is strictly smaller",
    ">=1 anchor cell in {6,7,8,9} (no-template boards CRASH the rule and are never generated)",
    "main-path stamps land fully in-bounds and pairwise disjoint",
]

DEGENERATE_TEXTURES = ("no_anchors",)
HELPFUL_TEXTURES = ("plain", "decoy_blob", "anchor_pair", "clip")

AXES = {
    "grid_h":    {"type": "int", "default": "rng 9..14", "valid": "8..18"},
    "grid_w":    {"type": "int", "default": "rng 11..16", "valid": "10..20"},
    "n_anchors": {"type": "int", "default": "rng 1..3", "valid": "1..4"},
    "tpl_size":  {"type": "int", "default": "rng 3..7", "valid": "3..8",
                  "doc": "Template cell count (mixed colors 2/4)."},
    "texture":   {"type": "str", "default": "rng helpful",
                  "valid": "plain|decoy_blob|anchor_pair|clip|no_anchors",
                  "doc": "decoy_blob: smaller {2,4} blob ignored; "
                         "anchor_pair: domino anchor = 2 offset stamps; "
                         "clip: one stamp partially out of bounds."},
}

_INT_AXES = {
    "grid_h": (8, 18),
    "grid_w": (10, 20),
    "n_anchors": (1, 4),
    "tpl_size": (3, 8),
}
_TEXTURES = HELPFUL_TEXTURES + DEGENERATE_TEXTURES


def _validate_overrides(overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for name, (low, high) in _INT_AXES.items():
        if name not in overrides:
            continue
        value = overrides[name]
        if type(value) is not int or not low <= value <= high:
            raise ValueError(f"{name} override must be an exact integer in {low}..{high}")
    if "texture" in overrides:
        value = overrides["texture"]
        if type(value) is not str or value not in _TEXTURES:
            raise ValueError(f"texture override must be one of {_TEXTURES}")
    if overrides.get("texture") == "no_anchors" and "n_anchors" in overrides:
        raise ValueError("texture='no_anchors' is incompatible with n_anchors override")


def _draw_int(ctx, overrides, name, sample_low, sample_high):
    """Use full declared bounds for an exact override, sampling bounds otherwise."""
    if name in overrides:
        low, high = _INT_AXES[name]
        return ctx.draw_int_strict(name, low, high)
    return ctx.draw_int(name, sample_low, sample_high)


def _grow(rng, k):
    cells = [(0, 0)]
    seen = {(0, 0)}
    while len(cells) < k:
        r, c = cells[rng.randrange(len(cells))]
        dr, dc = ((-1, 0), (1, 0), (0, -1), (0, 1))[rng.randrange(4)]
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc))
            seen.add((r + dr, c + dc))
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _stamp_free(g, taken, fr, fc, shape, h, w):
    """Stamp bbox-top-left at (fr,fc): all shape cells in-bounds + unreserved."""
    for r, c in shape:
        rr, cc = fr + r, fc + c
        if not (0 <= rr < h and 0 <= cc < w) or (rr, cc) in taken:
            return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if "texture" in overrides:
        texture = ctx.draw_choice("texture", _TEXTURES)
    else:
        texture = ctx.draw_choice(
            "texture", ("plain", "plain", "decoy_blob", "anchor_pair", "clip"))
    if difficulty == "easy":
        h = _draw_int(ctx, overrides, "grid_h", 9, 11)
        w = _draw_int(ctx, overrides, "grid_w", 11, 13)
        n_anchors = _draw_int(ctx, overrides, "n_anchors", 1, 2)
        tpl_size = _draw_int(ctx, overrides, "tpl_size", 3, 4)
    elif difficulty == "hard":
        h = _draw_int(ctx, overrides, "grid_h", 13, 14)
        w = _draw_int(ctx, overrides, "grid_w", 14, 16)
        n_anchors = _draw_int(ctx, overrides, "n_anchors", 2, 4)
        tpl_size = _draw_int(ctx, overrides, "tpl_size", 5, 7)
    else:
        h = _draw_int(ctx, overrides, "grid_h", 9, 14)
        w = _draw_int(ctx, overrides, "grid_w", 11, 16)
        n_anchors = _draw_int(ctx, overrides, "n_anchors", 1, 3)
        tpl_size = _draw_int(ctx, overrides, "tpl_size", 3, 7)
    rng = ctx.draw_rng("layout")

    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, rng, h, w, tpl_size)

    for _attempt in range(160):
        g = full_grid(h, w, 0)
        shape = _grow(rng, tpl_size)
        th = max(r for r, _ in shape) + 1
        tw = max(c for _, c in shape) + 1
        if th > h or tw > w:
            continue
        tr = rng.randint(0, h - th)
        tc = rng.randint(0, w - tw)
        for r, c in shape:
            g[tr + r][tc + c] = rng.choice((2, 2, 4, 4))
        # cells no anchor stamp may claim (stamps may overlap the
        # template visually — output is blank-based — but anchors
        # themselves must not land on occupied input cells, and a
        # {2,4} stamp-neighbor could merge with the template)
        blocked = {(tr + r + dr, tc + c + dc) for r, c in shape
                   for dr in (-1, 0, 1) for dc in (-1, 0, 1)}

        decoy_placed = texture != "decoy_blob"
        if texture == "decoy_blob" and tpl_size > 2:
            dshape = _grow(rng, rng.randint(2, tpl_size - 1))  # strictly smaller
            dh = max(r for r, _ in dshape) + 1
            dw = max(c for _, c in dshape) + 1
            for _try in range(80):
                dr0 = rng.randint(0, h - dh)
                dc0 = rng.randint(0, w - dw)
                spots = [(dr0 + r, dc0 + c) for r, c in dshape]
                if all((r, c) not in blocked and g[r][c] == 0 for r, c in spots):
                    for r, c in spots:
                        g[r][c] = rng.choice((2, 4))
                    blocked |= {(r + dr, c + dc) for r, c in spots
                                for dr in (-1, 0, 1) for dc in (-1, 0, 1)}
                    decoy_placed = True
                    break
        if not decoy_placed:
            continue

        taken = set()  # stamp footprints (keep output stamps disjoint)
        colors = [rng.choice((6, 7, 8, 9)) for _ in range(n_anchors)]
        placed = 0
        for ai, color in enumerate(colors):
            want_pair = texture == "anchor_pair" and ai == 0
            want_clip = texture == "clip" and ai == 0
            for _try in range(300):
                ar = rng.randint(0, h - 1)
                ac = rng.randint(0, w - 1)
                if g[ar][ac] != 0 or (ar, ac) in blocked:
                    continue
                cells = [(ar, ac)]
                if want_pair:
                    br, bc = ar, ac + 1
                    if not (bc < w and g[br][bc] == 0 and (br, bc) not in blocked):
                        continue
                    cells.append((br, bc))
                foot = [(r + sr, c + sc) for r, c in cells for sr, sc in shape]
                inb = [(r, c) for r, c in foot if 0 <= r < h and 0 <= c < w]
                if want_clip:
                    if len(inb) == len(foot) or not inb:
                        continue  # need PARTIAL clipping
                else:
                    if len(inb) != len(foot):
                        continue
                if any(p in taken for p in inb):
                    continue
                for r, c in cells:
                    g[r][c] = color
                taken |= set(inb)
                taken |= set(cells)  # anchors are also future stamp turf
                placed += 1
                break
        if placed == len(colors) and (texture != "decoy_blob" or _decoy_is_visible(g)):
            return g
    raise ValueError("could not realize stamp board")


def _draw_from_degenerate(name, rng, h, w, tpl_size):
    """no_anchors — template only. NOTE: the output is a BLANK grid
    (the rule rebuilds from empty-grid and has no anchors to stamp),
    not identity. no_template / single_cell_template were DROPPED:
    both crash the rule ((first '()) -> #f -> map over #f)."""
    g = full_grid(h, w, 0)
    shape = _grow(rng, tpl_size)
    th = max(r for r, _ in shape) + 1
    tw = max(c for _, c in shape) + 1
    tr = rng.randint(0, h - th)
    tc = rng.randint(0, w - tw)
    for r, c in shape:
        g[tr + r][tc + c] = rng.choice((2, 4))
    return g


def _components(grid, colors):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or grid[r][c] not in colors:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            comp = []
            while stack:
                rr, cc = stack.pop()
                comp.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] in colors):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(comp)
    return comps


def _normalize(cells):
    top = min(r for r, _ in cells)
    left = min(c for _, c in cells)
    return sorted((r - top, c - left) for r, c in cells)


def _stamp_output(grid, normalized):
    h, w = len(grid), len(grid[0])
    out = full_grid(h, w, 0)
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color not in {6, 7, 8, 9}:
                continue
            for dr, dc in normalized:
                rr, cc = r + dr, c + dc
                if 0 <= rr < h and 0 <= cc < w:
                    out[rr][cc] = color
    return out


def _decoy_is_visible(grid):
    """Require a decoy whose union-template rival changes a visible answer cell."""
    comps = [cells for cells in _components(grid, {2, 4}) if len(cells) > 1]
    if len(comps) < 2:
        return False
    comps.sort(key=len, reverse=True)
    if len(comps[0]) == len(comps[1]):
        return False
    official = _stamp_output(grid, _normalize(comps[0]))
    union = _stamp_output(grid, _normalize([cell for comp in comps for cell in comp]))
    return official != union


def self_check(grid, *, difficulty=None, meta=None):
    errs = []
    if type(grid) is not list or not grid or not all(type(row) is list and row for row in grid):
        return ["empty or malformed grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        errs.append("ragged grid")
        return errs
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["every ARC cell must be an exact integer in 0..9"]
    values = {v for row in grid for v in row}
    allowed = {0, 2, 4, 6, 7, 8, 9}
    extra = values - allowed
    if extra:
        errs.append(f"unexpected colors outside template/anchor palette: {sorted(extra)}")
    template_comps = [c for c in _components(grid, {2, 4}) if len(c) > 1]
    if not template_comps:
        errs.append("missing >1-cell {2,4} template component")
    else:
        sizes = sorted((len(c) for c in template_comps), reverse=True)
        if len(sizes) > 1 and sizes[0] == sizes[1]:
            errs.append(f"largest template component is not unique: sizes={sizes}")
    anchors = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v in {6, 7, 8, 9}]
    if not anchors:
        errs.append("default instance has no 6-9 anchor cells")
    return errs
