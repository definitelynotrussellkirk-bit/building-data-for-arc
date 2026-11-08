"""Semantic input generator for ``2d5acf84dd20`` (Depth-Colored Nested Frames).

The canonical Racket authority sorts nonzero components by descending bounding-
box area and recolors them 2, 3, 4, ... .  On the task's lawful grammar—strictly
nested rectangular frames separated by blank moats—that ordering is exactly
outermost-to-innermost containment depth.  This generator therefore varies the
nested-frame geometry without emitting the disjoint blobs that made the former
version teach an implementation-specific area-ranking shortcut.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "2d5acf84dd20"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "9cbecad9efb8"
MIN_STRICT_FRAC = 1.0
EXAMPLES_NEEDED = 4

SUMMARY = (
    "A binary grid contains 2-4 complete blue rectangular outlines, strictly "
    "nested with at least one blank cell between adjacent frames. Recolor the "
    "outermost frame red(2), the next green(3), then 4 and 5 moving inward, "
    "leaving all background cells black(0)."
)

INVARIANTS = [
    "the input palette is exactly a subset of background 0 and frame color 1",
    "there are 2-4 separate four-connected color-1 components",
    "each component is a complete rectangular outline; canonical 1x1 and 2x2 innermost frames are lawful",
    "frame boxes are strictly nested and separated by at least one blank-cell moat",
    "bounding-box areas are distinct, so outer-to-inner depth order is unambiguous",
    "the output preserves every frame cell and recolors depth ranks from 2 upward",
]

COUNTER_HYPOTHESES = [
    "rank arbitrary disjoint blobs by bounding-box area",
    "infer output color only from distance to the canvas border",
    "redraw all frames concentrically around the canvas center",
    "color every frame red without distinguishing depth",
    "use only two output colors regardless of nesting depth",
    "reverse the depth order and color the innermost frame red",
]

AXES = {
    "frame_count": {
        "type": "int",
        "default": "four-profile sample-index schedule",
        "valid": "2..4",
    },
    "layout_style": {
        "type": "str",
        "default": "four-profile sample-index schedule",
        "valid": "concentric|offset",
    },
    "outer_margin": {
        "type": "str",
        "default": "four-profile sample-index schedule",
        "valid": "edge|inset",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[tuple[str, ...], ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
_ALLOWED_OVERRIDES = frozenset(AXES)

# Every four consecutive samples contains a shallow anchor, an offset/inset
# discriminator, a deep example, and a second offset example.  Thus a normal
# four-demonstration lesson cannot accidentally preserve the declared rivals.
SCHEDULE_PROFILES = (
    (2, "concentric", "edge"),
    (3, "offset", "inset"),
    (4, "concentric", "edge"),
    (3, "offset", "edge"),
)

BBox = tuple[int, int, int, int]
_CARD = ((-1, 0), (1, 0), (0, -1), (0, 1))


def schedule_profile(seed, sample_index, difficulty=None):
    """Expose the four-step production schedule to the semantic gate."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _scheduled_int(ctx, name: str, lo: int, hi: int, default: int) -> int:
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, default, default)


def _scheduled_choice(
    ctx, name: str, options: tuple[str, ...], default: str
) -> str:
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return str(ctx.draw_choice(name, options))
    return str(ctx.draw_choice(name, (default,)))


def _outline_cells(box: BBox) -> set[tuple[int, int]]:
    r0, c0, r1, c1 = box
    return {
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if r in (r0, r1) or c in (c0, c1)
    }


def _paint_frame(grid: list[list[int]], box: BBox, color: int = 1) -> None:
    for r, c in _outline_cells(box):
        grid[r][c] = color


def _bbox(cells: list[tuple[int, int]] | tuple[tuple[int, int], ...]) -> BBox:
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _area(box: BBox) -> int:
    r0, c0, r1, c1 = box
    return (r1 - r0 + 1) * (c1 - c0 + 1)


def _components_of_one(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []
    for start_r in range(h):
        for start_c in range(w):
            if grid[start_r][start_c] != 1 or (start_r, start_c) in seen:
                continue
            queue = [(start_r, start_c)]
            seen.add((start_r, start_c))
            cells: list[tuple[int, int]] = []
            for r, c in queue:
                cells.append((r, c))
                for dr, dc in _CARD:
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == 1
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            components.append(cells)
    return components


def _rectangular_errors(grid: Any) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list of rows"]
    if not isinstance(grid[0], list) or not grid[0]:
        return ["rows must be non-empty lists"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if len(grid) > 30 or width > 30:
        return [f"grid exceeds ARC 30x30 limit: {len(grid)}x{width}"]
    errors: list[str] = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append(f"invalid ARC color at ({r},{c}): {value!r}")
    return errors


def _analyze(grid: Any) -> dict[str, Any]:
    errors = _rectangular_errors(grid)
    result: dict[str, Any] = {"errors": errors}
    if errors:
        return result

    h, w = len(grid), len(grid[0])
    palette = {value for row in grid for value in row}
    if not palette <= {0, 1}:
        errors.append(
            f"input palette must be a subset of {{0,1}}, found {sorted(palette)}"
        )

    components = _components_of_one(grid)
    if not 2 <= len(components) <= 4:
        errors.append(f"expected 2-4 blue frame components, found {len(components)}")

    boxes: list[BBox] = []
    for index, cells in enumerate(components):
        box = _bbox(cells)
        r0, c0, r1, c1 = box
        height, width = r1 - r0 + 1, c1 - c0 + 1
        # The canonical ledger includes 1x1 and 2x2 innermost rectangles.
        # Other one-cell-wide lines are not rectangular-frame morphology.
        if min(height, width) < 3 and (height, width) not in ((1, 1), (2, 2)):
            errors.append(
                f"component {index} is not a canonical frame shape: {height}x{width}"
            )
        expected = _outline_cells(box)
        actual = set(cells)
        if actual != expected:
            missing = len(expected - actual)
            extra = len(actual - expected)
            errors.append(
                f"component {index} is not a complete rectangular frame "
                f"(missing={missing}, extra={extra})"
            )
        boxes.append(box)

    boxes.sort(key=lambda box: (-_area(box), box[0], box[1]))
    areas = [_area(box) for box in boxes]
    if len(areas) != len(set(areas)):
        errors.append(f"frame bounding-box areas must be distinct, found {areas}")

    insets: list[tuple[int, int, int, int]] = []
    for index, (outer, inner) in enumerate(zip(boxes, boxes[1:])):
        or0, oc0, or1, oc1 = outer
        ir0, ic0, ir1, ic1 = inner
        inset = (ir0 - or0, ic0 - oc0, or1 - ir1, oc1 - ic1)
        insets.append(inset)
        if min(inset) < 2:
            errors.append(
                f"frames {index} and {index + 1} are not strictly nested "
                f"with a blank moat: insets={inset}"
            )

    layout_style = None
    outer_margin = None
    margins = None
    if boxes:
        layout_style = (
            "concentric"
            if insets and all(inset == (2, 2, 2, 2) for inset in insets)
            else "offset"
        )
        r0, c0, r1, c1 = boxes[0]
        margins = (r0, c0, h - 1 - r1, w - 1 - c1)
        outer_margin = "edge" if min(margins) == 0 else "inset"

    result.update(
        {
            "height": h,
            "width": w,
            "components": components,
            "boxes": boxes,
            "areas": areas,
            "insets": insets,
            "layout_style": layout_style,
            "outer_margin": outer_margin,
            "margins": margins,
            "frame_count": len(boxes),
        }
    )
    return result


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, disjoint, or rule-hiding scenes."""
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and observed.get(name) != requested:
            errors.append(
                f"override {name}={requested!r} realized as {observed.get(name)!r}"
            )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """All ordinary draws use the canonical nested-frame grammar."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every exact caller-facing axis from returned pixels."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {}
    return {
        "frame_count": analysis["frame_count"],
        "layout_style": analysis["layout_style"],
        "outer_margin": analysis["outer_margin"],
    }


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror; canonical Racket remains output authority."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid input: " + "; ".join(analysis["errors"]))
    output = full_grid(analysis["height"], analysis["width"], 0)
    for depth, box in enumerate(analysis["boxes"], start=2):
        for r, c in _outline_cells(box):
            output[r][c] = depth
    return output


def _rival_flat_red(grid):
    analysis = _analyze(grid)
    output = full_grid(analysis["height"], analysis["width"], 0)
    for box in analysis["boxes"]:
        for r, c in _outline_cells(box):
            output[r][c] = 2
    return output


def _rival_two_levels(grid):
    analysis = _analyze(grid)
    output = full_grid(analysis["height"], analysis["width"], 0)
    for index, box in enumerate(analysis["boxes"]):
        for r, c in _outline_cells(box):
            output[r][c] = 2 if index == 0 else 3
    return output


def _rival_reverse_depth(grid):
    analysis = _analyze(grid)
    output = full_grid(analysis["height"], analysis["width"], 0)
    count = len(analysis["boxes"])
    for index, box in enumerate(analysis["boxes"]):
        color = 2 + (count - 1 - index)
        for r, c in _outline_cells(box):
            output[r][c] = color
    return output


def _rival_canvas_distance(grid):
    """Canonical-fitting shortcut: color from distance to the canvas edge."""
    analysis = _analyze(grid)
    h, w = analysis["height"], analysis["width"]
    output = full_grid(h, w, 0)
    for box in analysis["boxes"]:
        r0, c0, r1, c1 = box
        distance = min(r0, c0, h - 1 - r1, w - 1 - c1)
        color = min(9, 2 + max(0, (distance - 1) // 2))
        for r, c in _outline_cells(box):
            output[r][c] = color
    return output


def _rival_recenter_frames(grid):
    """Canonical-fitting shortcut: redraw every frame around canvas center."""
    analysis = _analyze(grid)
    h, w = analysis["height"], analysis["width"]
    output = full_grid(h, w, 0)
    for depth, box in enumerate(analysis["boxes"], start=2):
        r0, c0, r1, c1 = box
        frame_h, frame_w = r1 - r0 + 1, c1 - c0 + 1
        nr0 = (h - frame_h) // 2
        nc0 = (w - frame_w) // 2
        centered = (nr0, nc0, nr0 + frame_h - 1, nc0 + frame_w - 1)
        for r, c in _outline_cells(centered):
            output[r][c] = depth
    return output


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "flat_red": _rival_flat_red,
    "only_two_depth_levels": _rival_two_levels,
    "reverse_depth": _rival_reverse_depth,
    "canvas_distance": _rival_canvas_distance,
    "recenter_frames": _rival_recenter_frames,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "canvas_distance": _rival_canvas_distance,
    "recenter_frames": _rival_recenter_frames,
}


def _valid_analysis(grid):
    analysis = _analyze(grid)
    return analysis if not analysis["errors"] else None


def _frame_count_is(count: int):
    return lambda grid: bool(
        (analysis := _valid_analysis(grid)) and analysis["frame_count"] == count
    )


def _offset_recenter_killer(grid) -> bool:
    analysis = _valid_analysis(grid)
    return bool(
        analysis
        and analysis["layout_style"] == "offset"
        and _rival_recenter_frames(grid) != rule_mirror(grid)
    )


def _edge_canvas_distance_killer(grid) -> bool:
    analysis = _valid_analysis(grid)
    return bool(
        analysis
        and analysis["outer_margin"] == "edge"
        and _rival_canvas_distance(grid) != rule_mirror(grid)
    )


def _non_square_recenter_killer(grid) -> bool:
    analysis = _valid_analysis(grid)
    if not analysis:
        return False
    r0, c0, r1, c1 = analysis["boxes"][0]
    non_square = (r1 - r0) != (c1 - c0)
    return bool(non_square and _rival_recenter_frames(grid) != rule_mirror(grid))


SEMANTIC_WITNESSES = {
    "two_frames": _frame_count_is(2),
    "three_frames": _frame_count_is(3),
    "four_frames": _frame_count_is(4),
    "offset_recenter_killer": _offset_recenter_killer,
    "edge_canvas_distance_killer": _edge_canvas_distance_killer,
    "non_square_recenter_killer": _non_square_recenter_killer,
}

WITNESS_RIVALS = {
    "two_frames": ["flat_red", "reverse_depth"],
    "three_frames": ["only_two_depth_levels", "flat_red"],
    "four_frames": ["only_two_depth_levels", "flat_red"],
    "offset_recenter_killer": ["recenter_frames"],
    "edge_canvas_distance_killer": ["canvas_distance"],
    "non_square_recenter_killer": ["recenter_frames"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require each four-demo lesson to falsify the declared shortcut family."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]
    if self_check(query["input"]):
        reasons.append("query input is outside the nested-frame teaching grammar")

    analyses: list[dict[str, Any]] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        analysis = _analyze(demo["input"])
        if analysis["errors"]:
            reasons.append(f"demo {index} input is outside the nested-frame grammar")
            continue
        if demo["output"] != rule_mirror(demo["input"]):
            reasons.append(f"demo {index} output is not the exact depth recolor")
        analyses.append(analysis)

    if analyses and len(analyses) == len(demos):
        for name, competitor in LESSON_COMPETITORS.items():
            if all(competitor(demo["input"]) == demo["output"] for demo in demos):
                reasons.append(f"named competitor survives all demonstrations: {name}")
    return reasons


def _anchor_grid(rng) -> list[list[int]]:
    """Exact canonical canvas sizes with seed-varying, non-replayed geometry."""
    h, w = ((9, 9), (10, 12))[rng.randrange(2)]
    count = 2
    minimum = 3 + 4 * (count - 1)
    outer_h = rng.randint(minimum, h)
    outer_w = rng.randint(minimum, w)
    max_r0 = h - outer_h
    max_c0 = w - outer_w
    r0 = rng.randint(0, max_r0)
    c0 = rng.randint(0, max_c0)

    # Pin one side to the canvas so this profile kills the canonical distance
    # shortcut while retaining exact canonical (height,width,palette) support.
    side = rng.randrange(4)
    if side == 0:
        r0 = 0
    elif side == 1:
        c0 = 0
    elif side == 2:
        r0 = max_r0
    else:
        c0 = max_c0

    boxes = []
    for depth in range(count):
        inset = 2 * depth
        boxes.append(
            (
                r0 + inset,
                c0 + inset,
                r0 + outer_h - 1 - inset,
                c0 + outer_w - 1 - inset,
            )
        )
    grid = full_grid(h, w, 0)
    for box in boxes:
        _paint_frame(grid, box)
    return grid


def _build_boxes(count: int, style: str, rng, difficulty: Any) -> list[BBox]:
    choices = {
        "easy": ((1, 1), (2, 2), (3, 3)),
        "medium": ((1, 1), (2, 2), (3, 3), (3, 4), (4, 3)),
        "hard": (
            (1, 1),
            (2, 2),
            (3, 3),
            (3, 4),
            (4, 3),
            (4, 5),
            (5, 4),
        ),
    }.get(difficulty, ((1, 1), (2, 2), (3, 3), (3, 4), (4, 3)))
    inner_h, inner_w = rng.choice(choices)

    boxes_inner_to_outer: list[BBox] = [(0, 0, inner_h - 1, inner_w - 1)]
    offset_witness_used = False
    for layer in range(count - 1):
        top = bottom = left = right = 2
        if style == "offset":
            side = (layer + rng.randrange(4)) % 4
            if side == 0:
                top = 3
            elif side == 1:
                left = 3
            elif side == 2:
                bottom = 3
            else:
                right = 3
            offset_witness_used = True
        r0, c0, r1, c1 = boxes_inner_to_outer[-1]
        boxes_inner_to_outer.append(
            (r0 - top, c0 - left, r1 + bottom, c1 + right)
        )

    if style == "offset" and not offset_witness_used:
        raise AssertionError("offset layout failed to create an asymmetric inset")

    outer = boxes_inner_to_outer[-1]
    shift_r, shift_c = -outer[0], -outer[1]
    return [
        (r0 + shift_r, c0 + shift_c, r1 + shift_r, c1 + shift_c)
        for r0, c0, r1, c1 in reversed(boxes_inner_to_outer)
    ]


def _place_boxes(
    boxes: list[BBox],
    margin_mode: str,
    rng,
    difficulty: Any,
    *,
    force_offcenter: bool = False,
) -> tuple[list[list[int]], list[BBox]]:
    outer = boxes[0]
    outer_h = outer[2] - outer[0] + 1
    outer_w = outer[3] - outer[1] + 1
    extra_cap = {"easy": 2, "medium": 3, "hard": 4}.get(difficulty, 3)

    if margin_mode == "inset":
        margins = [rng.randint(1, extra_cap + 1) for _ in range(4)]
        floors = [1, 1, 1, 1]
    else:
        margins = [rng.randint(0, extra_cap) for _ in range(4)]
        margins[rng.randrange(4)] = 0
        floors = [0, 0, 0, 0]

    for first, second, capacity in (
        (0, 2, 30 - outer_h),
        (1, 3, 30 - outer_w),
    ):
        minimum = floors[first] + floors[second]
        if capacity < minimum:
            raise ValueError(
                f"frame geometry leaves insufficient room for {margin_mode} margins"
            )
        while margins[first] + margins[second] > capacity:
            reducible = [
                index
                for index in (first, second)
                if margins[index] > floors[index]
            ]
            if not reducible:
                raise AssertionError("margin trimming stalled above ARC limit")
            index = reducible[rng.randrange(len(reducible))]
            margins[index] -= 1

    if force_offcenter:
        row_centered = margins[0] == (margins[0] + margins[2]) // 2
        col_centered = margins[1] == (margins[1] + margins[3]) // 2
        if row_centered and col_centered:
            adjusted = False
            for first, second, capacity in (
                (0, 2, 30 - outer_h),
                (1, 3, 30 - outer_w),
            ):
                total = max(
                    margins[first] + margins[second],
                    floors[first] + floors[second] + 1,
                )
                if total > capacity:
                    continue
                second_value = max(floors[second], (total - 1) // 2)
                first_value = total - second_value
                if first_value <= second_value or first_value < floors[first]:
                    continue
                margins[first] = first_value
                margins[second] = second_value
                adjusted = True
                break
            if not adjusted:
                raise AssertionError("could not place offset frames off canvas center")

    top, left, bottom, right = margins
    h = outer_h + top + bottom
    w = outer_w + left + right
    shifted = [
        (r0 + top, c0 + left, r1 + top, c1 + left)
        for r0, c0, r1, c1 in boxes
    ]
    grid = full_grid(h, w, 0)
    for box in shifted:
        _paint_frame(grid, box)
    return grid, shifted


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input; the canonical Racket rule owns output."""
    unknown = set(overrides) - _ALLOWED_OVERRIDES
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = int(sample_index) % len(SCHEDULE_PROFILES)
    default_count, default_style, default_margin = SCHEDULE_PROFILES[profile]
    frame_count = _scheduled_int(ctx, "frame_count", 2, 4, default_count)
    layout_style = _scheduled_choice(
        ctx, "layout_style", ("concentric", "offset"), default_style
    )
    outer_margin = _scheduled_choice(
        ctx, "outer_margin", ("edge", "inset"), default_margin
    )

    rng = ctx.draw_rng(f"geometry:{difficulty or 'medium'}")
    # Profile 0 provides exact canonical canvas dimensions without replaying a
    # canonical grid. Explicit overrides always use the general constructive path.
    if not overrides and profile == 0:
        grid = _anchor_grid(rng)
    else:
        boxes = _build_boxes(frame_count, layout_style, rng, difficulty)
        grid, _ = _place_boxes(
            boxes,
            outer_margin,
            rng,
            difficulty,
            force_offcenter=layout_style == "offset",
        )

    errors = self_check(grid, difficulty=difficulty, meta={"overrides": overrides})
    if errors:
        raise AssertionError("internal generator invariant failed: " + "; ".join(errors))
    return grid
