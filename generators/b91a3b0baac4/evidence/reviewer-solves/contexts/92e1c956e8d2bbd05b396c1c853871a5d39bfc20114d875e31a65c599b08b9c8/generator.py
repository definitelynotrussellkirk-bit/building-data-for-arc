"""Input sampler for the corner-marker beam task ``b91a3b0baac4``.

A unique nonzero corner contains a direction marker: 1=up, 2=right,
3=down, 4=left. Every other non-{0,5} cell is an emitter. Each emitter paints
its own color along that direction until a color-5 blocker or the grid edge.
The selected Racket rule remains the sole label authority; this module samples
inputs and exposes independent semantic rivals/witnesses for review gates.
"""
from __future__ import annotations

from copy import deepcopy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b91a3b0baac4"
TASK_ID = GENERATOR_ID
RULE_HASH = "46ed28101b5f"
VERSION = "4.0.0"
SUMMARY = (
    "A unique corner marker in {1,2,3,4} selects up/right/down/left. Every "
    "other non-{0,5} cell casts a same-color beam in that direction, stopping "
    "at the first color-5 blocker or the edge. Production draws contain both "
    "an active blocker and an irrelevant blocker."
)

INVARIANTS = [
    "the rectangular grid uses literal ARC colors 0..9",
    "exactly one corner is nonzero and it is a marker in {1,2,3,4}",
    "at least two non-corner emitter cells and at least one color-5 blocker exist",
    "every production draw has a blocker on an emitter ray and another upstream blocker",
]

_CORNERS = ("tl", "tr", "bl", "br")
_DIRECTIONS = (1, 2, 3, 4)

AXES = {
    "grid_h": {"type": "int", "default": "scheduled canonical/broad", "valid": "6..14"},
    "grid_w": {"type": "int", "default": "scheduled canonical/broad", "valid": "7..16"},
    "n_emitters": {"type": "int", "default": "difficulty-weighted", "valid": "4..8"},
    "n_blockers": {"type": "int", "default": "difficulty-weighted", "valid": "2..6"},
    "emitter_palette_size": {"type": "int", "default": "scheduled 2..4", "valid": "2..4"},
    "marker_corner": {"type": "str", "default": "uniform", "valid": "tl|tr|bl|br"},
    "marker_direction": {"type": "int", "default": "uniform", "valid": "1..4"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

# Five demonstrations are used by the retained shortcut finding. Every normal
# draw is itself a blocker witness, so every cyclic five-demo window refutes the
# blocker-ignoring rival even when any one sixth item is held out as query.
EXAMPLES_NEEDED = 5
SCHEDULE_PROFILES = ("canonical_6x9_palette6", "canonical_7x9_palette5", "broad")
MIN_STRICT_FRAC = 1.0


def schedule_profile(seed, sample_index, difficulty=None):
    """Deterministic profile schedule used for profile-floor auditability."""
    del seed, difficulty
    return (
        "canonical_6x9_palette6",
        "canonical_7x9_palette5",
        "canonical_6x9_palette6",
        "canonical_7x9_palette5",
        "broad",
    )[sample_index % 5]


def _validate_call(seed, sample_index, difficulty, overrides):
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer (not bool)")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    integer_ranges = {
        "grid_h": (6, 14),
        "grid_w": (7, 16),
        "n_emitters": (4, 8),
        "n_blockers": (2, 6),
        "emitter_palette_size": (2, 4),
        "marker_direction": (1, 4),
    }
    for name, (lo, hi) in integer_ranges.items():
        value = overrides.get(name)
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer (not bool)")
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo},{hi}]")
    corner = overrides.get("marker_corner")
    if corner is not None and (type(corner) is not str or corner not in _CORNERS):
        raise ValueError(f"marker_corner must be one of {_CORNERS}")


def _scheduled_int(ctx, name, lo, hi, scheduled):
    """Honor exact overrides; otherwise record the deterministic schedule value."""
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_choice(name, (scheduled,))


def _weighted_int(ctx, name, lo, hi, favored):
    options = list(range(lo, hi + 1))
    for value in favored:
        options.extend([value] * 8)
    return ctx.draw_choice(name, tuple(options))


def _profile_axes(ctx, seed, sample_index, difficulty):
    profile_name = schedule_profile(seed, sample_index, difficulty)
    if profile_name == "canonical_6x9_palette6":
        h = _scheduled_int(ctx, "grid_h", 6, 14, 6)
        w = _scheduled_int(ctx, "grid_w", 7, 16, 9)
        palette_size = _scheduled_int(ctx, "emitter_palette_size", 2, 4, 3)
    elif profile_name == "canonical_7x9_palette5":
        h = _scheduled_int(ctx, "grid_h", 6, 14, 7)
        w = _scheduled_int(ctx, "grid_w", 7, 16, 9)
        palette_size = _scheduled_int(ctx, "emitter_palette_size", 2, 4, 2)
    else:
        if difficulty == "easy":
            h = _weighted_int(ctx, "grid_h", 6, 14, (6, 7, 8))
            w = _weighted_int(ctx, "grid_w", 7, 16, (7, 8, 9, 10))
            palette_size = _weighted_int(ctx, "emitter_palette_size", 2, 4, (2,))
        elif difficulty == "hard":
            h = _weighted_int(ctx, "grid_h", 6, 14, (12, 13, 14))
            w = _weighted_int(ctx, "grid_w", 7, 16, (14, 15, 16))
            palette_size = _weighted_int(ctx, "emitter_palette_size", 2, 4, (4,))
        else:
            h = _weighted_int(ctx, "grid_h", 6, 14, (8, 9, 10, 11))
            w = _weighted_int(ctx, "grid_w", 7, 16, (9, 10, 11, 12, 13))
            palette_size = _weighted_int(ctx, "emitter_palette_size", 2, 4, (3,))
    return h, w, palette_size


def _point(direction, line, t, h, w):
    """Map beam-aligned coordinates to grid coordinates; t grows downstream."""
    if direction == 2:  # right
        return line, t
    if direction == 4:  # left
        return line, w - 1 - t
    if direction == 3:  # down
        return t, line
    if direction == 1:  # up
        return h - 1 - t, line
    raise ValueError(direction)


def _geometry(direction, h, w):
    return (h, w) if direction in (2, 4) else (w, h)


def _corner_position(name, h, w):
    return {
        "tl": (0, 0),
        "tr": (0, w - 1),
        "bl": (h - 1, 0),
        "br": (h - 1, w - 1),
    }[name]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h, w, emitter_palette_size = _profile_axes(ctx, seed, sample_index, difficulty)
    if difficulty == "easy":
        n_emitters = _weighted_int(ctx, "n_emitters", 4, 8, (4, 5))
        n_blockers = _weighted_int(ctx, "n_blockers", 2, 6, (2, 3))
    elif difficulty == "hard":
        n_emitters = _weighted_int(ctx, "n_emitters", 4, 8, (7, 8))
        n_blockers = _weighted_int(ctx, "n_blockers", 2, 6, (5, 6))
    else:
        n_emitters = _weighted_int(ctx, "n_emitters", 4, 8, (5, 6))
        n_blockers = _weighted_int(ctx, "n_blockers", 2, 6, (3, 4))
    marker_corner = ctx.draw_choice("marker_corner", _CORNERS)
    marker_direction = ctx.draw_int_strict("marker_direction", 1, 4)

    grid = full_grid(h, w, 0)
    marker_pos = _corner_position(marker_corner, h, w)
    grid[marker_pos[0]][marker_pos[1]] = marker_direction
    corners = {
        (0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)
    }
    n_lines, beam_length = _geometry(marker_direction, h, w)

    # Dedicated witness line: an emitter at t=1 sees a blocker at t=3, with
    # at least two downstream cells remaining at every declared minimum size.
    active_line = ctx.draw_rng("active_line").choice(list(range(n_lines)))
    active_emitter = _point(marker_direction, active_line, 1, h, w)
    active_blocker = _point(marker_direction, active_line, 3, h, w)
    used = {marker_pos, active_emitter, active_blocker}
    grid[active_blocker[0]][active_blocker[1]] = 5

    # All remaining blockers are upstream (t=0 or t=1) on other, non-corner
    # lines. Since all remaining emitters are placed at t>=2, these blockers
    # cannot be encountered by any beam and therefore remain informative
    # negative controls rather than accidental active blockers.
    inactive_candidates = []
    for line in range(1, n_lines - 1):
        if line == active_line:
            continue
        for t in (0, 1):
            point = _point(marker_direction, line, t, h, w)
            if point not in corners and point not in used:
                inactive_candidates.append(point)
    inactive_rng = ctx.draw_rng("inactive_blockers")
    inactive_rng.shuffle(inactive_candidates)
    needed_inactive = n_blockers - 1
    if len(inactive_candidates) < needed_inactive:
        raise RuntimeError("constructive blocker region unexpectedly too small")
    for r, c in inactive_candidates[:needed_inactive]:
        grid[r][c] = 5
        used.add((r, c))

    # Keep the witness line exclusive to its one emitter so the active blocker
    # always changes the blocker-ignoring rival's output in a transparent way.
    emitter_candidates = []
    for line in range(n_lines):
        if line == active_line:
            continue
        for t in range(2, beam_length):
            point = _point(marker_direction, line, t, h, w)
            if point not in corners and point not in used:
                emitter_candidates.append(point)
    emitter_rng = ctx.draw_rng("emitter_positions")
    emitter_rng.shuffle(emitter_candidates)
    positions = [active_emitter] + emitter_candidates[: n_emitters - 1]
    if len(positions) != n_emitters:
        raise RuntimeError("constructive emitter region unexpectedly too small")

    legal_colors = [color for color in (1, 2, 3, 4, 6, 7, 8, 9) if color != marker_direction]
    palette_rng = ctx.draw_rng("emitter_palette")
    emitter_colors = palette_rng.sample(legal_colors, emitter_palette_size)
    assigned_colors = list(emitter_colors)
    while len(assigned_colors) < n_emitters:
        assigned_colors.append(palette_rng.choice(emitter_colors))
    palette_rng.shuffle(assigned_colors)
    for (r, c), color in zip(positions, assigned_colors):
        grid[r][c] = color
    return grid


def _marker(grid):
    h, w = len(grid), len(grid[0])
    corners = ((0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1))
    hits = [(r, c, grid[r][c]) for r, c in corners if grid[r][c] in _DIRECTIONS]
    if len(hits) != 1:
        raise ValueError(f"expected one direction marker corner, found {hits}")
    return hits[0]


def _beam_output(grid, *, blockers_enabled=True):
    h, w = len(grid), len(grid[0])
    mr, mc, marker_color = _marker(grid)
    dr, dc = {1: (-1, 0), 2: (0, 1), 3: (1, 0), 4: (0, -1)}[marker_color]
    blockers = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 5}
    out = deepcopy(grid)
    for r in range(h):
        for c in range(w):
            value = grid[r][c]
            if value in (0, 5) or (r, c) == (mr, mc):
                continue
            rr, cc = r + dr, c + dc
            while 0 <= rr < h and 0 <= cc < w:
                if blockers_enabled and (rr, cc) in blockers:
                    break
                out[rr][cc] = value
                rr += dr
                cc += dc
    return out


def _active_and_inactive_blockers(grid):
    h, w = len(grid), len(grid[0])
    mr, mc, marker_color = _marker(grid)
    dr, dc = {1: (-1, 0), 2: (0, 1), 3: (1, 0), 4: (0, -1)}[marker_color]
    blockers = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 5}
    active = set()
    for r in range(h):
        for c in range(w):
            value = grid[r][c]
            if value in (0, 5) or (r, c) == (mr, mc):
                continue
            rr, cc = r + dr, c + dc
            while 0 <= rr < h and 0 <= cc < w:
                if (rr, cc) in blockers:
                    active.add((rr, cc))
                    break
                rr += dr
                cc += dc
    return active, blockers - active


def _ignore_blockers(grid):
    """Plausible wrong rule: beam through color-5 cells to the grid edge."""
    return _beam_output(grid, blockers_enabled=False)


def _mixed_blocker_witness(grid):
    try:
        active, inactive = _active_and_inactive_blockers(grid)
    except (TypeError, ValueError, IndexError):
        return False
    return bool(active and inactive)


def observe_overrides(grid):
    h, w = len(grid), len(grid[0])
    mr, mc, marker_direction = _marker(grid)
    corner = {
        (0, 0): "tl",
        (0, w - 1): "tr",
        (h - 1, 0): "bl",
        (h - 1, w - 1): "br",
    }[(mr, mc)]
    emitters = [
        grid[r][c]
        for r in range(h)
        for c in range(w)
        if (r, c) != (mr, mc) and grid[r][c] not in (0, 5)
    ]
    return {
        "grid_h": h,
        "grid_w": w,
        "n_emitters": len(emitters),
        "n_blockers": sum(value == 5 for row in grid for value in row),
        "emitter_palette_size": len(set(emitters)),
        "marker_corner": corner,
        "marker_direction": marker_direction,
    }


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    w = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return ["ragged grid"]
    h = len(grid)
    errors = []
    if not (5 <= h <= 30 and 5 <= w <= 30):
        errors.append(f"grid dimensions {h}x{w} outside lawful review bounds")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("all cells must be literal ARC color integers 0..9")
        return errors
    corners = ((0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1))
    nonzero_corners = [(r, c) for r, c in corners if grid[r][c] != 0]
    if len(nonzero_corners) != 1:
        errors.append(f"expected exactly one nonzero corner marker, found {nonzero_corners}")
        return errors
    mr, mc = nonzero_corners[0]
    if grid[mr][mc] not in _DIRECTIONS:
        errors.append("corner marker color must be one of {1,2,3,4}")
    if any(grid[r][c] == 5 for r, c in corners):
        errors.append("color-5 blockers may not occupy corners")
    emitters = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if (r, c) != (mr, mc) and grid[r][c] not in (0, 5)
    ]
    blockers = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 5]
    if len(emitters) < 2:
        errors.append("at least two emitter cells are required")
    if not blockers:
        errors.append("at least one color-5 blocker is required")
    return errors


def strict_canonical_like(grid):
    """All accepted instances exercise the same fixed corner-marker beam law."""
    return self_check(grid)


SEMANTIC_WITNESSES = {"active_and_inactive_blockers": _mixed_blocker_witness}
SEMANTIC_RIVALS = {"ignore_blockers": _ignore_blockers}
WITNESS_RIVALS = {"active_and_inactive_blockers": ["ignore_blockers"]}
LESSON_COMPETITORS = {"ignore_blockers": _ignore_blockers}
