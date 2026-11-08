"""Sort monochromatic 4-components by (left, top); stack RAW bbox crops.

Two fifths of default draws retain the canonical 10x10/three-shape morphology in
EVERY difficulty band. The remaining draws expose cropping, centering, color-
grouping, connectivity and ordering shortcuts. No reference labels are sampled
or embedded here. The unchanged Racket authority supplies production labels.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = TASK_ID = "f99263121e8a"
VERSION = "4.1.0"
RULE_HASH = "e2a77f9b1289"
SUMMARY = (
    "Zero background; 2-6 monochromatic 4-connected components. Sort by leftmost "
    "column then top row, take raw input bbox crops (including neighboring colors), "
    "and stack with one blank row and floor-centered horizontal padding. "
    "Two fifths of default draws are canonical-like three-object 10x10 scenes; other "
    "draws include touching crops, repeated colors, diagonal-only contact, tied "
    "left edges and wide/narrow crops. Inputs and outputs remain within 30x30."
)
INVARIANTS = [
    "background is 0",
    "2..6 monochromatic 4-connected components",
    "raw bbox crops, sorted by (leftmost column, top row)",
    "one blank row between crops; floor-centered horizontal alignment",
    "input and stacked output both fit 30x30",
]
HELPFUL_TEXTURES = (
    "canonical", "scattered", "crop_overlap", "shared_color", "wide_narrow",
    "equal_leftmosts", "diagonal_contact",
)
# Any five consecutive DEFAULT draws, with a fixed seed and difficulty, contain
# all three decisive contrasts plus two canonical-like examples. This is a
# coverage guarantee against named rivals, not a proof of unique inference.
EXAMPLES_NEEDED = 5
_SCHEDULE = ("canonical", "crop_overlap", "canonical", "wide_narrow", "diagonal_contact")
SCHEDULE_PROFILES = ("canonical", "crop_overlap", "wide_narrow", "diagonal_contact")


def schedule_profile(seed, sample_index, difficulty=None):
    return _SCHEDULE[(seed + sample_index) % len(_SCHEDULE)]


# Equal left edges are LAWFUL: the Racket comparator explicitly breaks ties by top.
DEGENERATE_TEXTURES = ("no_components", "single_component")
AXES = {
    "grid_h": {"type": "int", "default": "10 canonical; 10-22 otherwise", "valid": "8..30"},
    "grid_w": {"type": "int", "default": "10 canonical; 10-22 otherwise", "valid": "9..30"},
    "n_components": {"type": "int", "default": "3 canonical; 2-6 otherwise", "valid": "2..6"},
    "texture": {"type": "str", "default": "five-demo schedule; 2/5 canonical", "valid": "|".join(HELPFUL_TEXTURES)},
}
_CARD = ((1, 0), (-1, 0), (0, 1), (0, -1))
_L3 = ((0, 0), (1, 0), (1, 1))
_L5 = ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2))
_S4 = ((0, 0), (0, 1), (1, 1), (1, 2))
_T4 = ((0, 0), (0, 1), (0, 2), (1, 1))
_BANK = (_L3, _L5, _S4, _T4)


def _bbox(cells):
    return (min(r for r, c in cells), min(c for r, c in cells),
            max(r for r, c in cells), max(c for r, c in cells))


def _components(grid, *, connectivity=4, multicolor=False):
    seen, out = set(), []
    h, w = len(grid), len(grid[0])
    steps = _CARD if connectivity == 4 else _CARD + ((-1,-1),(-1,1),(1,-1),(1,1))
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            pending, cells = [(r, c)], []
            seen.add((r, c))
            while pending:
                rr, cc = pending.pop()
                cells.append((rr, cc))
                for dr, dc in steps:
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] != 0
                            and (multicolor or grid[nr][nc] == color)):
                        seen.add((nr, nc))
                        pending.append((nr, nc))
            out.append((color, cells))
    return out


def _components_same_color(grid):
    """Keep the predecessor's analysis helper compatible."""
    return _components(grid)


def _rand_poly(rng, size):
    """A connected polyomino with height <=4 and width <=5."""
    cells = {(1, 2)}
    while len(cells) < size:
        options = sorted({(r+dr, c+dc) for r,c in cells for dr,dc in _CARD
                          if 0 <= r+dr < 4 and 0 <= c+dc < 5
                          and (r+dr, c+dc) not in cells})
        cells.add(rng.choice(options))
    r0, c0, _, _ = _bbox(cells)
    return tuple(sorted((r-r0, c-c0) for r,c in cells))


def _free(grid, r, c, shape, *, isolated):
    h, w = len(grid), len(grid[0])
    _, _, rmax, cmax = _bbox(shape)
    if r < 0 or c < 0 or r+rmax >= h or c+cmax >= w:
        return False
    if isolated:
        return not any(grid[rr][cc] for rr in range(max(0,r-1), min(h,r+rmax+2))
                       for cc in range(max(0,c-1), min(w,c+cmax+2)))
    return not any(grid[r+dr][c+dc] for dr,dc in shape)


def _paint(grid, shape, r, c, color):
    for dr, dc in shape:
        grid[r+dr][c+dc] = color


def _draw_int(ctx, name, low, high, default_low, default_high):
    # Explicit overrides use the FULL advertised range, even in easy/hard bands.
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int(name, low, high)
    return ctx.draw_int(name, default_low, default_high)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unsupported override(s): {', '.join(sorted(unknown))}")
    for name in ("grid_h", "grid_w", "n_components"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise ValueError(f"override {name} must be an integer, not {type(value).__name__}")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    requested = overrides.get("texture")
    if requested in DEGENERATE_TEXTURES:
        # Explicit negative fixtures, NOT values in AXES['texture'].valid.
        h = _draw_int(ctx, "grid_h", 8, 30, 10, 10)
        w = _draw_int(ctx, "grid_w", 9, 30, 10, 10)
        grid = full_grid(h, w, 0)
        if requested == "single_component":
            _paint(grid, _L3, 2, 2, 4)
        return grid
    texture = ctx.draw_choice(
        "texture", HELPFUL_TEXTURES if requested is not None
        else (schedule_profile(seed, sample_index, difficulty),))
    if texture == "canonical":
        dh = dw = (10, 10)
        dn = (3, 3)
    elif difficulty == "easy":
        dh = dw = (10, 12)
        dn = (2, 3)
    elif difficulty == "hard":
        dh, dw, dn = (15, 22), (16, 22), (4, 6)
    else:
        dh, dw, dn = (12, 16), (13, 17), (3, 5)
    h = _draw_int(ctx, "grid_h", 8, 30, *dh)
    w = _draw_int(ctx, "grid_w", 9, 30, *dw)
    n = _draw_int(ctx, "n_components", 2, 6, *dn)
    rng = ctx.draw_rng("layout")
    colors = rng.sample(list(range(1, 10)), n)
    if texture in ("shared_color", "diagonal_contact"):
        colors[1] = colors[0]

    for attempt in range(160):
        grid = full_grid(h, w, 0)
        compact = n >= 5 and min(h, w) < 12
        if texture == "canonical":
            shapes = ([rng.choice((_L3,_T4)), _L5, _S4] if n == 3 else
                      [_L3 if compact else rng.choice(_BANK) for _ in range(n)])
            rng.shuffle(shapes)
        else:
            shapes = [_rand_poly(rng, rng.randint(1, 4 if compact else 9)) for _ in range(n)]
        placed, lefts, reserved = 0, set(), None
        if texture in ("crop_overlap", "wide_narrow", "equal_leftmosts", "diagonal_contact"):
            if texture == "crop_overlap":
                pair = ((_S4, 0, 0), (_T4, 0, 2))
            elif texture == "wide_narrow":
                pair = ((tuple((0,c) for c in range(5)), 0, 0),
                        (tuple((r,0) for r in range(3)), 2, 1))
            elif texture == "equal_leftmosts":
                pair = ((_L3, 0, 0), (_T4, 3, 0))
            else:
                pair = ((((0,0),), 0, 0), (((0,0),), 1, 1))
            ph = max(dr + max(r for r,c in s) + 1 for s,dr,dc in pair)
            pw = max(dc + max(c for r,c in s) + 1 for s,dr,dc in pair)
            r0, c0 = rng.randint(0, h-ph), rng.randint(0, w-pw)
            for k, (shape,dr,dc) in enumerate(pair):
                _paint(grid, shape, r0+dr, c0+dc, colors[k])
                lefts.add(c0+dc)
            reserved = (r0, c0, r0+ph-1, c0+pw-1)
            placed = 2
        for k in range(placed, n):
            shape = shapes[k]
            _, _, sr, sc = _bbox(shape)
            for _ in range(100):
                r, c = rng.randint(0,h-sr-1), rng.randint(0,w-sc-1)
                if texture == "canonical" and c in lefts:
                    continue
                # Preserve the diagnostic pair while varying its position, colors
                # and the other objects. No copying of a canonical input.
                if reserved:
                    ar, ac, br, bc = reserved
                    if r <= br+1 and r+sr >= ar-1 and c <= bc+1 and c+sc >= ac-1:
                        continue
                if not _free(grid, r, c, shape, isolated=texture != "scattered"):
                    continue
                _paint(grid, shape, r, c, colors[k])
                lefts.add(c)
                placed += 1
                break
            else:
                break
        if placed == n and not self_check(grid):
            return grid
    raise ValueError(f"could not place exactly {n} components in {h}x{w} for texture={texture}; no partial grid returned")


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid is empty or not a row sequence"]
    if any(not isinstance(row, (list, tuple)) or not row for row in grid):
        return ["grid contains an empty or non-sequence row"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["grid is ragged"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["grid cells must be integers in 0..9 (not booleans)"]
    errors = []
    if len(grid) > 30 or w > 30:
        errors.append("input exceeds 30x30")
    if not any(0 in row for row in grid):
        errors.append("background 0 is absent")
    comps = _components(grid)
    if not 2 <= len(comps) <= 6:
        errors.append(f"expected 2..6 sortable components, found {len(comps)}")
    if comps:
        boxes = [_bbox(cells) for _,cells in comps]
        oh = sum(b[2]-b[0]+1 for b in boxes) + len(boxes)-1
        ow = max(b[3]-b[1]+1 for b in boxes)
        if oh > 30 or ow > 30:
            errors.append(f"stacked output {oh}x{ow} exceeds 30x30")
    return errors


def observe_overrides(grid):
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "n_components": len(_components(grid))}


def _render(grid, comps, *, align="center", mask=False, order="left"):
    key = ((lambda comp: (_bbox(comp[1])[3], _bbox(comp[1])[0])) if order == "right" else
           (lambda comp: (_bbox(comp[1])[1], _bbox(comp[1])[0])))
    comps = sorted(comps, key=key)
    pieces = []
    for color, cells in comps:
        r0,c0,r1,c1 = _bbox(cells)
        if mask:
            piece = full_grid(r1-r0+1, c1-c0+1, 0)
            for r,c in cells:
                piece[r-r0][c-c0] = grid[r][c]
        else:
            piece = [list(row[c0:c1+1]) for row in grid[r0:r1+1]]
        pieces.append(piece)
    if not pieces:
        return [[]]
    width = max(len(p[0]) for p in pieces)
    output = []
    for piece in pieces:
        if output:
            output.append([0]*width)
        left = (width-len(piece[0]))//2 if align == "center" else 0
        output.extend([[0]*left + row + [0]*(width-left-len(row)) for row in piece])
    return output


def rule_mirror(grid):
    """Diagnostic mirror only; production labels still come from Racket."""
    return _render(grid, _components(grid))


def _rival_color_groups(grid):
    colors = sorted({v for row in grid for v in row if v})
    comps = [(color, [(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v == color])
             for color in colors]
    return _render(grid, comps)


SEMANTIC_RIVALS = {
    "left_align": lambda g: _render(g, _components(g), align="left"),
    "mask_each_component": lambda g: _render(g, _components(g), mask=True),
    "group_by_color": _rival_color_groups,
    "sort_by_right_edge": lambda g: _render(g, _components(g), order="right"),
    "merge_touching_colors": lambda g: _render(g, _components(g, multicolor=True)),
    "eight_connected": lambda g: _render(g, _components(g, connectivity=8)),
}


def _refutes(grid, name):
    return not self_check(grid) and SEMANTIC_RIVALS[name](grid) != rule_mirror(grid)


SEMANTIC_WITNESSES = {
    name: (lambda grid, rival=name: _refutes(grid, rival)) for name in SEMANTIC_RIVALS
}
WITNESS_RIVALS = {name: [name] for name in SEMANTIC_RIVALS}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def strict_canonical_like(grid) -> bool:
    if self_check(grid) or len(grid) != 10 or len(grid[0]) != 10:
        return False
    comps = _components(grid)
    if len(comps) != 3 or len({color for color,_ in comps}) != 3:
        return False
    if len({_bbox(cells)[1] for _,cells in comps}) != 3:
        return False
    normalized = []
    for _,cells in comps:
        r0,c0,_,_ = _bbox(cells)
        normalized.append(frozenset((r-r0,c-c0) for r,c in cells))
    return (all(shape in {frozenset(s) for s in _BANK} for shape in normalized)
            and frozenset(_L5) in normalized)


def lesson_identifiable(demos, query) -> list[str]:
    """Falsification against six named rivals, NOT a proof of unique inference."""
    qgrid = query["input"] if isinstance(query, dict) else query
    target = rule_mirror(qgrid)
    return [f"{name} fits every demo but disagrees on query"
            for name,rival in LESSON_COMPETITORS.items()
            if all(rival(demo["input"]) == demo["output"] for demo in demos)
            and rival(qgrid) != target]
