"""Generator for arc_additional_puzzle_bank_volume7:H46.

Rule: count red markers, then fill the correspondingly ranked band between
nested yellow rectangular frames with cyan.  Rank one is the band just inside
the outer frame; the last rank is the innermost frame's interior.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "819d58220317"
TASK_ID = "819d58220317"
VERSION = "4.0.0"
RULE_HASH = "0db6b727334d"

SUMMARY = (
    "A 0-background grid contains 2-5 strictly nested, disconnected yellow "
    "(4) hollow rectangular frames.  There are k red (2) markers outside the "
    "outer frame, where 1 <= k <= the number of frames.  Sort the frames from "
    "outside to inside and fill cyan (8) in the blank band immediately inside "
    "frame k but outside frame k+1; when k selects the innermost frame, fill "
    "its blank interior.  Grid dimensions, frame count and spacing, selected "
    "rank, frame placement, and marker-side layout vary."
)

INVARIANTS = [
    "exactly 2-5 disconnected yellow hollow rectangular frames",
    "frames are strictly nested with at least one blank cell between borders",
    "red marker count is a valid 1-based frame rank",
    "every red marker lies outside the outermost frame",
    "the selected band contains at least one blank cell",
    "ordinary generation always changes at least one blank cell to cyan",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-shaped, compatibility-aware",
        "valid": "11..30",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-shaped, compatibility-aware",
        "valid": "11..30",
    },
    "n_frames": {
        "type": "int",
        "default": "scheduled within the difficulty band",
        "valid": "2..5",
    },
    "rank": {
        "type": "int",
        "default": "sample-index schedule plus keyed variation",
        "valid": "1..5",
    },
    "marker_layout": {
        "type": "str",
        "default": "scheduled when rank permits",
        "valid": "single_side|multi_side",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

_DIFFICULTY_FRAME_BANDS = {
    None: (2, 5),
    "easy": (2, 3),
    "medium": (2, 4),
    "hard": (3, 5),
}
_DIFFICULTY_SIZE_BANDS = {
    None: (11, 30),
    "easy": (11, 18),
    "medium": (14, 24),
    "hard": (18, 30),
}
_MARKER_LAYOUTS = ("single_side", "multi_side")


@dataclass(frozen=True)
class _Scene:
    h: int
    w: int
    frames: tuple[tuple[int, int, int, int], ...]
    red_cells: tuple[tuple[int, int], ...]

    @property
    def rank(self) -> int:
        return len(self.red_cells)

    @property
    def selected_cells(self) -> tuple[tuple[int, int], ...]:
        return tuple(_selected_band_cells(self.frames, self.rank))


def _validate_call(difficulty, overrides) -> None:
    if difficulty not in _DIFFICULTY_FRAME_BANDS:
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for name in ("grid_h", "grid_w", "n_frames", "rank"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer")
    value = overrides.get("marker_layout")
    if value is not None and not isinstance(value, str):
        raise ValueError("marker_layout must be a string")


def _frame(grid, r0: int, c0: int, r1: int, c1: int) -> None:
    for row in range(r0, r1 + 1):
        grid[row][c0] = 4
        grid[row][c1] = 4
    for col in range(c0, c1 + 1):
        grid[r0][col] = 4
        grid[r1][col] = 4


def _frame_border(bounds: tuple[int, int, int, int]) -> set[tuple[int, int]]:
    r0, c0, r1, c1 = bounds
    return {
        (row, col)
        for row in range(r0, r1 + 1)
        for col in range(c0, c1 + 1)
        if row in (r0, r1) or col in (c0, c1)
    }


def _components(
    grid: list[list[int]], color: int
) -> list[set[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    remaining = {
        (row, col)
        for row in range(h)
        for col in range(w)
        if grid[row][col] == color
    }
    components: list[set[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        stack = [start]
        remaining.remove(start)
        component = {start}
        while stack:
            row, col = stack.pop()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                neighbor = (row + dr, col + dc)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    stack.append(neighbor)
        components.append(component)
    return components


def _component_bounds(
    component: Iterable[tuple[int, int]],
) -> tuple[int, int, int, int]:
    cells = tuple(component)
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _selected_band_cells(
    frames: Iterable[tuple[int, int, int, int]], rank: int
) -> list[tuple[int, int]]:
    ordered = tuple(frames)
    if not 1 <= rank <= len(ordered):
        return []
    r0, c0, r1, c1 = ordered[rank - 1]
    inner = ordered[rank] if rank < len(ordered) else None
    cells = []
    for row in range(r0 + 1, r1):
        for col in range(c0 + 1, c1):
            if inner is not None:
                ir0, ic0, ir1, ic1 = inner
                if ir0 <= row <= ir1 and ic0 <= col <= ic1:
                    continue
            cells.append((row, col))
    return cells


def _analyze(grid) -> tuple[_Scene | None, list[str]]:
    if not isinstance(grid, list) or not grid:
        return None, ["empty grid"]
    if not isinstance(grid[0], list) or not grid[0]:
        return None, ["empty row"]
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        return None, ["ragged grid"]
    if not (11 <= h <= 30 and 11 <= w <= 30):
        return None, [f"grid shape {h}x{w} outside lawful 11..30 envelope"]
    bad = [
        value
        for row in grid
        for value in row
        if type(value) is not int or value not in (0, 2, 4)
    ]
    if bad:
        return None, ["input colors must be exactly from {0,2,4}"]

    components = _components(grid, 4)
    if not 2 <= len(components) <= 5:
        return None, [
            f"expected 2-5 disconnected yellow frames, got {len(components)}"
        ]

    frames: list[tuple[int, int, int, int]] = []
    for component in components:
        bounds = _component_bounds(component)
        r0, c0, r1, c1 = bounds
        if r1 - r0 < 2 or c1 - c0 < 2:
            return None, [f"yellow component {bounds} is too small for a frame"]
        expected = _frame_border(bounds)
        if component != expected:
            return None, [f"yellow component {bounds} is not an exact hollow frame"]
        frames.append(bounds)
    frames.sort(
        key=lambda bounds: (
            -((bounds[2] - bounds[0] + 1) * (bounds[3] - bounds[1] + 1)),
            bounds,
        )
    )

    for outer, inner in zip(frames, frames[1:]):
        or0, oc0, or1, oc1 = outer
        ir0, ic0, ir1, ic1 = inner
        if not (
            ir0 >= or0 + 2
            and ic0 >= oc0 + 2
            and ir1 <= or1 - 2
            and ic1 <= oc1 - 2
        ):
            return None, [
                "yellow frames must be strictly nested with a blank gap"
            ]

    red_cells = tuple(
        (row, col)
        for row in range(h)
        for col in range(w)
        if grid[row][col] == 2
    )
    if not 1 <= len(red_cells) <= len(frames):
        return None, [
            f"red marker count {len(red_cells)} is not a valid frame rank"
        ]
    outer = frames[0]
    r0, c0, r1, c1 = outer
    inside = [
        cell
        for cell in red_cells
        if r0 <= cell[0] <= r1 and c0 <= cell[1] <= c1
    ]
    if inside:
        return None, ["red markers must lie outside the outermost frame"]

    selected = _selected_band_cells(frames, len(red_cells))
    blank_selected = [cell for cell in selected if grid[cell[0]][cell[1]] == 0]
    if not blank_selected:
        return None, ["selected band has no blank cell to fill"]

    return (
        _Scene(
            h=h,
            w=w,
            frames=tuple(frames),
            red_cells=red_cells,
        ),
        [],
    )


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or non-teaching nested-frame scenes."""
    del difficulty, meta
    _, errors = _analyze(grid)
    return errors


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python test mirror; Racket remains the output authority."""
    scene, errors = _analyze(grid)
    if errors or scene is None:
        raise ValueError("invalid nested-frame scene: " + "; ".join(errors))
    output = [row[:] for row in grid]
    for row, col in scene.selected_cells:
        if output[row][col] == 0:
            output[row][col] = 8
    return output


def _marker_side(row: int, col: int, h: int, w: int) -> str | None:
    # Horizontal edges take precedence at corners, matching canonical markers.
    if row == 0:
        return "top"
    if row == h - 1:
        return "bottom"
    if col == 0:
        return "left"
    if col == w - 1:
        return "right"
    return None


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every exact declared axis from a returned lawful grid."""
    scene, errors = _analyze(grid)
    if errors or scene is None:
        return {}
    sides = {
        side
        for row, col in scene.red_cells
        if (side := _marker_side(row, col, scene.h, scene.w)) is not None
    }
    if len(sides) == 1:
        marker_layout = "single_side"
    elif len(sides) >= 2:
        marker_layout = "multi_side"
    else:
        marker_layout = "margin"
    return {
        "grid_h": scene.h,
        "grid_w": scene.w,
        "n_frames": len(scene.frames),
        "rank": scene.rank,
        "marker_layout": marker_layout,
    }


def semantic_profile(grid) -> dict[str, object]:
    """Task-linked observables used by the strict distribution census."""
    scene, errors = _analyze(grid)
    if errors or scene is None:
        return {"valid": False, "errors": errors}
    observed = observe_overrides(grid)
    gaps = []
    for outer, inner in zip(scene.frames, scene.frames[1:]):
        gaps.append(
            (
                inner[0] - outer[0] - 1,
                outer[2] - inner[2] - 1,
                inner[1] - outer[1] - 1,
                outer[3] - inner[3] - 1,
            )
        )
    return {
        "valid": True,
        **observed,
        "branch": "innermost" if scene.rank == len(scene.frames) else "ring",
        "selected_blank_count": len(scene.selected_cells),
        "outer_bounds": scene.frames[0],
        "frame_bounds": scene.frames,
        "inter_frame_gaps": tuple(gaps),
        "marker_cells": scene.red_cells,
    }


def _max_frames_for_dim(size: int) -> int:
    # Minimum: one-cell outside margin on both sides, a 3-cell inner frame,
    # and two-cell bbox insets (one blank gap) per additional frame.
    return max(0, min(5, 1 + (size - 5) // 4))


def _scheduled_choice(ctx, label: str, options: tuple[int, ...], index: int) -> int:
    if not options:
        raise ValueError(f"no feasible values for {label}")
    selected = options[index % len(options)]
    return int(ctx.draw_choice(label, (selected,)))


def _choose_margins(rng, size: int, minimum_outer: int) -> tuple[int, int]:
    available = size - minimum_outer
    if available < 2:
        raise ValueError(
            f"grid dimension {size} cannot leave an outside margin around "
            f"minimum outer frame {minimum_outer}"
        )
    total = rng.randint(2, min(available, 8))
    first = rng.randint(1, total - 1)
    return first, total - first


def _choose_shrink(rng, current: int, minimum_next: int) -> tuple[int, int]:
    available = current - minimum_next
    if available < 4:
        raise ValueError("insufficient room for another disconnected frame")
    total = rng.randint(4, min(available, 8))
    first = rng.randint(2, total - 2)
    return first, total - first


def _draw_markers(
    grid: list[list[int]], rank: int, marker_layout: str, rng
) -> None:
    h, w = len(grid), len(grid[0])
    pools = {
        "top": [(0, col) for col in range(1, w - 1)],
        "bottom": [(h - 1, col) for col in range(1, w - 1)],
        "left": [(row, 0) for row in range(1, h - 1)],
        "right": [(row, w - 1) for row in range(1, h - 1)],
    }
    sides = tuple(pools)
    cells: list[tuple[int, int]] = []
    if marker_layout == "single_side":
        side = rng.choice(sides)
        cells = rng.sample(pools[side], rank)
    elif marker_layout == "multi_side":
        if rank < 2:
            raise ValueError("marker_layout='multi_side' is incompatible with rank=1")
        first, second = rng.sample(sides, 2)
        cells = [rng.choice(pools[first]), rng.choice(pools[second])]
        remaining = [
            cell
            for side in sides
            for cell in pools[side]
            if cell not in cells
        ]
        cells.extend(rng.sample(remaining, rank - 2))
    else:
        raise ValueError(f"unknown marker_layout {marker_layout!r}")
    for row, col in cells:
        grid[row][col] = 2


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    forced_h = overrides.get("grid_h")
    forced_w = overrides.get("grid_w")
    forced_frames = overrides.get("n_frames")
    forced_rank = overrides.get("rank")
    forced_layout = overrides.get("marker_layout")

    max_frames = 5
    if forced_h is not None:
        ctx.draw_int("grid_h", 11, 30)
        max_frames = min(max_frames, _max_frames_for_dim(forced_h))
    if forced_w is not None:
        ctx.draw_int("grid_w", 11, 30)
        max_frames = min(max_frames, _max_frames_for_dim(forced_w))
    minimum_frames = max(2, forced_rank or 1)
    if max_frames < minimum_frames:
        raise ValueError(
            "incompatible grid dimension/rank overrides leave no feasible "
            "nested-frame count"
        )

    if forced_frames is not None:
        n_frames = ctx.draw_int("n_frames", 2, 5)
        if not minimum_frames <= n_frames <= max_frames:
            raise ValueError(
                "incompatible n_frames override for the requested grid/rank"
            )
    else:
        band_lo, band_hi = _DIFFICULTY_FRAME_BANDS[difficulty]
        feasible = tuple(
            value
            for value in range(minimum_frames, max_frames + 1)
            if band_lo <= value <= band_hi
        )
        if not feasible:
            feasible = tuple(range(minimum_frames, max_frames + 1))
        n_frames = _scheduled_choice(
            ctx, "n_frames", feasible, int(sample_index)
        )

    if forced_rank is not None:
        rank = ctx.draw_int("rank", 1, n_frames)
    else:
        lower_rank = 2 if forced_layout == "multi_side" else 1
        if lower_rank > n_frames:
            raise ValueError("marker_layout override is incompatible with frame count")
        phase = int(sample_index) % 4
        if phase == 0:
            scheduled = 1
        elif phase == 1:
            scheduled = n_frames
        else:
            choices = tuple(range(lower_rank, n_frames + 1))
            scheduled = choices[
                ctx.draw_rng("rank_schedule").randrange(len(choices))
            ]
        if scheduled < lower_rank:
            scheduled = lower_rank
        rank = int(ctx.draw_choice("rank", (scheduled,)))

    minimum_dim = 5 + 4 * (n_frames - 1)
    size_lo, size_hi = _DIFFICULTY_SIZE_BANDS[difficulty]

    def draw_dimension(label: str, forced: int | None) -> int:
        if forced is not None:
            value = int(forced)
        else:
            lo = max(size_lo, minimum_dim)
            hi = size_hi
            if lo > hi:
                hi = 30
            value = ctx.draw_int(label, lo, hi)
        if value < minimum_dim:
            raise ValueError(
                f"{label}={value} is incompatible with n_frames={n_frames}; "
                f"minimum is {minimum_dim}"
            )
        return value

    h = draw_dimension("grid_h", forced_h)
    w = draw_dimension("grid_w", forced_w)

    if forced_layout is not None:
        marker_layout = ctx.draw_choice("marker_layout", _MARKER_LAYOUTS)
    else:
        options = (
            _MARKER_LAYOUTS
            if rank >= 2
            else ("single_side",)
        )
        preferred = options[int(sample_index) % len(options)]
        marker_layout = ctx.draw_choice("marker_layout", (preferred,))
    if marker_layout == "multi_side" and rank < 2:
        raise ValueError("marker_layout='multi_side' is incompatible with rank=1")

    rng = ctx.draw_rng("layout")
    minimum_outer = 3 + 4 * (n_frames - 1)
    top, bottom = _choose_margins(rng, h, minimum_outer)
    left, right = _choose_margins(rng, w, minimum_outer)
    r0, c0, r1, c1 = top, left, h - 1 - bottom, w - 1 - right
    frames = [(r0, c0, r1, c1)]
    for level in range(1, n_frames):
        remaining_after = n_frames - level - 1
        minimum_next = 3 + 4 * remaining_after
        dt, db = _choose_shrink(rng, r1 - r0 + 1, minimum_next)
        dl, dr = _choose_shrink(rng, c1 - c0 + 1, minimum_next)
        r0, c0, r1, c1 = r0 + dt, c0 + dl, r1 - db, c1 - dr
        frames.append((r0, c0, r1, c1))

    grid = full_grid(h, w, 0)
    for bounds in frames:
        _frame(grid, *bounds)
    _draw_markers(grid, rank, marker_layout, rng)

    errors = self_check(grid, difficulty=difficulty, meta={"overrides": overrides})
    if errors:
        raise AssertionError("generated invalid nested-frame scene: " + "; ".join(errors))
    return grid
