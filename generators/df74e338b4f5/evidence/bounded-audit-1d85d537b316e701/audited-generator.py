"""Semantic generator for ARC task ``df74e338b4f5``.

The input contains two or three disjoint rectangular color-9 frames, strictly
nested with a blank moat.  All remaining nonzero cells share one marker color.
For every marker, the output color is the number of frame interiors that
strictly contain that cell; frame and background cells are unchanged.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "df74e338b4f5"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "3ba84d8589ae"
MIN_STRICT_FRAC = 1.0
EXAMPLES_NEEDED = 4

SUMMARY = (
    "Nested hollow color-9 rectangular frames contain same-colored marker "
    "cells. Recolor each marker by its strict frame-containment depth, while "
    "leaving every frame and background cell unchanged."
)

INVARIANTS = [
    "the input palette is background 0, frame color 9, and one marker color 1-8",
    "there are two or three complete rectangular color-9 frame components",
    "successive frames are strictly nested with at least one blank cell of moat",
    "marker cells occupy non-frame cells and exhibit at least two containment depths",
    "the output changes only marker cells, replacing each by its containing-frame count",
]

COUNTER_HYPOTHESES = [
    "infer marker depth from distance to the canvas edge",
    "map every marker to color 1",
    "record only whether a marker is inside any frame",
    "assume every outer frame coincides with the canvas boundary",
]

AXES = {
    "grid_h": {"type": "int", "default": "five-profile schedule", "valid": "11..18"},
    "grid_w": {"type": "int", "default": "five-profile schedule", "valid": "11..18"},
    "n_frames": {"type": "int", "default": "difficulty/profile schedule", "valid": "2..3"},
}

# Three frames need an 11x11 minimum frame footprint plus a two-cell exterior
# strip on at least one axis to carry a decisive depth-zero shortcut witness.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"grid_h": (11, 12), "grid_w": (11, 12), "n_frames": 3},
]
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
_ALLOWED_OVERRIDES = frozenset(AXES)

# These are the five canonical (height, width, palette-size) profiles.  The
# ordinary no-difficulty stream preserves them exactly.  Hard examples use
# five compatible shapes because every hard example carries three frames and a
# depth-zero anti-shortcut witness.
_CANONICAL_SHAPES = ((11, 13), (12, 12), (13, 15), (11, 11), (12, 14))
_HARD_SHAPES = ((11, 13), (13, 11), (12, 13), (13, 12), (13, 15))
_PROFILE_FRAMES = (3, 2, 3, 2, 3)
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
BBox = tuple[int, int, int, int]


def _scheduled_int(ctx, name: str, lo: int, hi: int, default: int) -> int:
    """Use a fixed scheduled default while retaining an exact strict override."""
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_int_strict(name, default, default)


def _outline_cells(box: BBox) -> set[tuple[int, int]]:
    r0, c0, r1, c1 = box
    return {
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if r in (r0, r1) or c in (c0, c1)
    }


def _bbox(cells: list[tuple[int, int]]) -> BBox:
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _area(box: BBox) -> int:
    r0, c0, r1, c1 = box
    return (r1 - r0 + 1) * (c1 - c0 + 1)


def _rectangular_errors(grid: Any) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list of rows"]
    if not isinstance(grid[0], list) or not grid[0]:
        return ["rows must be non-empty lists"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if not 11 <= len(grid) <= 18 or not 11 <= width <= 18:
        return [f"expected an 11..18 by 11..18 grid, found {len(grid)}x{width}"]
    errors: list[str] = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                errors.append(f"invalid ARC color at ({r},{c}): {value!r}")
    return errors


def _components_of_nine(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []
    for start_r in range(h):
        for start_c in range(w):
            if grid[start_r][start_c] != 9 or (start_r, start_c) in seen:
                continue
            queue = [(start_r, start_c)]
            seen.add((start_r, start_c))
            cells: list[tuple[int, int]] = []
            for r, c in queue:
                cells.append((r, c))
                for dr, dc in _CARDINAL:
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == 9
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            components.append(cells)
    return components


def _depth_at(r: int, c: int, boxes: list[BBox]) -> int:
    return sum(r0 < r < r1 and c0 < c < c1 for r0, c0, r1, c1 in boxes)


def _analyze(grid: Any) -> dict[str, Any]:
    """Return frame/marker semantics plus diagnostics; never mutate ``grid``."""
    errors = _rectangular_errors(grid)
    result: dict[str, Any] = {"errors": errors}
    if errors:
        return result

    h, w = len(grid), len(grid[0])
    palette = {value for row in grid for value in row}
    marker_colors = sorted(palette - {0, 9})
    if 0 not in palette or 9 not in palette or len(marker_colors) != 1:
        errors.append(
            "input palette must contain 0, 9, and exactly one marker color 1-8; "
            f"found {sorted(palette)}"
        )
    marker_color = marker_colors[0] if len(marker_colors) == 1 else None

    components = _components_of_nine(grid)
    if not 2 <= len(components) <= 3:
        errors.append(f"expected 2-3 color-9 frame components, found {len(components)}")

    boxes: list[BBox] = []
    for index, cells in enumerate(components):
        box = _bbox(cells)
        r0, c0, r1, c1 = box
        frame_h, frame_w = r1 - r0 + 1, c1 - c0 + 1
        if frame_h < 3 or frame_w < 3:
            errors.append(
                f"component {index} is too small for a rectangular frame: "
                f"{frame_h}x{frame_w}"
            )
        expected = _outline_cells(box)
        actual = set(cells)
        if actual != expected:
            errors.append(
                f"component {index} is not a complete hollow rectangle "
                f"(missing={len(expected - actual)}, extra={len(actual - expected)})"
            )
        boxes.append(box)

    boxes.sort(key=lambda box: (-_area(box), box))
    if len({_area(box) for box in boxes}) != len(boxes):
        errors.append("frame bounding-box areas must be distinct")

    insets: list[tuple[int, int, int, int]] = []
    for index, (outer, inner) in enumerate(zip(boxes, boxes[1:])):
        or0, oc0, or1, oc1 = outer
        ir0, ic0, ir1, ic1 = inner
        inset = (ir0 - or0, ic0 - oc0, or1 - ir1, oc1 - ic1)
        insets.append(inset)
        if min(inset) < 2:
            errors.append(
                f"frames {index} and {index + 1} need a one-cell blank moat; "
                f"insets={inset}"
            )

    markers: list[dict[str, int]] = []
    if marker_color is not None:
        for r, row in enumerate(grid):
            for c, value in enumerate(row):
                if value == marker_color:
                    markers.append(
                        {"r": r, "c": c, "color": value, "depth": _depth_at(r, c, boxes)}
                    )
    if not 2 <= len(markers) <= 8:
        errors.append(f"expected 2-8 marker cells, found {len(markers)}")
    depths = sorted({marker["depth"] for marker in markers})
    if len(depths) < 2:
        errors.append(f"markers must expose at least two containment depths, found {depths}")

    result.update(
        {
            "height": h,
            "width": w,
            "palette": palette,
            "marker_color": marker_color,
            "markers": markers,
            "depths": depths,
            "components": components,
            "boxes": boxes,
            "insets": insets,
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
    """Reject malformed or semantically underdetermined nesting-depth scenes."""
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and requested is not None and observed.get(name) != requested:
            errors.append(
                f"override {name}={requested!r} realized as {observed.get(name)!r}"
            )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """All ordinary outputs use the same frame/marker grammar as canonical data."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    """Recover each exact caller-facing axis from a valid returned grid."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {}
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "n_frames": analysis["frame_count"],
    }


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror; canonical Racket remains output authority."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid input: " + "; ".join(analysis["errors"]))
    output = deepcopy(grid)
    for marker in analysis["markers"]:
        output[marker["r"]][marker["c"]] = marker["depth"]
    return output


def _rival_canvas_edge_distance_depth(grid) -> list[list[int]]:
    """Retained bad rule: estimate depth solely from distance to canvas edge."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid input")
    h, w = analysis["height"], analysis["width"]
    output = deepcopy(grid)
    for marker in analysis["markers"]:
        r, c = marker["r"], marker["c"]
        output[r][c] = (min(r, c, h - 1 - r, w - 1 - c) + 1) // 2
    return output


def _rival_constant_one(grid) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid input")
    output = deepcopy(grid)
    for marker in analysis["markers"]:
        output[marker["r"]][marker["c"]] = 1
    return output


def _rival_inside_any_frame(grid) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid input")
    output = deepcopy(grid)
    for marker in analysis["markers"]:
        output[marker["r"]][marker["c"]] = int(marker["depth"] > 0)
    return output


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "canvas_edge_distance_depth": _rival_canvas_edge_distance_depth,
    "constant_one": _rival_constant_one,
    "inside_any_frame": _rival_inside_any_frame,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS: dict[str, Callable[[Any], list[list[int]]]] = {}


def _valid_analysis(grid):
    analysis = _analyze(grid)
    return analysis if not analysis["errors"] else None


def _has_depth(depth: int):
    return lambda grid: bool(
        (analysis := _valid_analysis(grid))
        and depth in {marker["depth"] for marker in analysis["markers"]}
    )


def _has_all_depths(grid) -> bool:
    analysis = _valid_analysis(grid)
    return bool(
        analysis
        and {marker["depth"] for marker in analysis["markers"]}
        == set(range(analysis["frame_count"] + 1))
    )


def _canvas_distance_killer(grid) -> bool:
    return bool(
        _valid_analysis(grid)
        and rule_mirror(grid) != _rival_canvas_edge_distance_depth(grid)
    )


SEMANTIC_WITNESSES = {
    "depth_zero_marker": _has_depth(0),
    "depth_two_marker": _has_depth(2),
    "all_depths": _has_all_depths,
    "canvas_distance_killer": _canvas_distance_killer,
}
WITNESS_RIVALS = {
    "depth_zero_marker": ["constant_one"],
    "depth_two_marker": ["inside_any_frame", "constant_one"],
    "all_depths": ["constant_one", "inside_any_frame"],
    "canvas_distance_killer": ["canvas_edge_distance_depth"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lesson windows in which a named shortcut still fits every demo."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    if self_check(query["input"]):
        reasons.append("query input is outside the nesting-depth grammar")
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        if self_check(demo["input"]):
            reasons.append(f"demo {index} input is outside the nesting-depth grammar")
            continue
        if rule_mirror(demo["input"]) != demo["output"]:
            reasons.append(f"demo {index} output does not follow frame containment depth")

    if not reasons:
        for name, competitor in LESSON_COMPETITORS.items():
            if all(competitor(demo["input"]) == demo["output"] for demo in demos):
                reasons.append(f"named competitor survives all demonstrations: {name}")
    return reasons


def _minimum_outer_size(n_frames: int) -> int:
    return 4 * n_frames - 1


def _compatible_shape(h: int, w: int, n_frames: int) -> bool:
    minimum = _minimum_outer_size(n_frames)
    return h >= minimum and w >= minimum and (h >= minimum + 2 or w >= minimum + 2)


def _choose_outer_box(h: int, w: int, n_frames: int, rng) -> BBox:
    """Choose an outer box while reserving a thick exterior witness strip."""
    minimum = _minimum_outer_size(n_frames)
    reserve_axes = []
    if h >= minimum + 2:
        reserve_axes.append("row")
    if w >= minimum + 2:
        reserve_axes.append("col")
    if not reserve_axes:
        raise ValueError(
            f"grid_h={h}, grid_w={w}, n_frames={n_frames} leave no exterior witness strip"
        )
    reserve_axis = rng.choice(reserve_axes)

    max_h = h - 2 if reserve_axis == "row" else h
    max_w = w - 2 if reserve_axis == "col" else w
    outer_h = rng.randint(minimum, max_h)
    outer_w = rng.randint(minimum, max_w)

    def margins(total: int, reserve: bool) -> tuple[int, int]:
        if reserve:
            before_side = bool(rng.randrange(2))
            thick = rng.randint(2, total)
            if before_side:
                return thick, total - thick
            return total - thick, thick
        before = rng.randint(0, total)
        return before, total - before

    top, bottom = margins(h - outer_h, reserve_axis == "row")
    left, right = margins(w - outer_w, reserve_axis == "col")
    return top, left, h - 1 - bottom, w - 1 - right


def _nested_boxes(outer: BBox, n_frames: int, rng) -> list[BBox]:
    boxes = [outer]
    current = outer
    for index in range(1, n_frames):
        remaining_frames = n_frames - index
        next_minimum = _minimum_outer_size(remaining_frames)
        r0, c0, r1, c1 = current
        current_h, current_w = r1 - r0 + 1, c1 - c0 + 1

        def shrink(size: int) -> tuple[int, int]:
            spare = size - next_minimum - 4
            use = rng.randint(0, min(3, max(0, spare)))
            first_extra = rng.randint(0, use)
            return 2 + first_extra, 2 + use - first_extra

        top, bottom = shrink(current_h)
        left, right = shrink(current_w)
        current = (r0 + top, c0 + left, r1 - bottom, c1 - right)
        boxes.append(current)
    return boxes


def _generated_contract_errors(grid) -> list[str]:
    """Stronger teaching contract for generated data (not canonical acceptance)."""
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    expected_depths = set(range(analysis["frame_count"] + 1))
    actual_depths = {marker["depth"] for marker in analysis["markers"]}
    if actual_depths != expected_depths:
        errors.append(
            f"generated markers must show every depth {sorted(expected_depths)}, "
            f"found {sorted(actual_depths)}"
        )
    if rule_mirror(grid) == _rival_canvas_edge_distance_depth(grid):
        errors.append("generated scene does not refute canvas-edge distance shortcut")
    return errors


def _place_markers(
    grid: list[list[int]], boxes: list[BBox], marker_color: int, rng, difficulty
) -> None:
    h, w = len(grid), len(grid[0])
    by_depth: dict[int, list[tuple[int, int]]] = {
        depth: [] for depth in range(len(boxes) + 1)
    }
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0:
                continue
            depth = _depth_at(r, c, boxes)
            by_depth[depth].append((r, c))

    # The depth-zero witness must be at least one cell away from the canvas
    # edge, so the retained edge-distance rival predicts a nonzero depth.
    decisive_zero = [
        (r, c)
        for r, c in by_depth[0]
        if min(r, c, h - 1 - r, w - 1 - c) >= 1
    ]
    if not decisive_zero:
        raise AssertionError("constructive layout lost its depth-zero shortcut witness")

    selected = [rng.choice(decisive_zero)]
    for depth in range(1, len(boxes) + 1):
        if not by_depth[depth]:
            raise AssertionError(f"constructive layout has no marker candidate at depth {depth}")
        selected.append(rng.choice(by_depth[depth]))

    extras = {"easy": 0, "medium": 1, "hard": 2}.get(difficulty)
    if extras is None:
        extras = rng.randint(0, 2)
    remaining = [
        (r, c)
        for depth_cells in by_depth.values()
        for r, c in depth_cells
        if (r, c) not in selected
    ]
    selected.extend(rng.sample(remaining, min(extras, len(remaining))))
    for r, c in selected:
        grid[r][c] = marker_color


def _default_frame_count(sample_index: int, difficulty) -> int:
    if difficulty == "easy":
        return 2
    if difficulty == "hard":
        return 3
    return _PROFILE_FRAMES[sample_index % len(_PROFILE_FRAMES)]


def _default_shape(sample_index: int, difficulty, n_frames: int) -> tuple[int, int]:
    profile = sample_index % len(_CANONICAL_SHAPES)
    if difficulty == "hard" or n_frames == 3 and not _compatible_shape(
        *_CANONICAL_SHAPES[profile], n_frames
    ):
        return _HARD_SHAPES[profile]
    return _CANONICAL_SHAPES[profile]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input grid; the canonical rule owns output."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - _ALLOWED_OVERRIDES
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    n_frames = _scheduled_int(
        ctx,
        "n_frames",
        2,
        3,
        _default_frame_count(sample_index, difficulty),
    )
    default_h, default_w = _default_shape(sample_index, difficulty, n_frames)

    # A single explicit small dimension remains feasible: lift the unoverridden
    # partner dimension to 13 so three frames still have an exterior witness.
    if n_frames == 3:
        explicit_h = overrides.get("grid_h")
        explicit_w = overrides.get("grid_w")
        if explicit_h is not None and type(explicit_h) is int and explicit_h <= 12 and explicit_w is None:
            default_w = max(default_w, 13)
        if explicit_w is not None and type(explicit_w) is int and explicit_w <= 12 and explicit_h is None:
            default_h = max(default_h, 13)

    h = _scheduled_int(ctx, "grid_h", 11, 18, default_h)
    w = _scheduled_int(ctx, "grid_w", 11, 18, default_w)
    if not _compatible_shape(h, w, n_frames):
        raise ValueError(
            f"incompatible overrides: grid_h={h}, grid_w={w}, n_frames={n_frames}"
        )

    rng = ctx.draw_rng(f"layout:{difficulty or 'default'}")
    boxes = _nested_boxes(_choose_outer_box(h, w, n_frames, rng), n_frames, rng)
    grid = full_grid(h, w, 0)
    for box in boxes:
        draw_frame(grid, *box, 9)
    marker_color = rng.choice(tuple(range(1, 9)))
    _place_markers(grid, boxes, marker_color, rng, difficulty)

    errors = self_check(grid, difficulty=difficulty, meta={"overrides": overrides})
    errors.extend(_generated_contract_errors(grid))
    if errors:
        raise AssertionError("internal generator invariant failed: " + "; ".join(errors))
    return grid
