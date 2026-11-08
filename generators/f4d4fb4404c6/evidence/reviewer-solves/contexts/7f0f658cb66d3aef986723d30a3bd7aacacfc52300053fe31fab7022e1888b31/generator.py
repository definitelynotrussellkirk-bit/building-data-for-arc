"""Input curriculum for edge-directed replication of aligned hollow frames.

The canonical Racket authority is unchanged: every blue edge strip selects the
unique 4x4 hollow frame whose perpendicular span overlaps the strip, then copies
that frame repeatedly toward the marked edge.  This sampler cycles four lesson
profiles.  The fourth combines partial overlap with independently colored frames,
so every three-of-four query rotation still refutes both canonical shortcuts.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f4d4fb4404c6"
TASK_ID = GENERATOR_ID
RULE_HASH = "052ea839cbdd"
VERSION = "3.1.0"
SUMMARY = (
    "One or two separated 4x4 hollow frames are selected by color-1 strips on "
    "the grid edge. Each marker repeats its overlapping frame toward that edge "
    "in 4-cell steps, clipping the final copy. A four-profile cycle adds a "
    "combined witness so every three-of-four lesson rotation teaches both "
    "partial-overlap selection and per-frame color."
)

INVARIANTS = [
    "every non-marker object is an exact 4x4 hollow frame",
    "each straight color-1 edge marker overlaps exactly one frame span",
    "every frame has at least one marker and every marked direction fits a full copy",
    "default samples contain both vertical and horizontal markers, a multi-copy lane, and a multi-marker frame",
]

SCENE_PROFILES = (
    "canonical_core",
    "overlap_marker",
    "multicolor_frames",
    "combined_witness",
)
SCHEDULE_PROFILES = SCENE_PROFILES
SCHEDULE_PERIOD = len(SCHEDULE_PROFILES)
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0 / 5.0
CANONICAL_DIMENSIONS = ((18, 17), (22, 19), (22, 22), (24, 24))
BROAD_DIMENSIONS = ((18, 20), (19, 24), (20, 21), (21, 26), (23, 18), (25, 23), (26, 25))
DIRECTIONS = ("up", "down", "left", "right")

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "cyclic canonical_core / overlap_marker / multicolor_frames / combined_witness",
        "valid": "canonical_core|overlap_marker|multicolor_frames|combined_witness",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = ()


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the public deterministic three-profile lesson schedule."""
    del seed, difficulty
    if type(sample_index) is not int:
        raise ValueError("sample_index must be an integer")
    return SCHEDULE_PROFILES[sample_index % SCHEDULE_PERIOD]


def _draw_ring(grid, color, top, left):
    for r in range(top, top + 4):
        for c in range(left, left + 4):
            if r in (top, top + 3) or c in (left, left + 3):
                grid[r][c] = color


def _rooms(h, w, position):
    r, c = position
    return {
        "up": r,
        "down": h - 1 - (r + 3),
        "left": c,
        "right": w - 1 - (c + 3),
    }


@lru_cache(maxsize=64)
def _single_options(h, w):
    options = []
    for r in range(4, h - 7):
        for c in range(4, w - 7):
            rooms = _rooms(h, w, (r, c))
            for vertical in ("up", "down"):
                for horizontal in ("left", "right"):
                    if max(rooms[vertical], rooms[horizontal]) >= 8:
                        options.append(((r, c), vertical, horizontal))
    return tuple(options)


def _single_layout(ctx, h, w):
    options = _single_options(h, w)
    if not options:
        raise ValueError(f"{h}x{w} grid cannot host a long mixed-axis frame lesson")
    return ctx.draw_rng("single_layout").choice(options)


@lru_cache(maxsize=64)
def _double_pairs(h, w):
    positions = [(r, c) for r in range(4, h - 7) for c in range(4, w - 7)]
    return tuple(
        (first, second)
        for index, first in enumerate(positions)
        for second in positions[index + 1 :]
        if abs(first[0] - second[0]) >= 5 and abs(first[1] - second[1]) >= 5
    )


def _double_layout(ctx, h, w):
    pairs = _double_pairs(h, w)
    if not pairs:
        raise ValueError(f"{h}x{w} grid cannot host two uniquely aligned frames")
    first, second = ctx.draw_rng("double_layout").choice(pairs)
    if first[0] > second[0]:
        first, second = second, first
    # Vertical lanes point inward (and are long); horizontal lanes point outward.
    # Because row and column spans are disjoint, these four differently colored
    # chains do not intersect in the multicolor profile.
    first_dirs = ("down", "left" if first[1] < second[1] else "right")
    second_dirs = ("up", "right" if first[1] < second[1] else "left")
    return (first, first_dirs), (second, second_dirs)


def _put_marker(grid, frame, direction, *, length=4, offset=0):
    h, w = len(grid), len(grid[0])
    r, c = frame
    if not (1 <= length <= 4 and 0 <= offset <= 4 - length):
        raise ValueError("marker length/offset must select a nonempty frame-span subset")
    if direction in ("up", "down"):
        row = 0 if direction == "up" else h - 1
        for col in range(c + offset, c + offset + length):
            if grid[row][col] != 0:
                raise RuntimeError("marker collision")
            grid[row][col] = 1
    else:
        col = 0 if direction == "left" else w - 1
        for row in range(r + offset, r + offset + length):
            if grid[row][col] != 0:
                raise RuntimeError("marker collision")
            grid[row][col] = 1


def _dimensions(ctx, profile):
    band = ctx.difficulty if ctx.difficulty in ("easy", "medium", "hard") else "mixed"
    if profile == "canonical_core":
        choices = {
            "easy": CANONICAL_DIMENSIONS[:2],
            "medium": CANONICAL_DIMENSIONS[1:3],
            "hard": CANONICAL_DIMENSIONS[2:],
            "mixed": CANONICAL_DIMENSIONS,
        }[band]
        return ctx.draw_choice(f"canonical_dimensions_{band}", choices)
    choices = {
        "easy": BROAD_DIMENSIONS[:3],
        "medium": BROAD_DIMENSIONS[2:5],
        "hard": BROAD_DIMENSIONS[4:],
        "mixed": BROAD_DIMENSIONS,
    }[band]
    return ctx.draw_choice(f"broad_dimensions_{band}", choices)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    if type(seed) is not int or type(sample_index) is not int:
        raise ValueError("seed and sample_index must be integers")
    if "scene_profile" in overrides:
        value = overrides["scene_profile"]
        if not isinstance(value, str):
            raise ValueError("scene_profile must be a non-null string")
    requested = overrides.get("scene_profile", schedule_profile(seed, sample_index, difficulty))
    effective_overrides = dict(overrides)
    effective_overrides["scene_profile"] = requested
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective_overrides,
    )
    profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    h, w = _dimensions(ctx, profile)
    grid = full_grid(h, w, 0)

    if profile in ("multicolor_frames", "combined_witness"):
        colors = ctx.draw_distinct_colors("frame_colors", n=2, exclude=(0, 1))
        layouts = _double_layout(ctx, h, w)
        partial_target = None
        partial_length = None
        partial_offset = None
        if profile == "combined_witness":
            partial_frame = ctx.draw_choice("partial_frame", (0, 1))
            partial_direction = ctx.draw_rng("partial_direction").choice(
                layouts[partial_frame][1]
            )
            partial_target = (partial_frame, partial_direction)
            partial_length = ctx.draw_choice("partial_length", (2, 3))
            partial_offset = ctx.draw_int("partial_offset", 0, 4 - partial_length)
        for index, ((position, directions), color) in enumerate(zip(layouts, colors)):
            _draw_ring(grid, color, *position)
            for direction in directions:
                if partial_target == (index, direction):
                    _put_marker(
                        grid,
                        position,
                        direction,
                        length=partial_length,
                        offset=partial_offset,
                    )
                else:
                    _put_marker(grid, position, direction)
        return grid

    color = ctx.draw_color("frame_color", exclude=(0, 1))
    frame_count = 1 if profile == "overlap_marker" else ctx.draw_choice("frame_count", (1, 2, 2))
    if frame_count == 1:
        position, vertical, horizontal = _single_layout(ctx, h, w)
        directions = [vertical, horizontal]
        remaining = [direction for direction in DIRECTIONS if direction not in directions]
        if ctx.draw_choice("extra_marker", (False, True)):
            directions.append(ctx.draw_rng("extra_direction").choice(remaining))
        _draw_ring(grid, color, *position)
        partial_direction = (
            ctx.draw_rng("partial_direction").choice(directions)
            if profile == "overlap_marker"
            else None
        )
        partial_length = ctx.draw_choice("partial_length", (2, 3))
        partial_offset = ctx.draw_int("partial_offset", 0, 4 - partial_length)
        for direction in directions:
            if direction == partial_direction:
                _put_marker(
                    grid,
                    position,
                    direction,
                    length=partial_length,
                    offset=partial_offset,
                )
            else:
                _put_marker(grid, position, direction)
        return grid

    layouts = _double_layout(ctx, h, w)
    extra_frame = ctx.draw_choice("extra_marker_frame", (0, 1))
    for index, (position, base_directions) in enumerate(layouts):
        directions = list(base_directions)
        if index == extra_frame:
            remaining = [direction for direction in DIRECTIONS if direction not in directions]
            directions.append(ctx.draw_rng(f"extra_direction_{index}").choice(remaining))
        _draw_ring(grid, color, *position)
        for direction in directions:
            _put_marker(grid, position, direction)
    return grid


def _frame_ring(top, left):
    return {
        (r, c)
        for r in range(top, top + 4)
        for c in range(left, left + 4)
        if r in (top, top + 3) or c in (left, left + 3)
    }


def _marker_components(grid):
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 1}
    result = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        cells = {start}
        todo = [start]
        while todo:
            r, c = todo.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in unseen:
                    unseen.remove(point)
                    cells.add(point)
                    todo.append(point)
        result.append(cells)
    return result


def _analyze(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("expected a nonempty rectangular grid")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("expected nonempty rows")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("ragged grid")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("cells must be integer ARC colors 0..9")
    h, w = len(grid), width

    frames = []
    frame_cells = set()
    for top in range(h - 3):
        for left in range(w - 3):
            ring = _frame_ring(top, left)
            values = {grid[r][c] for r, c in ring}
            if len(values) != 1:
                continue
            color = next(iter(values))
            if color in (0, 1):
                continue
            if any(grid[r][c] != 0 for r in (top + 1, top + 2) for c in (left + 1, left + 2)):
                continue
            if frame_cells & ring:
                raise ValueError("overlapping 4x4 frame candidates")
            frames.append({
                "index": len(frames),
                "color": color,
                "r1": top,
                "r2": top + 3,
                "c1": left,
                "c2": left + 3,
                "cells": frozenset(ring),
            })
            frame_cells.update(ring)
    if not frames:
        raise ValueError("no 4x4 hollow frame")

    markers = []
    for cells in _marker_components(grid):
        rows = sorted({r for r, _ in cells})
        cols = sorted({c for _, c in cells})
        if not 1 <= len(cells) <= 4:
            raise ValueError(f"edge marker has {len(cells)} cells, expected 1..4")
        if len(rows) == 1 and rows[0] == 0 and cols == list(range(cols[0], cols[-1] + 1)):
            direction = "up"
        elif len(rows) == 1 and rows[0] == h - 1 and cols == list(range(cols[0], cols[-1] + 1)):
            direction = "down"
        elif len(cols) == 1 and cols[0] == 0 and rows == list(range(rows[0], rows[-1] + 1)):
            direction = "left"
        elif len(cols) == 1 and cols[0] == w - 1 and rows == list(range(rows[0], rows[-1] + 1)):
            direction = "right"
        else:
            raise ValueError("color-1 component is not a straight contiguous edge marker")
        markers.append({
            "direction": direction,
            "r1": rows[0],
            "r2": rows[-1],
            "c1": cols[0],
            "c2": cols[-1],
            "length": len(cells),
            "cells": frozenset(cells),
        })
    if not markers:
        raise ValueError("no color-1 edge marker")

    marker_cells = set().union(*(set(marker["cells"]) for marker in markers))
    foreground = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    stray = foreground - frame_cells - marker_cells
    if stray:
        raise ValueError(f"{len(stray)} foreground cells outside frames and markers")

    frame_marker_counts = [0] * len(frames)
    for marker in markers:
        matches = []
        for frame in frames:
            direction = marker["direction"]
            if direction in ("up", "down"):
                aligned = not (frame["c2"] < marker["c1"] or marker["c2"] < frame["c1"])
                room = frame["r1"] if direction == "up" else h - 1 - frame["r2"]
            else:
                aligned = not (frame["r2"] < marker["r1"] or marker["r2"] < frame["r1"])
                room = frame["c1"] if direction == "left" else w - 1 - frame["c2"]
            if aligned and room >= 4:
                matches.append((frame, room))
        if len(matches) != 1:
            raise ValueError(f"{marker['direction']} marker matches {len(matches)} frames, expected 1")
        frame, room = matches[0]
        marker["frame_index"] = frame["index"]
        marker["room"] = room
        frame_marker_counts[frame["index"]] += 1
    if any(count == 0 for count in frame_marker_counts):
        raise ValueError("every frame must be selected by at least one marker")
    return {
        "height": h,
        "width": w,
        "frames": frames,
        "markers": markers,
        "frame_marker_counts": frame_marker_counts,
    }


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    try:
        _analyze(grid)
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    return []


def _exact_span(marker, frame):
    if marker["direction"] in ("up", "down"):
        return marker["c1"] == frame["c1"] and marker["c2"] == frame["c2"]
    return marker["r1"] == frame["r1"] and marker["r2"] == frame["r2"]


def strict_canonical_like(grid):
    issues = self_check(grid)
    if issues:
        return issues
    parsed = _analyze(grid)
    palette_size = len({value for row in grid for value in row})
    profile = (parsed["height"], parsed["width"], palette_size)
    reasons = []
    if profile not in {(h, w, 3) for h, w in CANONICAL_DIMENSIONS}:
        reasons.append(f"profile {profile} is outside canonical dimensions/palette")
    if len(parsed["frames"]) not in (1, 2):
        reasons.append("canonical manifold has one or two frames")
    if len({frame["color"] for frame in parsed["frames"]}) != 1:
        reasons.append("canonical frames share one color")
    if any(
        marker["length"] != 4
        or not _exact_span(marker, parsed["frames"][marker["frame_index"]])
        for marker in parsed["markers"]
    ):
        reasons.append("canonical markers are full four-cell frame-span strips")
    return reasons


def observe_overrides(grid):
    parsed = _analyze(grid)
    multiple_colors = len({frame["color"] for frame in parsed["frames"]}) > 1
    partial_overlap = any(
        marker["length"] != 4
        or not _exact_span(marker, parsed["frames"][marker["frame_index"]])
        for marker in parsed["markers"]
    )
    if multiple_colors and partial_overlap:
        profile = "combined_witness"
    elif multiple_colors:
        profile = "multicolor_frames"
    elif partial_overlap:
        profile = "overlap_marker"
    else:
        profile = "canonical_core"
    return {"scene_profile": profile}


def _paint_ring(out, color, r1, c1, r2, c2):
    h, w = len(out), len(out[0])
    for r in range(r1, r2 + 1):
        for c in range(c1, c2 + 1):
            if (r in (r1, r2) or c in (c1, c2)) and 0 <= r < h and 0 <= c < w:
                out[r][c] = color


def _render(grid, *, exact_span_only=False, global_color=False, one_copy_only=False, first_marker_only=False):
    parsed = _analyze(grid)
    h, w = parsed["height"], parsed["width"]
    out = full_grid(h, w, 0)
    first_color = parsed["frames"][0]["color"]
    for frame in parsed["frames"]:
        color = first_color if global_color else frame["color"]
        _paint_ring(out, color, frame["r1"], frame["c1"], frame["r2"], frame["c2"])
    seen = set()
    for marker in parsed["markers"]:
        frame = parsed["frames"][marker["frame_index"]]
        if exact_span_only and not _exact_span(marker, frame):
            continue
        if first_marker_only and frame["index"] in seen:
            continue
        seen.add(frame["index"])
        color = first_color if global_color else frame["color"]
        direction = marker["direction"]
        step = 1
        while True:
            if direction == "up":
                top, left = frame["r1"] - 4 * step, frame["c1"]
                if top + 3 < 0:
                    break
            elif direction == "down":
                top, left = frame["r2"] + 1 + 4 * (step - 1), frame["c1"]
                if top >= h:
                    break
            elif direction == "left":
                top, left = frame["r1"], frame["c1"] - 4 * step
                if left + 3 < 0:
                    break
            else:
                top, left = frame["r1"], frame["c2"] + 1 + 4 * (step - 1)
                if left >= w:
                    break
            _paint_ring(out, color, top, left, top + 3, left + 3)
            if one_copy_only:
                break
            step += 1
    return out


def rule_mirror(grid):
    """Executable mirror used only for contract tests; Racket remains authority."""
    return _render(deepcopy(grid))


def _rival_exact_span_only(grid):
    return _render(deepcopy(grid), exact_span_only=True)


def _rival_global_frame_color(grid):
    return _render(deepcopy(grid), global_color=True)


def _rival_one_copy_only(grid):
    return _render(deepcopy(grid), one_copy_only=True)


def _rival_first_marker_only(grid):
    return _render(deepcopy(grid), first_marker_only=True)


def _has_partial_overlap(grid):
    parsed = _analyze(grid)
    return any(
        marker["length"] != 4
        or not _exact_span(marker, parsed["frames"][marker["frame_index"]])
        for marker in parsed["markers"]
    )


def _has_multiple_frame_colors(grid):
    return len({frame["color"] for frame in _analyze(grid)["frames"]}) > 1


def _has_long_chain(grid):
    return any(marker["room"] >= 8 for marker in _analyze(grid)["markers"])


def _has_multiple_markers_for_one_frame(grid):
    return any(count >= 2 for count in _analyze(grid)["frame_marker_counts"])


SEMANTIC_RIVALS = {
    "exact_span_only": _rival_exact_span_only,
    "global_frame_color": _rival_global_frame_color,
    "one_copy_only": _rival_one_copy_only,
    "first_marker_only": _rival_first_marker_only,
}
CANONICAL_SHORTCUTS = {
    "exact_span_only": _rival_exact_span_only,
    "global_frame_color": _rival_global_frame_color,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "partial_overlap_marker": _has_partial_overlap,
    "multiple_frame_colors": _has_multiple_frame_colors,
    "long_chain": _has_long_chain,
    "multiple_markers_per_frame": _has_multiple_markers_for_one_frame,
}
WITNESS_RIVALS = {
    "partial_overlap_marker": ["exact_span_only"],
    "multiple_frame_colors": ["global_frame_color"],
    "long_chain": ["one_copy_only"],
    "multiple_markers_per_frame": ["first_marker_only"],
}


def lesson_identifiable(demos, query):
    del query
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        survived = True
        for demo in demos:
            if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
                return ["demonstrations must contain input/output grids"]
            try:
                survived &= rival(demo["input"]) == demo["output"]
            except (TypeError, ValueError) as exc:
                return [f"{name} evaluation failed: {exc}"]
            if not survived:
                break
        if survived:
            reasons.append(f"{name} fits every demonstration")
    return reasons
