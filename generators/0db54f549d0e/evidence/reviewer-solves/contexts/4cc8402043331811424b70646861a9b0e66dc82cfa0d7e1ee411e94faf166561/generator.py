"""Input sampler for the fixed-window pairwise-intersection gallery.

The selected Racket authority supplies labels. Python ``rule_mirror`` is an
explicit diagnostic oracle for witness/rival checks, never a label authority.
Even unpinned sample indices provide asymmetric, color-permuted teaching
examples; odd indices preserve a broader density, padding and palette mixture.
"""
from __future__ import annotations

from itertools import permutations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0db54f549d0e"
TASK_ID = GENERATOR_ID
RULE_HASH = "2a9df9793155"
VERSION = "2.2.0"
SUMMARY = (
    "Four fixed 3x3 binary prototypes on a 7..11 by 11..15 canvas. "
    "Each row/column pair contributes its intersection, painted 8, to a "
    "fixed 7x7 gallery. Prototype colors do not determine their roles."
)
INVARIANTS = [
    "rectangular integer-color grid, 7..11 rows and 11..15 columns",
    "only the four fixed 3x3 prototype windows may contain nonzero cells",
    "each window is monochromatic or empty; its exact count is 0..9",
    "prototype colors may repeat, including 8; zero alone denotes absence",
]
DEGENERATE_TEXTURES = ("empty_shapes", "full_shapes", "single_overlap")
LAWFUL_DEGENERATE_TEXTURES = DEGENERATE_TEXTURES
SOLID_OUTPUT_JUSTIFICATION = (
    "The unchanged Racket rule intersects Boolean occupancy in four windows. "
    "Empty or pairwise disjoint prototypes legitimately yield an all-zero "
    "7x7 gallery; empty_shapes is an explicit lawful endpoint, not a lesson."
)
AXES = {
    "row0_cells": {"type": "int", "default": "band-weighted; teaching 3..6", "valid": "0..9"},
    "row1_cells": {"type": "int", "default": "band-weighted; teaching 3..6", "valid": "0..9"},
    "col0_cells": {"type": "int", "default": "band-weighted; teaching 3..6", "valid": "0..9"},
    "col1_cells": {"type": "int", "default": "band-weighted; teaching 3..6", "valid": "0..9"},
    "texture": {"type": "str", "default": "random", "valid": "random|empty_shapes|full_shapes|single_overlap"},
}
# A texture fixes every count. Matching counts remain legal; conflicting ones
# are identified precisely instead of accepting a silently ignored request.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"texture": texture, axis: [n for n in range(10) if n != required]}
    for texture, required in (("empty_shapes", 0), ("full_shapes", 9), ("single_overlap", 1))
    for axis in ("row0_cells", "row1_cells", "col0_cells", "col1_cells")
]
_WINDOWS = ((0, 0), (4, 0), (0, 4), (0, 8))
_COUNTS = ("row0_cells", "row1_cells", "col0_cells", "col1_cells")
_CELLS = tuple((r, c) for r in range(3) for c in range(3))
_COLOR_PERMUTATIONS = tuple(permutations((2, 3, 4, 5)))
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 2
SCHEDULE_PROFILES = ("teaching", "varied")
MIN_STRICT_FRAC = 1.0


def schedule_profile(seed, sample_index, difficulty=None):
    """Semantic schedule only; individual grids still depend on the keyed seed."""
    return "teaching" if sample_index % 2 == 0 else "varied"


def _masks(grid):
    return tuple(frozenset((r, c) for r, c in _CELLS if grid[top+r][left+c] != 0)
                 for top, left in _WINDOWS)


def _panels(shapes):
    return tuple(shapes[i] & shapes[2+j] for i in range(2) for j in range(2))


def _render(panels):
    out = full_grid(7, 7, 0)
    for index, cells in enumerate(panels):
        top, left = 4*(index//2), 4*(index % 2)
        for r, c in cells:
            out[top+r][left+c] = 8
    return out


def rule_mirror(grid):
    """Diagnostic occupancy oracle; real generated labels remain Racket-owned."""
    return _render(_panels(_masks(grid)))


def _has_truth_cases(shapes):
    cases = {(cell in shapes[i], cell in shapes[2+j])
             for i in range(2) for j in range(2) for cell in _CELLS}
    return len(cases) == 4


def _teaching_shapes(ctx, counts):
    # Counts are drawn once and never changed by rejection. This rejection only
    # chooses geometry with four distinguishable panels and all Boolean cases.
    rng = ctx.draw_rng("teaching_geometry")
    for _ in range(512):
        shapes = tuple(frozenset(rng.sample(_CELLS, count)) for count in counts)
        if len(set(_panels(shapes))) == 4 and _has_truth_cases(shapes):
            return shapes
    raise RuntimeError("Unable to place an informative teaching geometry in 512 attempts")


def _teaching_colors(ctx, shapes):
    # Preserve the exact canonical palette while breaking the canonical color
    # lookup shortcut. Swapping the two row colors always distinguishes a
    # four-distinct-panel geometry, so this feasible set is never empty.
    desired = _panels(shapes)
    choices = []
    for colors in _COLOR_PERMUTATIONS:
        by_color = dict(zip(colors, shapes))
        mapped = tuple(by_color[color] for color in (2, 3, 4, 5))
        if _panels(mapped) != desired:
            choices.append(colors)
    return ctx.draw_choice("prototype_colors", choices)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    texture = overrides.get("texture")
    texture = "random" if texture is None else texture
    if not isinstance(texture, str) or texture not in ("random", *DEGENERATE_TEXTURES):
        raise ValueError("texture must be random, empty_shapes, full_shapes or single_overlap")
    for axis in _COUNTS:
        value = overrides.get(axis)
        if value is not None and (type(value) is not int or not 0 <= value <= 9):
            raise ValueError(f"{axis} must be a Python integer in 0..9 (not bool)")
    required = {"empty_shapes": 0, "full_shapes": 9, "single_overlap": 1}.get(texture)
    if required is not None:
        for axis in _COUNTS:
            value = overrides.get(axis)
            if value is not None and value != required:
                raise ValueError(f"texture={texture!r} requires {axis}={required}, got {value}")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    ctx.draw_choice("texture", (texture,))
    teaching = (texture == "random" and sample_index % 2 == 0
                and not any(overrides.get(axis) is not None for axis in _COUNTS))
    lo, hi = (2, 4) if difficulty == "easy" else ((4, 8) if difficulty == "hard" else (2, 7))
    counts = []
    for axis in _COUNTS:
        if required is not None:
            bounds = (required, required)
        elif overrides.get(axis) is not None:
            bounds = (0, 9)
        else:
            bounds = (3, 6) if teaching else (lo, hi)
        counts.append(ctx.draw_int_strict(axis, *bounds))
    if texture == "single_overlap":
        point = ctx.draw_choice("singleton_position", _CELLS)
        shapes = (frozenset((point,)),) * 4
    elif teaching:
        shapes = _teaching_shapes(ctx, counts)
    else:
        shapes = tuple(frozenset(ctx.draw_rng(axis+"_geometry").sample(_CELLS, count))
                       for axis, count in zip(_COUNTS, counts))
    if texture != "random":
        height, width, colors = 7, 11, (4, 4, 4, 4)
    elif teaching:
        height, width, colors = 7, 11, _teaching_colors(ctx, shapes)
    else:
        height = 7 + ctx.draw_int("padding_rows", 0, 4)
        width = 11 + ctx.draw_int("padding_columns", 0, 4)
        mode = ctx.draw_choice("palette_profile", ("distinct", "distinct", "shared", "canonical"))
        if mode == "shared":
            color = ctx.draw_color("shared_color", exclude=(0,))
            colors = (color,) * 4
        elif mode == "canonical":
            colors = ctx.draw_choice("prototype_colors", _COLOR_PERMUTATIONS)
        else:
            colors = ctx.draw_distinct_colors("prototype_colors", n=4, exclude=(0,))
    grid = full_grid(height, width, 0)
    for (top, left), color, shape in zip(_WINDOWS, colors, shapes):
        for r, c in shape:
            grid[top+r][left+c] = color
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the declared input manifold without indexing malformed grids."""
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rows"]
    height, width = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid or invalid row"]
    if not (7 <= height <= 11 and 11 <= width <= 15):
        return [f"declared input support is 7..11 by 11..15, got {height}x{width}"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be Python integer ARC colors 0..9, not bool"]
    allowed = {(top+r, left+c) for top, left in _WINDOWS for r, c in _CELLS}
    errors = []
    if any(value != 0 and (r, c) not in allowed
           for r, row in enumerate(grid) for c, value in enumerate(row)):
        errors.append("nonzero cell outside the four fixed prototype windows")
    for axis, (top, left) in zip(_COUNTS, _WINDOWS):
        colors = {grid[top+r][left+c] for r, c in _CELLS} - {0}
        if len(colors) > 1:
            errors.append(f"{axis[:-6]} must be monochromatic or empty")
    return errors


def strict_canonical_like(grid):
    """Task-domain membership, including lawful empty/full endpoints."""
    return self_check(grid)


def observe_overrides(grid):
    """Read realized exact counts from pixels, independent of RNG provenance."""
    return dict(zip(_COUNTS, map(len, _masks(grid))))


def _rival_blank(grid):
    return full_grid(7, 7, 0)


def _rival_union(grid):
    s = _masks(grid)
    return _render(tuple(s[i] | s[2+j] for i in range(2) for j in range(2)))


def _rival_xor(grid):
    s = _masks(grid)
    return _render(tuple(s[i] ^ s[2+j] for i in range(2) for j in range(2)))


def _rival_row_only(grid):
    s = _masks(grid)
    return _render((s[0], s[0], s[1], s[1]))


def _rival_col_only(grid):
    s = _masks(grid)
    return _render((s[2], s[3], s[2], s[3]))


def _rival_transpose_panels(grid):
    p = _panels(_masks(grid))
    return _render((p[0], p[2], p[1], p[3]))


def _rival_swap_rows(grid):
    p = _panels(_masks(grid))
    return _render((p[2], p[3], p[0], p[1]))


def _rival_swap_columns(grid):
    p = _panels(_masks(grid))
    return _render((p[1], p[0], p[3], p[2]))


def _rival_color_roles(grid):
    """Incorrectly assign prototypes by colors 2,3,4,5, as in canonical data."""
    shapes = tuple(frozenset((r, c) for top, left in _WINDOWS for r, c in _CELLS
                             if grid[top+r][left+c] == color)
                   for color in (2, 3, 4, 5))
    return _render(_panels(shapes))


def _rival_color_equality(grid):
    panels = []
    for row_top, row_left in _WINDOWS[:2]:
        for col_top, col_left in _WINDOWS[2:]:
            panels.append(frozenset((r, c) for r, c in _CELLS
                                    if grid[row_top+r][row_left+c] != 0
                                    and grid[row_top+r][row_left+c] == grid[col_top+r][col_left+c]))
    return _render(panels)


def _w_overlap(grid):
    return any(_panels(_masks(grid)))


def _w_boolean_cases(grid):
    return _has_truth_cases(_masks(grid))


def _w_panel_order(grid):
    return len(set(_panels(_masks(grid)))) == 4


def _w_position_over_color(grid):
    return rule_mirror(grid) != _rival_color_roles(grid)


SEMANTIC_RIVALS = {
    "blank": _rival_blank, "union": _rival_union, "xor": _rival_xor,
    "row_only": _rival_row_only, "col_only": _rival_col_only,
    "transpose_panels": _rival_transpose_panels, "swap_rows": _rival_swap_rows,
    "swap_columns": _rival_swap_columns, "canonical_color_roles": _rival_color_roles,
    "color_equality": _rival_color_equality,
}
SEMANTIC_WITNESSES = {
    "positive_overlap": _w_overlap, "boolean_truth_cases": _w_boolean_cases,
    "panel_order": _w_panel_order, "position_over_color": _w_position_over_color,
}
WITNESS_RIVALS = {
    "positive_overlap": ["blank"], "boolean_truth_cases": ["union", "xor"],
    "panel_order": ["row_only", "col_only", "transpose_panels", "swap_rows", "swap_columns"],
    "position_over_color": ["canonical_color_roles"],
}
CANONICAL_SHORTCUTS = {"canonical_color_roles": _rival_color_roles}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
