"""Seeded Frame Fill: input distribution for the unchanged canonical Racket rule.

Every blue rectangular frame with one or more interior red markers is filled
with yellow. Marker multiplicity and other seeded frames do not change this
condition. Exterior red markers are preserved. This module generates INPUTS;
its explicitly named rivals are test hypotheses, never label authorities.

Default lessons use three consecutive profiles: single-marker frames; multiple
seeded frames with unequal marker counts; exterior markers plus an unseeded
frame. Three consecutive demonstrations refute the declared finite rival set.
Exact overrides take precedence and may remove that teaching guarantee.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, draw_frame

GENERATOR_ID = "59c2f0a5d4a9"
TASK_ID = GENERATOR_ID
RULE_HASH = "00c68f11bf7a"
VERSION = "2.0.0"
SUMMARY = "Fill every seeded blue frame; vary positive marker counts and preserve exterior red markers."

INVARIANTS = [
    "rectangular 9..20 by 9..20 integer grids with colors 0, 1 and 2",
    "2..4 disjoint nonnested complete color-1 rectangular frames with nonempty interiors",
    "frame bounding boxes have at least one intervening row or column",
    "1..4 frames contain 1..4 interior color-2 markers; other interiors contain only 0",
    "0..3 exterior color-2 markers lie outside every frame bounding box",
    "background is 0; no other colors or blue clutter are generated",
]

AXES = {
    "grid_h": {"type": "int", "default": "profile 0: 10/11/12; other profiles: 9..20", "valid": "9..20"},
    "grid_w": {"type": "int", "default": "profile 0: same canonical size; others: 9..20", "valid": "9..20"},
    "n_frames": {"type": "int", "default": "2..4, difficulty weighted", "valid": "2..4"},
    "n_seeded": {"type": "int", "default": "profiles 0/2: 1..n_frames-1; profile 1: 2..n_frames", "valid": "1..4"},
    "max_seeds_per_frame": {"type": "int", "default": "profile 0: 1; profile 1: 2..4; profile 2: 1..4", "valid": "1..4"},
    "n_outside_seeds": {"type": "int", "default": "profile 2: 1..3; otherwise 0", "valid": "0..3"},
}
_BOUNDS = {name: tuple(map(int, spec["valid"].split(".."))) for name, spec in AXES.items()}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [("n_frames", "n_seeded")]
SCHEDULE_PROFILES = ("single_marker_frames", "unequal_multiple", "exterior")
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0


class IncompatibleOverrides(ValueError):
    """A mathematically impossible combination, with machine-readable axes."""
    incompatible_axes = ("n_frames", "n_seeded")


def schedule_profile(seed, sample_index, difficulty=None):
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _axis(ctx, name, default_options):
    # Explicit controls use their FULL advertised domain in every band. Free
    # draws record their actual profile-dependent options and realized value.
    lo, hi = _BOUNDS[name]
    options = tuple(range(lo, hi + 1)) if name in ctx.overrides else tuple(default_options)
    return ctx.draw_choice(name, options)


def _spans(length, count, rng):
    """Partition an axis into >=4-cell slots separated by one background cell."""
    sizes = [4] * count
    for _ in range(length - (count - 1) - 4 * count):
        sizes[rng.randrange(count)] += 1
    spans, start = [], 0
    for size in sizes:
        spans.append((start, start + size - 1))
        start += size + 1
    return spans


def _frame_boxes(ctx, h, w, marker_counts):
    # Constructive packing has no rejection cap or fallback that can drop a
    # requested frame. Even four capacity-4 frames fit the 9x9 lower boundary.
    n = len(marker_counts)
    layouts = []
    for rows in range(1, n + 1):
        cols = (n + rows - 1) // rows
        if 4 * rows + rows - 1 <= h and 4 * cols + cols - 1 <= w:
            layouts.append((rows, cols))
    rng = ctx.draw_rng("frame_layout")
    rows, _ = rng.choice(layouts)
    row_counts = [n // rows] * rows
    for index in rng.sample(range(rows), n % rows):
        row_counts[index] += 1
    slots = []
    for (r0, r1), count in zip(_spans(h, rows, rng), row_counts):
        # Each row has its own column partition. A lone lower frame can
        # straddle the upper pair's gap, as in the canonical three-frame input.
        slots.extend((r0, c0, r1, c1) for c0, c1 in _spans(w, count, rng))
    rng.shuffle(slots)
    boxes = []
    for index, (slot, count) in enumerate(zip(slots, marker_counts)):
        r0, c0, r1, c1 = slot
        shape_rng = ctx.draw_rng(f"frame_shape_{index}")
        shapes = [(rh, rw) for rh in range(3, min(8, r1-r0+1) + 1)
                  for rw in range(3, min(8, c1-c0+1) + 1)
                  if (rh-2) * (rw-2) >= count]
        rh, rw = shape_rng.choice(shapes)
        top = shape_rng.randint(r0, r1-rh+1)
        left = shape_rng.randint(c0, c1-rw+1)
        boxes.append((top, left, top+rh-1, left+rw-1))
    return boxes


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        lo, hi = _BOUNDS[name]
        if type(value) is not int or not lo <= value <= hi:
            raise ValueError(f"{name} must be an integer in [{lo}, {hi}]")
    if overrides.get("n_seeded", 1) > overrides.get("n_frames", 4):
        raise IncompatibleOverrides("n_seeded cannot exceed n_frames")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    profile = sample_index % 3
    anchor = ctx.draw_choice("canonical_size", (10, 11, 12))
    if profile == 0:
        sizes = [anchor]
    else:
        favored = range(9, 13) if difficulty == "easy" else (range(15, 21) if difficulty == "hard" else range(11, 16))
        sizes = list(range(9, 21)) + list(favored)
    h, w = _axis(ctx, "grid_h", sizes), _axis(ctx, "grid_w", sizes)
    favored_frames = [2, 2, 3] if difficulty == "easy" else ([3, 4, 4] if difficulty == "hard" else [2, 3, 3, 4])
    frame_options = [n for n in favored_frames if n >= overrides.get("n_seeded", 1)]
    if not frame_options:
        frame_options = [overrides["n_seeded"]]
    n_frames = _axis(ctx, "n_frames", frame_options)
    seeded_options = range(2, n_frames+1) if profile == 1 else range(1, n_frames)
    n_seeded = _axis(ctx, "n_seeded", seeded_options)
    if n_seeded > n_frames:
        raise IncompatibleOverrides("n_seeded cannot exceed n_frames")
    maximum = _axis(ctx, "max_seeds_per_frame", [1] if profile == 0 else (range(2, 5) if profile == 1 else range(1, 5)))
    n_outside = _axis(ctx, "n_outside_seeds", range(1, 4) if profile == 2 else [0])
    rng = ctx.draw_rng("seed_counts")
    active_counts = [rng.randint(1, maximum) for _ in range(n_seeded)]
    active_counts[0] = maximum
    if n_seeded > 1 and maximum > 1:
        active_counts[1] = 1  # refute selection by greatest marker count
    marker_counts = active_counts + [0] * (n_frames-n_seeded)
    rng.shuffle(marker_counts)
    boxes = _frame_boxes(ctx, h, w, marker_counts)
    grid = full_grid(h, w, 0)
    for index, (box, count) in enumerate(zip(boxes, marker_counts)):
        top, left, bottom, right = box
        draw_frame(grid, top, left, bottom, right, 1)
        interior = [(r, c) for r in range(top+1, bottom) for c in range(left+1, right)]
        for r, c in ctx.draw_rng(f"marker_positions_{index}").sample(interior, count):
            grid[r][c] = 2
    exterior = [(r, c) for r in range(h) for c in range(w)
                if not any(top <= r <= bottom and left <= c <= right
                           for top, left, bottom, right in boxes)]
    for r, c in ctx.draw_rng("exterior_markers").sample(exterior, n_outside):
        grid[r][c] = 2
    return grid


def _frame_components(grid):
    """Recover color-1 components and marker counts from pixels only."""
    remaining = {(r, c) for r, row in enumerate(grid) for c, color in enumerate(row) if color == 1}
    frames = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        pending, cells = [start], {start}
        while pending:
            r, c = pending.pop()
            for p in ((r-1,c), (r+1,c), (r,c-1), (r,c+1)):
                if p in remaining:
                    remaining.remove(p)
                    cells.add(p)
                    pending.append(p)
        top, bottom = min(r for r, _ in cells), max(r for r, _ in cells)
        left, right = min(c for _, c in cells), max(c for _, c in cells)
        count = sum(grid[r][c] == 2 for r in range(top+1, bottom) for c in range(left+1, right))
        frames.append(((top, left, bottom, right), count, cells))
    return sorted(frames, key=lambda frame: frame[0])


def _inspect(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"], [], 0
    if any(not isinstance(row, (list, tuple)) for row in grid) or not grid[0]:
        return ["expected nonempty grid rows"], [], 0
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"], [], 0
    if any(type(color) is not int or color not in (0, 1, 2) for row in grid for color in row):
        return ["cells must be genuine integer colors from 0, 1, 2"], [], 0
    errors = []
    if not (9 <= h <= 20 and 9 <= w <= 20):
        errors.append("grid dimensions outside sampler domain 9..20")
    frames = _frame_components(grid)
    if not 2 <= len(frames) <= 4:
        errors.append(f"expected 2..4 blue frame components, got {len(frames)}")
    for (top, left, bottom, right), count, cells in frames:
        border = {(r, c) for r in range(top, bottom+1) for c in range(left, right+1)
                  if r in (top, bottom) or c in (left, right)}
        if bottom-top < 2 or right-left < 2 or cells != border:
            errors.append("blue component is not a complete rectangular perimeter with nonempty interior")
        if any(grid[r][c] not in (0, 2) for r in range(top+1, bottom) for c in range(left+1, right)):
            errors.append("frame interior contains blue clutter or a nested frame")
        if count > 4:
            errors.append("more than four markers in one frame")
    for index, (a, _, _) in enumerate(frames):
        for b, _, _ in frames[index+1:]:
            if not (a[2]+1 < b[0] or b[2]+1 < a[0] or a[3]+1 < b[1] or b[3]+1 < a[1]):
                errors.append("frames overlap, nest, or lack a one-cell separating gap")
    if not any(count for _, count, _ in frames):
        errors.append("at least one frame must contain an interior red marker")
    exterior = sum(color == 2 and not any(top < r < bottom and left < c < right
                   for (top, left, bottom, right), _, _ in frames)
                   for r, row in enumerate(grid) for c, color in enumerate(row))
    if exterior > 3:
        errors.append("more than three exterior red markers")
    return errors, frames, exterior


def self_check(grid, *, difficulty=None, meta=None):
    return _inspect(grid)[0]


def strict_canonical_like(grid):
    """Check the declared semantic manifold, including all canonical inputs."""
    return self_check(grid)


def observe_overrides(grid):
    errors, frames, outside = _inspect(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return {
        "grid_h": len(grid), "grid_w": len(grid[0]), "n_frames": len(frames),
        "n_seeded": sum(count > 0 for _, count, _ in frames),
        "max_seeds_per_frame": max(count for _, count, _ in frames),
        "n_outside_seeds": outside,
    }


def _paint_rival_boxes(grid, boxes):
    out = [list(row) for row in grid]
    for top, left, bottom, right in boxes:
        for r in range(top+1, bottom):
            for c in range(left+1, right):
                out[r][c] = 4
    return out


def _exactly_one_seed_per_frame(grid):
    return _paint_rival_boxes(grid, [box for box, count, _ in _frame_components(grid) if count == 1])


def _most_seeded_frames_only(grid):
    frames = _frame_components(grid)
    maximum = max((count for _, count, _ in frames), default=0)
    return _paint_rival_boxes(grid, [box for box, count, _ in frames if count and count == maximum])


def _first_seeded_only(grid):
    boxes = [box for box, count, _ in _frame_components(grid) if count]
    return _paint_rival_boxes(grid, boxes[:1])


def _fill_all_frames(grid):
    return _paint_rival_boxes(grid, [box for box, _, _ in _frame_components(grid)])


def _flood_all_seed_regions(grid):
    out = [list(row) for row in grid]
    h, w = len(grid), len(grid[0])
    reached = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2}
    pending = list(reached)
    while pending:
        r, c = pending.pop()
        for nr, nc in ((r-1,c), (r+1,c), (r,c-1), (r,c+1)):
            if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] in (0, 2) and (nr,nc) not in reached:
                reached.add((nr,nc))
                pending.append((nr,nc))
    for r, c in reached:
        out[r][c] = 4
    return out


def _multiple_seeded(grid):
    return sum(count > 0 for _, count, _ in _frame_components(grid)) > 1


def _multiple_markers(grid):
    return any(count > 1 for _, count, _ in _frame_components(grid))


def _unequal_markers(grid):
    return len({count for _, count, _ in _frame_components(grid) if count}) > 1


def _exterior_marker(grid):
    return observe_overrides(grid)["n_outside_seeds"] > 0


def _unseeded_frame(grid):
    return any(count == 0 for _, count, _ in _frame_components(grid))


CANONICAL_SHORTCUTS = {
    "exactly_one_seed_per_frame": _exactly_one_seed_per_frame,
    "most_seeded_frames_only": _most_seeded_frames_only,
    "flood_all_seed_regions": _flood_all_seed_regions,
}
LESSON_COMPETITORS = {
    **CANONICAL_SHORTCUTS,
    "first_seeded_only": _first_seeded_only,
    "fill_all_frames": _fill_all_frames,
}
SEMANTIC_RIVALS = dict(LESSON_COMPETITORS)
SEMANTIC_WITNESSES = {
    "multiple_seeded_frames": _multiple_seeded,
    "multiple_markers_in_frame": _multiple_markers,
    "unequal_positive_marker_counts": _unequal_markers,
    "exterior_red_marker": _exterior_marker,
    "unseeded_frame": _unseeded_frame,
}
WITNESS_RIVALS = {
    "multiple_seeded_frames": ["first_seeded_only"],
    "multiple_markers_in_frame": ["exactly_one_seed_per_frame"],
    "unequal_positive_marker_counts": ["most_seeded_frames_only"],
    "exterior_red_marker": ["flood_all_seed_regions"],
    "unseeded_frame": ["fill_all_frames"],
}


def lesson_identifiable(demos, query):
    """Finite-rival teaching check; does not assert universal rule induction."""
    return [f"declared rival survives demonstrations: {name}"
            for name, rival in LESSON_COMPETITORS.items()
            if all(rival(pair["input"]) == pair["output"] for pair in demos)]
