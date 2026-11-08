"""Generator for e39e9282 / ee6a99e8b7f9.

On a color-8 background, color-5 (gray) and color-6 (pink) rectangles have
one or more color-9 dots immediately outside their bounding-box edges.  Gray
rectangles are erased and each gray dot is copied one cell inward to the old
edge.  Pink rectangles remain; each pink dot is moved to the rectangle's
center row or center column, preserving its coordinate parallel to the edge.

The canonical examples contain only 3x3 rectangles, so a four-profile schedule
also includes non-3x3 rectangles.  Those examples refute the plausible but
wrong shortcut "pink moves two cells inward, gray one cell inward" while every
four-example lesson retains canonical-scale anchors.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from typing import Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ee6a99e8b7f9"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "faea8048f031"

SUMMARY = (
    "Color-8 scenes contain separated gray (5) and pink (6) rectangles with "
    "one or more adjacent exterior color-9 dots. Gray rectangles are erased "
    "while their dots are copied to the adjacent inner edge; pink rectangles "
    "remain while their dots move to the center row/column and their exterior "
    "sources clear. Scheduled 3x3 anchors and non-3x3 witnesses distinguish "
    "center/edge geometry from a fixed inward-step shortcut."
)

INVARIANTS = [
    "the rectangular grid uses only colors 5, 6, 8, and 9",
    "every same-color 4-connected color-5/color-6 component is a filled rectangle",
    "every color-9 dot lies immediately outside exactly one rectangle bbox edge",
    "every rectangle has at least one associated dot; border-touching rectangles are lawful",
    "gray sources remain while gray shapes erase; pink sources clear while pink shapes remain",
]

AXES = {
    "grid_h": {"type": "int", "default": "scheduled canonical profile", "valid": "9..18"},
    "grid_w": {"type": "int", "default": "scheduled canonical profile", "valid": "9..18"},
    "n_shapes": {"type": "int", "default": "scheduled 1,3,5,7", "valid": "1..7"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.25
_CARDINAL = ((1, 0), (-1, 0), (0, 1), (0, -1))
_PROFILE_NAMES = (
    "canonical_single",
    "canonical_mixed",
    "size_generalization_five",
    "size_generalization_border",
)
SCHEDULE_PROFILES = _PROFILE_NAMES
_PROFILE_DEFAULTS = (
    (9, 9, 1),
    (11, 11, 3),
    (15, 15, 5),
    (13, 13, 7),
)
_CANONICAL_COUNTS = {(9, 9): 1, (11, 11): 3, (15, 15): 5, (13, 13): 7}


def schedule_profile(seed, sample_index, difficulty=None):
    """Four consecutive accepted indices cover both anchors and two size witnesses."""
    del seed, difficulty
    return _PROFILE_NAMES[int(sample_index) % len(_PROFILE_NAMES)]


def _validate_override_types(overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}; valid axes: {sorted(AXES)}")
    for name, value in overrides.items():
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer, got {type(value).__name__}")


def _scheduled_int(ctx, overrides, label, default, lo, hi):
    if label in overrides:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, default, default)


def _validate_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return 0, 0, ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return len(grid), 0, ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return len(grid), width, ["grid must be rectangular"]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return len(grid), width, [f"cell ({r},{c}) is not a literal ARC color 0..9: {value!r}"]
    return len(grid), width, []


def _shape_components(grid):
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] in (5, 6)}
    found = []
    while unseen:
        start = min(unseen)
        color = grid[start[0]][start[1]]
        unseen.remove(start)
        queue = deque([start])
        cells = {start}
        while queue:
            r, c = queue.popleft()
            for dr, dc in _CARDINAL:
                point = (r + dr, c + dc)
                if point in unseen and grid[point[0]][point[1]] == color:
                    unseen.remove(point)
                    queue.append(point)
                    cells.add(point)
        r1, r2 = min(r for r, _ in cells), max(r for r, _ in cells)
        c1, c2 = min(c for _, c in cells), max(c for _, c in cells)
        found.append({
            "color": color,
            "bbox": (r1, c1, r2, c2),
            "cells": frozenset(cells),
            "filled": len(cells) == (r2 - r1 + 1) * (c2 - c1 + 1),
        })
    return sorted(found, key=lambda shape: shape["bbox"])


def _side_for(dot, bbox):
    r, c = dot
    r1, c1, r2, c2 = bbox
    if r1 <= r <= r2 and c == c1 - 1:
        return "left"
    if r1 <= r <= r2 and c == c2 + 1:
        return "right"
    if c1 <= c <= c2 and r == r1 - 1:
        return "above"
    if c1 <= c <= c2 and r == r2 + 1:
        return "below"
    return None


def _linked_dots(grid, shapes=None):
    shapes = _shape_components(grid) if shapes is None else shapes
    links = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 9:
                continue
            hits = []
            for index, shape in enumerate(shapes):
                side = _side_for((r, c), shape["bbox"])
                if side is not None:
                    hits.append((index, side))
            links.append(((r, c), hits))
    return links


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete lawful input grammar, including canonical borders."""
    del difficulty
    h, w, errors = _validate_grid(grid)
    if errors:
        return errors
    if not (9 <= h <= 18):
        errors.append(f"height {h} outside 9..18")
    if not (9 <= w <= 18):
        errors.append(f"width {w} outside 9..18")
    unexpected = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in {5, 6, 8, 9}
    ]
    if unexpected:
        errors.append(f"unexpected colors outside {{5,6,8,9}}: {unexpected[:3]}")
    if not any(value == 8 for row in grid for value in row):
        errors.append("background color 8 is absent")

    shapes = _shape_components(grid)
    if not shapes:
        errors.append("no color-5/color-6 rectangle")
    for index, shape in enumerate(shapes):
        if not shape["filled"]:
            errors.append(f"shape {index} is not a filled rectangle: bbox={shape['bbox']}")

    links = _linked_dots(grid, shapes)
    if not links:
        errors.append("no color-9 dots")
    counts = [0] * len(shapes)
    for dot, hits in links:
        if len(hits) != 1:
            errors.append(
                f"dot at {dot} must be immediately outside exactly one rectangle bbox edge; got {len(hits)}"
            )
        else:
            counts[hits[0][0]] += 1
    for index, count in enumerate(counts):
        if count == 0:
            errors.append(f"shape {index} at {shapes[index]['bbox']} has no associated dot")

    if isinstance(meta, dict):
        requested = meta.get("overrides", meta)
        if isinstance(requested, dict):
            observed = {"grid_h": h, "grid_w": w, "n_shapes": len(shapes)}
            for axis in AXES:
                if axis in requested and requested[axis] != observed[axis]:
                    errors.append(
                        f"requested {axis}={requested[axis]!r}, observed {observed[axis]!r}"
                    )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Accept exactly the canonical dimension/count/3x3 rectangle manifold."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    h, w = len(grid), len(grid[0])
    expected = _CANONICAL_COUNTS.get((h, w))
    shapes = _shape_components(grid)
    if expected is None:
        reasons.append(f"dimensions {h}x{w} are not one of the four canonical profiles")
    elif len(shapes) != expected:
        reasons.append(f"canonical {h}x{w} profile has {expected} shapes, found {len(shapes)}")
    for index, shape in enumerate(shapes):
        r1, c1, r2, c2 = shape["bbox"]
        if (r2 - r1 + 1, c2 - c1 + 1) != (3, 3):
            reasons.append(f"shape {index} is not canonical 3x3: {shape['bbox']}")
    expected_palette = 3 if (h, w) == (9, 9) else 4
    palette_size = len({value for row in grid for value in row})
    if palette_size != expected_palette:
        reasons.append(
            f"canonical {h}x{w} profile uses {expected_palette} colors, found {palette_size}"
        )
    return reasons


def observe_overrides(grid) -> dict[str, int]:
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_shapes": len(_shape_components(grid)),
    }


def _template_boxes(profile_index):
    if profile_index == 0:
        return [(4, 2, 3, 3)]
    if profile_index == 1:
        return [(1, 1, 3, 3), (2, 6, 3, 3), (7, 3, 3, 3)]
    if profile_index == 2:
        # Two dimensions differ from three, deliberately refuting fixed steps.
        return [
            (1, 1, 5, 3),
            (1, 9, 3, 5),
            (7, 1, 3, 3),
            (6, 6, 5, 3),
            (12, 11, 3, 3),
        ]
    return [
        # Several lawful border-touching shapes plus 1x3/3x1/1x5/5x1 witnesses.
        (0, 0, 1, 3),
        (0, 5, 3, 1),
        (0, 9, 3, 3),
        (5, 0, 3, 3),
        (5, 5, 1, 5),
        (5, 12, 5, 1),
        (10, 5, 3, 3),
    ]


def _partition_bounds(length, count):
    return [round(i * length / count) for i in range(count + 1)]


def _general_boxes(h, w, n_shapes, rng):
    if n_shapes <= 3:
        rows, cols = 1, n_shapes
    elif n_shapes <= 6:
        rows, cols = 2, (n_shapes + 1) // 2
    else:
        rows, cols = 3, 3
    rb = _partition_bounds(h, rows)
    cb = _partition_bounds(w, cols)
    boxes = []
    for index in range(n_shapes):
        rr, cc = divmod(index, cols)
        top, bottom = rb[rr], rb[rr + 1]
        left, right = cb[cc], cb[cc + 1]
        tile_h, tile_w = bottom - top, right - left
        h_options = [size for size in (1, 3, 5) if size <= tile_h - 2]
        w_options = [size for size in (1, 3, 5) if size <= tile_w - 2]
        sh = h_options[rng.randrange(len(h_options))]
        sw = w_options[rng.randrange(len(w_options))]
        row_room = tile_h - sh - 2
        col_room = tile_w - sw - 2
        r0 = top + 1 + (rng.randrange(row_room + 1) if row_room else 0)
        c0 = left + 1 + (rng.randrange(col_room + 1) if col_room else 0)
        boxes.append((r0, c0, sh, sw))
    return boxes


def _bbox(box):
    r0, c0, sh, sw = box
    return r0, c0, r0 + sh - 1, c0 + sw - 1


def _candidate_dots(box, boxes, h, w):
    r1, c1, r2, c2 = _bbox(box)
    raw = (
        [(r, c1 - 1, "left") for r in range(r1, r2 + 1)]
        + [(r, c2 + 1, "right") for r in range(r1, r2 + 1)]
        + [(r1 - 1, c, "above") for c in range(c1, c2 + 1)]
        + [(r2 + 1, c, "below") for c in range(c1, c2 + 1)]
    )
    result = []
    for r, c, side in raw:
        if not (0 <= r < h and 0 <= c < w):
            continue
        if any(br <= r < br + bh and bc <= c < bc + bw for br, bc, bh, bw in boxes):
            continue
        hits = sum(_side_for((r, c), _bbox(other)) is not None for other in boxes)
        if hits == 1:
            result.append((r, c, side))
    return result


def _target(dot, box, color, side, *, fixed_steps=False):
    r, c = dot
    r1, c1, r2, c2 = _bbox(box)
    if fixed_steps:
        step = 2 if color == 6 else 1
        dr, dc = {
            "left": (0, step), "right": (0, -step),
            "above": (step, 0), "below": (-step, 0),
        }[side]
        return r + dr, c + dc
    if color == 6:
        return (r, (c1 + c2) // 2) if side in ("left", "right") else ((r1 + r2) // 2, c)
    return {
        "left": (r, c1), "right": (r, c2),
        "above": (r1, c), "below": (r2, c),
    }[side]


def _paint_scene(h, w, boxes, colors, dot_goal, rng, *, require_fixed_witness=False):
    grid = full_grid(h, w, 8)
    for (r0, c0, sh, sw), color in zip(boxes, colors):
        for r in range(r0, r0 + sh):
            for c in range(c0, c0 + sw):
                grid[r][c] = color

    used_dots = set()
    witnessed_fixed = False
    for index, (box, color) in enumerate(zip(boxes, colors)):
        candidates = _candidate_dots(box, boxes, h, w)
        rng.shuffle(candidates)
        if not candidates:
            raise ValueError(f"shape {index} has no unambiguous dot position")
        requested = dot_goal[index]
        chosen = []
        unique_targets = set()

        # On a non-3 dimension, prioritize a side whose true midpoint is not
        # the canonical fixed 2-cell displacement.
        if require_fixed_witness and not witnessed_fixed and color == 6:
            _, _, sh, sw = box
            witness = [
                candidate for candidate in candidates
                if ((candidate[2] in ("above", "below") and sh != 3)
                    or (candidate[2] in ("left", "right") and sw != 3))
            ]
            if witness:
                candidate = witness[0]
                chosen.append(candidate)
                used_dots.add(candidate[:2])
                unique_targets.add(_target(candidate[:2], box, color, candidate[2]))
                witnessed_fixed = True

        # Prefer different destinations, then fill remaining requested sources.
        for candidate in candidates:
            if len(chosen) >= requested or candidate[:2] in used_dots:
                continue
            target = _target(candidate[:2], box, color, candidate[2])
            if target in unique_targets:
                continue
            chosen.append(candidate)
            used_dots.add(candidate[:2])
            unique_targets.add(target)
        for candidate in candidates:
            if len(chosen) >= requested or candidate[:2] in used_dots:
                continue
            chosen.append(candidate)
            used_dots.add(candidate[:2])
        if not chosen:
            raise ValueError(f"shape {index} lost all dot positions")
        for r, c, _ in chosen:
            grid[r][c] = 9

    if require_fixed_witness and not witnessed_fixed:
        raise ValueError("generalization template failed to realize a fixed-step witness")
    return grid


def _transform_square(grid, code):
    result = [list(row) for row in grid]
    if code >= 4:
        result = [row[::-1] for row in result]
        code -= 4
    for _ in range(code):
        result = [list(row) for row in zip(*result[::-1])]
    return result


def _transform_rect(grid, code):
    if code == 1:
        return [row[::-1] for row in grid]
    if code == 2:
        return [list(row) for row in grid[::-1]]
    if code == 3:
        return [row[::-1] for row in grid[::-1]]
    return [list(row) for row in grid]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_override_types(overrides)
    profile_index = int(sample_index) % len(_PROFILE_DEFAULTS)
    default_h, default_w, default_n = _PROFILE_DEFAULTS[profile_index]
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = _scheduled_int(ctx, overrides, "grid_h", default_h, 9, 18)
    w = _scheduled_int(ctx, overrides, "grid_w", default_w, 9, 18)
    n_shapes = _scheduled_int(ctx, overrides, "n_shapes", default_n, 1, 7)
    rng = ctx.draw_rng("layout")

    use_template = (h, w, n_shapes) == (default_h, default_w, default_n)
    boxes = _template_boxes(profile_index) if use_template else _general_boxes(h, w, n_shapes, rng)

    if n_shapes == 1:
        colors = [6]  # the 9x9 canonical profile has palette {6,8,9}
    elif use_template and profile_index in (2, 3):
        # Box 0 has a non-3 dimension. Pin it pink so the scheduled
        # fixed-step counterexample cannot disappear under random coloring;
        # box 1 stays gray so both semantic branches remain visible.
        colors = [6, 5] + [5 if rng.randrange(2) == 0 else 6 for _ in range(n_shapes - 2)]
    else:
        colors = [5, 6] + [5 if rng.randrange(2) == 0 else 6 for _ in range(n_shapes - 2)]
        rng.shuffle(colors)

    if use_template and profile_index == 0:
        dot_goal = [1]
    elif use_template:
        # Every mixed scheduled scene independently refutes one-dot-per-shape.
        dot_goal = [2 + int(difficulty == "hard" and (i + sample_index) % 2 == 0)
                    for i in range(n_shapes)]
    else:
        dot_goal = [2 for _ in range(n_shapes)]

    grid = _paint_scene(
        h,
        w,
        boxes,
        colors,
        dot_goal,
        rng,
        require_fixed_witness=use_template and profile_index in (2, 3),
    )
    if h == w:
        grid = _transform_square(grid, rng.randrange(8))
    else:
        grid = _transform_rect(grid, rng.randrange(4))

    errors = self_check(grid)
    if errors:
        raise ValueError(f"constructed invalid generator instance: {errors}")
    observed = observe_overrides(grid)
    for axis in AXES:
        requested = ctx.axis_value(axis)
        if observed[axis] != requested:
            raise ValueError(
                f"realized axis {axis!r}={observed[axis]!r} does not match keyed draw {requested!r}"
            )
    return [row[:] for row in grid]


def _apply_variant(
    grid,
    *,
    fixed_steps=False,
    first_dot_only=False,
    pink_inner=False,
    gray_center=False,
    keep_pink_source=False,
    clear_gray_source=False,
):
    shapes = _shape_components(grid)
    links = _linked_dots(grid, shapes)
    out = deepcopy(grid)
    for shape in shapes:
        if shape["color"] == 5:
            for r, c in shape["cells"]:
                out[r][c] = 8
    processed_shapes = set()
    for dot, hits in links:  # row-major, matching the selected authority
        if len(hits) != 1:
            continue
        index, side = hits[0]
        shape = shapes[index]
        if first_dot_only and index in processed_shapes:
            continue
        processed_shapes.add(index)
        r, c = dot
        color = shape["color"]
        if color == 6:
            if not keep_pink_source:
                out[r][c] = 8
            target_color = 5 if pink_inner else 6
        else:
            if clear_gray_source:
                out[r][c] = 8
            target_color = 6 if gray_center else 5
        box = (
            shape["bbox"][0],
            shape["bbox"][1],
            shape["bbox"][2] - shape["bbox"][0] + 1,
            shape["bbox"][3] - shape["bbox"][1] + 1,
        )
        nr, nc = _target(dot, box, target_color, side, fixed_steps=fixed_steps)
        if 0 <= nr < len(out) and 0 <= nc < len(out[0]):
            out[nr][nc] = 9
    return out


def rule_mirror(grid):
    """Independent callable mirror for probes; canonical Racket stays authority."""
    errors = self_check(grid)
    if errors:
        raise ValueError(f"invalid task input: {errors}")
    return _apply_variant(grid)


def _rival_fixed_inward_steps(grid):
    return _apply_variant(grid, fixed_steps=True)


def _rival_first_dot_per_shape(grid):
    return _apply_variant(grid, first_dot_only=True)


def _rival_pink_to_inner_edge(grid):
    return _apply_variant(grid, pink_inner=True)


def _rival_gray_to_centerline(grid):
    return _apply_variant(grid, gray_center=True)


def _rival_keep_pink_source(grid):
    return _apply_variant(grid, keep_pink_source=True)


def _rival_clear_gray_source(grid):
    return _apply_variant(grid, clear_gray_source=True)


SEMANTIC_RIVALS: dict[str, Callable] = {
    "fixed_inward_steps": _rival_fixed_inward_steps,
    "first_dot_per_shape": _rival_first_dot_per_shape,
    "pink_to_inner_edge": _rival_pink_to_inner_edge,
    "gray_to_centerline": _rival_gray_to_centerline,
    "keep_pink_source": _rival_keep_pink_source,
    "clear_gray_source": _rival_clear_gray_source,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
# Every canonical rectangle is 3x3, so this wrong metric rule fits all pairs.
CANONICAL_SHORTCUTS = {"fixed_inward_steps": _rival_fixed_inward_steps}


def _witness(name):
    rival = SEMANTIC_RIVALS[name]

    def predicate(grid):
        return not self_check(grid) and rival(grid) != rule_mirror(grid)

    return predicate


SEMANTIC_WITNESSES = {
    "non3_size_refutes_fixed_steps": _witness("fixed_inward_steps"),
    "multiple_dots_refute_first_only": _witness("first_dot_per_shape"),
    "pink_center_refutes_inner_edge": _witness("pink_to_inner_edge"),
    "gray_edge_refutes_centerline": _witness("gray_to_centerline"),
    "pink_source_clears": _witness("keep_pink_source"),
    "gray_source_remains": _witness("clear_gray_source"),
}
WITNESS_RIVALS = {
    "non3_size_refutes_fixed_steps": ["fixed_inward_steps"],
    "multiple_dots_refute_first_only": ["first_dot_per_shape"],
    "pink_center_refutes_inner_edge": ["pink_to_inner_edge"],
    "gray_edge_refutes_centerline": ["gray_to_centerline"],
    "pink_source_clears": ["keep_pink_source"],
    "gray_source_remains": ["clear_gray_source"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson only when a declared wrong rule fits demos but splits query."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]
    reasons = []
    normalized = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} input is invalid: {errors[0]}")
            continue
        exact = rule_mirror(demo["input"])
        if demo["output"] != exact:
            reasons.append(f"demo {index} output does not match the exact rectangle/dot rule")
            continue
        normalized.append(demo)
    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query input is invalid: {query_errors[0]}")
        return reasons
    exact_query = rule_mirror(query["input"])
    for name, rival in LESSON_COMPETITORS.items():
        if len(normalized) != len(demos):
            break
        if all(rival(demo["input"]) == demo["output"] for demo in normalized):
            if rival(query["input"]) != exact_query:
                reasons.append(f"declared rival {name!r} fits every demonstration but splits the query")
    return reasons
