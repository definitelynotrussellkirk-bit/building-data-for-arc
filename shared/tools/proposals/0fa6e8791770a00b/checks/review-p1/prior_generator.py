"""Input sampler for canonical recolor-stamping; Racket remains label authority."""
from __future__ import annotations
from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.objects import find_generator_objects, fg_partition

GENERATOR_ID = "144c5d002191"
TASK_ID = GENERATOR_ID
RULE_HASH = "c3118b3e9e62"
VERSION = "3.0.0"
SUMMARY = (
    "One connected template of 4..7 cells and 2..5 singleton markers. "
    "Stamp its binary bounding-box shape at each marker, recolored to that marker; "
    "clip individual out-of-bounds cells, with later row-major markers winning overlaps."
)
INVARIANTS = [
    "rectangular 7..16 by 9..18 grid of integer colors 0..9 with background 0",
    "exactly one multi-cell monochromatic 4-component, containing 4..7 template cells",
    "2..5 singleton monochromatic 4-components; marker colors may repeat",
    "different colors may touch and equal-colored singleton markers may touch diagonally",
    "canonical Racket authority is unchanged; Python generates inputs only",
]
AXES = {
    "grid_h": {"type": "int", "default": "canonical-profile mixture, 7..16", "valid": "7..16"},
    "grid_w": {"type": "int", "default": "canonical-profile mixture, 9..18", "valid": "9..18"},
    "n": {"type": "int", "default": "support 2..5, witness 3..5", "valid": "2..5"},
    "template_size": {"type": "int", "default": "4..7, larger favored on hard", "valid": "4..7"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
LESSON_SCHEDULE_PERIOD = 2
SCHEDULE_PROFILES = ("support", "witness")
_CANONICAL_PROFILES = ((10,12,4), (9,13,5), (11,14,4), (10,14,5))


def schedule_profile(seed, sample_index, difficulty=None):
    """Semantic profile repeats; geometry, colors and shape remain seeded."""
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _components(grid, *, diagonal=False, multicolor=False, by_color=False):
    if by_color:
        objects = list(fg_partition(grid, bg=0).values())
    else:
        objects = find_generator_objects(
            grid, univalued=not multicolor, diagonal=diagonal, without_bg=True, bg=0)
    result = []
    for obj in objects:
        cells = sorted(point for _, point in obj)
        r, c = cells[0]
        result.append((grid[r][c], cells))
    return sorted(result, key=lambda part: part[1][0])


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the declared training domain using actual component semantics."""
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        return ["expected a nonempty list of grid rows"]
    if not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["empty or ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["grid colors must be integers 0..9 (not booleans)"]
    if not 7 <= len(grid) <= 16 or not 9 <= len(grid[0]) <= 18:
        return ["grid dimensions outside declared 7..16 by 9..18 domain"]
    parts = _components(grid)
    templates = [part for part in parts if len(part[1]) > 1]
    markers = [part for part in parts if len(part[1]) == 1]
    reasons = []
    if len(templates) != 1:
        reasons.append("expected exactly one multi-cell monochromatic 4-component")
    elif not 4 <= len(templates[0][1]) <= 7:
        reasons.append("template must contain 4..7 connected cells")
    if not 2 <= len(markers) <= 5:
        reasons.append("expected 2..5 singleton monochromatic 4-components")
    return reasons


def strict_canonical_like(grid):
    return self_check(grid)


def observe_overrides(grid):
    parts = _components(grid)
    templates = [part for part in parts if len(part[1]) > 1]
    return {
        "grid_h": len(grid), "grid_w": len(grid[0]),
        "n": sum(len(cells) == 1 for _, cells in parts),
        "template_size": len(templates[0][1]) if len(templates) == 1 else None,
    }


def _axis(ctx, name, low, high, anchor=None, weight=0):
    choices = list(range(low, high+1))
    if anchor is not None:
        choices += [anchor]*weight
    return ctx.draw_choice(name, choices)


def _polyomino(rng, size):
    """Bounded frontier growth avoids rejection loops."""
    cells = {(0,0)}
    for _ in range(size-1):
        frontier = sorted({(r+dr,c+dc) for r,c in cells
                           for dr,dc in ((-1,0),(1,0),(0,-1),(0,1))} - cells)
        cells.add(rng.choice(frontier))
    r0, c0 = min(r for r,_ in cells), min(c for _,c in cells)
    return sorted((r-r0,c-c0) for r,c in cells)


def _witness_shape(size):
    # Empty bbox origin; the S shape and its extensions distinguish both row/
    # column paint order, clipping, and first/last-per-color marker deduplication.
    return [(0,1),(0,2),(1,0),(1,1)] + [(1,2),(2,0),(2,1)][:size-4]


def _paint_template(grid, cells, top, left, color):
    for r,c in cells:
        grid[top+r][left+c] = color


def _support_grid(ctx, h, w, n, size):
    rng = ctx.draw_rng("support_geometry")
    cells = _polyomino(rng, size)
    sh, sw = max(r for r,_ in cells)+1, max(c for _,c in cells)+1
    top, left = rng.randrange(h-sh+1), rng.randrange(w-sw+1)
    palette = sorted(ctx.draw_rng("support_palette").sample(range(1,10), n+1))
    roles = ctx.draw_rng("support_roles")
    # Rank varies over maximum and interior ranks, but is not minimum. This
    # profile always counters the minimum-color rival introduced by witnesses.
    template_color = roles.choice(palette[1:])
    marker_colors = [color for color in palette if color != template_color]
    roles.shuffle(marker_colors)
    grid = full_grid(h,w,0)
    _paint_template(grid,cells,top,left,template_color)
    anchors = [(r,c) for r in range(h-sh+1) for c in range(w-sw+1) if not grid[r][c]]
    if len(anchors) < n:
        # A long/thin template at the minimum dimensions may occupy several
        # full-fit anchors. Relocation preserves shape, size and all controls.
        grid = full_grid(h,w,0)
        _paint_template(grid,cells,h-sh,w-sw,template_color)
        anchors = [(r,c) for r in range(h-sh+1) for c in range(w-sw+1) if not grid[r][c]]
    if len(anchors) < n:
        raise ValueError("declared dimensions cannot fit the requested full-stamp anchors")
    for (r,c),color in zip(rng.sample(anchors,n),marker_colors):
        grid[r][c] = color
    return grid


def _witness_grid(ctx, h, w, n, size):
    unique_markers = n-1 if n >= 3 else n
    palette = sorted(ctx.draw_rng("witness_palette").sample(range(1,10),unique_markers+1))
    template_color, marker_palette = palette[0], palette[1:]
    a, b = marker_palette[-1], marker_palette[0]
    markers = [(0,w-3,a),(0,w-2,b)]
    if n >= 3:
        markers.append((1,w-4,a))
    if n >= 4:
        markers.append((h-2,w-2,marker_palette[1]))
    if n == 5:
        markers.append((h-1,w//2,marker_palette[2]))
    grid = full_grid(h,w,0)
    _paint_template(grid,_witness_shape(size),h-4,1,template_color)
    for r,c,color in markers:
        if grid[r][c]:
            raise RuntimeError("witness geometry collided with source template")
        grid[r][c] = color
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides)-set(AXES)
    if unknown:
        raise ValueError(f"unknown or retired override axes: {sorted(unknown)}")
    for name,value in overrides.items():
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be an integer (not bool, float or string)")
    if difficulty not in (None,"easy","medium","hard"):
        raise ValueError(f"unsupported difficulty: {difficulty!r}")
    ctx = gen_ctx(seed=seed,sample_index=sample_index,version=VERSION,task_id=TASK_ID,
                  difficulty=difficulty,overrides=overrides)
    profile = schedule_profile(seed,sample_index,difficulty)
    ah,aw,colors = ctx.draw_rng("canonical_profile").choice(_CANONICAL_PROFILES)
    core = ctx.draw_choice("profile_mix",("core","core","broad")) == "core"
    weight = 80 if core else 0
    h = _axis(ctx,"grid_h",7,16,ah,weight)
    w = _axis(ctx,"grid_w",9,18,aw,weight)
    anchor_n = colors-(1 if profile == "witness" else 2)
    if overrides.get("n") is not None:
        n = ctx.draw_int_strict("n",2,5)
    else:
        n = _axis(ctx,"n",3 if profile == "witness" else 2,5,anchor_n,80)
    favored = 4 if difficulty == "easy" else 7 if difficulty == "hard" else 5
    size = _axis(ctx,"template_size",4,7,favored,3)
    builder = _witness_grid if profile == "witness" else _support_grid
    return builder(ctx,h,w,n,size)


# Pure rival predictions and witness diagnostics below are never generation
# labels. Racket labels independently check them in the semantic gate/census.
def _predict(grid, *, selection="largest", grouping="four", anchor="bbox",
             edge="clip", order="row", retain_markers=False, deduplicate=None):
    h,w = len(grid),len(grid[0])
    parts = _components(grid,diagonal=grouping=="eight",
                        multicolor=grouping=="multicolor",by_color=grouping=="color")
    out = full_grid(h,w,0)
    if not parts:
        return out
    if selection == "first":
        template = parts[0]
    elif selection == "max_color":
        template = max(parts,key=lambda part: part[0])
    elif selection == "min_color":
        template = min(parts,key=lambda part: part[0])
    else:
        candidates = [part for part in parts if len(part[1]) > 1]
        if not candidates:
            return out
        template = max(candidates,key=lambda part: len(part[1]))
    r0,c0 = min(r for r,_ in template[1]),min(c for _,c in template[1])
    shape = [(r-r0,c-c0) for r,c in template[1]]
    if anchor == "occupied":
        dr,dc = min(shape)
        shape = [(r-dr,c-dc) for r,c in shape]
    markers = [part for part in parts if len(part[1]) == 1 and part != template]
    if deduplicate:
        kept = {}
        for part in markers:
            if deduplicate == "last" or part[0] not in kept:
                kept[part[0]] = part
        markers = sorted(kept.values(),key=lambda part: part[1][0])
    if order == "reverse":
        markers = list(reversed(markers))
    elif order == "color":
        markers = sorted(markers,key=lambda part: part[0])
    elif order == "column":
        markers = sorted(markers,key=lambda part: (part[1][0][1],part[1][0][0]))
    if retain_markers:
        for color,[(r,c)] in markers:
            out[r][c] = color
    for color,[(top,left)] in markers:
        if edge == "clamp":
            top = min(top,h-max(r for r,_ in shape)-1)
            left = min(left,w-max(c for _,c in shape)-1)
        targets = [(top+r,left+c) for r,c in shape]
        if edge == "drop" and any(not (0 <= r < h and 0 <= c < w) for r,c in targets):
            continue
        for r,c in targets:
            if edge == "wrap":
                r,c = r % h,c % w
            if 0 <= r < h and 0 <= c < w and (order != "first_wins" or out[r][c] == 0):
                out[r][c] = color
    return out


def rival_max_color(grid):
    return _predict(grid,selection="max_color")


def rival_first_object(grid):
    return _predict(grid,selection="first")


def rival_group_colors(grid):
    return _predict(grid,grouping="color")


def rival_eight_connected(grid):
    return _predict(grid,grouping="eight")


def rival_multicolor_components(grid):
    return _predict(grid,grouping="multicolor")


def rival_occupied_anchor(grid):
    return _predict(grid,anchor="occupied")


def rival_preserve_markers(grid):
    return _predict(grid,retain_markers=True)


def rival_discard_cropped(grid):
    return _predict(grid,edge="drop")


def rival_clamp_inside(grid):
    return _predict(grid,edge="clamp")


def rival_wrap(grid):
    return _predict(grid,edge="wrap")


def rival_reverse_order(grid):
    return _predict(grid,order="reverse")


def rival_first_wins(grid):
    return _predict(grid,order="first_wins")


def rival_color_order(grid):
    return _predict(grid,order="color")


def rival_column_order(grid):
    return _predict(grid,order="column")


def rival_first_per_color(grid):
    return _predict(grid,deduplicate="first")


def rival_last_per_color(grid):
    return _predict(grid,deduplicate="last")


def rival_min_color(grid):
    return _predict(grid,selection="min_color")


CANONICAL_SHORTCUTS = {
    "maximum_color_template": rival_max_color,
    "first_object_template": rival_first_object,
    "group_by_color": rival_group_colors,
    "eight_connected_objects": rival_eight_connected,
    "multicolor_objects": rival_multicolor_components,
    "first_occupied_cell_anchor": rival_occupied_anchor,
    "preserve_singleton_markers": rival_preserve_markers,
    "discard_cropped_stamp": rival_discard_cropped,
    "clamp_stamp_inside": rival_clamp_inside,
    "toroidal_wrap": rival_wrap,
    "reverse_marker_order": rival_reverse_order,
    "first_overlap_wins": rival_first_wins,
    "ascending_color_marker_order": rival_color_order,
    "column_major_marker_order": rival_column_order,
    "first_marker_per_color": rival_first_per_color,
    "last_marker_per_color": rival_last_per_color,
}
SEMANTIC_RIVALS = dict(CANONICAL_SHORTCUTS)
LESSON_COMPETITORS = dict(CANONICAL_SHORTCUTS,minimum_color_template=rival_min_color)


def _refutation_witness(rival):
    def witness(grid):
        return _predict(grid) != rival(grid)
    return witness


SEMANTIC_WITNESSES = {name: _refutation_witness(rival) for name,rival in SEMANTIC_RIVALS.items()}
WITNESS_RIVALS = {name: [name] for name in SEMANTIC_WITNESSES}


def lesson_identifiable(demos, query):
    """Finite declared-rival comparison; not universal rule identification."""
    reasons = []
    for name,rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"unrefuted declared rival changes query: {name}")
    return reasons
