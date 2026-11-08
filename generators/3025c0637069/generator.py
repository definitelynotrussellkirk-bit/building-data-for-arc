"""Generator for ARC task 3345333e / content hash 3025c0637069.

Rule: identify the solid rectangular occluder, remove it, and reconstruct the
hidden cells of the other color by reflecting the visible shape left-to-right
about its vertical symmetry axis.

The ordinary schedule alternates the occluder side and axis parity.  Every
consecutive two-example window therefore contains both left/right occlusion
and both between-column/integer-column symmetry, while each individual scene
contains hidden shape cells and hidden background cells.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect, full_grid

GENERATOR_ID = "3025c0637069"
TASK_ID = "3025c0637069"
VERSION = "3.0.0"
RULE_HASH = "d83ebbc6e8c5"  # sha256[:12] of whitespace-normalized canonical program_solution

SUMMARY = (
    "A 14..18 square-ish grid contains exactly two non-background colors: "
    "one forms a non-rectangular left-right-symmetric shape and the other a "
    "solid rectangular occluder covering the shape's left or right edge. "
    "Remove the rectangle and fill only those rectangle cells whose mirror "
    "counterparts are visible shape cells."
)

INVARIANTS = [
    "exactly one nonzero color is a solid rectangle",
    "the other nonzero color is a non-rectangular left-right-symmetric shape",
    "visible shape evidence is compatible with one left-right symmetry axis",
    "the occluder lies wholly on one side of the axis and overlaps the shape",
    "the occluder hides at least one shape cell and at least one background cell",
    "shape and occluder colors are distinct and nonzero",
]

PALETTE_PAIRS = {
    "p12": (1, 2),
    "p34": (3, 4),
    "p56": (5, 6),
    "p78": (7, 8),
    "p91": (9, 1),
}

AXES = {
    "canvas_kind": {
        "type": "str",
        "default": "scheduled",
        "valid": "canonical|expanded",
    },
    "shape_height": {"type": "int", "default": "difficulty-aware 8..10", "valid": "8..10"},
    "shape_width": {"type": "int", "default": "scheduled parity 8..10", "valid": "8..10"},
    "rect_height": {"type": "int", "default": "rng 3..5", "valid": "3..5"},
    "rect_width": {"type": "int", "default": "rng 3..4", "valid": "3..4"},
    "occluder_side": {"type": "str", "default": "scheduled", "valid": "left|right"},
    "position_bias": {"type": "str", "default": "scheduled", "valid": "left|center|right"},
    "palette_pair": {"type": "str", "default": "rng", "valid": "p12|p34|p56|p78|p91"},
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 0.95
SCHEDULE_PROFILES = (0, 1, 2, 3)


def schedule_profile(seed, sample_index, difficulty=None):
    """Four-profile cycle; seed/difficulty are intentionally nuisance inputs."""
    del seed, difficulty
    return int(sample_index) % 4


def _draw_int_axis(ctx, label: str, ordinary: tuple[int, int], full: tuple[int, int]) -> int:
    if label in ctx.overrides:
        return ctx.draw_int(label, *full)
    return ctx.draw_int(label, *ordinary)


def _draw_choice_axis(ctx, label: str, options: tuple[Any, ...], scheduled: Any | None = None):
    if label in ctx.overrides or scheduled is None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (scheduled,))


def _bbox(cells: list[tuple[int, int]]) -> tuple[int, int, int, int]:
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _is_solid_rectangle(cells: list[tuple[int, int]]) -> bool:
    if not cells:
        return False
    r0, c0, r1, c1 = _bbox(cells)
    return len(cells) == (r1 - r0 + 1) * (c1 - c0 + 1)


def _position_name(start: int, total: int, span: int) -> str:
    candidates = (("left", 1), ("center", (total - span) // 2), ("right", total - span - 1))
    return min(candidates, key=lambda item: (abs(start - item[1]), candidates.index(item)))[0]


def _analyze(grid) -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        return None, ["grid must be a non-empty list of rows"]
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return None, ["grid must be non-empty and rectangular"]
    height = len(grid)
    if not (14 <= height <= 18 and 14 <= width <= 18):
        errors.append(f"grid dimensions must be within 14..18, found {height}x{width}")
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append(f"cell ({r},{c}) has invalid ARC color {value!r}")
    if errors:
        return None, errors

    colors = sorted({value for row in grid for value in row if value != 0})
    if len(colors) != 2:
        return None, [f"expected exactly two non-background colors, found {colors}"]
    by_color = {
        color: [(r, c) for r in range(height) for c in range(width) if grid[r][c] == color]
        for color in colors
    }
    rectangle_colors = [color for color, cells in by_color.items() if _is_solid_rectangle(cells)]
    if len(rectangle_colors) != 1:
        return None, [f"expected exactly one solid-rectangle color, found {rectangle_colors}"]

    rect_color = rectangle_colors[0]
    shape_color = next(color for color in colors if color != rect_color)
    rect_cells = by_color[rect_color]
    shape_cells = by_color[shape_color]
    rr0, rc0, rr1, rc1 = _bbox(rect_cells)
    rect_height = rr1 - rr0 + 1
    rect_width = rc1 - rc0 + 1
    if not (3 <= rect_height <= 5):
        errors.append(f"rectangle height must be 3..5, found {rect_height}")
    if not (3 <= rect_width <= 4):
        errors.append(f"rectangle width must be 3..4, found {rect_width}")
    if _is_solid_rectangle(shape_cells):
        errors.append("shape color must not itself form a solid rectangle")

    sr0, visible_left, sr1, visible_right = _bbox(shape_cells)
    shape_height = sr1 - sr0 + 1
    if not (8 <= shape_height <= 10):
        errors.append(f"shape height must be 8..10, found {shape_height}")

    # This is the same axis reconstruction used by the canonical rule.  The
    # rectangle's outer edge extends one cell beyond the hidden shape edge.
    left_bound = min(visible_left, rc0 + 1)
    right_bound = max(visible_right, rc1 - 1)
    shape_width = right_bound - left_bound + 1
    axis2 = left_bound + right_bound
    if not (6 <= shape_width <= 10):
        errors.append(f"inferred symmetric shape width must be 6..10, found {shape_width}")

    rect_center2 = rc0 + rc1
    if rect_center2 < axis2:
        side = "left"
        if rc0 + 1 != left_bound:
            errors.append("left occluder must start one column outside the hidden shape")
        if 2 * rc1 >= axis2:
            errors.append("left occluder must remain wholly left of the symmetry axis")
    elif rect_center2 > axis2:
        side = "right"
        if rc1 - 1 != right_bound:
            errors.append("right occluder must end one column outside the hidden shape")
        if 2 * rc0 <= axis2:
            errors.append("right occluder must remain wholly right of the symmetry axis")
    else:
        side = "unknown"
        errors.append("occluder center may not coincide with the symmetry axis")

    if rr1 < sr0 or rr0 > sr1:
        errors.append("occluder must overlap the shape vertically")

    # Every visible shape cell must have a visible or occluded mirror mate.
    asymmetric: list[tuple[int, int, int]] = []
    for r, c in shape_cells:
        mirror_c = axis2 - c
        if not 0 <= mirror_c < width:
            asymmetric.append((r, c, mirror_c))
            continue
        inside_rect = rr0 <= r <= rr1 and rc0 <= mirror_c <= rc1
        if not inside_rect and grid[r][mirror_c] != shape_color:
            asymmetric.append((r, c, mirror_c))
    if asymmetric:
        errors.append(f"visible shape has {len(asymmetric)} unpaired cell(s), first={asymmetric[0]}")

    hidden_shape = 0
    hidden_background = 0
    mirror_inside = 0
    for r in range(rr0, rr1 + 1):
        for c in range(rc0, rc1 + 1):
            mirror_c = axis2 - c
            if rc0 <= mirror_c <= rc1:
                mirror_inside += 1
            if 0 <= mirror_c < width and grid[r][mirror_c] == shape_color:
                hidden_shape += 1
            else:
                hidden_background += 1
    if mirror_inside:
        errors.append(f"{mirror_inside} occluder cell(s) mirror back into the occluder")
    if hidden_shape == 0:
        errors.append("occluder hides no reconstructable shape cells")
    if hidden_background == 0:
        errors.append("occluder hides no background cells; solid-fill shortcut remains valid")

    palette_pair = next(
        (name for name, pair in PALETTE_PAIRS.items() if pair == (shape_color, rect_color)),
        None,
    )
    analysis = {
        "height": height,
        "width": width,
        "shape_color": shape_color,
        "rect_color": rect_color,
        "rect_bbox": (rr0, rc0, rr1, rc1),
        "shape_row_bounds": (sr0, sr1),
        "shape_bounds": (left_bound, right_bound),
        "axis2": axis2,
        "side": side,
        "shape_height": shape_height,
        "shape_width": shape_width,
        "rect_height": rect_height,
        "rect_width": rect_width,
        "hidden_shape": hidden_shape,
        "hidden_background": hidden_background,
        "palette_pair": palette_pair,
        "position_bias": _position_name(left_bound, width, shape_width),
    }
    return analysis, errors


def _symmetric_mask(shape_height: int, shape_width: int, rng) -> set[tuple[int, int]]:
    """Create a canonical-scale sparse, connected symmetric shape.

    A central spine connects every row. One full bridge row establishes the
    horizontal extent; a neighboring row keeps only the spine plus symmetric
    outer endpoints, producing a non-contiguous but still connected profile.
    """
    left_center = (shape_width - 1) // 2
    right_center = shape_width // 2
    max_distance = left_center
    cells: set[tuple[int, int]] = set()

    for r in range(shape_height):
        cells.add((r, left_center))
        cells.add((r, right_center))

    forced_gap_row = shape_height // 2
    if forced_gap_row % 2 == 0:
        forced_gap_row = min(shape_height - 2, forced_gap_row + 1)
    forced_gap_row = max(1, forced_gap_row)
    bridge_row = forced_gap_row - 1
    for c in range(shape_width):
        cells.add((bridge_row, c))
    cells.add((forced_gap_row, 0))
    cells.add((forced_gap_row, shape_width - 1))

    # Add a few smaller contiguous arms without coupling them to height.
    for r in range(0, shape_height, 2):
        if r == bridge_row:
            continue
        radius = rng.randint(1, max(1, max_distance - 1))
        for c in range(left_center - radius, right_center + radius + 1):
            cells.add((r, c))

    return cells


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)

    canvas_kind = _draw_choice_axis(
        ctx,
        "canvas_kind",
        ("canonical", "expanded"),
        "canonical" if profile in {0, 1} else "expanded",
    )
    occluder_side = _draw_choice_axis(
        ctx,
        "occluder_side",
        ("left", "right"),
        "left" if profile % 2 == 0 else "right",
    )
    position_bias = _draw_choice_axis(
        ctx,
        "position_bias",
        ("left", "center", "right"),
        ("left", "center", "right", "center")[profile],
    )
    palette_pair = _draw_choice_axis(ctx, "palette_pair", tuple(PALETTE_PAIRS))

    if difficulty == "easy":
        shape_h_bounds = (8, 9)
    elif difficulty == "hard":
        shape_h_bounds = (9, 10)
    else:
        shape_h_bounds = (8, 10)
    # Keep rectangle height independent of shape height; the rule does not
    # couple those dimensions, and independent draws prevent a spurious cue.
    rect_h_bounds = (3, 5)

    shape_height = _draw_int_axis(ctx, "shape_height", shape_h_bounds, (8, 10))
    scheduled_width = 8 if profile % 2 == 0 else 9
    shape_width = _draw_int_axis(ctx, "shape_width", (scheduled_width, scheduled_width), (8, 10))
    rect_height = _draw_int_axis(ctx, "rect_height", rect_h_bounds, (3, 5))
    rect_width = _draw_int_axis(ctx, "rect_width", (3, 4), (3, 4))

    if canvas_kind == "canonical":
        height = width = 16
    else:
        sizes = (14, 15, 17, 18)
        layout_rng = ctx.draw_rng("canvas_dimensions")
        height = layout_rng.choice(sizes)
        width = layout_rng.choice(sizes)

    shape_top_rng = ctx.draw_rng("shape_top")
    shape_top = shape_top_rng.randint(1, height - shape_height - 1)
    starts = {
        "left": 1,
        "center": (width - shape_width) // 2,
        "right": width - shape_width - 1,
    }
    shape_left = starts[position_bias]

    mask = _symmetric_mask(shape_height, shape_width, ctx.draw_rng("shape_texture"))
    shape_color, rect_color = PALETTE_PAIRS[palette_pair]
    grid = full_grid(height, width, 0)
    for dr, dc in mask:
        grid[shape_top + dr][shape_left + dc] = shape_color

    if occluder_side == "left":
        rect_left = shape_left - 1
    else:
        rect_left = shape_left + shape_width - rect_width + 1
    axis2 = 2 * shape_left + shape_width - 1
    valid_rect_tops: list[int] = []
    for candidate_top in range(shape_top, shape_top + shape_height - rect_height + 1):
        hidden_shape = hidden_background = 0
        for r in range(candidate_top, candidate_top + rect_height):
            for c in range(rect_left, rect_left + rect_width):
                mirror_c = axis2 - c
                if 0 <= mirror_c < width and grid[r][mirror_c] == shape_color:
                    hidden_shape += 1
                else:
                    hidden_background += 1
        if hidden_shape and hidden_background:
            valid_rect_tops.append(candidate_top)
    if not valid_rect_tops:
        raise ValueError("no lawful rectangle placement hides both shape and background")
    rect_top = ctx.draw_rng("rect_top").choice(valid_rect_tops)
    draw_rect(grid, rect_top, rect_left, rect_height, rect_width, rect_color)

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise ValueError(f"constructed invalid generator instance: {errors}")
    return [row[:] for row in grid]


def observe_overrides(grid) -> dict[str, Any]:
    analysis, errors = _analyze(grid)
    if analysis is None or errors:
        return {
            "canvas_kind": None,
            "shape_height": None,
            "shape_width": None,
            "rect_height": None,
            "rect_width": None,
            "occluder_side": None,
            "position_bias": None,
            "palette_pair": None,
        }
    return {
        "canvas_kind": "canonical" if analysis["height"] == analysis["width"] == 16 else "expanded",
        "shape_height": analysis["shape_height"],
        "shape_width": analysis["shape_width"],
        "rect_height": analysis["rect_height"],
        "rect_width": analysis["rect_width"],
        "occluder_side": analysis["side"],
        "position_bias": analysis["position_bias"],
        "palette_pair": analysis["palette_pair"],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    _, errors = _analyze(grid)
    return errors


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def _solve_grid(grid):
    analysis, errors = _analyze(grid)
    if analysis is None or errors:
        raise ValueError(f"cannot solve malformed grid: {errors}")
    output = [row[:] for row in grid]
    rr0, rc0, rr1, rc1 = analysis["rect_bbox"]
    axis2 = analysis["axis2"]
    shape_color = analysis["shape_color"]
    width = analysis["width"]
    for r in range(rr0, rr1 + 1):
        for c in range(rc0, rc1 + 1):
            mirror_c = axis2 - c
            output[r][c] = (
                shape_color
                if 0 <= mirror_c < width and grid[r][mirror_c] == shape_color
                else 0
            )
    return output


def _clear_rectangle_only(grid):
    analysis, errors = _analyze(grid)
    if analysis is None or errors:
        return [row[:] for row in grid]
    output = [row[:] for row in grid]
    rr0, rc0, rr1, rc1 = analysis["rect_bbox"]
    for r in range(rr0, rr1 + 1):
        for c in range(rc0, rc1 + 1):
            output[r][c] = 0
    return output


def _fill_rectangle_solid(grid):
    analysis, errors = _analyze(grid)
    if analysis is None or errors:
        return [row[:] for row in grid]
    output = [row[:] for row in grid]
    rr0, rc0, rr1, rc1 = analysis["rect_bbox"]
    for r in range(rr0, rr1 + 1):
        for c in range(rc0, rc1 + 1):
            output[r][c] = analysis["shape_color"]
    return output


def _one_side_only(grid, allowed_side: str):
    analysis, errors = _analyze(grid)
    if analysis is None or errors:
        return [row[:] for row in grid]
    return _solve_grid(grid) if analysis["side"] == allowed_side else _clear_rectangle_only(grid)


def _between_columns_only(grid):
    analysis, errors = _analyze(grid)
    if analysis is None or errors:
        return [row[:] for row in grid]
    if analysis["axis2"] % 2 == 1:
        return _solve_grid(grid)
    # Plausible bug: force an integer-axis task onto a between-column axis.
    output = [row[:] for row in grid]
    rr0, rc0, rr1, rc1 = analysis["rect_bbox"]
    used_axis2 = analysis["axis2"] + 1
    for r in range(rr0, rr1 + 1):
        for c in range(rc0, rc1 + 1):
            mirror_c = used_axis2 - c
            output[r][c] = (
                analysis["shape_color"]
                if 0 <= mirror_c < analysis["width"] and grid[r][mirror_c] == analysis["shape_color"]
                else 0
            )
    return output


def _analysis_predicate(grid, predicate: Callable[[dict[str, Any]], bool]) -> bool:
    analysis, errors = _analyze(grid)
    return bool(analysis is not None and not errors and predicate(analysis))


def _has_noncontiguous_symmetric_row(grid) -> bool:
    analysis, errors = _analyze(grid)
    if analysis is None or errors:
        return False
    shape_color = analysis["shape_color"]
    left, right = analysis["shape_bounds"]
    reconstructed = _solve_grid(grid)
    for row in reconstructed:
        cols = [c for c in range(left, right + 1) if row[c] == shape_color]
        if len(cols) >= 3 and any(b - a > 1 for a, b in zip(cols, cols[1:])):
            return True
    return False


SEMANTIC_WITNESSES = {
    "left_occluder": lambda grid: _analysis_predicate(grid, lambda a: a["side"] == "left"),
    "right_occluder": lambda grid: _analysis_predicate(grid, lambda a: a["side"] == "right"),
    "odd_width_integer_axis": lambda grid: _analysis_predicate(grid, lambda a: a["shape_width"] % 2 == 1),
    "even_width_between_axis": lambda grid: _analysis_predicate(grid, lambda a: a["shape_width"] % 2 == 0),
    "mixed_hidden_payload": lambda grid: _analysis_predicate(
        grid, lambda a: a["hidden_shape"] > 0 and a["hidden_background"] > 0
    ),
    "noncontiguous_row_texture": _has_noncontiguous_symmetric_row,
    "canonical_canvas": lambda grid: len(grid) == 16 and len(grid[0]) == 16,
}

SEMANTIC_RIVALS = {
    "clear_rectangle_only": _clear_rectangle_only,
    "fill_rectangle_solid": _fill_rectangle_solid,
    "left_occluder_only": lambda grid: _one_side_only(grid, "left"),
    "right_occluder_only": lambda grid: _one_side_only(grid, "right"),
    "between_columns_only": _between_columns_only,
}

WITNESS_RIVALS = {
    "mixed_hidden_payload": ["clear_rectangle_only", "fill_rectangle_solid"],
    "left_occluder": ["right_occluder_only"],
    "right_occluder": ["left_occluder_only"],
    "odd_width_integer_axis": ["between_columns_only"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} is missing input/output")
            continue
        try:
            expected = _solve_grid(pair["input"])
        except Exception as exc:
            reasons.append(f"pair {index} is outside the task grammar: {exc}")
            continue
        if pair["output"] != expected:
            reasons.append(f"pair {index} output disagrees with mirror reconstruction")

    for name, rival in LESSON_COMPETITORS.items():
        try:
            survives = all(rival(demo["input"]) == demo["output"] for demo in demos)
            query_differs = rival(query["input"]) != query["output"]
        except Exception as exc:
            reasons.append(f"competitor {name!r} raised: {exc}")
            continue
        if survives and query_differs:
            reasons.append(f"demonstrations do not refute competitor: {name}")
    return reasons
