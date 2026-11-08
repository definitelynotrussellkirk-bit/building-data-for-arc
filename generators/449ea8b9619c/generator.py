"""Generator for ARC task aabf363d / 449ea8b9619c.

A zero-background grid contains one connected shape in a single nonzero color
and a unique one-cell marker at the bottom-left in a different color.  The
output erases the marker and recolors the shape in place to the marker color.

The official examples contain exactly one non-marker color.  The selected
canonical Racket source and the preserved archival source choose that color by
different orderings, but those orderings are answer-equivalent on this lawful
envelope.  This generator therefore does not invent unsupported third-color
distractors merely to force an arbitrary ordering interpretation.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.blobs import grow_blob
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "449ea8b9619c"
TASK_ID = "449ea8b9619c"
VERSION = "3.0.0"
RULE_HASH = "042c5b1f1719"

SUMMARY = (
    "A 0-background grid contains one connected irregular shape in one "
    "nonzero color and a unique bottom-left marker in another nonzero color. "
    "Erase the marker and recolor every shape cell in place to the marker "
    "color. Default generation alternates exact canonical D4 morphologies "
    "with fresh connected irregular shapes, varying dimensions, size, "
    "placement, and both colors."
)

INVARIANTS = [
    "background is 0 and all cells are ARC colors 0..9",
    "the bottom-left marker is nonzero and its color occurs exactly once",
    "exactly one other nonzero color forms the selected shape",
    "the selected shape has 4..15 cells and is one 4-connected component",
    "the selected shape spans at least two rows and columns and is not a solid bbox",
]

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.40

# Every declared axis is exactly recoverable from the returned grid.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware with canonical prior",
        "valid": "7..16",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware with canonical prior",
        "valid": "7..16",
    },
    "shape_size": {
        "type": "int",
        "default": "difficulty-aware with canonical prior",
        "valid": "4..15",
    },
    "marker_color": {
        "type": "color",
        "default": "keyed nonzero color",
        "valid": "1..9",
    },
    "shape_color": {
        "type": "color",
        "default": "keyed nonzero color != marker",
        "valid": "1..9",
    },
}

# Must-reject mutation fixtures, not lawful generation axes.
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES = (
    "no_marker",
    "no_shape",
    "repeated_marker",
    "extra_nonmarker_color",
)
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))

# Normalized occupied-cell templates derived from every canonical train/test
# input.  The focused test independently re-derives this bank from canonical
# data so source drift is loud.
_CANONICAL_SHAPES = (
    (
        (0, 2),
        (1, 1), (1, 2), (1, 3),
        (2, 0), (2, 1), (2, 2), (2, 3),
        (3, 0), (3, 1),
        (4, 1), (4, 2),
    ),
    (
        (0, 0), (0, 1), (0, 2),
        (1, 1),
        (2, 0), (2, 1), (2, 2), (2, 3),
        (3, 1), (3, 2), (3, 3),
        (4, 2),
    ),
    (
        (0, 0), (0, 1), (0, 2),
        (1, 0), (1, 1), (1, 2), (1, 3), (1, 4),
        (2, 2), (2, 3),
        (3, 1), (3, 2),
        (4, 1), (4, 2), (4, 3),
    ),
)


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    row0 = min(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    return tuple(sorted((row - row0, col - col0) for row, col in cells))


def _transform(
    cells: Iterable[tuple[int, int]], rotation: int, reflect: bool
) -> tuple[tuple[int, int], ...]:
    out = list(_normalize(cells))
    if reflect:
        max_col = max(col for _, col in out)
        out = [(row, max_col - col) for row, col in out]
    for _ in range(rotation % 4):
        max_row = max(row for row, _ in out)
        out = [(col, max_row - row) for row, col in out]
        out = list(_normalize(out))
    return _normalize(out)


def _canonical_orbit() -> frozenset[tuple[tuple[int, int], ...]]:
    return frozenset(
        _transform(shape, rotation, reflect)
        for shape in _CANONICAL_SHAPES
        for reflect in (False, True)
        for rotation in range(4)
    )


_CANONICAL_ORBIT = _canonical_orbit()


def _components(cells: set[tuple[int, int]]) -> list[set[tuple[int, int]]]:
    remaining = set(cells)
    groups: list[set[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        group = {start}
        queue = deque([start])
        remaining.remove(start)
        while queue:
            row, col = queue.popleft()
            for drow, dcol in _DIR4:
                nxt = row + drow, col + dcol
                if nxt in remaining:
                    remaining.remove(nxt)
                    group.add(nxt)
                    queue.append(nxt)
        groups.append(group)
    return groups


def _analysis(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid:
        return {"errors": ["grid must be a non-empty list of rows"]}
    if not isinstance(grid[0], list) or not grid[0]:
        return {"errors": ["grid rows must be non-empty lists"]}
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular"]}
    height = len(grid)
    values = [value for row in grid for value in row]
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for value in values
    ):
        return {
            "errors": ["all cells must be integer ARC colors 0..9"],
            "height": height,
            "width": width,
        }

    marker = grid[height - 1][0]
    marker_cells = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if marker != 0 and grid[row][col] == marker
    }
    if marker == 0:
        errors.append("bottom-left marker must be nonzero")
    elif marker_cells != {(height - 1, 0)}:
        errors.append("marker color must occur exactly once at bottom-left")

    nonmarker_colors = sorted(set(values) - {0, marker})
    if len(nonmarker_colors) != 1:
        errors.append(
            f"expected exactly one nonzero non-marker shape color; got {nonmarker_colors}"
        )
        shape_color = nonmarker_colors[0] if nonmarker_colors else None
    else:
        shape_color = nonmarker_colors[0]

    shape_cells = (
        {
            (row, col)
            for row in range(height)
            for col in range(width)
            if grid[row][col] == shape_color
        }
        if shape_color is not None
        else set()
    )
    shape_groups = _components(shape_cells) if shape_cells else []
    if shape_cells:
        rows = [row for row, _ in shape_cells]
        cols = [col for _, col in shape_cells]
        bbox_h = max(rows) - min(rows) + 1
        bbox_w = max(cols) - min(cols) + 1
        bbox_area = bbox_h * bbox_w
    else:
        bbox_h = bbox_w = bbox_area = 0

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "marker": marker,
        "marker_cells": marker_cells,
        "shape_color": shape_color,
        "shape_cells": shape_cells,
        "shape_groups": shape_groups,
        "bbox_h": bbox_h,
        "bbox_w": bbox_w,
        "bbox_area": bbox_area,
        "palette": set(values),
    }


def observe_overrides(grid: Any) -> dict[str, int]:
    """Recover every exact semantic axis directly from the returned grid."""
    analysis = _analysis(grid)
    if analysis["errors"] or analysis["shape_color"] is None:
        return {}
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "shape_size": len(analysis["shape_cells"]),
        "marker_color": analysis["marker"],
        "shape_color": analysis["shape_color"],
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def self_check(grid: Any, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed and shortcut-hiding scenes; accept all canonical inputs."""
    del difficulty
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors

    height, width = analysis["height"], analysis["width"]
    shape_size = len(analysis["shape_cells"])
    if not 7 <= height <= 16 or not 7 <= width <= 16:
        errors.append(f"grid must be 7..16 by 7..16; got {height}x{width}")
    if not 4 <= shape_size <= 15:
        errors.append(f"shape must occupy 4..15 cells; got {shape_size}")
    if len(analysis["shape_groups"]) != 1:
        errors.append(
            f"shape must be one 4-connected component; got {len(analysis['shape_groups'])}"
        )
    if analysis["bbox_h"] < 2 or analysis["bbox_w"] < 2:
        errors.append("shape must span at least two rows and two columns")
    if analysis["bbox_area"] <= shape_size:
        errors.append("shape must leave at least one empty cell inside its bounding box")

    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in observed and observed[name] != requested:
            errors.append(
                f"override {name}={requested!r} realized as {observed[name]!r}"
            )
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    """Exact empirical-manifold predicate derived from all official inputs."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    analysis = _analysis(grid)
    if (analysis["height"], analysis["width"]) != (7, 7):
        reasons.append("canonical inputs are exactly 7x7")
    if len(analysis["palette"]) != 3:
        reasons.append("canonical inputs use exactly background, marker, and shape colors")
    if _normalize(analysis["shape_cells"]) not in _CANONICAL_ORBIT:
        reasons.append("shape morphology is outside the canonical D4 orbit bank")
    return reasons


def rule_python(grid: Any) -> list[list[int]]:
    """Independent mirror on the lawful one-shape-color envelope."""
    analysis = _analysis(grid)
    if analysis["errors"] or analysis["shape_color"] is None:
        raise ValueError("rule requires exactly one nonzero non-marker shape color")
    marker = analysis["marker"]
    shape_color = analysis["shape_color"]
    return [
        [marker if value == shape_color else 0 for value in row]
        for row in grid
    ]


def _competitor_keep_marker(grid: Any) -> list[list[int]]:
    output = rule_python(grid)
    output[-1][0] = _analysis(grid)["marker"]
    return output


def _competitor_fill_bbox(grid: Any) -> list[list[int]]:
    analysis = _analysis(grid)
    marker = analysis["marker"]
    rows = [row for row, _ in analysis["shape_cells"]]
    cols = [col for _, col in analysis["shape_cells"]]
    row0, row1 = min(rows), max(rows)
    col0, col1 = min(cols), max(cols)
    return [
        [
            marker if row0 <= row <= row1 and col0 <= col <= col1 else 0
            for col in range(analysis["width"])
        ]
        for row in range(analysis["height"])
    ]


def _competitor_leave_shape_unchanged(grid: Any) -> list[list[int]]:
    analysis = _analysis(grid)
    shape_color = analysis["shape_color"]
    return [
        [shape_color if value == shape_color else 0 for value in row]
        for row in grid
    ]


def _competitor_top_row_only(grid: Any) -> list[list[int]]:
    analysis = _analysis(grid)
    marker = analysis["marker"]
    top = min(row for row, _ in analysis["shape_cells"])
    return [
        [
            marker if (row, col) in analysis["shape_cells"] and row == top else 0
            for col in range(analysis["width"])
        ]
        for row in range(analysis["height"])
    ]


LESSON_COMPETITORS = {
    "preserve_bottom_left_marker": _competitor_keep_marker,
    "fill_selected_shape_bbox": _competitor_fill_bbox,
    "leave_shape_color_unchanged": _competitor_leave_shape_unchanged,
    "recolor_only_top_row_of_shape": _competitor_top_row_only,
}
SEMANTIC_RIVALS = LESSON_COMPETITORS


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a named rival fits every demo but changes the query."""
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    for index, pair in enumerate(demos):
        if pair.get("output") != rule_python(pair["input"]):
            reasons.append(f"demo {index} output disagrees with the recoloring rule")
    if query.get("output") is not None and query["output"] != rule_python(query["input"]):
        reasons.append("query output disagrees with the recoloring rule")
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            if competitor(query["input"]) != rule_python(query["input"]):
                reasons.append(
                    f"rival {name!r} fits every demonstration but changes the query"
                )
    return reasons


def _witness_canonical_anchor(grid: Any) -> bool:
    return not strict_canonical_like(grid)


def _witness_negative_space(grid: Any) -> bool:
    analysis = _analysis(grid)
    return not self_check(grid) and analysis["bbox_area"] > len(analysis["shape_cells"])


def _witness_marker_removed(grid: Any) -> bool:
    return not self_check(grid) and rule_python(grid)[-1][0] == 0


def _witness_recolor_changes_value(grid: Any) -> bool:
    analysis = _analysis(grid)
    return not self_check(grid) and analysis["marker"] != analysis["shape_color"]


def _witness_multirow_scope(grid: Any) -> bool:
    analysis = _analysis(grid)
    return not self_check(grid) and analysis["bbox_h"] >= 2


SEMANTIC_WITNESSES = {
    "canonical_D4_morphology_anchor": _witness_canonical_anchor,
    "shape_has_bbox_negative_space": _witness_negative_space,
    "bottom_left_marker_is_removed": _witness_marker_removed,
    "shape_cells_change_to_marker_color": _witness_recolor_changes_value,
    "recoloring_covers_multiple_shape_rows": _witness_multirow_scope,
}

WITNESS_RIVALS = {
    "canonical_D4_morphology_anchor": ["fill_selected_shape_bbox"],
    "shape_has_bbox_negative_space": ["fill_selected_shape_bbox"],
    "bottom_left_marker_is_removed": ["preserve_bottom_left_marker"],
    "shape_cells_change_to_marker_color": ["leave_shape_color_unchanged"],
    "recoloring_covers_multiple_shape_rows": ["recolor_only_top_row_of_shape"],
}


def _draw_canonical_shape(ctx, shape_size: int) -> set[tuple[int, int]]:
    candidates = [shape for shape in _CANONICAL_SHAPES if len(shape) == shape_size]
    rng = ctx.draw_rng("canonical-shape")
    shape = rng.choice(candidates)
    transformed = _transform(shape, rng.randrange(4), bool(rng.randrange(2)))
    shape_h = max(row for row, _ in transformed) + 1
    shape_w = max(col for _, col in transformed) + 1
    placements = [
        (top, left)
        for top in range(7 - shape_h + 1)
        for left in range(7 - shape_w + 1)
        if (6, 0) not in {(top + row, left + col) for row, col in transformed}
    ]
    top, left = rng.choice(placements)
    return {(top + row, left + col) for row, col in transformed}


def _draw_general_shape(
    ctx, *, height: int, width: int, shape_size: int
) -> set[tuple[int, int]]:
    marker_cell = (height - 1, 0)
    for attempt in range(512):
        rng = ctx.draw_rng(f"shape-layout:{attempt}")
        cells = grow_blob(
            rng,
            height,
            width,
            {marker_cell},
            shape_size,
            max_attempts=100,
        )
        if cells is None or len(_components(set(cells))) != 1:
            continue
        rows = [row for row, _ in cells]
        cols = [col for _, col in cells]
        bbox_h = max(rows) - min(rows) + 1
        bbox_w = max(cols) - min(cols) + 1
        if bbox_h >= 2 and bbox_w >= 2 and bbox_h * bbox_w > shape_size:
            return set(cells)
    raise ValueError("could not construct a connected irregular shape")


def _draw_degenerate(name: str) -> list[list[int]]:
    grid = full_grid(7, 7, 0)
    if name == "no_marker":
        for row, col in ((1, 1), (1, 2), (2, 1), (2, 2), (2, 3)):
            grid[row][col] = 3
    elif name == "no_shape":
        grid[6][0] = 6
    elif name == "repeated_marker":
        grid[6][0] = 6
        grid[0][0] = 6
        for row, col in ((1, 1), (1, 2), (2, 1), (2, 2), (2, 3)):
            grid[row][col] = 3
    elif name == "extra_nonmarker_color":
        grid[6][0] = 6
        for row, col in ((1, 1), (1, 2), (2, 1), (2, 2), (2, 3)):
            grid[row][col] = 3
        grid[5][5] = 8
    else:
        raise ValueError(f"unknown degenerate texture: {name}")
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            f"difficulty must be easy/medium/hard or None, got {difficulty!r}"
        )

    texture = overrides.get("texture")
    unknown = set(overrides) - set(AXES) - {"texture"}
    if unknown:
        raise ValueError(
            f"unknown override axis/axes: {sorted(unknown)}; valid axes: {sorted(AXES)}"
        )
    if texture is not None:
        if texture not in DEGENERATE_TEXTURES:
            raise ValueError(
                f"texture is only a defect fixture; valid values: {list(DEGENERATE_TEXTURES)}"
            )
        if len(overrides) != 1:
            raise ValueError("degenerate texture fixtures cannot combine with exact axes")
        return _draw_degenerate(texture)

    if (
        overrides.get("marker_color") is not None
        and overrides.get("shape_color") is not None
        and int(overrides["marker_color"]) == int(overrides["shape_color"])
    ):
        exc = ValueError("marker_color and shape_color must differ")
        exc.incompatible_axes = ("marker_color", "shape_color")
        raise exc

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    explicit = bool(overrides)
    schedule = sample_index % 4
    canonical_anchor = not explicit and schedule in (0, 3)

    if canonical_anchor:
        height = ctx.draw_int("grid_h", 7, 7)
        width = ctx.draw_int("grid_w", 7, 7)
        canonical_size = 12 if schedule == 0 else 15
        shape_size = ctx.draw_int("shape_size", canonical_size, canonical_size)
    else:
        height = ctx.draw_int_diff("grid_h", 7, 16)
        width = ctx.draw_int_diff("grid_w", 7, 16)
        shape_size = ctx.draw_int_diff("shape_size", 4, 15)

    explicit_shape_color = overrides.get("shape_color")
    marker_exclusions = {0}
    if explicit_shape_color is not None:
        marker_exclusions.add(int(explicit_shape_color))
    marker = ctx.draw_color("marker_color", exclude=marker_exclusions)
    shape_color = ctx.draw_color("shape_color", exclude={0, marker})

    grid = full_grid(height, width, 0)
    grid[height - 1][0] = marker
    shape_cells = (
        _draw_canonical_shape(ctx, shape_size)
        if canonical_anchor
        else _draw_general_shape(
            ctx, height=height, width=width, shape_size=shape_size
        )
    )
    for row, col in shape_cells:
        grid[row][col] = shape_color

    errors = self_check(
        grid,
        difficulty=difficulty,
        meta={"overrides": ctx.recorded_draws()},
    )
    if errors:
        raise AssertionError("generator emitted invalid scene: " + "; ".join(errors))
    return grid
