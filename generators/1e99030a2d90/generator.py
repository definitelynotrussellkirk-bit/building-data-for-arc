"""Teach the unchanged red-cardinal-center rule with explicit counterexamples.

Labels come only from the canonical Racket runtime. The Python alternatives
below are deliberately wrong, executable rivals for authoring checks.
"""
from __future__ import annotations

from functools import partial
from math import ceil, isqrt

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1e99030a2d90"
TASK_ID = GENERATOR_ID
VERSION = "2.1.0"
RULE_HASH = "54991f3f258a"
SUMMARY = (
    "Fill a blank cell with yellow 4 iff all four in-bounds cardinal neighbors "
    "are red 2. Lessons include missing arms, occupied centers, diagonal "
    "context, edge traps, and scheduled non-red arm counterexamples."
)
EXAMPLES_NEEDED = 4
LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = ("canonical_10", "color_counterexample", "canonical_11")
MIN_STRICT_FRAC = 0.3
INVARIANTS = [
    "rectangular integer ARC grid with background 0 and at least one true red-arm target",
    "only originally blank interior cells with all four red cardinal neighbors change",
    "n_diamonds is the realized number of qualifying centers, not a placement request",
    "unoverridden lessons alternate canonical 0/2 inputs and explicit color negatives",
    "default inputs refute missing-arm, isolated-template, occupied-center and edge-wrap rivals",
]
AXES = {
    "grid_h": {"type": "int", "default": "scheduled 10/11 or 10..24", "valid": "5..24"},
    "grid_w": {"type": "int", "default": "scheduled 10/11 or 10..24", "valid": "5..24"},
    "n_diamonds": {"type": "int", "default": "1..6 within available motif capacity", "valid": "1..12"},
}
# Exceptions name the actual conflicting axes; no blanket rejection exemption.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
_DIRECTIONS = ((-1, 0), (1, 0), (0, -1), (0, 1))
_NON_RED_COLORS = (1, 3, 4, 5, 6, 7, 8, 9)


def schedule_profile(seed, sample_index, difficulty=None):
    phase = sample_index % LESSON_SCHEDULE_PERIOD
    return "canonical_10" if phase == 0 else "canonical_11" if phase == 2 else "color_counterexample"


def _centers(grid):
    h, w = len(grid), len(grid[0])
    return [(r, c) for r in range(1, h - 1) for c in range(1, w - 1)
            if grid[r][c] == 0 and all(grid[r + dr][c + dc] == 2 for dr, dc in _DIRECTIONS)]


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the task domain, including canonical and extended color cases."""
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["empty or non-grid input"]
    if any(not isinstance(row, (list, tuple)) or not row for row in grid):
        return ["empty or non-sequence row"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    if not (3 <= h <= 30 and 3 <= w <= 30):
        return ["task-domain dimensions must be within 3..30"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be Python integer ARC colors 0..9, not booleans"]
    if not _centers(grid):
        return ["normal task domain requires at least one qualifying blank red-arm center"]
    return []


def strict_canonical_like(grid):
    errors = self_check(grid)
    if errors:
        return errors
    if any(value not in (0, 2) for row in grid for value in row):
        return ["extended color counterexample; outside the canonical 0/2 palette"]
    return []


def observe_overrides(grid):
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "n_diamonds": len(_centers(grid))}


def _incompatible(overrides, message):
    error = ValueError(message)
    error.incompatible_axes = tuple(sorted(overrides))
    raise error


def _dimension(ctx, name, preferred, minimum, broad, difficulty):
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int_strict(name, 5, 24)
    preferred = max(minimum, min(24, preferred))
    if not broad:
        return ctx.draw_choice(name, [preferred])
    lower = max(minimum, 10 if difficulty == "easy" else 11 if difficulty != "hard" else 14)
    return ctx.draw_choice(name, list(range(min(lower, 24), 25)))


def _starts(length, count, rng, *, touch_edges=False):
    """Randomize slack between disjoint 3-cell intervals without moving axes."""
    gaps = [0] * (count + 1)
    choices = list(range(1, count)) if touch_edges and count > 1 else list(range(count + 1))
    for _ in range(length - 3 * count):
        gaps[rng.choice(choices)] += 1
    starts, cursor = [], gaps[0]
    for index in range(count):
        starts.append(cursor)
        cursor += 3 + gaps[index + 1]
    return starts


def _put_cross(grid, center, protected, *, missing=None, arm_color=2, center_color=0):
    r, c = center
    grid[r][c] = center_color
    protected.add((r, c))
    for index, (dr, dc) in enumerate(_DIRECTIONS):
        grid[r + dr][c + dc] = 0 if index == missing else arm_color
        protected.add((r + dr, c + dc))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown or retired override(s): {sorted(unknown)}; supported axes: {sorted(AXES)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be a Python integer, not a boolean or coerced value")
        lo, hi = (1, 12) if name == "n_diamonds" else (5, 24)
        if value is not None and not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside {lo}..{hi}")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    mixed = schedule_profile(seed, sample_index, difficulty) == "color_counterexample"
    extras = 7 if mixed else 6
    requested = overrides.get("n_diamonds")
    required = requested or 1
    desired_slots = required + extras
    max_h, max_w = overrides.get("grid_h") or 24, overrides.get("grid_w") or 24
    if (max_h // 3) * (max_w // 3) < required:
        _incompatible(overrides, "grid_h/grid_w cannot fit n_diamonds disjoint 3x3 motifs")
    anchor = 10 if sample_index % 4 == 0 else 11
    if requested is not None:
        side = isqrt(desired_slots)
        if side * side < desired_slots:
            side += 1
        anchor = max(anchor, 3 * side)
    minimum_h = max(5, 3 * ceil(required / (max_w // 3)))
    preferred_h = max(anchor, min(24, 3 * ceil(desired_slots / (max_w // 3))))
    h = _dimension(ctx, "grid_h", preferred_h, minimum_h, mixed, difficulty)
    minimum_w = max(5, 3 * ceil(required / (h // 3)))
    preferred_w = max(anchor, min(24, 3 * ceil(desired_slots / (h // 3))))
    w = _dimension(ctx, "grid_w", preferred_w, minimum_w, mixed, difficulty)
    capacity = (h // 3) * (w // 3)
    if requested is not None:
        count = ctx.draw_int_strict("n_diamonds", 1, 12)
    else:
        spare = capacity - extras
        ceiling = min(6 if difficulty == "hard" else 4 if difficulty != "easy" else 3,
                      max(1, spare), 12)
        count = ctx.draw_choice("n_diamonds", list(range(1, ceiling + 1)))
    if count > capacity:
        _incompatible(overrides, "grid_h/grid_w cannot fit n_diamonds disjoint 3x3 motifs")

    # Tiny/dense explicit overrides remain exact but can fit fewer teaching cues.
    complete = capacity >= count + extras and h // 3 >= 2
    rng = ctx.draw_rng("motif_placement")
    row_starts = _starts(h, h // 3, rng, touch_edges=complete)
    column_starts = _starts(w, w // 3, rng)
    slots = [(r + 1, c + 1) for r in row_starts for c in column_starts]
    rng.shuffle(slots)
    grid = full_grid(h, w, 0)
    protected = set()
    if complete:
        column = rng.choice(column_starts) + 1
        first = (1, column)
        edge_slot = (h - 2, column)
        slots.remove(first)
        slots.remove(edge_slot)
        targets = [first] + [slots.pop() for _ in range(count - 1)]
        # The bottom false center has three red in-bounds arms and a fourth
        # red arm only under wrapping. Its counterpart at the top is a target.
        for point in ((h - 3, column), (h - 2, column),
                      (h - 1, column - 1), (h - 1, column + 1)):
            grid[point[0]][point[1]] = 2
        protected.update((r, c) for r in range(h - 3, h) for c in range(column - 1, column + 2))
    else:
        targets = [slots.pop() for _ in range(count)]
    for center in targets:
        _put_cross(grid, center, protected)
    r, c = rng.choice(targets)
    dr, dc = rng.choice(((-1, -1), (-1, 1), (1, -1), (1, 1)))
    grid[r + dr][c + dc] = 2
    protected.add((r + dr, c + dc))
    for missing in range(4):
        if slots:
            _put_cross(grid, slots.pop(), protected, missing=missing)
    if slots:
        _put_cross(grid, slots.pop(), protected, center_color=2)
    if mixed and slots:
        # A production episode keeps its family seed while advancing indices.
        # Latch the foreign color to that seed so a query never introduces a
        # color whose role its demonstrations did not establish. Record the
        # deterministic palette schedule through the normal keyed-draw API.
        color = ctx.draw_choice("non_red_arms", [_NON_RED_COLORS[seed % len(_NON_RED_COLORS)]])
        _put_cross(grid, slots.pop(), protected, arm_color=color)

    # Free-position red clutter joins/extends motifs while preserving targets
    # and reserved negative evidence. It is not an advertised exact control.
    candidates = [(r, c) for r in range(h) for c in range(w)
                  if (r, c) not in protected and grid[r][c] == 0]
    rng.shuffle(candidates)
    noise_budget = rng.randint(0, 2 if difficulty == "easy" else 8 if difficulty != "hard" else 16)
    added = 0
    for r, c in candidates:
        if added >= noise_budget:
            break
        grid[r][c] = 2
        if len(_centers(grid)) != count:
            grid[r][c] = 0
        else:
            added += 1
    if rng.choice((False, True)):
        grid = grid[::-1]
    if rng.choice((False, True)):
        grid = [row[::-1] for row in grid]
    if len(_centers(grid)) != count:
        raise RuntimeError("motif construction changed the exact qualifying-center count")
    return grid


def _rival(grid, mode):
    """Deliberately wrong alternatives; never supply generation labels."""
    h, w = len(grid), len(grid[0])
    result = [list(row) for row in grid]
    for r in range(h):
        for c in range(w):
            interior = 0 < r < h - 1 and 0 < c < w - 1
            if mode != "wrap_edges" and not interior:
                continue
            if mode != "ignore_center" and grid[r][c] != 0:
                continue
            arms = [grid[(r + dr) % h][(c + dc) % w] for dr, dc in _DIRECTIONS]
            if mode == "any_nonzero_arms":
                match = all(value != 0 for value in arms)
            elif mode == "warm_arms":
                match = all(value in (2, 4, 7, 9) for value in arms)
            elif mode.startswith("red_or_"):
                match = all(value in (2, int(mode.rsplit("_", 1)[1])) for value in arms)
            elif mode == "three_red_arms":
                match = sum(value == 2 for value in arms) >= 3
            elif mode.startswith("omit_"):
                omitted = {"omit_up": 0, "omit_down": 1, "omit_left": 2, "omit_right": 3}[mode]
                match = all(value == 2 for i, value in enumerate(arms) if i != omitted)
            else:
                match = all(value == 2 for value in arms)
                if mode == "isolated_template":
                    match = match and all(grid[r + dr][c + dc] == 0
                                          for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1)))
            if match:
                result[r][c] = 4
    return result


def _has_feature(grid, feature):
    h, w = len(grid), len(grid[0])
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            arms = [grid[r + dr][c + dc] for dr, dc in _DIRECTIONS]
            if feature.startswith("missing_"):
                missing = {"missing_up": 0, "missing_down": 1, "missing_left": 2, "missing_right": 3}[feature]
                if grid[r][c] == 0 and arms[missing] != 2 and all(v == 2 for i, v in enumerate(arms) if i != missing):
                    return True
            elif feature == "diagonal_context":
                if grid[r][c] == 0 and all(v == 2 for v in arms) and any(
                        grid[r + dr][c + dc] != 0 for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1))):
                    return True
            elif feature == "occupied_center":
                if grid[r][c] not in (0, 4) and all(v == 2 for v in arms):
                    return True
            elif feature == "foreign_arms":
                if grid[r][c] == 0 and all(v != 0 for v in arms) and any(v != 2 for v in arms):
                    return True
            elif feature == "warm_foreign_arms":
                if grid[r][c] == 0 and all(v in (2, 4, 7, 9) for v in arms) and any(v != 2 for v in arms):
                    return True
    if feature == "boundary_trap":
        return any(grid[r][c] == 0 and all(grid[(r + dr) % h][(c + dc) % w] == 2
                                         for dr, dc in _DIRECTIONS)
                   for r in range(h) for c in range(w) if r in (0, h - 1) or c in (0, w - 1))
    return False


SEMANTIC_RIVALS = {name: partial(_rival, mode=name) for name in (
    "isolated_template", "any_nonzero_arms", "ignore_center", "wrap_edges",
    "three_red_arms", "omit_up", "omit_down", "omit_left", "omit_right", "warm_arms")}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS.update({f"red_or_{color}": partial(_rival, mode=f"red_or_{color}")
                          for color in _NON_RED_COLORS})
WITNESS_RIVALS = {
    "diagonal_context": ["isolated_template"],
    "foreign_arms": ["any_nonzero_arms"],
    "warm_foreign_arms": ["warm_arms"],
    "occupied_center": ["ignore_center"],
    "boundary_trap": ["wrap_edges"],
    "missing_up": ["omit_up", "three_red_arms"],
    "missing_down": ["omit_down", "three_red_arms"],
    "missing_left": ["omit_left", "three_red_arms"],
    "missing_right": ["omit_right", "three_red_arms"],
}
SEMANTIC_WITNESSES = {name: partial(_has_feature, feature=name) for name in WITNESS_RIVALS}


def lesson_identifiable(demos, query):
    """Finite declared-rival check over actual supplied reference labels."""
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"{name} fits every demonstration but changes the query answer")
    return reasons
