"""Generator for the legend-ordered component gallery ARC task.

The nonzero cells of row 0 form an ordered color legend.  Row 1 is a
blank separator.  The body contains exactly one isolated homogeneous
component for every legend color.  The canonical rule crops those
components and packs the crops left-to-right in legend order.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "4e53f3cd64e8"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "5bdc8d1d0941"
SUMMARY = "Separated top-row legend plus one crop-sized component per legend color."

INVARIANTS = [
    "background is 0",
    "all nonzero cells of row 0, including cells after gaps, form the legend",
    "row 1 is an all-zero separator",
    "the legend contains 3 or 4 distinct colors",
    "the body has exactly one isolated homogeneous 3-5 cell component per legend color",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
AXES = {
    "grid_h": {"type": "int", "default": "rng 9..12", "valid": "9..12"},
    "grid_w": {"type": "int", "default": "rng 12..16", "valid": "12..16"},
    "n_legend": {"type": "int", "default": "rng 3..4", "valid": "3..4"},
    "palette_kind": {
        "type": "str",
        "default": "rng default|warm|cool|varied",
        "valid": "default|warm|cool|varied",
    },
}

# Each exact palette has a unique color set, so palette_kind is recoverable from
# returned pixels rather than from RNG bookkeeping.
_PALETTES = {
    ("default", 3): (1, 2, 3),
    ("default", 4): (1, 2, 3, 4),
    ("warm", 3): (2, 4, 9),
    ("warm", 4): (2, 4, 8, 9),
    ("cool", 3): (1, 6, 7),
    ("cool", 4): (1, 5, 6, 7),
    ("varied", 3): (3, 5, 8),
    ("varied", 4): (3, 5, 8, 9),
}
_KIND_BY_PALETTE = {
    frozenset(colors): kind for (kind, _count), colors in _PALETTES.items()
}

# (height, width, legend count) profiles from the five canonical inputs.  A
# deterministic quarter of default calls lands exactly on this support, in all
# difficulty bands, while explicit overrides retain the full declared domain.
_CANONICAL_PROFILES = (
    (9, 14, 3),
    (10, 14, 4),
    (11, 12, 4),
    (12, 12, 4),
    (12, 16, 4),
)
_BAND_OFFSET = {None: 0, "easy": 1, "medium": 2, "hard": 3}

_LEGEND_POSITION_PATTERNS = {
    3: ((0, 2, 4), (0, 1, 3), (0, 2, 3), (0, 1, 4)),
    4: ((0, 1, 3, 5), (0, 2, 4, 5), (0, 2, 4, 6), (0, 1, 2, 4)),
}

# Connected templates normalized at (0, 0), all fitting inside a 3x3 box.
_SHAPES = {
    3: (
        ((0, 0), (1, 0), (2, 0)),
        ((0, 0), (0, 1), (0, 2)),
        ((0, 0), (1, 0), (1, 1)),
        ((0, 1), (1, 0), (1, 1)),
    ),
    4: (
        ((0, 0), (0, 1), (1, 0), (1, 1)),
        ((0, 0), (1, 0), (2, 0), (2, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 1)),
        ((0, 1), (1, 0), (1, 1), (2, 1)),
    ),
    5: (
        ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
        ((0, 0), (0, 1), (1, 0), (2, 0), (2, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1)),
        ((0, 0), (1, 0), (1, 1), (1, 2), (2, 2)),
    ),
}


def _validate_call(seed, sample_index, difficulty, overrides):
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")

    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")

    for name, value in overrides.items():
        if value is None:
            continue
        if name in ("grid_h", "grid_w", "n_legend"):
            if type(value) is not int:
                raise TypeError(f"{name} must be an integer (not bool)")
            lo, hi = {
                "grid_h": (9, 12),
                "grid_w": (12, 16),
                "n_legend": (3, 4),
            }[name]
            if not lo <= value <= hi:
                raise ValueError(f"{name}={value} outside [{lo}, {hi}]")
        elif name == "palette_kind":
            if type(value) is not str:
                raise TypeError("palette_kind must be a string")
            if value not in PALETTE_KINDS:
                raise ValueError(
                    f"palette_kind={value!r} not in {list(PALETTE_KINDS)}"
                )


def _draw_int_axis(ctx, name, lo, hi, anchored_value=None):
    """Consume an exact int override or make one honest keyed draw."""
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int_strict(name, lo, hi)
    if anchored_value is not None:
        return ctx.draw_choice(name, (anchored_value,))
    return ctx.draw_int_strict(name, lo, hi)


def _profile_anchor(sample_index, difficulty):
    if sample_index % 4:
        return None
    offset = _BAND_OFFSET[difficulty]
    return _CANONICAL_PROFILES[(sample_index // 4 + offset) % len(_CANONICAL_PROFILES)]


def _grid_error(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return "expected a nonempty rectangular grid"
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return "expected nonempty rows"
    width = len(grid[0])
    for row in grid:
        if not isinstance(row, (list, tuple)) or len(row) != width:
            return "ragged grid"
        if any(type(value) is not int or not 0 <= value <= 9 for value in row):
            return "cells must be integer ARC colors 0..9"
    return None


def _nonzero_components(grid):
    """Return 4-connected nonzero components in row-major discovery order."""
    height, width = len(grid), len(grid[0])
    seen = set()
    components = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    point = (rr + dr, cc + dc)
                    if (
                        0 <= point[0] < height
                        and 0 <= point[1] < width
                        and point not in seen
                        and grid[point[0]][point[1]] != 0
                    ):
                        seen.add(point)
                        stack.append(point)
            components.append(cells)
    return components


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the canonical legend row, separator, and body manifold."""
    problem = _grid_error(grid)
    if problem:
        return [problem]
    height, width = len(grid), len(grid[0])
    errors = []
    if not 9 <= height <= 12:
        errors.append(f"grid height {height} outside 9..12")
    if not 12 <= width <= 16:
        errors.append(f"grid width {width} outside 12..16")
    if height < 3:
        return errors + ["grid needs a legend row, blank separator row, and body"]

    legend = [value for value in grid[0] if value != 0]
    if not 3 <= len(legend) <= 4:
        errors.append(f"top-row legend has {len(legend)} colors, expected 3 or 4")
    if len(set(legend)) != len(legend):
        errors.append("top-row legend colors must be distinct")
    if any(grid[1]):
        errors.append("row 1 must be an all-zero separator")

    legend_set = set(legend)
    body = [list(row) for row in grid[2:]]
    components = _nonzero_components(body)
    by_color = {color: [] for color in legend}
    for cells in components:
        colors = {body[row][col] for row, col in cells}
        if len(colors) != 1:
            errors.append(
                f"body component at {min(cells)} mixes colors {sorted(colors)}"
            )
            continue
        color = next(iter(colors))
        if color not in legend_set:
            errors.append(f"body component uses unlisted color {color}")
            continue
        by_color[color].append(cells)
        rows = [row for row, _ in cells]
        cols = [col for _, col in cells]
        if not 3 <= len(cells) <= 5:
            errors.append(
                f"color {color} component has {len(cells)} cells, expected 3..5"
            )
        if max(rows) - min(rows) + 1 > 3 or max(cols) - min(cols) + 1 > 3:
            errors.append(f"color {color} component must fit within a 3x3 box")

    for color in legend:
        count = len(by_color.get(color, ()))
        if count != 1:
            errors.append(
                f"legend color {color} has {count} body components, expected exactly 1"
            )
    return errors


def strict_canonical_like(grid):
    """Accept exactly the declared lawful input manifold."""
    return self_check(grid)


def _legend_colors(ctx, kind, count):
    colors = list(_PALETTES[(kind, count)])
    ctx.draw_rng("legend_order").shuffle(colors)
    # A sorted legend would not expose why legend order matters.  Keep every
    # generated lesson as a counterexample to the tempting numeric-sort rival.
    if colors == sorted(colors):
        colors[0], colors[1] = colors[1], colors[0]
    return colors


def _shape_sizes(difficulty, count, rng):
    choices = {
        "easy": (3, 3, 4),
        "medium": (3, 4, 4, 5),
        "hard": (4, 4, 5, 5),
        None: (3, 4, 5),
    }[difficulty]
    sizes = [rng.choice(choices) for _ in range(count)]
    # Mixed crop geometry prevents accidental agreement through repeated shapes.
    if len(set(sizes)) == 1:
        sizes[-1] = 3 if sizes[0] != 3 else 4
    return sizes


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    anchor = _profile_anchor(sample_index, difficulty)
    h = _draw_int_axis(ctx, "grid_h", 9, 12, None if anchor is None else anchor[0])
    w = _draw_int_axis(ctx, "grid_w", 12, 16, None if anchor is None else anchor[1])
    count = _draw_int_axis(
        ctx, "n_legend", 3, 4, None if anchor is None else anchor[2]
    )
    kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)

    grid = [[0 for _ in range(w)] for _ in range(h)]
    legend = _legend_colors(ctx, kind, count)
    positions = ctx.draw_rng("legend_positions").choice(
        _LEGEND_POSITION_PATTERNS[count]
    )
    for col, color in zip(positions, legend):
        grid[0][col] = color

    # Six 3x3 slots fit even in the smallest 7x12 body.  Blank row/column
    # gutters make cross-color merging impossible by construction.
    slots = [(0, 0), (0, 4), (0, 8), (4, 0), (4, 4), (4, 8)]
    slot_rng = ctx.draw_rng("component_slots")
    selected_slots = slot_rng.sample(slots, count)
    size_rng = ctx.draw_rng("component_sizes")
    shape_rng = ctx.draw_rng("component_shapes")
    sizes = _shape_sizes(difficulty, count, size_rng)

    # Components are deliberately assigned independently of legend order in the
    # input; only the legend determines output order.
    component_order = list(range(count))
    ctx.draw_rng("component_assignment").shuffle(component_order)
    for slot, legend_index in zip(selected_slots, component_order):
        color = legend[legend_index]
        shape = shape_rng.choice(_SHAPES[sizes[legend_index]])
        top, left = slot
        for dr, dc in shape:
            grid[2 + top + dr][left + dc] = color

    problems = self_check(grid)
    if problems:
        raise RuntimeError(f"constructive generator produced invalid grid: {problems}")
    return grid


def observe_overrides(grid):
    """Recover every declared exact axis from returned pixels."""
    problems = self_check(grid)
    if problems:
        raise ValueError(f"cannot observe overrides on invalid grid: {problems}")
    legend = [value for value in grid[0] if value != 0]
    palette_set = frozenset(legend)
    try:
        kind = _KIND_BY_PALETTE[palette_set]
    except KeyError as exc:
        raise ValueError(f"unrecognized exact palette {sorted(palette_set)}") from exc
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_legend": len(legend),
        "palette_kind": kind,
    }


def _component_crop(body, cells):
    top = min(row for row, _ in cells)
    bottom = max(row for row, _ in cells)
    left = min(col for _, col in cells)
    right = max(col for _, col in cells)
    membership = set(cells)
    return [
        [body[row][col] if (row, col) in membership else 0 for col in range(left, right + 1)]
        for row in range(top, bottom + 1)
    ]


def _gallery_for_order(grid, color_order):
    body = [list(row) for row in grid[2:]]
    components = _nonzero_components(body)
    by_color = {
        body[cells[0][0]][cells[0][1]]: cells
        for cells in components
    }
    crops = [_component_crop(body, by_color[color]) for color in color_order]
    output_height = max(len(crop) for crop in crops)
    output_width = sum(len(crop[0]) for crop in crops) + len(crops) - 1
    output = [[0 for _ in range(output_width)] for _ in range(output_height)]
    cursor = 0
    for crop in crops:
        for row, values in enumerate(crop):
            output[row][cursor : cursor + len(values)] = values
        cursor += len(crop[0]) + 1
    return output


def solve(grid):
    """Python mirror of the pinned canonical Racket authority."""
    problems = self_check(grid)
    if problems:
        raise ValueError(f"invalid legend-gallery input: {problems}")
    legend = [value for value in grid[0] if value != 0]
    return _gallery_for_order(grid, legend)


def _contiguous_prefix_gallery(grid):
    """Rival: incorrectly stops reading the legend at its first zero."""
    legend = []
    for value in grid[0]:
        if value == 0:
            break
        legend.append(value)
    return _gallery_for_order(grid, legend)


def _numeric_order_gallery(grid):
    """Rival: ignores the legend sequence and sorts colors numerically."""
    legend = sorted(value for value in grid[0] if value != 0)
    return _gallery_for_order(grid, legend)


def _has_separated_legend(grid):
    seen_color = False
    seen_gap = False
    for value in grid[0]:
        if value:
            if seen_gap:
                return True
            seen_color = True
        elif seen_color:
            seen_gap = True
    return False


def _has_nonnumeric_legend_order(grid):
    legend = [value for value in grid[0] if value != 0]
    return legend != sorted(legend)


SEMANTIC_WITNESSES = {
    "read_all_nonzero_legend_cells": _has_separated_legend,
    "preserve_legend_order": _has_nonnumeric_legend_order,
}
SEMANTIC_RIVALS = {
    "contiguous_prefix_only": _contiguous_prefix_gallery,
    "numeric_color_order": _numeric_order_gallery,
}
WITNESS_RIVALS = {
    "read_all_nonzero_legend_cells": ["contiguous_prefix_only"],
    "preserve_legend_order": ["numeric_color_order"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 1.0


def lesson_identifiable(demos, query):
    """Report any declared competitor that demos fail to disambiguate."""
    reasons = []
    for name, competitor in LESSON_COMPETITORS.items():
        try:
            fits_demos = all(
                competitor(pair["input"]) == pair["output"] for pair in demos
            )
            changes_query = competitor(query["input"]) != query["output"]
        except (KeyError, TypeError, ValueError) as exc:
            reasons.append(f"competitor {name} could not be scored: {exc}")
            continue
        if fits_demos and changes_query:
            reasons.append(
                f"competitor {name} fits every demonstration but changes the query"
            )
    return reasons
