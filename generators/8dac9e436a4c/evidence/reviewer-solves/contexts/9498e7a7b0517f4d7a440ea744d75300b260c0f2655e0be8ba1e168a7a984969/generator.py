"""Constructive input sampler for canonical ARC task 8dac9e436a4c.

Rule authority is unchanged: every 4-connected color-6 component that is
exactly the border of its bounding box has its strict interior painted color 8.
Completely filled color-6 rectangles are distractors and remain unchanged.

The sampler deliberately teaches both universal quantification (two hollow
frames on alternating samples) and the frame-vs-solid distinction (every
ordinary sample has at least one filled rectangle).  Canonical dimensions are
sampled densely, while exact size and object-count controls stay constructive
throughout their declared Cartesian domain.
"""
from __future__ import annotations

from copy import deepcopy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "8dac9e436a4c"
TASK_ID = GENERATOR_ID
RULE_HASH = "1ee9a2a0fa3f"
VERSION = "3.1.0"
SUMMARY = (
    "A 0-background grid contains one or two hollow color-6 rectangular "
    "frames and one or two filled color-6 rectangular distractors, all as "
    "separate components, plus a short non-6 decoration. Fill the strict "
    "interior of every hollow frame with color 8; leave filled rectangles "
    "unchanged. Canonical-size profiles are sampled densely, frame aspect and "
    "scale vary constructively, and all declared numeric controls are exact."
)

INVARIANTS = [
    "one or two hollow color-6 rectangular frames, each with a nonempty interior",
    "one or two filled color-6 rectangular distractors in every ordinary sample",
    "all color-6 rectangles are separate 4-connected components",
    "exactly one short straight decoration (length 1..3) uses a non-0/6/8 color",
]

AXES = {
    "grid_h": {"type": "int", "default": "canonical-dense; broad every fifth draw",
               "valid": "8..16"},
    "grid_w": {"type": "int", "default": "canonical-dense; broad every fifth draw",
               "valid": "8..16"},
    "n_frames": {"type": "int", "default": "alternates 2 and 1 by lesson schedule",
                 "valid": "1..2"},
    "n_solids": {"type": "int", "default": "alternates 1 and 2 by lesson schedule",
                 "valid": "1..2"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

# Exact canonical (height, width, input-palette-size) profiles.  The palette is
# always {0, 6, decoration}; dimensions are used by the dense curriculum branch.
_CANONICAL_DIMENSIONS = ((8, 12), (9, 10), (9, 13), (10, 11), (11, 11))
_DECORATION_COLORS = (1, 2, 3, 4, 5, 7, 9)

EXAMPLES_NEEDED = 3
SCHEDULE_PROFILES = ("multiple_frames", "extra_solids")


def schedule_profile(seed, sample_index, difficulty=None):
    """Every four-pair window has two multi-frame examples.

    Therefore every three-demo query rotation retains a counterexample to the
    canonical shortcut "fill only the first hollow frame".
    """
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % 2]


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name in AXES:
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")


def _draw_dimensions(ctx, sample_index, overrides):
    # Any explicit dimension request is independent and exact.  Otherwise four
    # out of five samples use an exact canonical profile; the fifth explores the
    # full declared size range.
    if overrides.get("grid_h") is not None or overrides.get("grid_w") is not None:
        h = ctx.draw_int_strict("grid_h", 8, 16)
        w = ctx.draw_int_strict("grid_w", 8, 16)
        return h, w
    if sample_index % 5 != 4:
        h, w = ctx.draw_choice("canonical_dimensions", _CANONICAL_DIMENSIONS)
        # Record each exact public axis independently for the override/provenance
        # contract, while preserving the correlated canonical pair.
        return ctx.draw_choice("grid_h", (h,)), ctx.draw_choice("grid_w", (w,))
    return ctx.draw_int_strict("grid_h", 8, 16), ctx.draw_int_strict("grid_w", 8, 16)


def _draw_scheduled_count(ctx, name, lo, hi, scheduled, overrides):
    if overrides.get(name) is not None:
        return ctx.draw_int_strict(name, lo, hi)
    # Singleton choice is intentional: schedule_profile is the lesson-level
    # contract. Exact overrides still draw against the complete declared range.
    return ctx.draw_choice(name, (scheduled,))


def _rectangles_separated(left, right):
    """True when bboxes have at least one full blank row or column between."""
    ar0, ac0, ar1, ac1 = left
    br0, bc0, br1, bc1 = right
    return (
        ar1 + 1 < br0 or br1 + 1 < ar0 or
        ac1 + 1 < bc0 or bc1 + 1 < ac0
    )


def _candidate_bboxes(h, w, bh, bw, rng):
    """At most nine anchor placements: corners, edge midpoints, and center.

    An earlier exhaustive list made failed large-shape probes exponential: up
    to 196 candidates per rectangle and four nested levels before the sampler
    could fall back to a smaller lawful shape.  These anchors retain every
    constructive corner packing used by the declared domain while bounding a
    failed shape probe to 9**4 candidate tuples.
    """
    max_top, max_left = h - bh, w - bw
    tops = sorted({0, max_top // 2, max_top})
    lefts = sorted({0, max_left // 2, max_left})
    boxes = [
        (top, left, top + bh - 1, left + bw - 1)
        for top in tops
        for left in lefts
    ]
    rng.shuffle(boxes)
    return boxes


def _try_place_rectangles(ctx, h, w, frame_dims, n_frames, n_solids):
    fh, fw = frame_dims
    items = [
        ("frame", index, fh, fw) for index in range(n_frames)
    ] + [
        ("solid", index, 3, 3) for index in range(n_solids)
    ]
    # Largest first is a fail-fast constructive search. Identity remains in
    # each tuple, so candidate order stays stable under sorting.
    items.sort(key=lambda item: (-(item[2] * item[3]), item[0], item[1]))
    placements = {}
    chosen = []
    candidates = {
        (kind, index): _candidate_bboxes(
            h, w, bh, bw,
            ctx.draw_rng(f"placement:{frame_dims}:{kind}:{index}"),
        )
        for kind, index, bh, bw in items
    }

    def search(item_index):
        if item_index == len(items):
            return True
        kind, index, _, _ = items[item_index]
        key = (kind, index)
        for bbox in candidates[key]:
            if all(_rectangles_separated(bbox, prior) for prior in chosen):
                chosen.append(bbox)
                placements[key] = bbox
                if search(item_index + 1):
                    return True
                placements.pop(key)
                chosen.pop()
        return False

    return placements if search(0) else None


def _shape_family(ctx):
    return ctx.draw_choice("frame_shape_family", ("square", "wide", "tall"))


def _frame_shape_candidates(ctx, h, w, difficulty):
    family = _shape_family(ctx)
    pools = {
        "square": [(6, 6), (5, 5), (4, 4), (3, 3)],
        "wide": [(5, 7), (4, 6), (3, 5), (3, 4), (3, 3)],
        "tall": [(7, 5), (6, 4), (5, 3), (4, 3), (3, 3)],
    }
    candidates = [shape for shape in pools[family] if shape[0] <= h and shape[1] <= w]
    if (3, 3) not in candidates:
        candidates.append((3, 3))
    if difficulty == "easy":
        candidates.sort(key=lambda shape: (shape[0] * shape[1], shape))
    elif difficulty == "hard":
        candidates.sort(key=lambda shape: (-(shape[0] * shape[1]), shape))
    elif difficulty == "medium":
        # Prefer a middle scale but retain monotone fallbacks.
        candidates.sort(key=lambda shape: (abs(shape[0] * shape[1] - 20), shape))
    else:
        ctx.draw_rng("frame_scale_order").shuffle(candidates)
    # De-duplicate after any family fallback while retaining deterministic order.
    result = []
    for shape in candidates:
        if shape not in result:
            result.append(shape)
    return result


def _place_rectangles(ctx, h, w, n_frames, n_solids, difficulty):
    attempted = []
    for frame_dims in _frame_shape_candidates(ctx, h, w, difficulty):
        attempted.append(frame_dims)
        placements = _try_place_rectangles(
            ctx, h, w, frame_dims, n_frames, n_solids
        )
        if placements is not None:
            return placements
    raise RuntimeError(
        f"constructive placement failed for {h}x{w}, "
        f"n_frames={n_frames}, n_solids={n_solids}, attempted={attempted}"
    )


def _paint_solid(grid, bbox, color=6):
    r0, c0, r1, c1 = bbox
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            grid[r][c] = color


def _decoration_length(ctx, difficulty):
    if difficulty == "easy":
        return ctx.draw_choice("decoration_length", (1,))
    if difficulty == "medium":
        return ctx.draw_choice("decoration_length", (2,))
    if difficulty == "hard":
        return ctx.draw_choice("decoration_length", (3,))
    return ctx.draw_choice("decoration_length", (1, 2, 3))


def _place_decoration(ctx, grid, reserved, difficulty):
    h, w = len(grid), len(grid[0])
    length = _decoration_length(ctx, difficulty)
    color = ctx.draw_choice("decoration_color", _DECORATION_COLORS)
    candidates = []
    for r in range(h):
        for c in range(w - length + 1):
            cells = tuple((r, c + offset) for offset in range(length))
            if all(point not in reserved and grid[point[0]][point[1]] == 0 for point in cells):
                candidates.append(cells)
    if length > 1:
        for r in range(h - length + 1):
            for c in range(w):
                cells = tuple((r + offset, c) for offset in range(length))
                if all(point not in reserved and grid[point[0]][point[1]] == 0 for point in cells):
                    candidates.append(cells)
    if not candidates:
        raise RuntimeError(f"no free run of length {length} for decoration")
    cells = ctx.draw_rng("decoration_position").choice(candidates)
    for r, c in cells:
        grid[r][c] = color


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
    h, w = _draw_dimensions(ctx, sample_index, overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    scheduled_counts = {
        "multiple_frames": (2, 1),
        "extra_solids": (1, 2),
    }[profile]
    n_frames = _draw_scheduled_count(
        ctx, "n_frames", 1, 2, scheduled_counts[0], overrides
    )
    n_solids = _draw_scheduled_count(
        ctx, "n_solids", 1, 2, scheduled_counts[1], overrides
    )

    placements = _place_rectangles(
        ctx, h, w, n_frames, n_solids, difficulty
    )
    grid = full_grid(h, w, 0)
    reserved = set()
    for (kind, _), bbox in sorted(placements.items()):
        r0, c0, r1, c1 = bbox
        reserved.update(
            (r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)
        )
        if kind == "frame":
            draw_frame(grid, r0, c0, r1, c1, 6)
        else:
            _paint_solid(grid, bbox)
    _place_decoration(ctx, grid, reserved, difficulty)
    return grid


def _edge_fixture(name):
    h, w = 9, 10
    grid = full_grid(h, w, 0)
    if name == "no_frame":
        _paint_solid(grid, (2, 5, 4, 7))
    elif name == "no_solid":
        draw_frame(grid, 1, 1, 5, 4, 6)
    elif name == "both_hollow":
        draw_frame(grid, 1, 0, 4, 3, 6)
        draw_frame(grid, 1, 6, 5, 9, 6)
    else:
        raise ValueError(f"unknown edge fixture: {name!r}")
    grid[8][0] = 3
    return grid


def mutation_fixtures():
    """Named task-local impostors that self_check must reject."""
    return [("no_hollow_frame", _edge_fixture("no_frame"))]


def lawful_edge_cases():
    """Lawful but out-of-ordinary-distribution rule inputs for probes/tests."""
    return {
        "no_solid": _edge_fixture("no_solid"),
        "both_hollow": _edge_fixture("both_hollow"),
    }


def _components(grid, color=6):
    remaining = {
        (r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
        if value == color
    }
    components = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        cells = {start}
        while stack:
            r, c = stack.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in remaining:
                    remaining.remove(point)
                    cells.add(point)
                    stack.append(point)
        components.append(cells)
    return components


def _analyze(grid):
    frames, solids, invalid = [], [], []
    for cells in _components(grid):
        rows = [point[0] for point in cells]
        cols = [point[1] for point in cells]
        r0, r1, c0, c1 = min(rows), max(rows), min(cols), max(cols)
        full = {
            (r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)
        }
        border = {
            point for point in full
            if point[0] in (r0, r1) or point[1] in (c0, c1)
        }
        record = {
            "bbox": (r0, c0, r1, c1),
            "cells": cells,
            "height": r1 - r0 + 1,
            "width": c1 - c0 + 1,
        }
        if record["height"] >= 3 and record["width"] >= 3 and cells == border:
            frames.append(record)
        elif cells == full:
            solids.append(record)
        else:
            invalid.append(record)
    frames.sort(key=lambda item: item["bbox"])
    solids.sort(key=lambda item: item["bbox"])
    return {"frames": frames, "solids": solids, "invalid": invalid}


def _decoration_error(grid, rectangles):
    cells = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 6)
    ]
    colors = {value for _, _, value in cells}
    if len(colors) != 1:
        return f"expected exactly one decoration color, found {sorted(colors)}"
    if not 1 <= len(cells) <= 3:
        return f"decoration length {len(cells)} outside 1..3"
    points = {(r, c) for r, c, _ in cells}
    rows = {r for r, _ in points}
    cols = {c for _, c in points}
    straight = False
    if len(rows) == 1:
        row = next(iter(rows))
        straight = points == {(row, c) for c in range(min(cols), max(cols) + 1)}
    elif len(cols) == 1:
        col = next(iter(cols))
        straight = points == {(r, col) for r in range(min(rows), max(rows) + 1)}
    if not straight:
        return "decoration must be one contiguous horizontal or vertical line"
    for point in points:
        for record in rectangles:
            r0, c0, r1, c1 = record["bbox"]
            if r0 <= point[0] <= r1 and c0 <= point[1] <= c1:
                return "decoration must lie outside every color-6 bounding box"
    return None


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the task grammar from pixels; metadata cannot waive defects."""
    del difficulty, meta
    if (
        not isinstance(grid, (list, tuple))
        or not grid
        or not isinstance(grid[0], (list, tuple))
        or not grid[0]
    ):
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    h, w = len(grid), width
    errors = []
    if not (8 <= h <= 16 and 8 <= w <= 16):
        errors.append(f"grid dimensions {h}x{w} outside 8..16")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("cells must be integer colors 0..9 (bool is not a color)")
        return errors
    if any(value == 8 for row in grid for value in row):
        errors.append("input must not already contain output color 8")
    info = _analyze(grid)
    if info["invalid"]:
        errors.append(
            f"{len(info['invalid'])} color-6 component(s) are neither rectangular "
            "frames nor filled rectangles"
        )
    if not info["frames"]:
        errors.append("expected at least one hollow color-6 rectangular frame")
    if len(info["frames"]) > 2:
        errors.append(f"too many hollow frames: {len(info['frames'])} > 2")
    if len(info["solids"]) > 2:
        errors.append(f"too many solid rectangles: {len(info['solids'])} > 2")
    for frame in info["frames"]:
        r0, c0, r1, c1 = frame["bbox"]
        if any(grid[r][c] != 0 for r in range(r0 + 1, r1) for c in range(c0 + 1, c1)):
            errors.append("hollow frame interiors must be background in the input")
    decoration_error = _decoration_error(grid, info["frames"] + info["solids"])
    if decoration_error:
        errors.append(decoration_error)
    return errors


def observe_overrides(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe invalid grid: " + "; ".join(errors))
    info = _analyze(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_frames": len(info["frames"]),
        "n_solids": len(info["solids"]),
    }


def strict_canonical_like(grid):
    errors = list(self_check(grid))
    if errors:
        return errors
    palette_size = len({value for row in grid for value in row})
    if (len(grid), len(grid[0]), palette_size) not in {
        (h, w, 3) for h, w in _CANONICAL_DIMENSIONS
    }:
        errors.append("grid does not match a canonical size/palette profile")
    info = _analyze(grid)
    if len(info["frames"]) != 1:
        errors.append("canonical profile has exactly one hollow frame")
    if not info["solids"]:
        errors.append("canonical profile includes a solid rectangle distractor")
    return errors


def _apply_intended(grid):
    out = deepcopy(grid)
    for frame in _analyze(grid)["frames"]:
        r0, c0, r1, c1 = frame["bbox"]
        for r in range(r0 + 1, r1):
            for c in range(c0 + 1, c1):
                out[r][c] = 8
    return out


def _first_frame_only(grid):
    """Plausible canonical shortcut: transform only the first hollow frame."""
    out = deepcopy(grid)
    frames = _analyze(grid)["frames"]
    if frames:
        r0, c0, r1, c1 = frames[0]["bbox"]
        for r in range(r0 + 1, r1):
            for c in range(c0 + 1, c1):
                out[r][c] = 8
    return out


def _fill_all_rectangles(grid):
    """Wrong rule: fill strict interiors of frames and already-filled solids."""
    out = deepcopy(grid)
    info = _analyze(grid)
    for record in info["frames"] + info["solids"]:
        r0, c0, r1, c1 = record["bbox"]
        for r in range(r0 + 1, r1):
            for c in range(c0 + 1, c1):
                out[r][c] = 8
    return out


def _has_multiple_frames(grid):
    return len(_analyze(grid)["frames"]) >= 2


def _has_solid_distractor(grid):
    return bool(_analyze(grid)["solids"])


SEMANTIC_WITNESSES = {
    "multiple_frames": _has_multiple_frames,
    "solid_distractor": _has_solid_distractor,
}
SEMANTIC_RIVALS = {
    "first_frame_only": _first_frame_only,
    "fill_all_rectangles": _fill_all_rectangles,
}
WITNESS_RIVALS = {
    "multiple_frames": ["first_frame_only"],
    "solid_distractor": ["fill_all_rectangles"],
}
CANONICAL_SHORTCUTS = {"first_frame_only": _first_frame_only}
LESSON_COMPETITORS = {
    "first_frame_only": _first_frame_only,
    "fill_all_rectangles": _fill_all_rectangles,
}


def lesson_identifiable(demos, query):
    """Name any declared rival that fits all demos but changes the query."""
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        try:
            fits = all(rival(pair["input"]) == pair["output"] for pair in demos)
            changes_query = rival(query["input"]) != query["output"]
        except Exception as exc:  # malformed lesson should be loud and diagnostic
            reasons.append(f"{name} could not be evaluated: {type(exc).__name__}: {exc}")
            continue
        if fits and changes_query:
            reasons.append(
                f"{name} fits every demonstration but predicts a different query output"
            )
    return reasons
