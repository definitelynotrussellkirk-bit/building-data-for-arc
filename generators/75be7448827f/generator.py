"""Generator for selecting and cropping the frame with the most filled cells.

The canonical Racket authority detects hollow color-1 rectangles, counts every
nonzero cell in each interior, chooses the first top-left frame attaining the
largest raw count, and returns that interior crop.

Default examples alternate two constructive conflicts.  Even sample indices
make a smaller, denser loser; odd indices make a larger-area loser.  Therefore
any consecutive three demonstrations refute both "densest frame" and "largest
frame" shortcuts while retaining a unique raw-count winner.
"""
from __future__ import annotations

from collections import deque

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "75be7448827f"
TASK_ID = GENERATOR_ID
RULE_HASH = "6f03f2e69da2"
VERSION = "2.2.0"
SUMMARY = (
    "Two or three hollow color-1 frames; crop the unique raw-count winner. "
    "Alternating examples refute both density and frame-area shortcuts."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "background is 0 and every frame is an exact hollow color-1 rectangle",
    "each frame interior uses one distinct nonzero color",
    "the generated count winner is unique and contains 6-8 filled cells",
    "the runner-up has 1-2 fewer cells",
    "even samples have a denser loser; odd samples have a larger-area loser",
    "all foreground cells belong to a frame border or its interior",
]

AXES = {
    "grid_h": {"type": "int", "default": "canonical anchor every fourth default sample; otherwise difficulty-aware 13..20", "valid": "13..20"},
    "grid_w": {"type": "int", "default": "canonical anchor every fourth default sample; otherwise difficulty-aware 14..22", "valid": "14..22"},
    "n_frames": {"type": "int", "default": "3 on canonical anchors; otherwise uniform 2..3", "valid": "2..3"},
    "winner_count": {"type": "int", "default": "uniform 6..8", "valid": "6..8"},
    "count_margin": {"type": "int", "default": "uniform 1..2", "valid": "1..2"},
    "rival_kind": {"type": "enum", "default": "density on even sample indices; area on odd", "valid": "density|area"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

_RIVAL_KINDS = ("density", "area")

_AXIS_BOUNDS = {
    "grid_h": (13, 20),
    "grid_w": (14, 22),
    "n_frames": (2, 3),
    "winner_count": (6, 8),
    "count_margin": (1, 2),
}

# Three nonoverlapping 6x6 slots inside a 13x14 template. Every generated
# outer frame is at most 6x6, and the template can be translated inside larger
# requested grids without rejection sampling.
_SLOTS = (
    (0, 0, 6, 6),
    (0, 8, 6, 6),
    (7, 4, 6, 6),
)

# Exact (height, width) profiles from the five selected canonical inputs. A
# no-override sample at every fourth sample index uses one of these with three
# frames, so its palette size is also the canonical five colors (0, 1, plus
# three distinct interior colors). The remaining samples retain the broad axes.
_CANONICAL_INPUT_PROFILES = ((14, 16), (15, 17), (14, 18), (14, 17), (15, 18))


def _validate_request(sample_index, difficulty, overrides):
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(sorted(unknown))}")
    for name, value in overrides.items():
        if value is None:
            continue
        if name == "rival_kind":
            if not isinstance(value, str):
                raise TypeError("rival_kind override must be a string")
            if value not in _RIVAL_KINDS:
                raise ValueError(f"rival_kind override must be one of {_RIVAL_KINDS}")
            continue
        if type(value) is not int:
            raise TypeError(f"{name} override must be an integer (not bool)")
        lo, hi = _AXIS_BOUNDS[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name} override {value} outside [{lo}, {hi}]")


def _paint_frame(grid, r0, c0, ih, iw, color, count, rng):
    """Paint one hollow frame and exactly ``count`` colored interior cells."""
    r1, c1 = r0 + ih + 1, c0 + iw + 1
    for c in range(c0, c1 + 1):
        grid[r0][c] = 1
        grid[r1][c] = 1
    for r in range(r0, r1 + 1):
        grid[r][c0] = 1
        grid[r][c1] = 1
    interior = [(r, c) for r in range(r0 + 1, r1) for c in range(c0 + 1, c1)]
    for r, c in rng.sample(interior, count):
        grid[r][c] = color


def _reflect(grid, code):
    if code & 1:
        grid = [row[::-1] for row in grid]
    if code & 2:
        grid = [row[:] for row in grid[::-1]]
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    # With no overrides, one sample in every four anchors the exact canonical
    # (height, width, palette-size) manifold in every difficulty band. The
    # other three samples preserve the broader scale curriculum. Any explicit
    # override takes the ordinary exact-control path and is never rewritten.
    canonical_anchor = not overrides and sample_index % 4 == 0
    if canonical_anchor:
        profile = ctx.draw_choice("canonical_profile", _CANONICAL_INPUT_PROFILES)
        h = ctx.draw_choice("grid_h", (profile[0],))
        w = ctx.draw_choice("grid_w", (profile[1],))
        n_frames = ctx.draw_choice("n_frames", (3,))
    else:
        h = ctx.draw_int_diff("grid_h", 13, 20)
        w = ctx.draw_int_diff("grid_w", 14, 22)
        n_frames = ctx.draw_int_strict("n_frames", 2, 3)
    winner_count = ctx.draw_int_strict("winner_count", 6, 8)
    count_margin = ctx.draw_int_strict("count_margin", 1, 2)
    scheduled_rival = "density" if sample_index % 2 == 0 else "area"
    rival_kind = ctx.draw_choice(
        "rival_kind",
        _RIVAL_KINDS if overrides.get("rival_kind") is not None else (scheduled_rival,),
    )

    runner_up_count = winner_count - count_margin
    if rival_kind == "density":
        specs = [
            # The raw-count winner is largest, but not densest.
            {"name": "winner", "shape": (4, 4), "count": winner_count},
            {"name": "density_rival", "shape": (3, 3), "count": runner_up_count},
        ]
    else:
        specs = [
            # The raw-count winner is densest, but not largest.
            {"name": "winner", "shape": (3, 3), "count": winner_count},
            {"name": "area_rival", "shape": (4, 4), "count": runner_up_count},
        ]
    if n_frames == 3:
        third_shape = ctx.draw_rng("third_shape").choice(((3, 4), (4, 3)))
        specs.append(
            {"name": "third", "shape": third_shape, "count": runner_up_count - 1}
        )

    layout_rng = ctx.draw_rng("slot_order")
    slot_indices = layout_rng.sample(range(len(_SLOTS)), n_frames)
    layout_rng.shuffle(specs)
    colors = ctx.draw_rng("palette").sample(range(2, 10), n_frames)

    offset_rng = ctx.draw_rng("template_offset")
    base_r = offset_rng.randint(0, h - 13)
    base_c = offset_rng.randint(0, w - 14)
    grid = full_grid(h, w, 0)

    for spec, slot_index, color in zip(specs, slot_indices, colors):
        sr, sc, sh, sw = _SLOTS[slot_index]
        ih, iw = spec["shape"]
        oh, ow = ih + 2, iw + 2
        position_rng = ctx.draw_rng(f"{spec['name']}_position")
        r0 = base_r + sr + position_rng.randint(0, sh - oh)
        c0 = base_c + sc + position_rng.randint(0, sw - ow)
        _paint_frame(
            grid,
            r0,
            c0,
            ih,
            iw,
            color,
            spec["count"],
            ctx.draw_rng(f"{spec['name']}_cells"),
        )

    return _reflect(grid, ctx.draw_rng("reflection").randrange(4))


def _rectangular_grid_error(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return "expected a nonempty rectangular grid"
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return "expected a nonempty rectangular grid"
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return "ragged grid"
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return "cells must be integer colors in 0..9"
    if len(grid) > 30 or width > 30:
        return f"grid too large: {len(grid)}x{width}"
    return None


def _component(start, remaining):
    queue = deque([start])
    remaining.remove(start)
    cells = {start}
    while queue:
        r, c = queue.popleft()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nxt = (r + dr, c + dc)
            if nxt in remaining:
                remaining.remove(nxt)
                cells.add(nxt)
                queue.append(nxt)
    return cells


def _parse_frames(grid):
    """Return top-left-sorted frame records or raise ValueError."""
    grid_error = _rectangular_grid_error(grid)
    if grid_error:
        raise ValueError(grid_error)
    h, w = len(grid), len(grid[0])
    remaining = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 1}
    records = []
    while remaining:
        cells = _component(min(remaining), remaining)
        r0 = min(r for r, _ in cells)
        r1 = max(r for r, _ in cells)
        c0 = min(c for _, c in cells)
        c1 = max(c for _, c in cells)
        if r1 - r0 - 1 < 3 or c1 - c0 - 1 < 3:
            raise ValueError("each color-1 frame must have an interior at least 3x3")
        border = {
            (r, c)
            for r in range(r0, r1 + 1)
            for c in range(c0, c1 + 1)
            if r in (r0, r1) or c in (c0, c1)
        }
        if cells != border:
            raise ValueError("color-1 components must be exact hollow rectangles")
        records.append({"bbox": (r0, c0, r1, c1)})

    records.sort(key=lambda record: record["bbox"])
    if len(records) not in (2, 3):
        raise ValueError(f"expected 2 or 3 frames, found {len(records)}")

    # The canonical task contains separate frames, never nested or overlapping.
    for index, left in enumerate(records):
        ar0, ac0, ar1, ac1 = left["bbox"]
        for right in records[index + 1 :]:
            br0, bc0, br1, bc1 = right["bbox"]
            if not (ar1 < br0 or br1 < ar0 or ac1 < bc0 or bc1 < ac0):
                raise ValueError("frame bounding boxes must not overlap")

    claimed = {}
    interior_colors = []
    for record_index, record in enumerate(records):
        r0, c0, r1, c1 = record["bbox"]
        crop = [list(row[c0 + 1 : c1]) for row in grid[r0 + 1 : r1]]
        colors = {value for row in crop for value in row if value != 0}
        if len(colors) != 1 or 1 in colors:
            raise ValueError("each frame interior must use exactly one non-frame color")
        count = sum(value != 0 for row in crop for value in row)
        if count == 0:
            raise ValueError("frame interiors must contain foreground cells")
        for r in range(r0 + 1, r1):
            for c in range(c0 + 1, c1):
                if (r, c) in claimed:
                    raise ValueError("frame interiors must be disjoint")
                claimed[(r, c)] = record_index
        record.update(
            crop=crop,
            count=count,
            area=len(crop) * len(crop[0]),
            color=next(iter(colors)),
        )
        interior_colors.append(record["color"])

    if len(set(interior_colors)) != len(interior_colors):
        raise ValueError("frame interiors must use distinct colors")

    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value not in (0, 1) and (r, c) not in claimed:
                raise ValueError("foreground found outside all frame interiors")

    return records


def self_check(grid, *, difficulty=None, meta=None):
    try:
        _parse_frames(grid)
    except (TypeError, ValueError, IndexError) as exc:
        return [str(exc)]
    return []


def strict_canonical_like(grid):
    return self_check(grid)


def _largest_by_count(frames):
    # Python max is stable, matching the Racket authority's top-left tie break.
    return max(frames, key=lambda frame: frame["count"])


def _largest_by_density(frames):
    return max(frames, key=lambda frame: frame["count"] / frame["area"])


def _largest_by_area(frames):
    return max(frames, key=lambda frame: frame["area"])


def _count_crop(grid):
    return [row[:] for row in _largest_by_count(_parse_frames(grid))["crop"]]


def _highest_density(grid):
    return [row[:] for row in _largest_by_density(_parse_frames(grid))["crop"]]


def _largest_area(grid):
    return [row[:] for row in _largest_by_area(_parse_frames(grid))["crop"]]


def observe_overrides(grid):
    frames = _parse_frames(grid)
    counts = sorted((frame["count"] for frame in frames), reverse=True)
    if counts[0] == counts[1]:
        raise ValueError("generated override observation requires a unique count winner")
    count_winner = _largest_by_count(frames)["bbox"]
    density_conflict = count_winner != _largest_by_density(frames)["bbox"]
    area_conflict = count_winner != _largest_by_area(frames)["bbox"]
    if density_conflict == area_conflict:
        raise ValueError("expected exactly one generated shortcut conflict")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_frames": len(frames),
        "winner_count": counts[0],
        "count_margin": counts[0] - counts[1],
        "rival_kind": "density" if density_conflict else "area",
    }


def _count_over_density(grid):
    frames = _parse_frames(grid)
    return _largest_by_count(frames)["bbox"] != _largest_by_density(frames)["bbox"]


def _count_over_area(grid):
    frames = _parse_frames(grid)
    return _largest_by_count(frames)["bbox"] != _largest_by_area(frames)["bbox"]


def lesson_identifiable(demos, query):
    """Require demonstrations to refute both simple selection shortcuts."""
    missing = []
    for name, rival in (("highest-density", _highest_density), ("largest-area", _largest_area)):
        refuted = False
        for pair in demos:
            try:
                if rival(pair["input"]) != pair["output"]:
                    refuted = True
                    break
            except (KeyError, TypeError, ValueError):
                continue
        if not refuted:
            missing.append(f"demonstrations do not refute selecting the {name} frame")
    return missing


SEMANTIC_WITNESSES = {
    "count_over_density": _count_over_density,
    "count_over_area": _count_over_area,
}
SEMANTIC_RIVALS = {
    "highest_density": _highest_density,
    "largest_area": _largest_area,
}
WITNESS_RIVALS = {
    "count_over_density": ["highest_density"],
    "count_over_area": ["largest_area"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
