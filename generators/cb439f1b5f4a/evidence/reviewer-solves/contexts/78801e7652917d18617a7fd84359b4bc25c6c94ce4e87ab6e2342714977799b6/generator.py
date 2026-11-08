"""Sample connected prototypes repeated by the blue header count (M136).

Labels remain the unchanged Racket authority. The Python transformations below
are explicitly wrong rival rules used only for semantic/lesson diagnostics.
"""
from __future__ import annotations

from functools import partial

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "cb439f1b5f4a"
TASK_ID = GENERATOR_ID
RULE_HASH = "33d95b8e8c4d"
VERSION = "3.0.0"
SUMMARY = (
    "Count blue cells in row 0, crop the one connected nonzero prototype below "
    "the header, and repeat the entire colored crop horizontally that many "
    "times with one blank column between copies. The body may contain blue, "
    "multiple colors, holes, and arbitrary padding. Generated K is 1..4."
)
INVARIANTS = [
    "rectangular integer ARC grid; background is 0; header contains only 0 and 1",
    "positive header count; exactly one connected union of nonzero body cells",
    "body colors and internal zeros are preserved, including body color 1",
    "cropped output width K*prototype_width + K-1 is at most 30",
]
AXES = {
    "grid_h": {"type": "int", "default": "4 in compact phases; 5..12 otherwise", "valid": "4..12"},
    "grid_w": {"type": "int", "default": "6..7 in compact phases; 6..15 otherwise", "valid": "6..15"},
    "K": {"type": "int", "default": "seed-rotated period-five count curriculum", "valid": "1..4"},
    "prototype_color": {"type": "color", "default": "first nonblue body cell; uniform 2..9", "valid": "2..9"},
    "texture": {"type": "str", "default": "period-five shape/color curriculum",
                "valid": "solid|notched|multicolor|blue_motif"},
}
HELPFUL_TEXTURES = ("solid", "notched", "multicolor", "blue_motif")
# Every advertised joint setting is constructed; no rejection/shrink fallback.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0
SCHEDULE_PROFILES = (0, 1, 2, 3, 4)


def schedule_profile(seed, sample_index, difficulty=None):
    """Five consecutive accepted inputs cover every teaching profile."""
    return sample_index % 5


def _integer(ctx, name, lower, upper, default_lower, default_upper):
    # Default curriculum bounds never narrow the caller's explicit legal domain.
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int_strict(name, lower, upper)
    return ctx.draw_int_strict(name, default_lower, default_upper)


def _shape(rng, height, width, solid):
    if solid:
        return [(r, c) for r in range(height) for c in range(width)]
    # A top/left spine touches all four bbox sides. Grow from its frontier while
    # leaving one corner empty, so every non-solid shape is connected and sparse.
    cells = {(r, 0) for r in range(height)} | {(0, c) for c in range(width)}
    forbidden = (height - 1, width - 1)
    target = rng.randint(len(cells), height * width - 1)
    while len(cells) < target:
        frontier = sorted({(r + dr, c + dc) for r, c in cells
                           for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
                           if 0 <= r + dr < height and 0 <= c + dc < width
                           and (r + dr, c + dc) not in cells
                           and (r + dr, c + dc) != forbidden})
        cells.add(rng.choice(frontier))
    flip_r, flip_c = rng.randrange(2), rng.randrange(2)
    return sorted((height - 1 - r if flip_r else r,
                   width - 1 - c if flip_c else c) for r, c in cells)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override keys: {sorted(unknown)}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    phase = schedule_profile(seed, sample_index, difficulty)
    compact = phase in (0, 1)
    band = difficulty or "medium"
    h_range, w_range = {
        "easy": ((5, 7), (6, 10)),
        "medium": ((6, 9), (7, 13)),
        "hard": ((8, 12), (9, 15)),
    }[band]
    h = _integer(ctx, "grid_h", 4, 12, *((4, 4) if compact else h_range))
    w = _integer(ctx, "grid_w", 6, 15, *((6, 7) if compact else w_range))
    scheduled_count = 1 + (seed + phase) % 4
    count = _integer(ctx, "K", 1, 4, scheduled_count, scheduled_count)
    color = ctx.draw_int_strict("prototype_color", 2, 9)
    defaults = ("solid", "notched") if compact else (
        ("multicolor",) if phase == 2 else ("blue_motif",))
    texture = ctx.draw_choice("texture", HELPFUL_TEXTURES if overrides.get("texture") is not None else defaults)

    rng = ctx.draw_rng("prototype_geometry")
    solid = texture == "solid"
    min_extent = 1 if solid else 2
    max_width = min(w, (31 - count) // count)
    if compact:
        body_h = rng.randint(min_extent, 2)
        body_w = rng.randint(min_extent, min(4, max_width))
    else:
        # Free broad draws have >=3 body rows and >=1 blank bottom row. A valid
        # small height override relaxes those preferences instead of being lost.
        height_cap = max(min_extent, h - 2)
        body_h = rng.randint(min(3, height_cap), min(height_cap, 8))
        body_w = rng.randint(min_extent, min(max_width, 9))
    cells = _shape(rng, body_h, body_w, solid)
    max_top = h - body_h - (1 if not compact and h >= body_h + 2 else 0)
    top = ctx.draw_rng("prototype_row").randint(1, max_top)
    left = ctx.draw_rng("prototype_column").randint(0, w - body_w)

    grid = full_grid(h, w, 0)
    header_rng = ctx.draw_rng("header_position")
    if not compact or header_rng.randrange(2) == 0:
        start = header_rng.randint(0, w - count)
        columns = range(start, start + count)
    else:
        columns = header_rng.sample(range(w), count)
    for column in columns:
        grid[0][column] = 1
    for r, c in cells:
        grid[top + r][left + c] = color
    if texture in ("multicolor", "blue_motif"):
        # Preserve the row-major first body pixel as the recoverable primary
        # color. Recolor other cells; never repaint/drop geometry after drawing.
        palette_rng = ctx.draw_rng("prototype_palette")
        alternate = 1 if texture == "blue_motif" else palette_rng.choice(
            [value for value in range(2, 10) if value != color])
        amount = palette_rng.randint(1, max(1, (len(cells) - 1) // 2))
        for r, c in palette_rng.sample(cells[1:], amount):
            grid[top + r][left + c] = alternate
    return grid


def _body_cells(grid):
    return [(r, c) for r in range(1, len(grid))
            for c, value in enumerate(grid[r]) if value != 0]


def _crop(grid, cells=None):
    cells = _body_cells(grid) if cells is None else cells
    if not cells:
        return [[0]]  # total rival function on an empty wrongly selected body
    top, bottom = min(r for r, _ in cells), max(r for r, _ in cells)
    left, right = min(c for _, c in cells), max(c for _, c in cells)
    return [row[left:right + 1] for row in grid[top:bottom + 1]]


def observe_overrides(grid):
    """Recover controls; a lawful all-blue body has no primary nonblue color."""
    body = _body_cells(grid)
    colors = {grid[r][c] for r, c in body}
    primary = next((grid[r][c] for r, c in body if grid[r][c] != 1), None)
    crop = _crop(grid)
    if 1 in colors:
        texture = "blue_motif"
    elif len(colors) > 1:
        texture = "multicolor"
    else:
        texture = "notched" if any(0 in row for row in crop) else "solid"
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "K": grid[0].count(1),
            "prototype_color": primary, "texture": texture}


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if any(not isinstance(row, (list, tuple)) for row in grid):
        return ["every row must be a sequence"]
    h, w = len(grid), len(grid[0])
    if not (2 <= h <= 30 and 1 <= w <= 30):
        return ["input must have 2..30 rows and 1..30 columns"]
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer colors 0..9; booleans and floats are invalid"]
    if any(value not in (0, 1) for value in grid[0]):
        return ["header must contain only 0 and 1"]
    count = grid[0].count(1)
    if count == 0:
        return ["header must contain at least one blue marker"]
    body = set(_body_cells(grid))
    if not body:
        return ["prototype is empty"]
    reached = {min(body)}
    pending = list(reached)
    while pending:
        r, c = pending.pop()
        for point in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
            if point in body and point not in reached:
                reached.add(point)
                pending.append(point)
    if reached != body:
        return ["body must be one connected union of nonzero cells"]
    width = max(c for _, c in body) - min(c for _, c in body) + 1
    if count * width + count - 1 > 30:
        return ["repeated prototype exceeds the 30-column output limit"]
    return []


def strict_canonical_like(grid):
    return self_check(grid)


def _repeat(prototype, count, gap=1):
    """Common assembly for deliberately incorrect diagnostic rivals only."""
    count = max(1, count)
    return [(row + [0] * gap) * (count - 1) + row for row in prototype]


def _header_runs(grid):
    return sum(value == 1 and (c == 0 or grid[0][c-1] != 1)
               for c, value in enumerate(grid[0]))


def _rival_runs(grid):
    return _repeat(_crop(grid), _header_runs(grid))


def _rival_marker_gap(grid):
    positions = [c for c, value in enumerate(grid[0]) if value == 1]
    gap = positions[1] - positions[0] - 1 if len(positions) > 1 else 1
    return _repeat(_crop(grid), len(positions), gap)


def _rival_last_two_rows(grid):
    # Incorrectly assumes the prototype lives in the last two input rows.
    body = [(r, c) for r, c in _body_cells(grid) if r >= len(grid) - 2]
    return _repeat(_crop(grid, body), grid[0].count(1))


def _rival_two_row_crop(grid):
    return _repeat(_crop(grid)[:2], grid[0].count(1))


def _rival_all_blue(grid):
    return _repeat(_crop(grid), sum(row.count(1) for row in grid))


def _rival_erase_blue(grid):
    changed = [list(grid[0])] + [[0 if value == 1 else value for value in row]
                               for row in grid[1:]]
    return _repeat(_crop(changed), grid[0].count(1))


def _rival_first_nonblue_component(grid):
    cells = [(r, c) for r, c in _body_cells(grid) if grid[r][c] != 1]
    if not cells:
        return [[0]]
    first = cells[0]
    color = grid[first[0]][first[1]]
    component, pending = {first}, [first]
    while pending:
        r, c = pending.pop()
        for rr, cc in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
            if (1 <= rr < len(grid) and 0 <= cc < len(grid[0])
                    and grid[rr][cc] == color and (rr, cc) not in component):
                component.add((rr, cc))
                pending.append((rr, cc))
    changed = [[value if (r, c) in component else 0 for c, value in enumerate(row)]
               for r, row in enumerate(grid)]
    return _repeat(_crop(changed), grid[0].count(1))


def _rival_fixed_count(grid, *, count):
    return _repeat(_crop(grid), count)


def _rival_fixed_gap(grid, *, gap):
    return _repeat(_crop(grid), grid[0].count(1), gap)


def _rival_fill_box(grid):
    crop = _crop(grid)
    color = next(value for row in crop for value in row if value != 0)
    return _repeat([[color] * len(crop[0]) for _ in crop], grid[0].count(1))


def _rival_mirror(grid):
    return _repeat([row[::-1] for row in _crop(grid)], grid[0].count(1))


def _rival_vertical(grid):
    crop = _crop(grid)
    return (crop + [[0] * len(crop[0])]) * (grid[0].count(1) - 1) + crop


CANONICAL_SHORTCUTS = {
    "header_runs": _rival_runs,
    "header_spacing_is_output_gap": _rival_marker_gap,
    "last_two_input_rows": _rival_last_two_rows,
    "two_row_crop": _rival_two_row_crop,
    "count_all_blue": _rival_all_blue,
    "erase_blue_body": _rival_erase_blue,
    "first_nonblue_component": _rival_first_nonblue_component,
}
LESSON_COMPETITORS = {
    **{f"fixed_count_{count}": partial(_rival_fixed_count, count=count) for count in range(1, 5)},
    "zero_separator": partial(_rival_fixed_gap, gap=0),
    "two_column_separator": partial(_rival_fixed_gap, gap=2),
    "fill_bounding_box": _rival_fill_box,
    "mirror_prototype": _rival_mirror,
    "vertical_repetition": _rival_vertical,
}
SEMANTIC_RIVALS = {**CANONICAL_SHORTCUTS, "fill_bounding_box": _rival_fill_box}
SEMANTIC_WITNESSES = {
    "adjacent_header_markers": lambda g: _header_runs(g) < g[0].count(1),
    "noncanonical_marker_spacing": lambda g: (g[0].count(1) > 1 and
        [c for c, value in enumerate(g[0]) if value == 1][1] -
        [c for c, value in enumerate(g[0]) if value == 1][0] != 2),
    "body_above_last_two_rows": lambda g: min(r for r, _ in _body_cells(g)) < len(g) - 2,
    "tall_prototype": lambda g: len(_crop(g)) > 2,
    "blue_in_body": lambda g: any(g[r][c] == 1 for r, c in _body_cells(g)),
    "multicolor_body": lambda g: len({g[r][c] for r, c in _body_cells(g)}) > 1,
    "internal_background": lambda g: any(0 in row for row in _crop(g)),
}
WITNESS_RIVALS = {
    "adjacent_header_markers": ["header_runs"],
    "noncanonical_marker_spacing": ["header_spacing_is_output_gap"],
    "body_above_last_two_rows": ["last_two_input_rows"],
    "tall_prototype": ["two_row_crop"],
    "blue_in_body": ["count_all_blue", "erase_blue_body"],
    "multicolor_body": ["first_nonblue_component"],
    "internal_background": ["fill_bounding_box"],
}


def lesson_identifiable(demos, query):
    """Finite declared-rival check, not a claim of universal identifiability."""
    reasons = []
    for name, rival in {**CANONICAL_SHORTCUTS, **LESSON_COMPETITORS}.items():
        if (all(rival(pair["input"]) == pair["output"] for pair in demos)
                and rival(query["input"]) != query["output"]):
            reasons.append(f"{name} fits every demonstration but changes the query")
    return reasons
