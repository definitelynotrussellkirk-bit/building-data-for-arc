"""Input curriculum for reflecting source colors across a central 9-column.

Alternating indices draw two connected monochrome objects or scattered
marks with a singleton at the outer source edge, with seed-parity phase. Exact controls
remain independent of difficulty. Labels are produced only by the unchanged
Racket authority; Python functions below are explicitly incorrect rival rules.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "70a3d3e2c975"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "740ca06f408e"
SUMMARY = (
    "Reflect every source color 1..8 across the full-height central 9-axis on "
    "a zero background, preserving the source and axis. The right half starts "
    "empty. Mix connected monochrome objects with isolated, edge, and varied-"
    "color marks; exact count/palette/geometry overrides are honored or rejected."
)
INVARIANTS = [
    "rectangular integer grid with height 5..14 and width 2*half_w+1, half_w 2..8",
    "exactly one full-height 9-axis at the center; no other 9 cells",
    "the right half is entirely zero and the left half has at least one color 1..8",
    "source cells and axis remain unchanged by the selected reference rule",
]
PALETTE_KINDS = ("default", "warm", "cool", "varied")
_PALETTES = {"default": tuple(range(1, 9)), "warm": (2, 4, 6, 7),
             "cool": (1, 3, 8), "varied": tuple(range(1, 9))}
HELPFUL_TEXTURES = PALETTE_KINDS
DEGENERATE_TEXTURES = ("empty_left", "full_left", "no_axis")
LAWFUL_DEGENERATE_TEXTURES = ("full_left",)
AXES = {
    "grid_h": {"type": "int", "default": "core 7..8; scatter 5..14", "valid": "5..14"},
    "half_w": {"type": "int", "default": "core 3..4; scatter 2..8", "valid": "2..8"},
    "marks": {"type": "int", "default": "core 6..7; scatter 1..20, capacity bound", "valid": "1..20"},
    "palette_size": {"type": "int", "default": "core 2; scatter 1..8, count/pool bound", "valid": "1..8"},
    "palette_kind": {"type": "str", "default": "keyed palette family", "valid": "|".join(PALETTE_KINDS)},
    "texture": {"type": "str", "default": "alias of palette_kind", "valid": "|".join(HELPFUL_TEXTURES)},
    "position_bias": {"type": "str", "default": "left_half", "valid": "left_half", "probe": "diagnostic"},
    "density": {"type": "str", "default": "mixed", "valid": "mixed", "probe": "diagnostic"},
}
# Compatibility names do not pretend to be independent combinatorial axes.
AXIS_ALIASES = {"n_distinct_colors": "palette_size"}
# Infeasible tuples are rejected with precise exception.incompatible_axes.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
EXAMPLES_NEEDED = 3
SCHEDULE_PROFILES = ("objects", "scatter")


def schedule_profile(seed, sample_index, difficulty=None):
    """Seed-phased alternation; exact overrides may relax teaching geometry."""
    return SCHEDULE_PROFILES[(sample_index + seed) % 2]


def _incompatible(message, axes, supplied):
    exc = ValueError(message)
    exc.incompatible_axes = tuple(name for name in axes if name in supplied)
    raise exc


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES) - set(AXIS_ALIASES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    clean = dict(overrides)
    limits = {"grid_h": (5, 14), "half_w": (2, 8), "marks": (1, 20),
              "palette_size": (1, 8), "n_distinct_colors": (1, 8)}
    for key, (lo, hi) in limits.items():
        if key in clean and (type(clean[key]) is not int or not lo <= clean[key] <= hi):
            raise ValueError(f"{key} must be an integer in {lo}..{hi}")
    for key, choices in (("palette_kind", PALETTE_KINDS),
                         ("texture", PALETTE_KINDS + DEGENERATE_TEXTURES),
                         ("position_bias", ("left_half",)), ("density", ("mixed",))):
        if key in clean and (not isinstance(clean[key], str) or clean[key] not in choices):
            raise ValueError(f"{key} must be one of {choices}")
    if all(key in clean for key in ("palette_size", "n_distinct_colors")):
        if clean["palette_size"] != clean["n_distinct_colors"]:
            _incompatible("palette_size and n_distinct_colors must agree",
                          ("palette_size", "n_distinct_colors"), clean)
    if clean.get("texture") in PALETTE_KINDS and "palette_kind" in clean:
        if clean["texture"] != clean["palette_kind"]:
            _incompatible("texture and palette_kind aliases must agree",
                          ("texture", "palette_kind"), clean)
    return clean


def _count(ctx, name, lo, hi, ordinary):
    # Every band honors the full advertised domain. Defaults can favor a core.
    if name in ctx.overrides:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_choice(name, tuple(ordinary))


def _connected_shape(candidates, count, rng):
    allowed = set(candidates)
    cells = {rng.choice(sorted(allowed))}
    while len(cells) < count:
        frontier = sorted({(r + dr, c + dc) for r, c in cells
                           for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
                          if (r + dr, c + dc) in allowed and (r + dr, c + dc) not in cells})
        if not frontier:
            raise RuntimeError("connected placement exhausted a feasible rectangle")
        cells.add(rng.choice(frontier))
    return sorted(cells)


def _place_objects(grid, ctx, colors, marks):
    """Two disjoint row bands retain true components without fixed templates."""
    h, half_w = len(grid), len(grid[0]) // 2
    split = h // 2
    bands = ([ (r, c) for r in range(split) for c in range(half_w)],
             [ (r, c) for r in range(split + 1, h) for c in range(half_w)])
    counts = (marks // 2, marks - marks // 2)
    if len(colors) != 2 or min(counts) < 2 or any(n > len(b) for n, b in zip(counts, bands)):
        return False
    for index, (band, count, color) in enumerate(zip(bands, counts, colors)):
        for r, c in _connected_shape(band, count, ctx.draw_rng(f"object_{index}")):
            grid[r][c] = color
    return True


def _place_scatter(grid, ctx, colors, marks):
    h, half_w = len(grid), len(grid[0]) // 2
    rng = ctx.draw_rng("scattered_positions")
    all_cells = [(r, c) for r in range(h) for c in range(half_w)]
    # Reserve the two neighbors of a corner singleton. Dense exact overrides
    # can consume those neighbors; this is an explicit override-only relaxation.
    if marks <= len(all_cells) - 2:
        row = rng.choice((0, h - 1))
        anchor = (row, 0)
        forbidden = {anchor, (row, 1), (1 if row == 0 else h - 2, 0)}
        positions = [anchor] + rng.sample([p for p in all_cells if p not in forbidden], marks - 1)
    else:
        positions = rng.sample(all_cells, marks)
    values = list(colors)
    values.extend(ctx.draw_rng("repeated_colors").choices(colors, k=marks - len(colors)))
    # Every drawn foreground color is realized; no coupon-collector shortfall.
    ctx.draw_rng("color_positions").shuffle(values)
    for (r, c), value in zip(positions, values):
        grid[r][c] = value


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    supplied = _validate_overrides(overrides)
    normalized = dict(supplied)
    count_request = supplied.get("palette_size", supplied.get("n_distinct_colors"))
    count_axes = tuple(name for name in ("palette_size", "n_distinct_colors") if name in supplied)
    if count_request is not None:
        normalized["palette_size"] = count_request
        normalized["n_distinct_colors"] = count_request
    fixture = supplied.get("texture") if supplied.get("texture") in DEGENERATE_TEXTURES else None
    kind_request = supplied.get("palette_kind", supplied.get("texture") if not fixture else None)
    if kind_request is not None:
        normalized["palette_kind"] = kind_request
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=normalized)
    core = schedule_profile(seed, sample_index, difficulty) == "objects"
    # A feasible exact count must constrain free geometry before it is drawn.
    # Only a fully pinned impossible geometry/count tuple is rejected below.
    if fixture == "full_left" and "marks" in supplied:
        feasible = [(height, half) for height in range(5, 15) for half in range(2, 9)
                    if height * half == supplied["marks"]
                    and ("grid_h" not in supplied or height == supplied["grid_h"])
                    and ("half_w" not in supplied or half == supplied["half_w"])]
        if not feasible:
            _incompatible("full_left marks has no feasible grid_h * half_w equality",
                          ("texture", "marks", "grid_h", "half_w"), supplied)
        h = _count(ctx, "grid_h", 5, 14, sorted({height for height, half in feasible}))
        half_w = _count(ctx, "half_w", 2, 8, [half for height, half in feasible if height == h])
    else:
        required_marks = supplied.get("marks", 1)
        requested_half = supplied.get("half_w", 8)
        minimum_h = max(5, (required_marks + requested_half - 1) // requested_half)
        h_defaults = tuple(v for v in ((7, 8) if core else range(5, 15)) if v >= minimum_h)
        if not h_defaults:
            h_defaults = tuple(range(minimum_h, 15))
        h = _count(ctx, "grid_h", 5, 14, h_defaults)
        minimum_half = max(2, (required_marks + h - 1) // h)
        half_defaults = tuple(v for v in (((3, 4) if h == 7 else (4,)) if core else range(2, 9))
                              if v >= minimum_half)
        if not half_defaults:
            half_defaults = tuple(range(minimum_half, 9))
        half_w = _count(ctx, "half_w", 2, 8, half_defaults)
    capacity = h * half_w
    if fixture == "full_left":
        if "marks" in supplied and supplied["marks"] != capacity:
            _incompatible("full_left requires marks equal grid_h * half_w",
                          ("texture", "marks", "grid_h", "half_w"), supplied)
        marks = capacity
    else:
        default_max = min(20, capacity - 2)
        lower = max(1, count_request or 1)
        if lower > min(20, capacity):
            _incompatible("palette_size/n_distinct_colors exceeds available marks/capacity",
                          count_axes + ("marks", "grid_h", "half_w"), supplied)
        core_marks = {"easy": (6, 6, 7), "hard": (6, 7, 7)}.get(difficulty, (6, 7))
        defaults = tuple(n for n in (core_marks if core else range(lower, default_max + 1)) if n >= lower)
        if not core:
            favored = range(2, 7) if difficulty == "easy" else (range(12, 21) if difficulty == "hard" else ())
            defaults += tuple(n for n in favored if lower <= n <= default_max) * 3
        if not defaults:
            defaults = tuple(range(lower, min(20, capacity) + 1))
        marks = _count(ctx, "marks", 1, 20, defaults)
        if marks > capacity:
            _incompatible("marks exceeds grid_h * half_w",
                          ("marks", "grid_h", "half_w"), supplied)
    if count_request is not None and count_request > marks:
        _incompatible("palette_size/n_distinct_colors cannot exceed marks",
                      count_axes + ("marks",), supplied)
    allowed_kinds = tuple(k for k in PALETTE_KINDS if count_request is None or len(_PALETTES[k]) >= count_request)
    if kind_request is not None and kind_request not in allowed_kinds:
        _incompatible("palette_size/n_distinct_colors exceeds requested palette_kind/texture pool",
                      count_axes + ("palette_kind", "texture"), supplied)
    # A default scatter example must use a color unseen in the canonical data.
    # Warm-only is still available as an exact control and in object examples.
    defaults = allowed_kinds if core else tuple(k for k in allowed_kinds if k != "warm")
    kind = ctx.draw_choice("palette_kind", allowed_kinds if kind_request is not None else defaults)
    if not fixture:
        ctx.draw_choice("texture", (kind,))
    ctx.draw_choice("position_bias", ("left_half",))
    ctx.draw_choice("density", ("mixed",))
    pool = _PALETTES[kind]
    max_colors = min(marks, len(pool))
    choices = (min(2, max_colors),) if core else tuple(range(1, max_colors + 1))
    ncolors = _count(ctx, "palette_size", 1, max_colors, choices)
    ctx.draw_choice("n_distinct_colors", (ncolors,))
    palette_rng = ctx.draw_rng("foreground_palette:" + kind)
    novel = [v for v in pool if v in (1, 5, 8)]
    if not core and novel:
        first = palette_rng.choice(novel)
        colors = [first] + palette_rng.sample([v for v in pool if v != first], ncolors - 1)
    else:
        colors = palette_rng.sample(pool, ncolors)
    grid = full_grid(h, 2 * half_w + 1, 0)
    for row in grid:
        row[half_w] = 9
    if fixture == "empty_left":
        return grid
    if fixture == "full_left":
        for i in range(capacity):
            grid[i // half_w][i % half_w] = colors[i % len(colors)]
        return grid
    if not core or not _place_objects(grid, ctx, colors, marks):
        _place_scatter(grid, ctx, colors, marks)
    if fixture == "no_axis":
        for row in grid:
            row[half_w] = 0
    return grid


def self_check(grid, *, difficulty=None, meta=None):
    """Pixel-only domain checks; metadata cannot waive an invalid input."""
    if not isinstance(grid, (list, tuple)) or not grid or not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer colors 0..9"]
    errors = []
    if not 5 <= h <= 14 or w % 2 != 1 or not 2 <= w // 2 <= 8:
        errors.append("geometry outside height 5..14 and odd width 5..17")
    axis = w // 2
    if any(row[axis] != 9 for row in grid):
        errors.append("central column must be a full-height 9-axis")
    if any(value == 9 for row in grid for c, value in enumerate(row) if c != axis):
        errors.append("9 may occur only on the central axis")
    if any(value != 0 for row in grid for value in row[axis + 1:]):
        errors.append("right half must initially be zero")
    if not any(1 <= value <= 8 for row in grid for value in row[:axis]):
        errors.append("left half must contain at least one source mark")
    return errors


def observe_overrides(grid):
    axis = len(grid[0]) // 2
    values = [v for row in grid for v in row[:axis] if v not in (0, 9)]
    return {"grid_h": len(grid), "half_w": axis, "marks": len(values),
            "palette_size": len(set(values)), "n_distinct_colors": len(set(values))}


def _components(grid):
    """4-connected nonbackground source components, allowing mixed colors."""
    axis = len(grid[0]) // 2
    unseen = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row[:axis]) if value not in (0, 9)}
    components = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        component, todo = {start}, [start]
        while todo:
            r, c = todo.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in unseen:
                    unseen.remove(point)
                    component.add(point)
                    todo.append(point)
        components.append(component)
    return components


def strict_canonical_like(grid):
    errors = self_check(grid)
    if errors:
        return errors
    components = _components(grid)
    if len(components) != 2 or any(not 2 <= len(cells) <= 4 for cells in components):
        errors.append("canonical topology needs two source components of 2..4 cells")
    if any(len({grid[r][c] for r, c in cells}) != 1 for cells in components):
        errors.append("canonical components must be monochrome")
    if observe_overrides(grid)["palette_size"] != 2:
        errors.append("canonical topology uses two distinct source colors")
    if (len(grid), len(grid[0])) not in ((7, 7), (7, 9), (8, 9)):
        errors.append("outside canonical size profiles")
    return errors


def _rival(grid, keep):
    """Rival helper only; never used to generate reference labels."""
    axis = len(grid[0]) // 2
    out = [list(row) for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row[:axis]):
            if value not in (0, 9) and keep(r, c, value):
                out[r][2 * axis - c] = value
    return out


def _drop_singletons(grid):
    kept = set().union(*(cells for cells in _components(grid) if len(cells) > 1))
    return _rival(grid, lambda r, c, value: (r, c) in kept)


def _ignore_outer_edge(grid):
    return _rival(grid, lambda r, c, value: c > 0)


def _canonical_colors_only(grid):
    return _rival(grid, lambda r, c, value: value in (2, 3, 4, 6, 7))


SEMANTIC_RIVALS = {"drop_singletons": _drop_singletons,
                   "ignore_outer_edge": _ignore_outer_edge,
                   "canonical_colors_only": _canonical_colors_only}
SEMANTIC_WITNESSES = {
    "singleton_source": lambda grid: any(len(cells) == 1 for cells in _components(grid)),
    "outer_edge_source": lambda grid: any(row[0] not in (0, 9) for row in grid),
    "novel_source_color": lambda grid: any(value in (1, 5, 8) for row in grid for value in row),
}
WITNESS_RIVALS = {"singleton_source": ["drop_singletons"],
                  "outer_edge_source": ["ignore_outer_edge"],
                  "novel_source_color": ["canonical_colors_only"]}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Finite declared-rival teaching check, not a universal induction proof."""
    return [f"declared competitor {name!r} fits every demonstration"
            for name, rival in LESSON_COMPETITORS.items()
            if all(rival(pair["input"]) == pair["output"] for pair in demos)]
