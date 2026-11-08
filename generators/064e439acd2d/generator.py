"""Exact input sampler for 1f642eb9 / 064e439acd2d.

The unchanged canonical Racket rule copies aligned colored sources onto a
solid cyan region's near bounding-box edge, preserving the sources. Diagonal
sources are ignored. This sampler keeps projection targets distinct, so the
reference rule's collision priority is intentionally outside its domain.

Default lessons alternate rich line witnesses with varied ordinary boards.
Explicit controls select ordinary draws and are realized exactly or rejected
with a structured incompatibility. n_dots counts ALIGNED source cells; a
requested diag_decoy adds exactly one extra diagonal source.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "064e439acd2d"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "7288da9bfc7e"
SUMMARY = (
    "Copy 1-8 aligned colored source cells onto the near edge of a solid "
    "cyan line or rectangle, keeping sources and ignoring optional diagonal "
    "decoys. Exact geometry/count controls; repeated colors and interior "
    "sources; four-example lessons distinguish eight executable rivals."
)
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0
INVARIANTS = [
    "solid color-8 line or rectangle with background 0 and exterior colored sources",
    "at least one aligned source; every intended target is distinct",
    "n_dots counts aligned sources exactly; diag_decoy adds one ignored source",
    "source colors may repeat; color 8 and background 0 retain their fixed roles",
    "unoverridden even samples each refute every declared lesson competitor",
]
HELPFUL_TEXTURES = ("plain", "diag_decoy", "both_sides")
# These remain callable negative fixtures, not ordinary training textures.
DEGENERATE_TEXTURES = ("no_dots", "full_grid")
AXES = {
    "grid_h": {"type": "int", "default": "10 on rich draws; band-weighted 5..14 otherwise", "valid": "5..14"},
    "grid_w": {"type": "int", "default": "10 on rich draws; band-weighted 5..14 otherwise", "valid": "5..14"},
    "shape_kind": {"type": "str", "default": "rich hline/broad/rich vline/broad schedule", "valid": "hline|vline|rect"},
    "n_dots": {"type": "int", "default": "3 on rich draws; band-weighted 1..8 otherwise", "valid": "1..8",
               "doc": "Exact number of aligned source cells, including repeated colors; excludes the single diagonal decoy."},
    "texture": {"type": "str", "default": "diag_decoy on rich draws; rng helpful otherwise", "valid": "plain|diag_decoy|both_sides",
                "doc": "plain: no diagonal; diag_decoy: exactly one extra diagonal; both_sides: opposite source sides and no diagonal."},
}
# Only actual impossible tuples raise with their precise incompatible_axes.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = ("rich_hline", "broad", "rich_vline")
_DOT_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)


def schedule_profile(seed, sample_index, difficulty=None):
    """Semantic profile of a default draw; random geometry is not periodic."""
    return ("rich_hline", "broad", "rich_vline", "broad")[sample_index % 4]


def _project(r, c, rmin, rmax, cmin, cmax):
    if rmin <= r <= rmax:
        return (r, cmin) if c < cmin else (r, cmax)
    if cmin <= c <= cmax:
        return (rmin, c) if r < rmin else (rmax, c)
    return None


def _bbox(grid):
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 8]
    if not cells:
        raise ValueError("no color-8 cells")
    return (min(r for r, c in cells), max(r for r, c in cells),
            min(c for r, c in cells), max(c for r, c in cells))


def _validate_call_arguments(seed, sample_index):
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be non-negative")


def _validate_overrides(overrides, difficulty):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    for name, value in overrides.items():
        if value is None:
            continue
        if name in ("grid_h", "grid_w", "n_dots"):
            low, high = (1, 8) if name == "n_dots" else (5, 14)
            if type(value) is not int or not low <= value <= high:
                raise ValueError(f"{name} must be an integer in {low}..{high}, not {value!r}")
        else:
            allowed = ("hline", "vline", "rect") if name == "shape_kind" else HELPFUL_TEXTURES + DEGENERATE_TEXTURES
            if not isinstance(value, str) or value not in allowed:
                raise ValueError(f"invalid {name}: {value!r}; expected {allowed}")


def _incompatible(ctx, reason, axes):
    active = tuple(name for name in axes if ctx.overrides.get(name) is not None)
    error = ValueError(f"incompatible overrides {active}: {reason}")
    error.incompatible_axes = active
    raise error


def _integer_axis(ctx, name, choices):
    low, high = (1, 8) if name == "n_dots" else (5, 14)
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int_strict(name, low, high)
    return ctx.draw_choice(name, choices)


def _weighted_values(low, high, favored):
    return list(range(low, high + 1)) + [value for value in favored if low <= value <= high] * 3


def _size_options(h, w, kind, count):
    if kind == "hline":
        return [(1, length) for length in range(max(3, count), w - 1)]
    if kind == "vline":
        return [(length, 1) for length in range(max(3, count), h - 1)]
    return [(rh, rw) for rh in range(2, min(6, h - 2) + 1)
            for rw in range(2, min(6, w - 2) + 1) if 2 * rh + 2 * rw - 4 >= count]


def _parameters(ctx, rich):
    ov = ctx.overrides
    minimum = 2 if ov.get("texture") == "both_sides" else 1
    maximum = 8
    if ov.get("shape_kind") == "hline" and ov.get("grid_w") is not None:
        maximum = min(maximum, ov["grid_w"] - 2)
    if ov.get("shape_kind") == "vline" and ov.get("grid_h") is not None:
        maximum = min(maximum, ov["grid_h"] - 2)
    favored_count = (1, 2, 3) if ctx.difficulty == "easy" else (5, 6, 7, 8) if ctx.difficulty == "hard" else (2, 3, 4, 5)
    count = _integer_axis(ctx, "n_dots", [3] if rich else _weighted_values(minimum, maximum, favored_count))
    if count < minimum:
        _incompatible(ctx, "both_sides requires n_dots >= 2", ("texture", "n_dots"))
    h_limit, w_limit = ov.get("grid_h") or 14, ov.get("grid_w") or 14
    feasible = [kind for kind in ("hline", "vline", "rect") if _size_options(h_limit, w_limit, kind, count)]
    if ov.get("shape_kind") is not None and ov["shape_kind"] not in feasible:
        _incompatible(ctx, "shape_kind and n_dots exceed distinct target capacity for grid_h/grid_w",
                      ("shape_kind", "n_dots", "grid_h", "grid_w"))
    if ov.get("shape_kind") is not None:
        kind = ctx.draw_choice("shape_kind", feasible)
    elif rich:
        kind = ctx.draw_choice("shape_kind", ["hline" if ctx.sample_index % 4 == 0 else "vline"])
    else:
        kind = ctx.draw_choice("shape_kind", feasible)
    min_h = max(5, count + 2) if kind == "vline" else 5
    min_w = max(5, count + 2) if kind == "hline" else 5
    favored_size = (5, 6, 7, 8) if ctx.difficulty == "easy" else (10, 11, 12, 13, 14) if ctx.difficulty == "hard" else (7, 8, 9, 10, 11)
    h = _integer_axis(ctx, "grid_h", [10] if rich else _weighted_values(min_h, 14, favored_size))
    w = _integer_axis(ctx, "grid_w", [10] if rich else _weighted_values(min_w, 14, favored_size))
    textures = [name for name in HELPFUL_TEXTURES if name != "both_sides" or count >= 2]
    texture = ctx.draw_choice("texture", textures if ov.get("texture") is not None else ["diag_decoy"] if rich else textures)
    return h, w, kind, count, texture


def _put_region(grid, bounds):
    rmin, rmax, cmin, cmax = bounds
    for r in range(rmin, rmax + 1):
        for c in range(cmin, cmax + 1):
            grid[r][c] = 8


def _rich_board(ctx, h, w, kind):
    """One random input independently distinguishes all eight named rivals."""
    rng = ctx.draw_rng("rich_layout")
    length = rng.choice((4, 5, 6))
    rh, rw = (1, length) if kind == "hline" else (length, 1)
    rmin, cmin = rng.randint(2, h - rh - 2), rng.randint(2, w - rw - 2)
    rmax, cmax = rmin + rh - 1, cmin + rw - 1
    grid = full_grid(h, w, 0)
    _put_region(grid, (rmin, rmax, cmin, cmax))
    if kind == "hline":
        sources = [(rmin, cmin - 1), (rmin - 1, cmin + 1), (rmin + 2, cmin + 2)]
    else:
        sources = [(rmin - 1, cmin), (rmin + 1, cmin - 1), (rmin + 2, cmin + 2)]
    colors = ctx.draw_rng("source_palette").sample(_DOT_COLORS, 3)
    for (r, c), color in zip(sources, (colors[0], colors[0], colors[1])):
        grid[r][c] = color
    # The opposite endpoint stays cyan: the diagonal rival cannot be masked.
    dr, dc = rng.randint(rmax + 1, h - 1), rng.randint(cmax + 1, w - 1)
    grid[dr][dc] = colors[2]
    if ctx.draw_choice("reflect_rows", (False, True)):
        grid.reverse()
    if ctx.draw_choice("reflect_columns", (False, True)):
        grid = [list(reversed(row)) for row in grid]
    return grid


def _source_groups(h, w, bounds):
    rmin, rmax, cmin, cmax = bounds
    groups = {}
    for r in range(h):
        for c in range(w):
            if rmin <= r <= rmax and cmin <= c <= cmax:
                continue
            target = _project(r, c, *bounds)
            if target is not None:
                side = ("left" if c < cmin else "right") if rmin <= r <= rmax else ("above" if r < rmin else "below")
                groups.setdefault(target, []).append((r, c, side))
    return groups


def _ordinary_board(ctx, h, w, kind, count, texture):
    rng = ctx.draw_rng("layout")
    sizes = _size_options(h, w, kind, count)
    if not sizes:
        _incompatible(ctx, "shape_kind and n_dots exceed distinct target capacity for grid_h/grid_w",
                      ("shape_kind", "n_dots", "grid_h", "grid_w"))
    rh, rw = rng.choice(sizes)
    rmin, cmin = rng.randint(1, h - rh - 1), rng.randint(1, w - rw - 1)
    bounds = rmin, rmin + rh - 1, cmin, cmin + rw - 1
    grid = full_grid(h, w, 0)
    _put_region(grid, bounds)
    groups = _source_groups(h, w, bounds)
    chosen = []
    used = set()
    if texture == "both_sides":
        first, second = rng.choice((("left", "right"), ("above", "below")))
        for side in (first, second):
            available = [(target, source) for target in sorted(groups) if target not in used
                         for source in groups[target] if source[2] == side]
            target, source = rng.choice(available)
            chosen.append(source)
            used.add(target)
    remaining = rng.sample([target for target in sorted(groups) if target not in used], count - len(chosen))
    chosen.extend(rng.choice(groups[target]) for target in remaining)
    palette = ctx.draw_rng("source_palette").sample(_DOT_COLORS, count + (1 if texture == "diag_decoy" and count < 8 else 0))
    source_colors = palette[:count]
    # Repeated source colors are canonical-lawful; vary them outside rich draws.
    if count >= 2 and ctx.draw_choice("repeat_source_color", (False, True)):
        source_colors[-1] = source_colors[0]
    for (r, c, side), color in zip(chosen, source_colors):
        grid[r][c] = color
    if texture == "diag_decoy":
        r0, r1, c0, c1 = bounds
        outside_rows = list(range(r0)) + list(range(r1 + 1, h))
        outside_columns = list(range(c0)) + list(range(c1 + 1, w))
        color = palette[-1] if count < 8 else ctx.draw_rng("diagonal_palette").choice(_DOT_COLORS)
        grid[rng.choice(outside_rows)][rng.choice(outside_columns)] = color
    return grid


def _draw_from_degenerate(name, ctx):
    if ctx.overrides.get("n_dots") is not None:
        _incompatible(ctx, "negative no-dot fixture cannot realize a positive n_dots", ("texture", "n_dots"))
    h = _integer_axis(ctx, "grid_h", list(range(5, 15)))
    w = _integer_axis(ctx, "grid_w", list(range(5, 15)))
    if name == "full_grid":
        if ctx.overrides.get("shape_kind") not in (None, "rect"):
            _incompatible(ctx, "full_grid is a rectangle, not the requested shape_kind", ("texture", "shape_kind"))
        return full_grid(h, w, 8)
    kind = ctx.draw_choice("shape_kind", ("hline", "vline", "rect"))
    rng = ctx.draw_rng("negative_layout")
    rh, rw = rng.choice(_size_options(h, w, kind, 1))
    r, c = rng.randint(1, h - rh - 1), rng.randint(1, w - rw - 1)
    grid = full_grid(h, w, 0)
    _put_region(grid, (r, r + rh - 1, c, c + rw - 1))
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call_arguments(seed, sample_index)
    _validate_overrides(overrides, difficulty)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], ctx)
    rich = sample_index % 2 == 0 and not any(value is not None for value in overrides.values())
    h, w, kind, count, texture = _parameters(ctx, rich)
    return _rich_board(ctx, h, w, kind) if rich else _ordinary_board(ctx, h, w, kind, count, texture)


def observe_overrides(grid):
    """Recover exact controls from the returned pixels, never RNG bookkeeping."""
    bounds = _bbox(grid)
    rmin, rmax, cmin, cmax = bounds
    kind = "hline" if rmin == rmax else "vline" if cmin == cmax else "rect"
    count = sum(_project(r, c, *bounds) is not None for r, row in enumerate(grid)
                for c, color in enumerate(row) if color not in (0, 8))
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "shape_kind": kind, "n_dots": count}


def self_check(grid, *, difficulty=None, meta=None):
    """Check lawful task structure, independently of the sampler's count cap."""
    if not isinstance(grid, (list, tuple)) or not grid or not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid must be nonempty and rectangular"]
    if any(not isinstance(row, (list, tuple)) or len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    if any(type(color) is not int or not 0 <= color <= 9 for row in grid for color in row):
        return ["cells must be integer colors 0..9, not booleans or coerced values"]
    cyans = [(r, c) for r, row in enumerate(grid) for c, color in enumerate(row) if color == 8]
    if not cyans:
        return ["no color-8 cells (reference rule requires a cyan region)"]
    bounds = _bbox(grid)
    rmin, rmax, cmin, cmax = bounds
    errors = []
    if len(cyans) != (rmax - rmin + 1) * (cmax - cmin + 1):
        errors.append("color-8 bounding box must be a solid line or rectangle")
    if len(cyans) < 3:
        errors.append("color-8 region needs at least three cells")
    targets = []
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color in (0, 8):
                continue
            if rmin <= r <= rmax and cmin <= c <= cmax:
                errors.append("colored sources must be exterior to the cyan region")
            target = _project(r, c, *bounds)
            if target is not None:
                targets.append(target)
    if not targets:
        errors.append("at least one aligned source is required; no-dot identities are negative fixtures")
    if len(targets) != len(set(targets)):
        errors.append("projection target collision is outside this generator's declared domain")
    return errors


# Task-local executable semantic declarations for 064e439acd2d.
# These diagnostics construct executable rivals and witnesses. They NEVER
# supply generated labels; the unchanged canonical Racket rule does that.
# No imports or external state are needed by these pure diagnostics.


def _semantic_scene(grid):
    """Read geometry independently of layout helpers; do not modify the grid."""
    cyans = [(r, c) for r, row in enumerate(grid)
             for c, color in enumerate(row) if color == 8]
    if not cyans:
        raise ValueError("semantic diagnostics require at least one color-8 cell")
    bounds = (min(r for r, c in cyans), max(r for r, c in cyans),
              min(c for r, c in cyans), max(c for r, c in cyans))
    dots = [(r, c, color) for r, row in enumerate(grid)
            for c, color in enumerate(row) if color not in (0, 8)]
    return bounds, dots


def _semantic_target(r, c, bounds):
    rmin, rmax, cmin, cmax = bounds
    if rmin <= r <= rmax:
        return r, cmin if c < cmin else cmax
    if cmin <= c <= cmax:
        return (rmin if r < rmin else rmax), c
    return None


def _semantic_dot_order(dot):
    return dot[2], dot[0], dot[1]


def _diagnostic_projection_prediction(grid, variant="intended"):
    """A pure prediction for rival comparisons, never a label authority.

    The intended variant mirrors the selected rule so the Racket-backed gate
    can independently verify each claimed counterexample. Source positions and
    cyan bounds are frozen from the input. The declared generator manifold has
    a solid cyan bbox, exterior sources, and distinct intended targets.
    """
    variants = {"intended", "border_only", "project_diagonal_to_corner",
                "rectangle_only", "one_per_color", "move_sources",
                "horizontal_projection_only", "vertical_projection_only",
                "ignore_touching_sources"}
    if variant not in variants:
        raise ValueError(f"unknown diagnostic rival: {variant}")
    bounds, dots = _semantic_scene(grid)
    rmin, rmax, cmin, cmax = bounds
    out = [list(row) for row in grid]
    h, w = len(grid), len(grid[0])
    if variant == "rectangle_only" and (rmin == rmax or cmin == cmax):
        return out
    seen_colors = set()
    for r, c, color in sorted(dots, key=_semantic_dot_order):
        if variant == "one_per_color":
            if color in seen_colors:
                continue
            seen_colors.add(color)
        if variant == "border_only" and r not in (0, h - 1) and c not in (0, w - 1):
            continue
        target = _semantic_target(r, c, bounds)
        horizontal = rmin <= r <= rmax
        if variant == "horizontal_projection_only" and not horizontal:
            continue
        if variant == "vertical_projection_only" and horizontal:
            continue
        if target is None:
            if variant != "project_diagonal_to_corner":
                continue
            target = (min(max(r, rmin), rmax), min(max(c, cmin), cmax))
        tr, tc = target
        if variant == "ignore_touching_sources" and abs(tr - r) + abs(tc - c) == 1:
            continue
        if variant == "move_sources":
            out[r][c] = 0
        out[tr][tc] = color
    return out


def _rival_border_only(grid):
    return _diagnostic_projection_prediction(grid, "border_only")


def _rival_project_diagonal_to_corner(grid):
    return _diagnostic_projection_prediction(grid, "project_diagonal_to_corner")


def _rival_rectangle_only(grid):
    return _diagnostic_projection_prediction(grid, "rectangle_only")


def _rival_one_per_color(grid):
    return _diagnostic_projection_prediction(grid, "one_per_color")


def _rival_move_sources(grid):
    return _diagnostic_projection_prediction(grid, "move_sources")


def _rival_horizontal_projection_only(grid):
    return _diagnostic_projection_prediction(grid, "horizontal_projection_only")


def _rival_vertical_projection_only(grid):
    return _diagnostic_projection_prediction(grid, "vertical_projection_only")


def _rival_ignore_touching_sources(grid):
    return _diagnostic_projection_prediction(grid, "ignore_touching_sources")


def _witness_nonborder_projection(grid):
    return _diagnostic_projection_prediction(grid) != _rival_border_only(grid)


def _witness_ignored_diagonal(grid):
    # Exact disagreement avoids claiming that a diagonal refutes a rival when
    # its hypothetical corner write is masked by a later colored projection.
    return _diagnostic_projection_prediction(grid) != _rival_project_diagonal_to_corner(grid)


def _witness_line_projection(grid):
    return _diagnostic_projection_prediction(grid) != _rival_rectangle_only(grid)


def _witness_repeated_source_color(grid):
    return _diagnostic_projection_prediction(grid) != _rival_one_per_color(grid)


def _witness_preserved_sources(grid):
    return _diagnostic_projection_prediction(grid) != _rival_move_sources(grid)


def _witness_horizontal_projection(grid):
    return _diagnostic_projection_prediction(grid) != _rival_vertical_projection_only(grid)


def _witness_vertical_projection(grid):
    return _diagnostic_projection_prediction(grid) != _rival_horizontal_projection_only(grid)


def _witness_touching_source(grid):
    return _diagnostic_projection_prediction(grid) != _rival_ignore_touching_sources(grid)


SEMANTIC_RIVALS = {
    "border_only": _rival_border_only,
    "project_diagonal_to_corner": _rival_project_diagonal_to_corner,
    "rectangle_only": _rival_rectangle_only,
    "one_per_color": _rival_one_per_color,
    "move_sources": _rival_move_sources,
    "horizontal_projection_only": _rival_horizontal_projection_only,
    "vertical_projection_only": _rival_vertical_projection_only,
    "ignore_touching_sources": _rival_ignore_touching_sources,
}

SEMANTIC_WITNESSES = {
    "nonborder_projection": _witness_nonborder_projection,
    "ignored_diagonal": _witness_ignored_diagonal,
    "line_projection": _witness_line_projection,
    "repeated_source_color": _witness_repeated_source_color,
    "preserved_sources": _witness_preserved_sources,
    "horizontal_projection": _witness_horizontal_projection,
    "vertical_projection": _witness_vertical_projection,
    "touching_source": _witness_touching_source,
}

WITNESS_RIVALS = {
    "nonborder_projection": ["border_only"],
    "ignored_diagonal": ["project_diagonal_to_corner"],
    "line_projection": ["rectangle_only"],
    "repeated_source_color": ["one_per_color"],
    "preserved_sources": ["move_sources"],
    "horizontal_projection": ["vertical_projection_only"],
    "vertical_projection": ["horizontal_projection_only"],
    "touching_source": ["ignore_touching_sources"],
}

# These four fit all available labeled canonical pairs. The other four are
# already refuted canonically but remain important finite lesson competitors.
CANONICAL_SHORTCUTS = {
    "border_only": _rival_border_only,
    "project_diagonal_to_corner": _rival_project_diagonal_to_corner,
    "rectangle_only": _rival_rectangle_only,
    "ignore_touching_sources": _rival_ignore_touching_sources,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def strict_canonical_like(grid):
    """Validate this task's declared manifold, including its canonical inputs.

    self_check validates task structure independently of sampler count controls: a real
    canonical train input has six projected dots, and the query input has seven.
    """
    return self_check(grid)


def lesson_identifiable(demos, query):
    """Detect ambiguity relative to the finite declared rival set only.

    Observed Racket labels are the sole answers being checked. Surviving all
    demos AND agreeing on the query is reported by the gate as survived_all;
    it is not a different answer to this query and is not rejected here.
    """
    reasons = []
    for name, rival in sorted(LESSON_COMPETITORS.items()):
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"{name} fits every demonstration but changes the query answer")
    return reasons
