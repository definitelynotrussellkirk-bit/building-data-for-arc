"""Generator for task 6c0ee2a97246 — replace each object by its bbox outline.

For every 4-connected monochrome object, erase its original pixels and draw the
perimeter of its tight bounding box in the same color.  Objects are generated
with missing border cells, and larger objects may also contain interior pixels,
so both the additive and subtractive parts of the rule are observable.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "6c0ee2a97246"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "ae8cc57061a0"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.40

SUMMARY = (
    "A zero-background grid contains 3-5 separated, 4-connected monochrome "
    "objects. For each object independently, replace its occupied cells by "
    "the perimeter of its tight bounding box in the same color. Generated "
    "lessons include 2xN boxes where the perimeter is the whole box, larger "
    "boxes with missing border cells, and larger boxes with interior input "
    "pixels that must be erased."
)

INVARIANTS = [
    "background is color 0",
    "each foreground object is a 4-connected monochrome component",
    "object bounding boxes are disjoint and at least 2x2",
    "every object differs from its bounding-box perimeter",
    "the output is the same-size grid containing only each object's bbox perimeter in its input color",
]

PALETTE_MODES = ("distinct", "repeated")
AXES = {
    "grid_h": {
        "type": "int",
        "default": "profile-keyed 8..14",
        "valid": "8..14",
    },
    "grid_w": {
        "type": "int",
        "default": "profile-keyed 9..18",
        "valid": "9..18",
    },
    "n_components": {
        "type": "int",
        "default": "3 canonical; 3/4/5 generalized by difficulty",
        "valid": "3..5",
    },
    "palette_mode": {
        "type": "enum",
        "default": "profile-keyed",
        "valid": PALETTE_MODES,
    },
}

# Executably derived in the task-local review from all three train inputs and
# the held-out test input.  Object morphology is deliberately coarse because
# the oracle uses only each object's bbox, not its exact bitmap.
_CANONICAL_LINKED_SIGNATURES = {
    (
        9,
        9,
        4,
        (
            (3, 2, 2, 1, 0),
            (5, 3, 3, 4, 1),
            (6, 3, 3, 3, 0),
        ),
    ),
    (
        8,
        10,
        4,
        (
            (3, 2, 2, 1, 0),
            (3, 2, 2, 1, 0),
            (4, 2, 3, 2, 0),
        ),
    ),
    (
        9,
        9,
        4,
        (
            (3, 2, 2, 1, 0),
            (3, 2, 2, 1, 0),
            (4, 2, 3, 2, 0),
        ),
    ),
    (
        9,
        10,
        4,
        (
            (3, 2, 2, 1, 0),
            (3, 2, 2, 1, 0),
            (4, 2, 3, 2, 0),
        ),
    ),
}


def _draw_int_axis(ctx, overrides, label: str, default: int, lo: int, hi: int) -> int:
    """Use a safe profile default while keeping every declared override valid."""
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, default, default)


def _draw_choice_axis(ctx, overrides, label: str, default: str, options) -> str:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (default,))


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    r0 = min(row for row, _col in cells)
    c0 = min(col for _row, col in cells)
    return tuple(sorted((row - r0, col - c0) for row, col in cells))


def _rotate(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    norm = _normalize(cells)
    width = max(col for _row, col in norm) + 1
    return _normalize((col, width - 1 - row) for row, col in norm)


def _flip_lr(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    norm = _normalize(cells)
    width = max(col for _row, col in norm) + 1
    return _normalize((row, width - 1 - col) for row, col in norm)


def _transform_shape(shape, code: int, *, preserve_bbox_orientation: bool = False):
    current = _normalize(shape)
    if preserve_bbox_orientation:
        # Canonical 2x3 examples vary by reflection but never swap to 3x2.
        if code & 1:
            current = _flip_lr(current)
        if code & 2:
            height = max(row for row, _col in current) + 1
            current = _normalize((height - 1 - row, col) for row, col in current)
        return current
    if code >= 4:
        current = _flip_lr(current)
    for _ in range(code % 4):
        current = _rotate(current)
    return current


def _path_shape(height: int, width: int, rng) -> tuple[tuple[int, int], ...]:
    """Connected spanning path, with an interior cell whenever one exists."""
    steps = ["d"] * (height - 1) + ["r"] * (width - 1)
    for _attempt in range(64):
        rng.shuffle(steps)
        row = col = 0
        cells = [(row, col)]
        for step in steps:
            if step == "d":
                row += 1
            else:
                col += 1
            cells.append((row, col))
        if height < 3 or width < 3 or any(
            0 < r < height - 1 and 0 < c < width - 1 for r, c in cells
        ):
            return _normalize(cells)
    # Deterministic interior-bearing fallback.
    cells = [(0, 0)]
    row = col = 0
    while row < height - 1 or col < width - 1:
        if col < width - 1:
            col += 1
            cells.append((row, col))
        if row < height - 1:
            row += 1
            cells.append((row, col))
    return _normalize(cells)


def _shape_dimensions(shape) -> tuple[int, int]:
    return (
        max(row for row, _col in shape) + 1,
        max(col for _row, col in shape) + 1,
    )


def _profile_shapes(profile: int, band: str, n: int, rng):
    l_shape = ((0, 0), (0, 1), (1, 1))
    s_shape = ((0, 0), (0, 1), (1, 1), (1, 2))
    t_shape = ((0, 0), (0, 1), (0, 2), (1, 1))
    stair_3 = ((0, 0), (0, 1), (1, 1), (1, 2), (2, 2))
    border_6 = ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0), (2, 1))

    preserve = []
    if profile == 0:  # canonical simple morphology
        shapes = [l_shape, l_shape, rng.choice((s_shape, t_shape))]
        preserve = [False, False, True]
    elif profile == 3:  # canonical complex morphology
        shapes = [l_shape, stair_3, border_6]
        preserve = [False, False, False]
    elif profile == 1:  # explicit add+delete witness
        size = {"easy": (3, 3), "medium": (3, 4), "hard": (4, 4)}[band]
        shapes = [_path_shape(*size, rng), s_shape, l_shape]
        preserve = [False] * len(shapes)
    else:  # broad morphology and orientation witness
        if band == "easy":
            shapes = [t_shape, _rotate(s_shape), l_shape]
        elif band == "medium":
            shapes = [_path_shape(3, 3, rng), _path_shape(2, 4, rng), _rotate(s_shape)]
        else:
            shapes = [_path_shape(4, 3, rng), _path_shape(3, 4, rng), _path_shape(2, 4, rng)]
        preserve = [False] * len(shapes)

    while len(shapes) < n:
        shapes.append(l_shape if len(shapes) % 2 else s_shape)
        preserve.append(False)
    shapes = shapes[:n]
    preserve = preserve[:n]

    transformed = []
    for index, (shape, keep_orientation) in enumerate(zip(shapes, preserve)):
        code = rng.randrange(4 if keep_orientation else 8)
        transformed.append(
            _transform_shape(
                shape,
                code,
                preserve_bbox_orientation=keep_orientation,
            )
        )
    return transformed


def _rect_separated(rect, other, gap: int = 1) -> bool:
    r0, c0, r1, c1 = rect
    or0, oc0, or1, oc1 = other
    return (
        r1 + gap < or0
        or or1 + gap < r0
        or c1 + gap < oc0
        or oc1 + gap < c0
    )


def _pack_shapes(height: int, width: int, shapes, rng):
    """Backtracking rectangle packer; bbox separation keeps oracle roles clean."""
    order = sorted(
        range(len(shapes)),
        key=lambda i: (_shape_dimensions(shapes[i])[0] * _shape_dimensions(shapes[i])[1], i),
        reverse=True,
    )
    placements: dict[int, tuple[int, int]] = {}
    rects: list[tuple[int, int, int, int]] = []

    def search(depth: int) -> bool:
        if depth == len(order):
            return True
        index = order[depth]
        shape_h, shape_w = _shape_dimensions(shapes[index])
        candidates = [
            (row, col)
            for row in range(height - shape_h + 1)
            for col in range(width - shape_w + 1)
        ]
        rng.shuffle(candidates)
        for row, col in candidates:
            rect = (row, col, row + shape_h - 1, col + shape_w - 1)
            if any(not _rect_separated(rect, other, gap=1) for other in rects):
                continue
            placements[index] = (row, col)
            rects.append(rect)
            if search(depth + 1):
                return True
            rects.pop()
            placements.pop(index, None)
        return False

    if not search(0):
        raise ValueError(
            f"cannot place {len(shapes)} separated object bboxes in {height}x{width}"
        )
    return [placements[index] for index in range(len(shapes))]


def _default_dimensions(profile: int, band: str, rng) -> tuple[int, int]:
    if profile == 0:
        return rng.choice(((8, 10), (9, 9), (9, 10)))
    if profile == 3:
        return (9, 9)
    if profile == 1:
        return {
            "easy": (9, 12),
            "medium": (11, 14),
            "hard": (13, 17),
        }[band]
    return {
        "easy": (10, 12),
        "medium": (12, 15),
        "hard": (14, 18),
    }[band]


def _default_component_count(profile: int, band: str) -> int:
    if profile in (0, 3):
        return 3
    return {"easy": 3, "medium": 4, "hard": 5}[band]


def _colors(n: int, mode: str, rng) -> list[int]:
    if mode == "distinct":
        return rng.sample(list(range(1, 10)), n)
    distinct_n = max(2, n - 2)
    palette = rng.sample(list(range(1, 10)), distinct_n)
    colors = [palette[index % distinct_n] for index in range(n)]
    rng.shuffle(colors)
    if len(set(colors)) == n:
        colors[-1] = colors[0]
    return colors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    band = difficulty if difficulty in ("easy", "medium", "hard") else "medium"
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    profile = int(sample_index) % 4
    layout_rng = ctx.draw_rng("layout")
    default_h, default_w = _default_dimensions(profile, band, layout_rng)
    default_n = _default_component_count(profile, band)
    default_palette_mode = "distinct" if profile in (0, 3) else "repeated"

    height = _draw_int_axis(ctx, overrides, "grid_h", default_h, 8, 14)
    width = _draw_int_axis(ctx, overrides, "grid_w", default_w, 9, 18)
    n_components = _draw_int_axis(
        ctx, overrides, "n_components", default_n, 3, 5
    )
    palette_mode = _draw_choice_axis(
        ctx,
        overrides,
        "palette_mode",
        default_palette_mode,
        PALETTE_MODES,
    )

    # Re-transforming shapes across attempts keeps explicit small canvases
    # feasible without silently changing any declared axis.
    last_error = None
    for attempt in range(24):
        attempt_rng = ctx.draw_rng(f"shape-layout-{attempt}")
        shapes = _profile_shapes(profile, band, n_components, attempt_rng)
        try:
            placements = _pack_shapes(height, width, shapes, attempt_rng)
        except ValueError as exc:
            last_error = exc
            continue
        colors = _colors(n_components, palette_mode, ctx.draw_rng(f"colors-{attempt}"))
        grid = full_grid(height, width, 0)
        for shape, (top, left), color in zip(shapes, placements, colors):
            for row, col in shape:
                grid[top + row][left + col] = color
        errors = self_check(
            grid,
            difficulty=band,
            meta={"n_components": n_components, "palette_mode": palette_mode},
        )
        if not errors:
            return grid
        last_error = ValueError("; ".join(errors))
    raise ValueError(str(last_error or "could not construct a valid scene"))


def _components(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    components = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            color = grid[row][col]
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                current = stack.pop()
                cells.append(current)
                r, c = current
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append((color, tuple(sorted(cells))))
    return components


def _bbox_border(r0: int, c0: int, r1: int, c1: int):
    return {
        (row, col)
        for row in range(r0, r1 + 1)
        for col in range(c0, c1 + 1)
        if row in (r0, r1) or col in (c0, c1)
    }


def _analyze(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return {"errors": ["grid must be a nonempty list of rows"]}
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular"]}
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return {"errors": ["all cells must be integer ARC colors 0..9"]}

    height = len(grid)
    components = []
    frame_cells_seen: set[tuple[int, int]] = set()
    rects = []
    output = full_grid(height, width, 0)
    for color, cells in _components(grid):
        rows = [row for row, _col in cells]
        cols = [col for _row, col in cells]
        r0, r1, c0, c1 = min(rows), max(rows), min(cols), max(cols)
        bbox_h, bbox_w = r1 - r0 + 1, c1 - c0 + 1
        border = _bbox_border(r0, c0, r1, c1)
        cell_set = set(cells)
        interior = cell_set - border
        missing_border = border - cell_set
        rect = (r0, c0, r1, c1)
        if any(not _rect_separated(rect, other, gap=0) for other in rects):
            errors.append(f"component color {color} has an overlapping bbox")
        if frame_cells_seen & border:
            errors.append(f"component color {color} has a frame collision")
        frame_cells_seen.update(border)
        rects.append(rect)
        for row, col in border:
            output[row][col] = color
        components.append(
            {
                "color": color,
                "cells": cells,
                "cell_set": cell_set,
                "size": len(cells),
                "bbox": rect,
                "bbox_h": bbox_h,
                "bbox_w": bbox_w,
                "bbox_area": bbox_h * bbox_w,
                "border": border,
                "interior_count": len(interior),
                "missing_border_count": len(missing_border),
                "signature": (
                    len(cells),
                    bbox_h,
                    bbox_w,
                    bbox_h * bbox_w - len(cells),
                    len(interior),
                ),
            }
        )
    return {
        "errors": errors,
        "height": height,
        "width": width,
        "components": components,
        "palette": set(value for row in grid for value in row),
        "output": output,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    height, width = analysis["height"], analysis["width"]
    if not 8 <= height <= 14:
        errors.append(f"grid height must be 8..14, got {height}")
    if not 9 <= width <= 18:
        errors.append(f"grid width must be 9..18, got {width}")
    components = analysis["components"]
    if not 3 <= len(components) <= 5:
        errors.append(f"expected 3..5 components, got {len(components)}")
    for index, component in enumerate(components):
        if component["bbox_h"] < 2 or component["bbox_w"] < 2:
            errors.append(
                f"component {index} has a {component['bbox_h']}x{component['bbox_w']} bbox; both dimensions must be >=2"
            )
        if component["cell_set"] == component["border"]:
            errors.append(f"component {index} is already its bbox perimeter")
        if component["missing_border_count"] == 0:
            errors.append(f"component {index} has no missing border cell")
    if grid == analysis["output"]:
        errors.append("the bbox-outline transformation is an identity")

    requested_n = None
    requested_palette_mode = None
    if isinstance(meta, dict):
        requested_n = meta.get("n_components")
        requested_palette_mode = meta.get("palette_mode")
        nested = meta.get("overrides")
        if isinstance(nested, dict):
            requested_n = nested.get("n_components", requested_n)
            requested_palette_mode = nested.get("palette_mode", requested_palette_mode)
    if requested_n is not None and len(components) != int(requested_n):
        errors.append(
            f"n_components requested {requested_n}, observed {len(components)}"
        )
    nonzero_colors = {component["color"] for component in components}
    if requested_palette_mode == "distinct" and len(nonzero_colors) != len(components):
        errors.append("palette_mode='distinct' but component colors repeat")
    if requested_palette_mode == "repeated" and len(nonzero_colors) >= len(components):
        errors.append("palette_mode='repeated' but all component colors are distinct")
    return errors


def observe_overrides(grid) -> dict[str, int]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "n_components": len(analysis["components"]),
    }


def _linked_signature(analysis: dict[str, Any]):
    return (
        analysis["height"],
        analysis["width"],
        len(analysis["palette"]),
        tuple(sorted(component["signature"] for component in analysis["components"])),
    )


def strict_canonical_like(grid) -> list[str]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return list(analysis["errors"])
    signature = _linked_signature(analysis)
    if signature not in _CANONICAL_LINKED_SIGNATURES:
        return [f"joint canonical signature not observed: {signature!r}"]
    return []


def canonical_profile_signature(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return None
    return _linked_signature(analysis)


def semantic_signature(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    components = analysis["components"]
    return {
        "height": analysis["height"],
        "width": analysis["width"],
        "component_count": len(components),
        "distinct_nonzero_colors": len({component["color"] for component in components}),
        "object_signatures": tuple(sorted(component["signature"] for component in components)),
        "objects_with_interior_input": sum(component["interior_count"] > 0 for component in components),
        "objects_with_missing_border": sum(component["missing_border_count"] > 0 for component in components),
        "added_border_cells": sum(component["missing_border_count"] for component in components),
        "deleted_interior_cells": sum(component["interior_count"] for component in components),
        "strict_canonical_like": not strict_canonical_like(grid),
    }


def rule_mirror(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return deepcopy(analysis["output"])


def _witness(predicate):
    def wrapped(grid):
        analysis = _analyze(grid)
        return not analysis["errors"] and bool(predicate(analysis))

    return wrapped


SEMANTIC_WITNESSES = {
    "adds_missing_border_cells": _witness(
        lambda a: any(c["missing_border_count"] > 0 for c in a["components"])
    ),
    "deletes_interior_input_cells": _witness(
        lambda a: any(c["interior_count"] > 0 for c in a["components"])
    ),
    "two_by_n_bbox_branch": _witness(
        lambda a: any(c["bbox_h"] == 2 or c["bbox_w"] == 2 for c in a["components"])
    ),
    "three_by_three_or_larger_bbox": _witness(
        lambda a: any(c["bbox_h"] >= 3 and c["bbox_w"] >= 3 for c in a["components"])
    ),
    "multiple_independent_objects": _witness(lambda a: len(a["components"]) >= 3),
    "distinct_component_colors": _witness(
        lambda a: len({c["color"] for c in a["components"]}) == len(a["components"])
    ),
    "repeated_color_separate_objects": _witness(
        lambda a: len({c["color"] for c in a["components"]}) < len(a["components"])
    ),
    "canonical_linked_profile": _witness(
        lambda a: _linked_signature(a) in _CANONICAL_LINKED_SIGNATURES
    ),
}


def _pair_analysis(pair, label: str):
    if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
        return None, [f"{label} must contain input and output grids"]
    analysis = _analyze(pair["input"])
    if analysis["errors"]:
        return None, [f"{label}: {error}" for error in analysis["errors"]]
    expected = analysis["output"]
    if pair["output"] != expected:
        return None, [f"{label} output is not the per-object bbox perimeter"]
    return analysis, []


def _fill_bbox_output(analysis):
    output = full_grid(analysis["height"], analysis["width"], 0)
    for component in analysis["components"]:
        r0, c0, r1, c1 = component["bbox"]
        for row in range(r0, r1 + 1):
            for col in range(c0, c1 + 1):
                output[row][col] = component["color"]
    return output


def _add_only_output(grid, analysis):
    output = deepcopy(grid)
    for component in analysis["components"]:
        for row, col in component["border"]:
            output[row][col] = component["color"]
    return output


def _mask(grid):
    return tuple(tuple(value != 0 for value in row) for row in grid)


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons compatible with named bbox shortcuts."""
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    analyses = []
    for index, pair in enumerate(demos):
        analysis, pair_errors = _pair_analysis(pair, f"demo {index}")
        reasons.extend(pair_errors)
        if analysis is not None:
            analyses.append((pair, analysis))
    query_analysis, query_errors = _pair_analysis(query, "query")
    reasons.extend(query_errors)
    if reasons:
        return reasons

    if all(pair["input"] == pair["output"] for pair, _analysis in analyses):
        reasons.append("the no-op rule remains consistent with every demonstration")
    if all(_fill_bbox_output(analysis) == pair["output"] for pair, analysis in analyses):
        reasons.append("fill each bbox solid remains consistent with every demonstration")
    if all(_add_only_output(pair["input"], analysis) == pair["output"] for pair, analysis in analyses):
        reasons.append("add the missing border without erasing interiors remains consistent")
    if not any(
        any(c["interior_count"] > 0 for c in analysis["components"])
        for _pair, analysis in analyses
    ):
        reasons.append("no demonstration requires deleting an interior input cell")
    if not any(
        any(c["bbox_h"] >= 3 and c["bbox_w"] >= 3 for c in analysis["components"])
        for _pair, analysis in analyses
    ):
        reasons.append("no demonstration distinguishes an outline from a filled 2xN box")
    if not any(
        any(c["bbox_h"] == 2 or c["bbox_w"] == 2 for c in analysis["components"])
        for _pair, analysis in analyses
    ):
        reasons.append("the degenerate 2xN perimeter branch is not demonstrated")

    all_bbox_sizes = {
        (c["bbox_h"], c["bbox_w"])
        for _pair, analysis in analyses
        for c in analysis["components"]
    }
    if len(all_bbox_sizes) < 3:
        reasons.append("too few bbox sizes to rule out fixed-shape completion")
    if len({(a["height"], a["width"]) for _p, a in analyses}) < 3:
        reasons.append("grid dimensions vary fewer than three ways")
    if len({tuple(c["bbox"][:2] for c in a["components"]) for _p, a in analyses}) < 3:
        reasons.append("object positions vary fewer than three ways")

    by_count: dict[int, set[Any]] = {}
    for pair, analysis in analyses:
        by_count.setdefault(len(analysis["components"]), set()).add(_mask(pair["output"]))
    if not any(len(outputs) >= 2 for outputs in by_count.values()):
        reasons.append("count-only prediction is not contradicted at a fixed object count")

    # A single foreground-bbox frame must disagree with at least one demo's
    # disconnected per-object output mask.
    whole_scene_rebutted = False
    for pair, analysis in analyses:
        cells = [cell for component in analysis["components"] for cell in component["cells"]]
        r0 = min(r for r, _c in cells)
        r1 = max(r for r, _c in cells)
        c0 = min(c for _r, c in cells)
        c1 = max(c for _r, c in cells)
        whole_mask = full_grid(analysis["height"], analysis["width"], 0)
        for row, col in _bbox_border(r0, c0, r1, c1):
            whole_mask[row][col] = 1
        if _mask(whole_mask) != _mask(pair["output"]):
            whole_scene_rebutted = True
            break
    if not whole_scene_rebutted:
        reasons.append("frame the whole foreground bbox remains consistent")

    if query_analysis is not None and not query_analysis["components"]:
        reasons.append("query contains no object to transform")
    return reasons
