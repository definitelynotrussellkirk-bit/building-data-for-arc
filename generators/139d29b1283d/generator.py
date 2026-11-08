"""Lawful inputs for two translated template stamps; Racket supplies labels.

Two of every three default draws distinguish the declared canonical shortcuts.
The third retains small/canonical templates and empty or clipped intersections.
Exact overrides take precedence; their lessons still need the rival checks.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.objects import find_objects

GENERATOR_ID = "139d29b1283d"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "fcd41965ebef"
SUMMARY = (
    "Select the unique largest 4-connected color-3 template, normalize its "
    "bounding-box origin, and stamp it at the color-1 and color-2 anchors. "
    "The unchanged Racket rule paints only their in-bounds intersection in 8 "
    "on a new zero grid. Smaller green distractors and clipping are supported."
)
INVARIANTS = [
    "8..24 rows and columns; integer colors 0,1,2,3 with fixed semantic roles",
    "one anchor of each color 1 and 2; a unique largest green component of 2..8 cells",
    "0..2 smaller green components; connectivity is monochrome and four-neighbor",
    "overlap and no_overlap stamps fit; clipped stamps have nonempty visible intersection",
]
AXES = {
    "grid_h": {"type": "int", "default": "canonical profiles mixed with 8..24", "valid": "8..24"},
    "grid_w": {"type": "int", "default": "canonical profiles mixed with 8..24", "valid": "8..24"},
    "template_size": {"type": "int", "default": "witness 5..8; general 2..8 favoring 4", "valid": "2..8"},
    "n_distractors": {"type": "int", "default": "witness 1..2; general 0", "valid": "0..2"},
    "texture": {"type": "str", "default": "witness overlap; general all modes", "valid": "overlap|no_overlap|clipped"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
TEXTURES = ("overlap", "no_overlap", "clipped")
HELPFUL_TEXTURES = TEXTURES
DEGENERATE_TEXTURES = ()
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 3
SCHEDULE_PROFILES = ("witness_a", "witness_b", "general")
MIN_STRICT_FRAC = 0.05
SOLID_OUTPUT_JUSTIFICATION = (
    "The selected Racket rule returns a same-size all-zero grid when the two "
    "translated finite templates have no in-bounds intersection."
)
_PROFILES = ((10, 12), (11, 13), (12, 14))
_BOUNDS = {"grid_h": (8, 24), "grid_w": (8, 24), "template_size": (2, 8), "n_distractors": (0, 2)}
_NEIGHBORS = ((-1, 0), (0, -1), (0, 1), (1, 0))


def schedule_profile(seed, sample_index, difficulty=None):
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _normalize(cells):
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _shift(cells, anchor):
    return {(r + anchor[0], c + anchor[1]) for r, c in cells}


def _green_components(grid):
    # The shared helper defaults to multicolor objects; match Racket explicitly.
    components = find_objects(grid, univalued=True, diagonal=False, bg=0)
    return sorted(
        ({point for color, point in obj} for obj in components if next(iter(obj))[0] == 3),
        key=lambda cells: (-len(cells), min(cells)),
    )


def _parts(grid, *, first_component=False, first_cell_origin=False, limit=None):
    groups = _green_components(grid)
    component = min(groups, key=min) if first_component else groups[0]
    if first_cell_origin:
        r0, c0 = min(component)
        shape = tuple(sorted((r - r0, c - c0) for r, c in component))
    else:
        shape = _normalize(component)
    if limit is not None:
        shape = shape[:limit]
    anchors = [next((r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == color)
               for color in (1, 2)]
    return shape, anchors, [_shift(shape, anchor) for anchor in anchors]


def _visible(grid, cells):
    return {(r, c) for r, c in cells if 0 <= r < len(grid) and 0 <= c < len(grid[0])}


def _paint_rival(grid, cells):
    out = full_grid(len(grid), len(grid[0]), 0)
    for r, c in _visible(grid, cells):
        out[r][c] = 8
    return out


def _cropped_first_stamp(grid):
    shape, anchors, stamps = _parts(grid)
    h = max(r for r, _ in shape) + 1
    w = max(c for _, c in shape) + 1
    ar, ac = anchors[1]
    return _paint_rival(grid, {(r, c) for r, c in stamps[0] if ar <= r < ar + h and ac <= c < ac + w})


def _southeast_first_stamp(grid):
    _, anchors, stamps = _parts(grid)
    ar, ac = anchors[1]
    return _paint_rival(grid, {(r, c) for r, c in stamps[0] if r >= ar and c >= ac})


def _first_cell_origin(grid):
    _, _, stamps = _parts(grid, first_cell_origin=True)
    return _paint_rival(grid, stamps[0] & stamps[1])


def _first_four_cells(grid):
    _, _, stamps = _parts(grid, limit=4)
    return _paint_rival(grid, stamps[0] & stamps[1])


def _first_green_component(grid):
    _, _, stamps = _parts(grid, first_component=True)
    return _paint_rival(grid, stamps[0] & stamps[1])


def _first_size_four_component(grid):
    groups = _green_components(grid)
    eligible = [cells for cells in groups if len(cells) >= 4]
    shape = _normalize(min(eligible, key=min) if eligible else groups[0])
    _, anchors, _ = _parts(grid)
    return _paint_rival(grid, _shift(shape, anchors[0]) & _shift(shape, anchors[1]))


def _overlap_bbox(grid):
    _, _, stamps = _parts(grid)
    cells = stamps[0] & stamps[1]
    if not cells:
        return _paint_rival(grid, ())
    r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
    c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
    return _paint_rival(grid, {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)})


# These are explicit WRONG alternatives, never label authority.
CANONICAL_SHORTCUTS = {
    "first_stamp_clipped_to_second_bbox": _cropped_first_stamp,
    "first_stamp_southeast_of_second_anchor": _southeast_first_stamp,
    "first_occupied_template_cell_origin": _first_cell_origin,
    "first_four_template_cells": _first_four_cells,
    "first_color3_component": _first_green_component,
    "first_component_at_least_four": _first_size_four_component,
    "fill_overlap_bbox": _overlap_bbox,
}
LESSON_COMPETITORS = dict(CANONICAL_SHORTCUTS)
SEMANTIC_RIVALS = dict(CANONICAL_SHORTCUTS)


def _all_shortcuts_refuted(grid):
    _, _, stamps = _parts(grid)
    expected = _paint_rival(grid, stamps[0] & stamps[1])
    return all(rival(grid) != expected for rival in CANONICAL_SHORTCUTS.values())


SEMANTIC_WITNESSES = {"occupancy_origin_and_selection": _all_shortcuts_refuted}
WITNESS_RIVALS = {"occupancy_origin_and_selection": list(SEMANTIC_RIVALS)}


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid or not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    if any(not isinstance(row, (list, tuple)) or len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or value not in (0, 1, 2, 3) for row in grid for value in row):
        return ["input cells must be integer colors 0,1,2,3 (not bool)"]
    errors = []
    if not (8 <= len(grid) <= 24 and 8 <= len(grid[0]) <= 24):
        errors.append("grid dimensions must be 8..24")
    for color in (1, 2):
        count = sum(value == color for row in grid for value in row)
        if count != 1:
            errors.append(f"expected exactly one color-{color} anchor, found {count}")
    groups = _green_components(grid)
    if not groups:
        errors.append("missing color-3 template")
    else:
        if not 2 <= len(groups[0]) <= 8:
            errors.append("largest template must have 2..8 cells")
        if len(groups) > 3:
            errors.append("at most two smaller green distractors are supported")
        if len(groups) > 1 and len(groups[0]) == len(groups[1]):
            errors.append("largest color-3 template must be unique")
    if errors:
        return errors
    _, _, stamps = _parts(grid)
    if not _visible(grid, stamps[0] & stamps[1]) and _visible(grid, stamps[0] | stamps[1]) != stamps[0] | stamps[1]:
        errors.append("clipped examples must retain a nonempty visible intersection")
    return errors


def observe_overrides(grid):
    groups = _green_components(grid)
    _, _, stamps = _parts(grid)
    clipped = _visible(grid, stamps[0] | stamps[1]) != stamps[0] | stamps[1]
    texture = "clipped" if clipped else ("overlap" if stamps[0] & stamps[1] else "no_overlap")
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "template_size": len(groups[0]),
            "n_distractors": len(groups) - 1, "texture": texture}


def strict_canonical_like(grid):
    errors = self_check(grid)
    if errors:
        return errors
    observed = observe_overrides(grid)
    if observed["template_size"] != 4 or observed["n_distractors"] != 0 or observed["texture"] != "overlap":
        return ["canonical core has one four-cell template and fully in-bounds nonempty overlap"]
    return []


def _integer(ctx, name, choices):
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int_strict(name, *_BOUNDS[name])
    return ctx.draw_choice(name, choices)


def _poly(rng, size, h, w):
    """Grow a connected polyomino with enough room for all texture modes."""
    cells = {(0, 0)}
    while len(cells) < size:
        candidates = set()
        for r, c in cells:
            for dr, dc in _NEIGHBORS:
                p = (r + dr, c + dc)
                if p in cells:
                    continue
                trial = cells | {p}
                if (max(r for r, _ in trial) - min(r for r, _ in trial) < h - 2
                        and max(c for _, c in trial) - min(c for _, c in trial) < w - 2):
                    candidates.add(p)
        cells.add(rng.choice(sorted(candidates)))
    return _normalize(cells)


def _strong_offset(shape, offset):
    first = set(shape)
    second = _shift(shape, offset)
    overlap = first & second
    if not overlap or shape[0] == (0, 0):
        return False
    h, w = max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1
    dr, dc = offset
    crop = {(r, c) for r, c in first if dr <= r < dr + h and dc <= c < dc + w}
    quadrant = {(r, c) for r, c in first if r >= dr and c >= dc}
    prefix = set(shape[:4])
    small = prefix & _shift(prefix, offset)
    bbox = {(r, c) for r in range(min(r for r, _ in overlap), max(r for r, _ in overlap) + 1)
            for c in range(min(c for _, c in overlap), max(c for _, c in overlap) + 1)}
    return all(overlap != rival for rival in (crop, quadrant, small, bbox))


def _anchors(rng, shape, h, w, texture, strong):
    sh, sw = max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1
    if texture == "no_overlap":
        # A connected <=8-cell shape has sh+sw<=9, so at least one axis
        # admits disjoint bounding boxes even in the minimum 8x8 canvas.
        if 2 * sw <= w:
            left = rng.randint(0, w - 2 * sw)
            a1 = (rng.randint(0, h - sh), left)
            a2 = (rng.randint(0, h - sh), rng.randint(left + sw, w - sw))
        else:
            top = rng.randint(0, h - 2 * sh)
            a1 = (top, rng.randint(0, w - sw))
            a2 = (rng.randint(top + sh, h - sh), rng.randint(0, w - sw))
        return (a1, a2) if rng.randrange(2) else (a2, a1)
    diffs = sorted({(r - rr, c - cc) for r, c in shape for rr, cc in shape} - {(0, 0)})
    if strong:
        diffs = [delta for delta in diffs if _strong_offset(shape, delta)]
    diffs = [delta for delta in diffs if sh + abs(delta[0]) <= h and sw + abs(delta[1]) <= w]
    if not diffs:
        return None
    dr, dc = rng.choice(diffs)
    if texture == "clipped":
        pivot = rng.choice(sorted(set(shape) & _shift(shape, (dr, dc))))
        # Put an overlapping cell in the bottom-right corner. Both anchors
        # stay inside, while some cell of the unequal stamps must extend out.
        a1 = (h - 1 - pivot[0], w - 1 - pivot[1])
    else:
        a1 = (rng.randint(max(0, -dr), min(h - sh, h - sh - dr)),
              rng.randint(max(0, -dc), min(w - sw, w - sw - dc)))
    return a1, (a1[0] + dr, a1[1] + dc)


def _green_fits(grid, cells):
    h, w = len(grid), len(grid[0])
    for r, c in cells:
        if not (0 <= r < h and 0 <= c < w) or grid[r][c] != 0:
            return False
        if any(0 <= r + dr < h and 0 <= c + dc < w and grid[r + dr][c + dc] == 3
               for dr, dc in _NEIGHBORS):
            return False
    return True


def _place_greens(rng, h, w, shape, anchors, count, strong):
    sh, sw = max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1
    origins = [(r, c) for r in range(h - sh + 1) for c in range(w - sw + 1)]
    rng.shuffle(origins)
    for origin in origins:
        grid = full_grid(h, w, 0)
        for color, (r, c) in enumerate(anchors, 1):
            grid[r][c] = color
        main = _shift(shape, origin)
        if not _green_fits(grid, main):
            continue
        for r, c in main:
            grid[r][c] = 3
        for index in range(count):
            # Force real size comparison in teaching slots. A size<=3 cap
            # would let "first component of size>=4" replace largest-object
            # selection on every generated input.
            minimum = 4 if strong and index == 0 else 1
            noise = _poly(rng, rng.randint(minimum, len(shape) - 1), h, w)
            nh, nw = max(r for r, _ in noise) + 1, max(c for _, c in noise) + 1
            places = [(r, c) for r in range(h - nh + 1) for c in range(w - nw + 1)]
            rng.shuffle(places)
            for place in places:
                cells = _shift(noise, place)
                if strong and index == 0 and min(cells) >= min(main):
                    continue
                if _green_fits(grid, cells):
                    for r, c in cells:
                        grid[r][c] = 3
                    break
            else:
                break
        else:
            if not strong or _all_shortcuts_refuted(grid):
                return grid
    return None


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    for name, (lo, hi) in _BOUNDS.items():
        value = overrides.get(name)
        if value is not None and (type(value) is not int or not lo <= value <= hi):
            raise ValueError(f"{name} must be an integer in {lo}..{hi}, not bool")
    if overrides.get("texture") is not None and overrides["texture"] not in TEXTURES:
        raise ValueError(f"texture must be one of {TEXTURES}")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    strong_slot = sample_index % LESSON_SCHEDULE_PERIOD != 2
    canonical_canvas = not strong_slot or ctx.draw_choice("canvas_kind", ("core", "core", "broad")) == "core"
    profile = ctx.draw_choice("canonical_profile", _PROFILES)
    h = _integer(ctx, "grid_h", (profile[0],) if canonical_canvas else tuple(range(8, 25)))
    w = _integer(ctx, "grid_w", (profile[1],) if canonical_canvas else tuple(range(8, 25)))
    sizes = ((5, 5, 6, 7, 8) if difficulty == "easy" else
             (5, 6, 7, 8, 8) if difficulty == "hard" else (5, 6, 7, 8))
    size = _integer(ctx, "template_size", sizes if strong_slot else (2, 3, 4, 4, 4, 4, 4, 5, 6, 7, 8))
    count = _integer(ctx, "n_distractors", (1, 2) if strong_slot else (0,))
    texture = ctx.draw_choice("texture", TEXTURES if overrides.get("texture") is not None else
                              (("overlap",) if strong_slot else ("overlap", "overlap", "overlap", "no_overlap", "clipped")))
    strong = strong_slot and size >= 5 and count > 0 and texture == "overlap"
    for attempt in range(96):
        if strong and attempt >= 80:
            # Constructive backstop still honors every exact control. These
            # hooks have an empty bbox corner and nonrectangular intersection.
            hook = {(0, 1), (0, 2)} | {(1, c) for c in range(size - 2)}
            shape = _normalize(hook if attempt % 2 else {(c, r) for r, c in hook})
        else:
            shape = _poly(rng, size, h, w)
        anchors = _anchors(rng, shape, h, w, texture, strong)
        if anchors is None:
            continue
        grid = _place_greens(rng, h, w, shape, anchors, count, strong)
        if grid is not None:
            return grid
    raise RuntimeError(f"constructive placement exhausted without changing controls: {h}x{w}, size={size}, distractors={count}, texture={texture}")
