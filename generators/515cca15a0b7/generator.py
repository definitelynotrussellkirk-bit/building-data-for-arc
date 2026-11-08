"""Input sampler for keeping components that span a corner's two border axes.

The selected Racket authority keeps a same-color 4-connected component exactly
when it touches a horizontal border (top or bottom) AND a vertical border (left
or right).  A kept component need not occupy the literal corner cell.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "515cca15a0b7"
TASK_ID = GENERATOR_ID
RULE_HASH = "8a3c35320856"
VERSION = "2.1.0"
SUMMARY = (
    "Several monochrome components. Keep exactly those touching one horizontal "
    "and one vertical border; erase components touching only one border or none."
)
EXAMPLES_NEEDED = 3

_LAYOUT_VALUES = (
    "canonical_mix",
    "kept_variety",
    "edge_contrast",
    "dense",
)
# Two canonical-profile scenes in five positions keep profile coverage safely
# above the 25% floor. The two split-color positions and two extended-shape
# positions are interleaved so every cyclic three-example window contains
# both semantic witnesses.
_LAYOUT_SCHEDULE = (
    "canonical_mix",
    "dense",
    "canonical_mix",
    "edge_contrast",
    "kept_variety",
)
_LAYOUT_COUNTS = {
    "canonical_mix": {
        "noncorner_keep": 1,
        "corner_keep": 1,
        "edge_drop": 1,
        "interior_drop": 1,
    },
    "edge_contrast": {
        "noncorner_keep": 1,
        "corner_keep": 1,
        "edge_drop": 2,
        "interior_drop": 0,
    },
    "kept_variety": {
        "noncorner_keep": 2,
        "corner_keep": 1,
        "edge_drop": 1,
        "interior_drop": 1,
    },
    "dense": {
        "noncorner_keep": 2,
        "corner_keep": 2,
        "edge_drop": 2,
        "interior_drop": 1,
    },
}
_CANONICAL_SHAPES = ((8, 10), (9, 9), (9, 10), (10, 11))

INVARIANTS = [
    "background is 0 and every foreground component is monochrome and 4-connected",
    "at least one component touches both a horizontal and a vertical border",
    "at least one component fails that conjunction and is erased",
    "every ordinary three-example window includes an extended dual-border component with no literal corner cell",
    "every ordinary three-example window includes disconnected same-color edge components with complementary one-axis contacts",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical profile",
        "valid": "8..10",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical profile",
        "valid": "9..11",
    },
    "layout": {
        "type": "str",
        "default": "five-position witness-balanced sample-index schedule",
        "valid": "|".join(_LAYOUT_VALUES),
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

# Top-left templates; _orient maps them to any corner.
# The short path reproduces the canonical maximum component size.  The extended
# path reaches Chebyshev radius 3, refuting the canonical-fitting "within 3x3
# corner zone" shortcut.  Alternating them guarantees that every three-example
# lesson contains the stronger witness without abandoning canonical morphology.
_SHORT_NONCORNER = ((0, 1), (1, 1), (1, 0))
_EXTENDED_NONCORNER = ((0, 1), (1, 1), (2, 1), (3, 1), (3, 0))
_NONCORNER_TEMPLATE_BY_LAYOUT = {
    "canonical_mix": _SHORT_NONCORNER,
    "edge_contrast": _SHORT_NONCORNER,
    "kept_variety": _EXTENDED_NONCORNER,
    "dense": _EXTENDED_NONCORNER,
}
_LITERAL_CORNER_SHAPES = (
    ((0, 0), (0, 1)),
    ((0, 0), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (1, 0)),
)
_LITERAL_CORNER_SHAPE_BY_DIFFICULTY = {
    "easy": _LITERAL_CORNER_SHAPES[0],
    "medium": _LITERAL_CORNER_SHAPES[1],
    "hard": _LITERAL_CORNER_SHAPES[2],
}


def _orient(cells, corner, height, width):
    result = []
    for row, col in cells:
        if corner in (2, 3):
            row = height - 1 - row
        if corner in (1, 3):
            col = width - 1 - col
        result.append((row, col))
    return tuple(result)


def _choose_disjoint(candidates, count, used, rng, label):
    if count == 0:
        return []
    pool = list(candidates)
    rng.shuffle(pool)
    chosen = []
    for cells in pool:
        if not any(cell in used for cell in cells):
            chosen.append(cells)
            used.update(cells)
            if len(chosen) == count:
                return chosen
    raise RuntimeError(f"could not place {count} disjoint {label} components")


def _horizontal_edge_candidates(height, width):
    result = []
    for col in range(2, width - 2):
        result.append(((0, col), (1, col)))
        result.append(((height - 1, col), (height - 2, col)))
    return result


def _vertical_edge_candidates(height, width):
    result = []
    for row in range(2, height - 2):
        result.append(((row, 0), (row, 1)))
        result.append(((row, width - 1), (row, width - 2)))
    return result


def _edge_candidates(height, width):
    return _horizontal_edge_candidates(height, width) + _vertical_edge_candidates(height, width)


def _interior_candidates(height, width):
    result = []
    for row in range(2, height - 2):
        for col in range(2, width - 3):
            result.append(((row, col), (row, col + 1)))
    for row in range(2, height - 3):
        for col in range(2, width - 2):
            result.append(((row, col), (row + 1, col)))
    return result


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name in ("grid_h", "grid_w"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
    value = overrides.get("layout")
    if value is not None and type(value) is not str:
        raise ValueError(f"layout must be a string, not {type(value).__name__}")


def _scheduled_draw(ctx, label, scheduled, lo, hi):
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_choice(label, (scheduled,))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile_h, profile_w = _CANONICAL_SHAPES[sample_index % len(_CANONICAL_SHAPES)]
    height = _scheduled_draw(ctx, "grid_h", profile_h, 8, 10)
    width = _scheduled_draw(ctx, "grid_w", profile_w, 9, 11)
    if "layout" in overrides and overrides["layout"] is not None:
        layout = ctx.draw_choice("layout", _LAYOUT_VALUES)
    else:
        layout = ctx.draw_choice(
            "layout", (_LAYOUT_SCHEDULE[sample_index % len(_LAYOUT_SCHEDULE)],)
        )
    counts = _LAYOUT_COUNTS[layout]

    geometry_rng = ctx.draw_rng("component_geometry")
    corner_order = [0, 1, 2, 3]
    geometry_rng.shuffle(corner_order)
    used = set()
    components = []

    noncorner_shape = _NONCORNER_TEMPLATE_BY_LAYOUT[layout]
    for corner in corner_order[: counts["noncorner_keep"]]:
        cells = _orient(noncorner_shape, corner, height, width)
        if any(cell in used for cell in cells):
            raise RuntimeError("corner schedule produced overlapping extended components")
        components.append(cells)
        used.update(cells)

    start = counts["noncorner_keep"]
    for corner in corner_order[start : start + counts["corner_keep"]]:
        shape = _LITERAL_CORNER_SHAPE_BY_DIFFICULTY.get(difficulty)
        if shape is None:
            shape = geometry_rng.choice(_LITERAL_CORNER_SHAPES)
        cells = _orient(shape, corner, height, width)
        if any(cell in used for cell in cells):
            raise RuntimeError("corner schedule produced overlapping literal components")
        components.append(cells)
        used.update(cells)

    edge_start = len(components)
    if counts["edge_drop"] == 2:
        # One horizontal-only and one vertical-only component receive the same
        # color.  Treating all cells of a color as one global object would keep
        # both, while the intended 4-connected-component rule erases both.
        edge_components = _choose_disjoint(
            _horizontal_edge_candidates(height, width),
            1,
            used,
            geometry_rng,
            "horizontal-edge-only",
        )
        edge_components += _choose_disjoint(
            _vertical_edge_candidates(height, width),
            1,
            used,
            geometry_rng,
            "vertical-edge-only",
        )
    else:
        edge_components = _choose_disjoint(
            _edge_candidates(height, width),
            counts["edge_drop"],
            used,
            geometry_rng,
            "edge-only",
        )
    components.extend(edge_components)
    edge_indices = tuple(range(edge_start, edge_start + len(edge_components)))
    components.extend(
        _choose_disjoint(
            _interior_candidates(height, width),
            counts["interior_drop"],
            used,
            geometry_rng,
            "interior",
        )
    )

    if len(edge_indices) == 2:
        distinct = iter(
            ctx.draw_distinct_colors(
                "component_colors", n=len(components) - 1, exclude={0}
            )
        )
        colors = []
        shared_edge_color = None
        for index in range(len(components)):
            if index == edge_indices[0]:
                shared_edge_color = next(distinct)
                colors.append(shared_edge_color)
            elif index == edge_indices[1]:
                colors.append(shared_edge_color)
            else:
                colors.append(next(distinct))
    else:
        colors = ctx.draw_distinct_colors(
            "component_colors", n=len(components), exclude={0}
        )
    grid = full_grid(height, width, 0)
    for color, cells in zip(colors, components):
        for row, col in cells:
            grid[row][col] = color
    return grid


def _coerce_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("expected a nonempty rectangular grid")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("expected a nonempty rectangular grid")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("ragged grid")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("cells must be integer ARC colors 0..9")
    return [list(row) for row in grid]


def _components(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    found = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    rr, cc = r + dr, c + dc
                    if (
                        0 <= rr < height
                        and 0 <= cc < width
                        and (rr, cc) not in seen
                        and grid[rr][cc] == color
                    ):
                        seen.add((rr, cc))
                        stack.append((rr, cc))
            found.append((color, frozenset(cells)))
    return found


def _touches(component, height, width):
    horizontal = any(row in (0, height - 1) for row, _ in component)
    vertical = any(col in (0, width - 1) for _, col in component)
    return horizontal, vertical


def _role_counts(grid):
    height, width = len(grid), len(grid[0])
    corners = {
        (0, 0),
        (0, width - 1),
        (height - 1, 0),
        (height - 1, width - 1),
    }
    result = {
        "noncorner_keep": 0,
        "corner_keep": 0,
        "edge_drop": 0,
        "interior_drop": 0,
    }
    for _, cells in _components(grid):
        horizontal, vertical = _touches(cells, height, width)
        if horizontal and vertical:
            result["corner_keep" if cells & corners else "noncorner_keep"] += 1
        elif horizontal or vertical:
            result["edge_drop"] += 1
        else:
            result["interior_drop"] += 1
    return result


def observe_overrides(grid):
    normalized = _coerce_grid(grid)
    counts = _role_counts(normalized)
    layout = next(
        (name for name, expected in _LAYOUT_COUNTS.items() if counts == expected),
        "unclassified",
    )
    return {"grid_h": len(normalized), "grid_w": len(normalized[0]), "layout": layout}


def self_check(grid, *, difficulty=None, meta=None):
    try:
        normalized = _coerce_grid(grid)
    except ValueError as exc:
        return [str(exc)]
    height, width = len(normalized), len(normalized[0])
    errors = []
    if not any(value == 0 for row in normalized for value in row):
        errors.append("background color 0 is absent")
    components = _components(normalized)
    if not components:
        errors.append("no foreground components")
        return errors
    kept = 0
    dropped = 0
    for _, cells in components:
        horizontal, vertical = _touches(cells, height, width)
        kept += bool(horizontal and vertical)
        dropped += not (horizontal and vertical)
    if not kept:
        errors.append("no component touches both a horizontal and a vertical border")
    if not dropped:
        errors.append("no component demonstrates the rejected one-axis/interior case")
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def rule_mirror(grid):
    normalized = _coerce_grid(grid)
    height, width = len(normalized), len(normalized[0])
    out = full_grid(height, width, 0)
    for color, cells in _components(normalized):
        horizontal, vertical = _touches(cells, height, width)
        if horizontal and vertical:
            for row, col in cells:
                out[row][col] = color
    return out


def _paint_selected(grid, predicate):
    normalized = _coerce_grid(grid)
    height, width = len(normalized), len(normalized[0])
    out = full_grid(height, width, 0)
    for color, cells in _components(normalized):
        if predicate(cells, height, width):
            for row, col in cells:
                out[row][col] = color
    return out


def _literal_corner_only(grid):
    def predicate(cells, height, width):
        corners = {
            (0, 0),
            (0, width - 1),
            (height - 1, 0),
            (height - 1, width - 1),
        }
        return bool(cells & corners)

    return _paint_selected(grid, predicate)


def _any_border(grid):
    def predicate(cells, height, width):
        horizontal, vertical = _touches(cells, height, width)
        return horizontal or vertical

    return _paint_selected(grid, predicate)


def _global_color_union(grid):
    normalized = _coerce_grid(grid)
    height, width = len(normalized), len(normalized[0])
    out = full_grid(height, width, 0)
    by_color = {}
    for row in range(height):
        for col in range(width):
            color = normalized[row][col]
            if color != 0:
                by_color.setdefault(color, []).append((row, col))
    for color, cells in by_color.items():
        horizontal = any(row in (0, height - 1) for row, _ in cells)
        vertical = any(col in (0, width - 1) for _, col in cells)
        if horizontal and vertical:
            for row, col in cells:
                out[row][col] = color
    return out


def _near_corner_radius2(grid):
    def predicate(cells, height, width):
        corners = (
            (0, 0),
            (0, width - 1),
            (height - 1, 0),
            (height - 1, width - 1),
        )
        return any(
            all(max(abs(row - cr), abs(col - cc)) <= 2 for row, col in cells)
            for cr, cc in corners
        )

    return _paint_selected(grid, predicate)


def _keep_two_nearest(grid):
    normalized = _coerce_grid(grid)
    height, width = len(normalized), len(normalized[0])
    corners = (
        (0, 0),
        (0, width - 1),
        (height - 1, 0),
        (height - 1, width - 1),
    )
    components = _components(normalized)
    ranked = sorted(
        components,
        key=lambda item: (
            min(
                abs(row - cr) + abs(col - cc)
                for row, col in item[1]
                for cr, cc in corners
            ),
            -len(item[1]),
            item[0],
            tuple(sorted(item[1])),
        ),
    )
    chosen = set(id(cells) for _, cells in ranked[:2])
    out = full_grid(height, width, 0)
    for color, cells in components:
        if id(cells) in chosen:
            for row, col in cells:
                out[row][col] = color
    return out


def _has_extended_noncorner(grid):
    normalized = _coerce_grid(grid)
    height, width = len(normalized), len(normalized[0])
    corners = (
        (0, 0),
        (0, width - 1),
        (height - 1, 0),
        (height - 1, width - 1),
    )
    corner_cells = set(corners)
    for _, cells in _components(normalized):
        horizontal, vertical = _touches(cells, height, width)
        if horizontal and vertical and not (cells & corner_cells):
            if not any(
                all(max(abs(row - cr), abs(col - cc)) <= 2 for row, col in cells)
                for cr, cc in corners
            ):
                return True
    return False


def _has_edge_only(grid):
    normalized = _coerce_grid(grid)
    height, width = len(normalized), len(normalized[0])
    return any(
        horizontal != vertical
        for _, cells in _components(normalized)
        for horizontal, vertical in (_touches(cells, height, width),)
    )


def _has_split_same_color_edges(grid):
    normalized = _coerce_grid(grid)
    height, width = len(normalized), len(normalized[0])
    by_color = {}
    for color, cells in _components(normalized):
        by_color.setdefault(color, []).append(_touches(cells, height, width))
    return any(
        any(horizontal and not vertical for horizontal, vertical in roles)
        and any(vertical and not horizontal for horizontal, vertical in roles)
        for roles in by_color.values()
    )


def _has_more_than_two_kept(grid):
    normalized = _coerce_grid(grid)
    height, width = len(normalized), len(normalized[0])
    return sum(
        1
        for _, cells in _components(normalized)
        if all(_touches(cells, height, width))
    ) > 2


SEMANTIC_WITNESSES = {
    "extended_noncorner_keep": _has_extended_noncorner,
    "edge_only_reject": _has_edge_only,
    "split_same_color_edges": _has_split_same_color_edges,
    "more_than_two_kept": _has_more_than_two_kept,
}
SEMANTIC_RIVALS = {
    "literal_corner_only": _literal_corner_only,
    "keep_any_border": _any_border,
    "global_color_union": _global_color_union,
    "near_corner_radius2": _near_corner_radius2,
    "keep_two_nearest": _keep_two_nearest,
}
WITNESS_RIVALS = {
    "extended_noncorner_keep": ["literal_corner_only", "near_corner_radius2"],
    "edge_only_reject": ["keep_any_border"],
    "split_same_color_edges": ["global_color_union"],
    "more_than_two_kept": ["keep_two_nearest"],
}
CANONICAL_SHORTCUTS = {
    "near_corner_radius2": _near_corner_radius2,
    "keep_two_nearest": _keep_two_nearest,
    "global_color_union": _global_color_union,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
