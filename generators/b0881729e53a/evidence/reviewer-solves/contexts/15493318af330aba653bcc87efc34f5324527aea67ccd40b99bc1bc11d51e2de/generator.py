"""Generator for ``medium_i12`` — move the selected object into a frame.

The grid contains one hollow monochrome rectangular frame and one or two
monochrome objects outside it.  The selected object is the last non-frame
4-connected component in row-major discovery order, exactly matching the
canonical Racket authority.  The output keeps only the frame and pastes the
selected object's cropped shape, unchanged, centered inside the frame's
interior.  Every external object is erased from its source position.

One canonical training input contains two external objects and proves that the
authority does not simply use the first component.  The old generated lessons,
however, always made the later component smaller, rightmost and usually closest
to the frame.  Version 4 schedules four deconfounded two-object profiles plus a
single-object profile.  Under every one-pair query holdout, the demonstrations
still distinguish row-major-last selection from size, side, distance, color and
bottom-edge shortcuts.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "b0881729e53a"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "b7117efbdd28"

SUMMARY = (
    "Find the hollow rectangular frame. Among all other same-color "
    "4-connected components, select the last component in row-major discovery "
    "order. Erase every non-frame component, crop the selected component to its "
    "bounding box, and paste that shape unchanged at the floor-centered position "
    "inside the frame's interior."
)

EXAMPLES_NEEDED = 4
LESSON_SCHEDULE_PERIOD = 5
MIN_STRICT_FRAC = 1.0
# The override matrix is fully Cartesian for this generator.  Declare that
# explicitly so strict tooling does not fall back to the ambiguous legacy
# policy for an absent incompatibility contract.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()

INVARIANTS = [
    "background is 0 and all foreground cells use ARC colors 1..9",
    "exactly one foreground component is a complete hollow rectangular frame",
    "one or two non-frame 4-connected monochrome components lie outside the frame",
    "the selected component is the row-major-last non-frame component",
    "the selected crop fits inside the frame interior and is not already there",
    "scheduled two-object scenes deconfound scan order from size, side, distance, color, and bottom edge",
]

_PLACEMENTS = ("touching", "separated")
AXES = {
    "grid_h": {
        "type": "int",
        "default": "80% canonical profile, otherwise difficulty-aware",
        "valid": "8..14",
    },
    "grid_w": {
        "type": "int",
        "default": "80% canonical profile, otherwise difficulty-aware",
        "valid": "9..15",
    },
    "placement": {
        "type": "str",
        "default": "five-slot schedule; exact override supported",
        "valid": "touching|separated",
    },
}

_FRAME_COLORS = (8, 4, 6, 2, 9, 5, 3, 1)
_SINGLE_SHAPES = (
    ((0, 0), (1, 0), (2, 0)),
    ((0, 0), (1, 0), (1, 1), (2, 0)),
    ((0, 0), (0, 1), (1, 1), (1, 2)),
    ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2)),
    ((0, 0), (1, 0), (2, 0), (2, 1)),
)
_CANONICAL_PROFILES = ((9, 9), (8, 10), (10, 10), (9, 11))
_SCAN_ORDER_PROFILES = (
    # layout, selected-to-frame placement, shape-role profile
    ("side_left", "separated", "bent_over_line"),
    ("side_left", "touching", "line_over_bent"),
    ("top_right", "touching", "bent_orientation_a"),
    ("top_right", "separated", "bent_orientation_b"),
)
_VERTICAL_LINE = ((0, 0), (1, 0), (2, 0))
_L_MISSING_BR = ((0, 0), (0, 1), (1, 0))
_L_MISSING_BL = ((0, 0), (0, 1), (1, 1))
_L_MISSING_TR = ((0, 0), (1, 0), (1, 1))
_L_MISSING_TL = ((0, 1), (1, 0), (1, 1))


@dataclass(frozen=True)
class _Object:
    color: int
    cells: tuple[tuple[int, int], ...]

    @property
    def bbox(self) -> tuple[int, int, int, int]:
        rows = [r for r, _ in self.cells]
        cols = [c for _, c in self.cells]
        return min(rows), min(cols), max(rows), max(cols)

    @property
    def size(self) -> int:
        return len(self.cells)


def _shape_dims(shape: tuple[tuple[int, int], ...]) -> tuple[int, int]:
    return (
        max(r for r, _ in shape) + 1,
        max(c for _, c in shape) + 1,
    )


def _components(grid: list[list[int]]) -> list[_Object]:
    """Same-color 4-connected objects in Racket ``objects`` scan order."""
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    found: list[_Object] = []
    for start_r in range(h):
        for start_c in range(w):
            color = grid[start_r][start_c]
            if color == 0 or (start_r, start_c) in seen:
                continue
            queue = [(start_r, start_c)]
            seen.add((start_r, start_c))
            cells: list[tuple[int, int]] = []
            for r, c in queue:
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            found.append(_Object(color, tuple(cells)))
    return found


def _outline_cells(bbox: tuple[int, int, int, int]) -> set[tuple[int, int]]:
    r0, c0, r1, c1 = bbox
    return {
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if r in (r0, r1) or c in (c0, c1)
    }


def _is_frame(obj: _Object) -> bool:
    r0, c0, r1, c1 = obj.bbox
    return r1 - r0 + 1 >= 3 and c1 - c0 + 1 >= 3 and set(obj.cells) == _outline_cells(obj.bbox)


def _scene(grid: list[list[int]]) -> tuple[_Object, list[_Object], _Object]:
    components = _components(grid)
    frames = [obj for obj in components if _is_frame(obj)]
    if len(frames) != 1:
        raise ValueError(f"expected exactly one frame, found {len(frames)}")
    frame = frames[0]
    nonframes = [obj for obj in components if obj is not frame]
    if not nonframes:
        raise ValueError("expected at least one non-frame object")
    return frame, nonframes, nonframes[-1]


def _normalized_shape(obj: _Object) -> tuple[tuple[int, int], ...]:
    r0, c0, _, _ = obj.bbox
    return tuple((r - r0, c - c0) for r, c in obj.cells)


def _center_top_left(frame: _Object, shape: tuple[tuple[int, int], ...]) -> tuple[int, int]:
    fr0, fc0, fr1, fc1 = frame.bbox
    sh, sw = _shape_dims(shape)
    interior_h = fr1 - fr0 - 1
    interior_w = fc1 - fc0 - 1
    return (
        fr0 + 1 + (interior_h - sh) // 2,
        fc0 + 1 + (interior_w - sw) // 2,
    )


def _render_rule(
    grid: list[list[int]],
    *,
    select: Callable[[list[_Object]], _Object] | None = None,
    keep_sources: bool = False,
    paste_top_left: bool = False,
) -> list[list[int]]:
    frame, nonframes, canonical_selected = _scene(grid)
    selected = select(nonframes) if select is not None else canonical_selected
    shape = _normalized_shape(selected)
    if keep_sources:
        output = [row[:] for row in grid]
    else:
        output = full_grid(len(grid), len(grid[0]), 0)
        for r, c in frame.cells:
            output[r][c] = frame.color
    if paste_top_left:
        top, left = frame.bbox[0] + 1, frame.bbox[1] + 1
    else:
        top, left = _center_top_left(frame, shape)
    for dr, dc in shape:
        output[top + dr][left + dc] = selected.color
    return output


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror for tests; Racket remains authoritative."""
    return _render_rule(grid)


def _touching(a: _Object, b: _Object) -> bool:
    b_cells = set(b.cells)
    return any(
        (r + dr, c + dc) in b_cells
        for r, c in a.cells
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
    )


def _bbox_gap(a: _Object, b: _Object) -> int:
    """Manhattan gap between disjoint bounding boxes; touching gives zero."""
    ar0, ac0, ar1, ac1 = a.bbox
    br0, bc0, br1, bc1 = b.bbox
    vertical = max(ar0 - br1 - 1, br0 - ar1 - 1, 0)
    horizontal = max(ac0 - bc1 - 1, bc0 - ac1 - 1, 0)
    return vertical + horizontal


def observe_overrides(grid) -> dict[str, int | str]:
    frame, _, selected = _scene(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "placement": "touching" if _touching(frame, selected) else "separated",
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural validator for generated and canonical task inputs."""
    del difficulty, meta
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a non-empty list of rows"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular and non-empty"]
    errors: list[str] = []
    height = len(grid)
    if not (8 <= height <= 14 and 9 <= width <= 15):
        errors.append(f"dimensions {height}x{width} outside supported 8..14 x 9..15")
    if any(
        not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid contains a non-ARC color")
        return errors

    components = _components(grid)
    frames = [obj for obj in components if _is_frame(obj)]
    if len(frames) != 1:
        errors.append(f"expected exactly one hollow rectangular frame, found {len(frames)}")
        return errors
    frame = frames[0]
    fr0, fc0, fr1, fc1 = frame.bbox
    fh, fw = fr1 - fr0 + 1, fc1 - fc0 + 1
    if fh < 5 or fw < 5:
        errors.append(f"frame {fh}x{fw} has an interior too small to teach centering")

    nonframes = [obj for obj in components if obj is not frame]
    if not (1 <= len(nonframes) <= 2):
        errors.append(f"expected one or two non-frame objects, found {len(nonframes)}")
        return errors
    for index, obj in enumerate(nonframes):
        r0, c0, r1, c1 = obj.bbox
        if not (r1 < fr0 or r0 > fr1 or c1 < fc0 or c0 > fc1):
            errors.append(f"non-frame object {index} is not wholly outside the frame bbox")
        if obj.size > 5:
            errors.append(f"non-frame object {index} has {obj.size} cells; maximum is 5")

    selected = nonframes[-1]
    shape = _normalized_shape(selected)
    sh, sw = _shape_dims(shape)
    if sh > fh - 2 or sw > fw - 2:
        errors.append(f"selected crop {sh}x{sw} does not fit the {fh - 2}x{fw - 2} interior")
    if len(nonframes) == 2:
        earlier = nonframes[0]
        if earlier.color == selected.color and _normalized_shape(earlier) == shape:
            errors.append(
                "two-object scene must make the selected component observably different "
                "from the earlier component"
            )
    try:
        output = rule_mirror(grid)
    except ValueError as exc:
        errors.append(str(exc))
    else:
        if output == grid:
            errors.append("canonical transformation is an identity")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """All generated draws intentionally stay inside the task's true grammar."""
    return self_check(grid)


def _witness_single_object(grid) -> bool:
    try:
        _, nonframes, _ = _scene(grid)
    except ValueError:
        return False
    return len(nonframes) == 1


def _two_object_parts(grid):
    try:
        frame, nonframes, selected = _scene(grid)
    except ValueError:
        return None
    if len(nonframes) != 2:
        return None
    return frame, nonframes[0], selected


def _witness_scan_order_tie_decoy(grid) -> bool:
    parts = _two_object_parts(grid)
    if parts is None:
        return False
    _, earlier, selected = parts
    return (
        earlier.size == selected.size
        and earlier.color == selected.color
        and _normalized_shape(earlier) != _normalized_shape(selected)
    )


def _witness_same_top_edge_decoy(grid) -> bool:
    parts = _two_object_parts(grid)
    return parts is not None and parts[1].bbox[0] == parts[2].bbox[0]


def _witness_same_bottom_edge_decoy(grid) -> bool:
    parts = _two_object_parts(grid)
    return parts is not None and parts[1].bbox[2] == parts[2].bbox[2]


def _witness_equal_frame_distance_decoy(grid) -> bool:
    parts = _two_object_parts(grid)
    if parts is None:
        return False
    frame, earlier, selected = parts
    return _bbox_gap(frame, earlier) == _bbox_gap(frame, selected)


def _witness_selected_left_of_decoy(grid) -> bool:
    parts = _two_object_parts(grid)
    return parts is not None and parts[2].bbox[1] < parts[1].bbox[1]


def _witness_selected_right_of_decoy(grid) -> bool:
    parts = _two_object_parts(grid)
    return parts is not None and parts[2].bbox[1] > parts[1].bbox[1]


def _witness_selected_closer_than_decoy(grid) -> bool:
    parts = _two_object_parts(grid)
    if parts is None:
        return False
    frame, earlier, selected = parts
    return _bbox_gap(frame, selected) < _bbox_gap(frame, earlier)


def _witness_selected_farther_than_decoy(grid) -> bool:
    parts = _two_object_parts(grid)
    if parts is None:
        return False
    frame, earlier, selected = parts
    return _bbox_gap(frame, selected) > _bbox_gap(frame, earlier)


def _bbox_height(obj: _Object) -> int:
    return obj.bbox[2] - obj.bbox[0] + 1


def _bbox_width(obj: _Object) -> int:
    return obj.bbox[3] - obj.bbox[1] + 1


def _bbox_area(obj: _Object) -> int:
    return _bbox_height(obj) * _bbox_width(obj)


def _is_bent(obj: _Object) -> bool:
    return _bbox_area(obj) > obj.size


def _witness_selected_wider_than_decoy(grid) -> bool:
    parts = _two_object_parts(grid)
    return parts is not None and _bbox_width(parts[2]) > _bbox_width(parts[1])


def _witness_selected_narrower_than_decoy(grid) -> bool:
    parts = _two_object_parts(grid)
    return parts is not None and _bbox_width(parts[2]) < _bbox_width(parts[1])


def _witness_selected_taller_than_decoy(grid) -> bool:
    parts = _two_object_parts(grid)
    return parts is not None and _bbox_height(parts[2]) > _bbox_height(parts[1])


def _witness_selected_shorter_than_decoy(grid) -> bool:
    parts = _two_object_parts(grid)
    return parts is not None and _bbox_height(parts[2]) < _bbox_height(parts[1])


def _witness_selected_bent_with_straight_decoy(grid) -> bool:
    parts = _two_object_parts(grid)
    return parts is not None and _is_bent(parts[2]) and not _is_bent(parts[1])


def _witness_selected_straight_with_bent_decoy(grid) -> bool:
    parts = _two_object_parts(grid)
    return parts is not None and not _is_bent(parts[2]) and _is_bent(parts[1])


def _witness_touching(grid) -> bool:
    try:
        frame, _, selected = _scene(grid)
    except ValueError:
        return False
    return _touching(frame, selected)


def _witness_separated(grid) -> bool:
    try:
        frame, _, selected = _scene(grid)
    except ValueError:
        return False
    return not _touching(frame, selected)


def _witness_non_cyan_frame(grid) -> bool:
    try:
        frame, _, _ = _scene(grid)
    except ValueError:
        return False
    return frame.color != 8


def _witness_source_erasure(grid) -> bool:
    try:
        _, nonframes, _ = _scene(grid)
    except ValueError:
        return False
    return bool(nonframes)


def _witness_center_not_corner(grid) -> bool:
    try:
        frame, _, selected = _scene(grid)
    except ValueError:
        return False
    return _center_top_left(frame, _normalized_shape(selected)) != (
        frame.bbox[0] + 1,
        frame.bbox[1] + 1,
    )


SEMANTIC_WITNESSES = {
    "scan_order_size_color_tie": _witness_scan_order_tie_decoy,
    "same_top_edge_decoy": _witness_same_top_edge_decoy,
    "same_bottom_edge_decoy": _witness_same_bottom_edge_decoy,
    "equal_frame_distance_decoy": _witness_equal_frame_distance_decoy,
    "selected_left_of_decoy": _witness_selected_left_of_decoy,
    "selected_right_of_decoy": _witness_selected_right_of_decoy,
    "selected_closer_than_decoy": _witness_selected_closer_than_decoy,
    "selected_farther_than_decoy": _witness_selected_farther_than_decoy,
    "selected_wider_than_decoy": _witness_selected_wider_than_decoy,
    "selected_narrower_than_decoy": _witness_selected_narrower_than_decoy,
    "selected_taller_than_decoy": _witness_selected_taller_than_decoy,
    "selected_shorter_than_decoy": _witness_selected_shorter_than_decoy,
    "selected_bent_with_straight_decoy": _witness_selected_bent_with_straight_decoy,
    "selected_straight_with_bent_decoy": _witness_selected_straight_with_bent_decoy,
    "frame_color_not_cyan": _witness_non_cyan_frame,
    "external_sources_must_be_erased": _witness_source_erasure,
    "center_differs_from_interior_corner": _witness_center_not_corner,
}


def _rival_copy_not_move(grid):
    return _render_rule(grid, keep_sources=True)


def _rival_first_external(grid):
    return _render_rule(grid, select=lambda objs: objs[0])


def _rival_smallest_external(grid):
    return _render_rule(grid, select=lambda objs: min(objs, key=lambda obj: obj.size))


def _rival_largest_external(grid):
    return _render_rule(grid, select=lambda objs: max(objs, key=lambda obj: obj.size))


def _rival_leftmost_external(grid):
    return _render_rule(grid, select=lambda objs: min(objs, key=lambda obj: obj.bbox[1]))


def _rival_rightmost_external(grid):
    return _render_rule(grid, select=lambda objs: max(objs, key=lambda obj: obj.bbox[1]))


def _rival_closest_to_frame(grid):
    frame, nonframes, _ = _scene(grid)
    selected = min(nonframes, key=lambda obj: _bbox_gap(frame, obj))
    return _render_rule(grid, select=lambda objs: selected)


def _rival_farthest_from_frame(grid):
    frame, nonframes, _ = _scene(grid)
    selected = max(nonframes, key=lambda obj: _bbox_gap(frame, obj))
    return _render_rule(grid, select=lambda objs: selected)


def _rival_lowest_bottom(grid):
    return _render_rule(grid, select=lambda objs: max(objs, key=lambda obj: obj.bbox[2]))


def _rival_lowest_top(grid):
    return _render_rule(grid, select=lambda objs: max(objs, key=lambda obj: obj.bbox[0]))


def _rival_widest_bbox(grid):
    return _render_rule(grid, select=lambda objs: max(objs, key=_bbox_width))


def _rival_narrowest_bbox(grid):
    return _render_rule(grid, select=lambda objs: min(objs, key=_bbox_width))


def _rival_tallest_bbox(grid):
    return _render_rule(grid, select=lambda objs: max(objs, key=_bbox_height))


def _rival_shortest_bbox(grid):
    return _render_rule(grid, select=lambda objs: min(objs, key=_bbox_height))


def _rival_largest_bbox_area(grid):
    return _render_rule(grid, select=lambda objs: max(objs, key=_bbox_area))


def _rival_smallest_bbox_area(grid):
    return _render_rule(grid, select=lambda objs: min(objs, key=_bbox_area))


def _rival_bent_external(grid):
    return _render_rule(grid, select=lambda objs: max(objs, key=_is_bent))


def _rival_straight_external(grid):
    return _render_rule(grid, select=lambda objs: min(objs, key=_is_bent))


def _rival_lowest_color(grid):
    return _render_rule(grid, select=lambda objs: min(objs, key=lambda obj: obj.color))


def _rival_highest_color(grid):
    return _render_rule(grid, select=lambda objs: max(objs, key=lambda obj: obj.color))


def _rival_paste_at_interior_corner(grid):
    return _render_rule(grid, paste_top_left=True)


def _rival_cyan_frame_only(grid):
    try:
        frame, _, _ = _scene(grid)
    except ValueError:
        return [row[:] for row in grid]
    return rule_mirror(grid) if frame.color == 8 else [row[:] for row in grid]


SEMANTIC_RIVALS = {
    "copy_not_move": _rival_copy_not_move,
    "first_external_object": _rival_first_external,
    "smallest_external_object": _rival_smallest_external,
    "largest_external_object": _rival_largest_external,
    "leftmost_external_object": _rival_leftmost_external,
    "rightmost_external_object": _rival_rightmost_external,
    "closest_to_frame": _rival_closest_to_frame,
    "farthest_from_frame": _rival_farthest_from_frame,
    "lowest_top": _rival_lowest_top,
    "lowest_bottom": _rival_lowest_bottom,
    "widest_bbox": _rival_widest_bbox,
    "narrowest_bbox": _rival_narrowest_bbox,
    "tallest_bbox": _rival_tallest_bbox,
    "shortest_bbox": _rival_shortest_bbox,
    "largest_bbox_area": _rival_largest_bbox_area,
    "smallest_bbox_area": _rival_smallest_bbox_area,
    "bent_external": _rival_bent_external,
    "straight_external": _rival_straight_external,
    "lowest_color": _rival_lowest_color,
    "highest_color": _rival_highest_color,
    "paste_at_interior_corner": _rival_paste_at_interior_corner,
    "cyan_frame_only": _rival_cyan_frame_only,
}


WITNESS_RIVALS = {
    "external_sources_must_be_erased": ["copy_not_move"],
    "scan_order_size_color_tie": [
        "first_external_object",
        "smallest_external_object",
        "largest_external_object",
        "lowest_color",
        "highest_color",
    ],
    "same_top_edge_decoy": ["lowest_top"],
    "same_bottom_edge_decoy": ["lowest_bottom"],
    "equal_frame_distance_decoy": ["closest_to_frame", "farthest_from_frame"],
    "selected_left_of_decoy": ["rightmost_external_object"],
    "selected_right_of_decoy": ["leftmost_external_object"],
    "selected_closer_than_decoy": ["farthest_from_frame"],
    "selected_farther_than_decoy": ["closest_to_frame"],
    "selected_wider_than_decoy": ["narrowest_bbox"],
    "selected_narrower_than_decoy": ["widest_bbox"],
    "selected_taller_than_decoy": ["shortest_bbox"],
    "selected_shorter_than_decoy": ["tallest_bbox"],
    "selected_bent_with_straight_decoy": ["straight_external", "smallest_bbox_area"],
    "selected_straight_with_bent_decoy": ["bent_external", "largest_bbox_area"],
    "center_differs_from_interior_corner": ["paste_at_interior_corner"],
    "frame_color_not_cyan": ["cyan_frame_only"],
}


CANONICAL_SHORTCUTS = {
    "smallest_external_object": _rival_smallest_external,
    "rightmost_external_object": _rival_rightmost_external,
    "farthest_from_frame": _rival_farthest_from_frame,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when a named plausible rival survives every demo."""
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        try:
            expected = rule_mirror(demo["input"])
        except ValueError as exc:
            reasons.append(f"demo {index} is outside the rule domain: {exc}")
            continue
        if expected != demo["output"]:
            reasons.append(f"demo {index} output does not match the canonical move-and-center rule")
    try:
        query_answer = rule_mirror(query["input"])
    except ValueError as exc:
        reasons.append(f"query is outside the rule domain: {exc}")
        return reasons
    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(demo["input"]) == demo["output"] for demo in demos)
        if survives and competitor(query["input"]) != query_answer:
            reasons.append(
                f"competing rule '{name}' matches every demonstration but answers the query differently"
            )
    return reasons


def _axis_int(ctx, overrides, name, default_lo, default_hi, valid_lo, valid_hi):
    if overrides.get(name) is not None:
        return ctx.draw_int(name, valid_lo, valid_hi)
    return ctx.draw_int(name, default_lo, default_hi)


def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    profile = sample_index % LESSON_SCHEDULE_PERIOD
    if profile < 4:
        layout, placement, shape_role = _SCAN_ORDER_PROFILES[profile]
        return f"scan_order_{layout}_{placement}_{shape_role}"
    return "single_object"


def _choose_dimensions(ctx, overrides, difficulty, sample_index):
    profile = _CANONICAL_PROFILES[sample_index % 5] if sample_index % 5 < 4 else None
    if profile is not None:
        default_h = (profile[0], profile[0])
        default_w = (profile[1], profile[1])
    elif difficulty == "easy":
        default_h, default_w = (8, 10), (9, 11)
    elif difficulty == "hard":
        default_h, default_w = (10, 14), (11, 15)
    else:
        default_h, default_w = (9, 12), (10, 13)
    h = _axis_int(ctx, overrides, "grid_h", *default_h, 8, 14)
    w = _axis_int(ctx, overrides, "grid_w", *default_w, 9, 15)
    return h, w


def _paint_shape(grid, shape, top, left, color):
    for dr, dc in shape:
        grid[top + dr][left + dc] = color


def _draw_single_scene(grid, shape, placement, frame_color, motif_color, rng):
    h, w = len(grid), len(grid[0])
    sh, sw = _shape_dims(shape)
    gap = 0 if placement == "touching" else 1
    candidates = []
    if sh + gap + max(5, sh + 2) <= h:
        candidates.extend(("top", "bottom"))
    if sw + gap + max(5, sw + 2) <= w:
        candidates.extend(("left", "right"))
    if not candidates:
        raise ValueError(f"no frame/object layout fits {h}x{w} with shape {sh}x{sw}")
    side = rng.choice(candidates)
    min_fh, min_fw = max(5, sh + 2), max(5, sw + 2)
    if side in ("top", "bottom"):
        fh = rng.randint(min_fh, min(7, h - sh - gap))
        fw = rng.randint(min_fw, min(7, w))
        sc0 = rng.randint(0, w - sw)
        fc0_lo = max(0, sc0 + sw - fw)
        fc0_hi = min(sc0, w - fw)
        fc0 = rng.randint(fc0_lo, fc0_hi)
        if side == "top":
            sr0, fr0 = 0, sh + gap
        else:
            sr0, fr0 = h - sh, h - sh - gap - fh
    else:
        fh = rng.randint(min_fh, min(7, h))
        fw = rng.randint(min_fw, min(7, w - sw - gap))
        sr0 = rng.randint(0, h - sh)
        fr0_lo = max(0, sr0 + sh - fh)
        fr0_hi = min(sr0, h - fh)
        fr0 = rng.randint(fr0_lo, fr0_hi)
        if side == "left":
            sc0, fc0 = 0, sw + gap
        else:
            sc0, fc0 = w - sw, w - sw - gap - fw
    draw_frame(grid, fr0, fc0, fr0 + fh - 1, fc0 + fw - 1, frame_color)
    _paint_shape(grid, shape, sr0, sc0, motif_color)


def _profile_shapes(shape_role):
    if shape_role == "bent_over_line":
        return _L_MISSING_BR, _VERTICAL_LINE
    if shape_role == "line_over_bent":
        return _VERTICAL_LINE, _L_MISSING_BL
    if shape_role == "bent_orientation_a":
        return _L_MISSING_BL, _L_MISSING_BR
    if shape_role == "bent_orientation_b":
        return _L_MISSING_TL, _L_MISSING_TR
    raise ValueError(f"unknown shape-role profile {shape_role!r}")


def _draw_side_scan_order_scene(
    grid, selected_shape, earlier_shape, placement, frame_color, motif_color
):
    """Put a later component on the left, defeating left/right heuristics.

    The earlier component begins on row 0 at the right edge.  The selected
    component begins on row 1 at the left edge, so row-major discovery chooses
    it even though it is leftmost.  Shape roles reverse across schedule slots.
    """
    h, w = len(grid), len(grid[0])
    selected_h, selected_w = _shape_dims(selected_shape)
    _, earlier_w = _shape_dims(earlier_shape)
    selected_gap = 0 if placement == "touching" else 1
    earlier_gap = 1 - selected_gap
    selected_left = 0
    earlier_left = w - earlier_w
    frame_left = selected_w + selected_gap
    frame_right = earlier_left - earlier_gap - 1
    if frame_right - frame_left + 1 < 5:
        raise ValueError(f"side scan-order frame is too narrow in {h}x{w}")
    if 1 + selected_h > h:
        raise ValueError(f"selected shape does not fit {h}x{w}")
    draw_frame(grid, 0, frame_left, h - 1, frame_right, frame_color)
    _paint_shape(grid, earlier_shape, 0, earlier_left, motif_color)
    _paint_shape(grid, selected_shape, 1, selected_left, motif_color)


def _draw_top_scan_order_scene(
    grid, selected_shape, earlier_shape, placement, frame_color, motif_color
):
    """Tie the objects' first row; the right-hand component is selected.

    Both equal-size/color objects begin on row 0 and have equal 2x2 bounding
    boxes.  Their frame distance, top edge, bottom edge and compactness tie, so
    only the later start column establishes row-major-last selection.
    """
    h, w = len(grid), len(grid[0])
    selected_h, selected_w = _shape_dims(selected_shape)
    earlier_h, earlier_w = _shape_dims(earlier_shape)
    if (selected_h, selected_w) != (2, 2) or (earlier_h, earlier_w) != (2, 2):
        raise ValueError("top scan-order profiles require two distinct 2x2 triominoes")
    selected_gap = 0 if placement == "touching" else 1
    frame_top = selected_h + selected_gap
    if h - frame_top < 5:
        raise ValueError(f"top scan-order frame is too short in {h}x{w}")
    selected_left = w - selected_w
    earlier_left = 0
    if earlier_left + earlier_w >= selected_left:
        raise ValueError(f"top scan-order objects overlap in {h}x{w}")
    draw_frame(grid, frame_top, 0, h - 1, w - 1, frame_color)
    _paint_shape(grid, earlier_shape, 0, earlier_left, motif_color)
    _paint_shape(grid, selected_shape, 0, selected_left, motif_color)


def _choose_placement(ctx, overrides, default):
    options = _PLACEMENTS if overrides.get("placement") is not None else (default,)
    return ctx.draw_choice("placement", options)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axis/axes: {sorted(unknown)}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty {difficulty!r}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h, w = _choose_dimensions(ctx, overrides, difficulty, sample_index)
    profile = sample_index % LESSON_SCHEDULE_PERIOD
    default_placement = _SCAN_ORDER_PROFILES[profile][1] if profile < 4 else "touching"
    placement = _choose_placement(ctx, overrides, default_placement)
    rng = ctx.draw_rng("layout")

    frame_color = _FRAME_COLORS[sample_index % len(_FRAME_COLORS)]
    motif_color = rng.choice([color for color in range(1, 10) if color != frame_color])
    grid = full_grid(h, w, 0)

    # A five-pair production window contains four deconfounded scan-order
    # scenes and one single-object scene.  Holding out any one pair still leaves
    # both row-order modes, both selected sides, both placements, and reversed
    # shape/bounding-box preferences in the demonstrations.
    if profile < 4:
        layout, _, shape_role = _SCAN_ORDER_PROFILES[profile]
        selected_shape, earlier_shape = _profile_shapes(shape_role)
        if layout == "side_left":
            _draw_side_scan_order_scene(
                grid,
                selected_shape,
                earlier_shape,
                placement,
                frame_color,
                motif_color,
            )
        elif layout == "top_right":
            _draw_top_scan_order_scene(
                grid,
                selected_shape,
                earlier_shape,
                placement,
                frame_color,
                motif_color,
            )
        else:
            raise ValueError(f"unknown scan-order layout {layout!r}")
    else:
        shape = rng.choice(_SINGLE_SHAPES)
        _draw_single_scene(grid, shape, placement, frame_color, motif_color, rng)

    errors = self_check(grid)
    if errors:
        raise ValueError("constructed invalid scene: " + "; ".join(errors))
    return grid
